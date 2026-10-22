import { normalizeLocale, translateText as translateCoreText, resolveField as resolveCoreField } from './lri-translation-core.js';
import { translateBatch as translateBrowserNative } from './lri-browser-translator.js';

const CACHE_PREFIX = 'lri.translation.v1:';
const RUNTIME_SCHEMA = 'lri.translation-runtime/v1';
const DEFAULT_TRANSLATION_CONCURRENCY = 8;
const MAX_TRANSLATION_CONCURRENCY = 12;
const BROWSER_NATIVE_FALLBACK_CONCURRENCY = 3;
let browserNativeActive = 0;
const browserNativeWaiters = [];
const SKIP_SELECTOR = 'script,style,code,pre,svg,math,textarea,input,select,option,[data-lri-no-translate]';
const PRIORITY_SELECTOR = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', '[role="heading"]', 'summary',
  '[data-i18n-en]', '[data-i18n-zh]', '[data-domain-title]', '[data-domain-period]',
  '.page-title', '.report-title', '.section-title', '.card-title',
  '.expert-banner b', '.expert-banner span', '.official-domain-heading',
].join(',');
const STRUCTURAL_EXPLICIT_SELECTOR = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', '[role="heading"]', 'summary',
  '.page-title', '.report-title', '.section-title', '.card-title',
  '.expert-banner b', '.expert-banner span', '.official-domain-heading',
].join(',');
let documentEpoch = 0;
const sourceTextByNode = new WeakMap();
const sourceTextByExplicitElement = new WeakMap();

function hashText(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

function cacheKey(sourceLanguage, targetLanguage, text) {
  return `${CACHE_PREFIX}${normalizeLocale(sourceLanguage)}:${normalizeLocale(targetLanguage)}:${hashText(text)}`;
}

function readCache(sourceLanguage, targetLanguage, text) {
  try {
    const raw = localStorage.getItem(cacheKey(sourceLanguage, targetLanguage, text));
    if (!raw) return null;
    const entry = JSON.parse(raw);
    if (entry?.source_text !== text) return null;
    return typeof entry.translated_text === 'string' ? entry.translated_text : null;
  } catch (_) { return null; }
}

function writeCache(sourceLanguage, targetLanguage, text, translatedText, provider) {
  try {
    localStorage.setItem(cacheKey(sourceLanguage, targetLanguage, text), JSON.stringify({
      schema: RUNTIME_SCHEMA,
      source_language: normalizeLocale(sourceLanguage),
      target_language: normalizeLocale(targetLanguage),
      source_text: text,
      translated_text: translatedText,
      provider,
    }));
  } catch (_) {}
}

export function sourceLanguageForDocument(doc = document) {
  return normalizeLocale(doc.documentElement?.dataset?.sourceLang || doc.documentElement?.lang || 'en');
}

function browserCache() {
  return {
    read({ sourceLanguage, targetLanguage, text }) { return readCache(sourceLanguage, targetLanguage, text); },
    write({ sourceLanguage, targetLanguage, text, translatedText, provider }) { writeCache(sourceLanguage, targetLanguage, text, translatedText, provider); },
  };
}

async function withBrowserNativeSlot(task) {
  if (browserNativeActive >= BROWSER_NATIVE_FALLBACK_CONCURRENCY) {
    await new Promise((resolve) => browserNativeWaiters.push(resolve));
  }
  browserNativeActive += 1;
  try { return await task(); }
  finally {
    browserNativeActive -= 1;
    browserNativeWaiters.shift()?.();
  }
}

async function browserNativeFallback({ text, sourceLanguage, targetLanguage, protectedTerms }) {
  return withBrowserNativeSlot(async () => {
    const native = await translateBrowserNative({ sourceLanguage, targetLanguage, protectedTerms, items: [{ id: 'text', text }] });
    const item = native.items?.[0];
    if (item?.status !== 'machine_draft' || !item.translated_text) throw new Error(native.error?.message || item?.error?.message || native.state || 'browser-native unavailable');
    return { text: item.translated_text, provider: 'browser-native' };
  });
}

export async function translateText(text, options = {}) {
  return translateCoreText(text, { ...options, cache: browserCache(), fallbackProvider: browserNativeFallback });
}

export async function resolveField(row, field, targetLanguage, options = {}) {
  return resolveCoreField(row, field, targetLanguage, { ...options, cache: browserCache(), fallbackProvider: browserNativeFallback });
}

function explicitElementPatch(element, locale) {
  const value = element.getAttribute?.(`data-i18n-${normalizeLocale(locale)}`);
  return typeof value === 'string' && value.length ? value : null;
}

function shouldSkipTextNode(node) {
  return !node.parentElement || Boolean(node.parentElement.closest(SKIP_SELECTOR));
}

function originalText(node) {
  if (!sourceTextByNode.has(node)) sourceTextByNode.set(node, node.nodeValue || '');
  return sourceTextByNode.get(node);
}

function collectTextNodes(root) {
  if (!root) return [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!originalText(node).trim() || shouldSkipTextNode(node)) continue;
    nodes.push(node);
  }
  return nodes;
}

