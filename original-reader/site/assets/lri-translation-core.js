const CORE_SCHEMA = 'lri.translation-core/v1';

export function normalizeLocale(value) {
  const raw = String(value || '').trim().toLowerCase().replace('_', '-');
  if (raw === 'zh-cn' || raw === 'zh-hans' || raw === 'chinese') return 'zh';
  if (raw === 'en-us' || raw === 'en-gb' || raw === 'english') return 'en';
  return raw || 'en';
}

export function googleLocale(value) {
  const locale = normalizeLocale(value);
  return locale === 'zh' ? 'zh-CN' : locale;
}

function tokenPattern(terms = []) {
  const escapedTerms = terms
    .filter(Boolean)
    .map((term) => String(term).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .sort((a, b) => b.length - a.length);
  const parts = [
    'https?:\\/\\/[^\\s<>()]+',
    '`[^`]+`',
    '\\$\\{[^}]+\\}',
    '\\{\\{[^}]+\\}\\}',
    '\\{[A-Za-z0-9_.:-]+\\}',
    '%(?:\\d+\\$)?[sdif]',
    '\\bv?\\d+\\.\\d+(?:\\.\\d+)*(?:[-+][A-Za-z0-9_.-]+)?\\b',
  ];
  if (escapedTerms.length) parts.push(...escapedTerms);
  return new RegExp(parts.join('|'), 'g');
}

export function protectText(text, protectedTerms = []) {
  const tokens = [];
  const protectedText = String(text).replace(tokenPattern(protectedTerms), (value) => {
    const marker = `⟦LRI_${String(tokens.length).padStart(4, '0')}⟧`;
    tokens.push({ marker, value });
    return marker;
  });
  return { protectedText, tokens };
}

export function restoreText(text, tokens) {
  let restored = String(text);
  const missing = [];
  for (const token of tokens) {
    if (!restored.includes(token.marker)) {
      missing.push(token.marker);
      continue;
    }
    restored = restored.split(token.marker).join(token.value);
  }
  return { text: restored, missing };
}

export function explicitFieldPatch(row, field, locale) {
  const patches = row?.[`${field}_i18n`];
  if (!patches || typeof patches !== 'object' || Array.isArray(patches)) return null;
  const target = normalizeLocale(locale);
  // Storage uses both BCP-47 (zh-CN) and historical short (zh) keys.
  // Resolve aliases here, once, instead of duplicating locale rules in views.
  const values = Object.entries(patches)
    .filter(([key, value]) => normalizeLocale(key) === target && typeof value === 'string' && value.trim())
    .map(([, value]) => value);
  const unique = [...new Set(values)];
  if (unique.length > 1) throw new Error(`conflicting locale aliases for ${field}:${target}`);
  return unique[0] ?? null;
}

export async function googleRemoteTranslate(text, sourceLanguage, targetLanguage, protectedTerms = [], fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== 'function') throw new Error('fetch is unavailable in this JavaScript runtime');
  const { protectedText, tokens } = protectText(text, protectedTerms);
  const params = new URLSearchParams({ client: 'gtx', sl: googleLocale(sourceLanguage), tl: googleLocale(targetLanguage), dt: 't', q: protectedText });
  const response = await fetchImpl(`https://translate.googleapis.com/translate_a/single?${params}`, { mode: 'cors', credentials: 'omit' });
  if (!response.ok) throw new Error(`google remote translation failed: ${response.status}`);
  const payload = await response.json();
  const segments = Array.isArray(payload?.[0]) ? payload[0] : [];
  const translated = segments.filter((segment) => Array.isArray(segment) && typeof segment[0] === 'string').map((segment) => segment[0]).join('').trim();
  if (!translated) throw new Error('google remote translation returned no text');
  const restored = restoreText(translated, tokens);
  if (restored.missing.length) throw new Error(`google remote translation lost protected tokens: ${restored.missing.join(',')}`);
  return restored.text;
}

export async function translateText(text, {
  sourceLanguage,
  targetLanguage,
  explicitTranslation = null,
  protectedTerms = [],
  cache = null,
  googleProvider = googleRemoteTranslate,
  fallbackProvider = null,
} = {}) {
  const source = normalizeLocale(sourceLanguage);
  const target = normalizeLocale(targetLanguage);
  const sourceText = String(text ?? '');
  if (target === source) return { schema: CORE_SCHEMA, text: sourceText, provider: 'source', status: 'source' };
  if (typeof explicitTranslation === 'string' && explicitTranslation.length) {
    return { schema: CORE_SCHEMA, text: explicitTranslation, provider: 'explicit', status: 'explicit' };
  }
  if (cache?.read) {
    const cached = await cache.read({ sourceLanguage: source, targetLanguage: target, text: sourceText });
    if (typeof cached === 'string') return { schema: CORE_SCHEMA, text: cached, provider: 'cache', status: 'automatic' };
  }
  try {
    const translated = await googleProvider(sourceText, source, target, protectedTerms);
    await cache?.write?.({ sourceLanguage: source, targetLanguage: target, text: sourceText, translatedText: translated, provider: 'google-remote-free' });
    return { schema: CORE_SCHEMA, text: translated, provider: 'google-remote-free', status: 'automatic' };
  } catch (googleError) {
    if (!fallbackProvider) {
      return { schema: CORE_SCHEMA, text: sourceText, provider: null, status: 'unavailable', errors: [String(googleError?.message || googleError)] };
    }
    try {
      const fallback = await fallbackProvider({ text: sourceText, sourceLanguage: source, targetLanguage: target, protectedTerms, googleError });
      const translated = typeof fallback === 'string' ? fallback : fallback?.text;
      if (!translated) throw new Error('fallback provider returned no text');
      const provider = typeof fallback === 'object' && fallback?.provider ? fallback.provider : 'fallback';
      await cache?.write?.({ sourceLanguage: source, targetLanguage: target, text: sourceText, translatedText: translated, provider });
      return { schema: CORE_SCHEMA, text: translated, provider, status: 'automatic' };
    } catch (fallbackError) {
      return { schema: CORE_SCHEMA, text: sourceText, provider: null, status: 'unavailable', errors: [String(googleError?.message || googleError), String(fallbackError?.message || fallbackError)] };
    }
  }
}

export async function resolveField(row, field, targetLanguage, options = {}) {
  const sourceLanguage = normalizeLocale(options.sourceLanguage || row?.source_language || 'en');
  const sourceText = row?.[field];
  if (typeof sourceText !== 'string') return { schema: CORE_SCHEMA, text: sourceText, provider: 'source', status: 'non_string' };
  if (sourceLanguage === normalizeLocale(targetLanguage)) {
    return { schema: CORE_SCHEMA, text: sourceText, provider: 'source', status: 'source' };
  }
  let explicitTranslation;
  try { explicitTranslation = explicitFieldPatch(row, field, targetLanguage); }
  catch (error) {
    // Conflicting curated text must never silently fall through to a machine provider.
    return { schema: CORE_SCHEMA, text: sourceText, provider: null, status: 'unavailable', errors: [String(error.message || error)] };
  }
  return translateText(sourceText, {
    ...options,
    sourceLanguage,
    targetLanguage,
    explicitTranslation,
  });
}

globalThis.LRITranslationCore = Object.freeze({ normalizeLocale, googleLocale, protectText, restoreText, explicitFieldPatch, googleRemoteTranslate, translateText, resolveField });

