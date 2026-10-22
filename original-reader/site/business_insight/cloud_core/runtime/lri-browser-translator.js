import { protectText, restoreText } from './lri-translation-core.js';
export { protectText, restoreText } from './lri-translation-core.js';

const PROVIDER_SCHEMA = 'lri.browser-native-translator/v1';

function now() {
  return globalThis.performance?.now?.() ?? Date.now();
}

function normalizeLanguage(value) {
  return String(value || '').trim();
}

function runtimeInfo() {
  return {
    user_agent: globalThis.navigator?.userAgent || '',
    platform: globalThis.navigator?.platform || '',
    secure_context: Boolean(globalThis.isSecureContext),
    top_level: typeof window !== 'undefined' && window.top === window,
  };
}

function errorInfo(error) {
  return {
    name: error?.name || 'Error',
    message: error?.message || String(error),
  };
}

export async function probe({ sourceLanguage, targetLanguage }) {
  const source = normalizeLanguage(sourceLanguage);
  const target = normalizeLanguage(targetLanguage);
  const base = {
    schema: PROVIDER_SCHEMA,
    provider: 'browser-native',
    source_language: source,
    target_language: target,
    runtime: runtimeInfo(),
    api_present: typeof globalThis.Translator !== 'undefined',
  };
  if (!base.api_present) return { ...base, state: 'unsupported', availability: 'unavailable' };
  try {
    const availability = await globalThis.Translator.availability({ sourceLanguage: source, targetLanguage: target });
    return { ...base, state: availability === 'unavailable' ? 'unsupported_pair' : 'probed', availability };
  } catch (error) {
    return { ...base, state: 'probe_failed', availability: 'unknown', error: errorInfo(error) };
  }
}

async function createTranslator({ sourceLanguage, targetLanguage, progress }) {
  const started = now();
  try {
    const session = await globalThis.Translator.create({
      sourceLanguage,
      targetLanguage,
      monitor(monitor) {
        monitor.addEventListener('downloadprogress', (event) => {
          progress.push({
            elapsed_ms: Math.round((now() - started) * 10) / 10,
            loaded: Number(event.loaded),
            total: Number(event.total),
          });
        });
      },
    });
    return { state: 'ready', session, create_ms: now() - started };
  } catch (error) {
    return { state: 'create_failed', error: errorInfo(error), create_ms: now() - started };
  }
}

export async function translateBatch({ sourceLanguage, targetLanguage, items, protectedTerms = [] }) {
  const source = normalizeLanguage(sourceLanguage);
  const target = normalizeLanguage(targetLanguage);
  const requestItems = Array.isArray(items) ? items : [];
  const apiPresent = typeof globalThis.Translator !== 'undefined';
  const result = {
    schema: PROVIDER_SCHEMA,
    provider: 'browser-native',
    source_language: source,
    target_language: target,
    translation_status: 'machine_draft',
    runtime: runtimeInfo(),
    availability: 'unknown',
    state: apiPresent ? 'creating' : 'unsupported',
    download_progress: [],
    items: [],
  };
  if (!apiPresent) return result;

  // Keep create() as the first awaited browser-AI action in the translation
  // gesture. A cold model download may require transient user activation.
  const created = await createTranslator({
    sourceLanguage: source,
    targetLanguage: target,
    progress: result.download_progress,
  });
  result.create_ms = Math.round(created.create_ms * 10) / 10;
  if (created.state !== 'ready') {
    result.state = 'create_failed';
    result.error = created.error;
    try {
      result.availability = await globalThis.Translator.availability({ sourceLanguage: source, targetLanguage: target });
    } catch (_) {}
    return result;
  }

  result.state = 'ready';
  result.availability = 'available';
  const session = created.session;
  try {
    // Chromium documents one Translator session as sequential. Keep this loop
    // intentionally serial; speed comes from delta jobs and translation memory.
    for (const item of requestItems) {
      const id = String(item?.id ?? '');
      const sourceText = String(item?.text ?? '');
      const { protectedText, tokens } = protectText(sourceText, protectedTerms);
      const started = now();
      try {
        const raw = await session.translate(protectedText);
        const restored = restoreText(raw, tokens);
        result.items.push({
          id,
          source_text: sourceText,
          translated_text: restored.text,
          status: restored.missing.length ? 'invalid_protected_tokens' : 'machine_draft',
          missing_protected_tokens: restored.missing,
          elapsed_ms: Math.round((now() - started) * 10) / 10,
        });
      } catch (error) {
        result.items.push({ id, source_text: sourceText, status: 'translate_failed', error: errorInfo(error) });
      }
    }
  } finally {
    session.destroy?.();
  }
  result.state = result.items.every((item) => item.status === 'machine_draft') ? 'translated' : 'partial';
  return result;
}

globalThis.LRIBrowserTranslator = Object.freeze({ probe, protectText, restoreText, translateBatch });