function isPriorityTextNode(node) {
  return Boolean(node.parentElement?.closest(PRIORITY_SELECTOR));
}

function explicitElements(scope) {
  if (!scope) return [];
  const selector = '[data-i18n-en],[data-i18n-zh]';
  const result = scope.matches?.(selector) ? [scope] : [];
  result.push(...scope.querySelectorAll(selector));
  return result;
}

function applyExplicitElements(scope, target, source, report) {
  const applied = new Set();
  explicitElements(scope).forEach((element) => {
    if (element.children.length && !element.matches(STRUCTURAL_EXPLICIT_SELECTOR)) return;
    if (!sourceTextByExplicitElement.has(element)) sourceTextByExplicitElement.set(element, element.textContent || '');
    const sourceText = explicitElementPatch(element, source) ?? sourceTextByExplicitElement.get(element);
    const translatedText = explicitElementPatch(element, target);
    const value = target === source ? sourceText : translatedText;
    if (typeof value !== 'string' || !value.length) return;
    if (element.textContent !== value) element.textContent = value;
    applied.add(element);
    report.explicit += 1;
  });
  return applied;
}

function containedByExplicit(node, applied) {
  for (const element of applied) if (element.contains(node)) return true;
  return false;
}

async function mapLimit(items, limit, mapper) {
  let next = 0;
  async function worker() {
    while (true) {
      const index = next++;
      if (index >= items.length) return;
      await mapper(items[index], index);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
}

export async function applyDocumentLocale(targetLanguage, { root = document.querySelector('main') || document.body, priorityRoot = document.body, sourceLanguage = sourceLanguageForDocument(document), protectedTerms = [], concurrency = DEFAULT_TRANSLATION_CONCURRENCY } = {}) {
  const epoch = ++documentEpoch;
  const source = normalizeLocale(sourceLanguage);
  const target = normalizeLocale(targetLanguage);
  const report = { schema: RUNTIME_SCHEMA, source_language: source, target_language: target, explicit: 0, automatic: 0, unavailable: 0, priority_nodes: 0 };
  if (!root) return report;
  const priorityScope = priorityRoot || root;
  const appliedExplicit = applyExplicitElements(priorityScope, target, source, report);
  const priorityNodes = collectTextNodes(priorityScope).filter((node) => isPriorityTextNode(node) && !containedByExplicit(node, appliedExplicit));
  const prioritySet = new Set(priorityNodes);
  const regularNodes = collectTextNodes(root).filter((node) => !prioritySet.has(node) && !containedByExplicit(node, appliedExplicit));
  const normalLimit = Math.max(1, Math.min(MAX_TRANSLATION_CONCURRENCY, Number(concurrency) || DEFAULT_TRANSLATION_CONCURRENCY));
  const applyNode = async (node) => {
    if (epoch !== documentEpoch) return;
    const sourceText = originalText(node);
    const result = await translateText(sourceText, { sourceLanguage: source, targetLanguage: target, protectedTerms });
    if (epoch !== documentEpoch) return;
    node.nodeValue = result.text;
    if (result.status === 'explicit') report.explicit += 1;
    else if (result.status === 'automatic') report.automatic += 1;
    else if (result.status === 'unavailable') report.unavailable += 1;
  };
  await mapLimit(priorityNodes, MAX_TRANSLATION_CONCURRENCY, applyNode);
  if (epoch !== documentEpoch) return report;
  report.priority_nodes = priorityNodes.length + appliedExplicit.size;
  await mapLimit(regularNodes, normalLimit, applyNode);
  return report;
}

export function automaticTranslationEnabled(doc = document) {
  return doc.documentElement?.dataset?.lriAutoTranslate === 'true';
}

globalThis.LRITranslation = Object.freeze({ applyDocumentLocale, automaticTranslationEnabled, resolveField, sourceLanguageForDocument, translateText });


