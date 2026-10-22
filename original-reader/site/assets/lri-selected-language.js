/** Read-only projection of the existing LRI Shell language choice.
 * Does not set document language, persist preferences or control player state.
 */
const eventChoices = new WeakMap();
export const SELECTED_LANGUAGE_EVENT = 'lri:locale-change';

export function normalizeSelectedLanguage(value) {
  if (typeof value !== 'string') return null;
  const match = /^(en|zh)(?:-[a-z0-9]+)*$/i.exec(value.trim());
  return match ? match[1].toLowerCase() : null;
}

export function readSelectedLanguage(doc = globalThis.document) {
  // Shell is the owner. documentElement.lang may deliberately describe source prose.
  const shell = normalizeSelectedLanguage(doc?.querySelector?.('lri-site-shell')?.locale);
  if (shell) return shell;
  const choice = doc && eventChoices.get(doc);
  if (choice) return choice;
  try {
    const storage = doc?.defaultView?.localStorage ?? globalThis.localStorage;
    const saved = normalizeSelectedLanguage(storage?.getItem('lri_locale'));
    if (saved) return saved;
  } catch { /* Storage may be disabled; the Shell/event still works. */ }
  return normalizeSelectedLanguage(doc?.documentElement?.lang) || 'zh';
}

export function subscribeSelectedLanguage(listener, options = {}) {
  if (typeof listener !== 'function') throw new TypeError('A language listener is required');
  const { document: doc = globalThis.document, immediate = true, signal } = options;
  if (signal?.aborted) return () => {};
  const win = doc?.defaultView ?? globalThis;
  let selected = readSelectedLanguage(doc), disposed = false;
  const notify = () => {
    const next = readSelectedLanguage(doc);
    if (!disposed && next !== selected) { selected = next; listener(next); }
  };
  const fromShell = event => {
    const next = normalizeSelectedLanguage(event.detail?.locale);
    if (!next || !doc) return;
    eventChoices.set(doc, next);
    notify();
  };
  const fromStorage = event => { if (event.key === 'lri_locale' || event.key === null) notify(); };
  const Observer = win.MutationObserver ?? globalThis.MutationObserver;
  const observer = doc?.documentElement && typeof Observer === 'function' ? new Observer(notify) : null;
  function dispose() {
    if (disposed) return;
    disposed = true;
    doc?.removeEventListener?.(SELECTED_LANGUAGE_EVENT, fromShell);
    win.removeEventListener?.('pageshow', notify);
    win.removeEventListener?.('storage', fromStorage);
    signal?.removeEventListener('abort', dispose);
    observer?.disconnect();
  }
  doc?.addEventListener?.(SELECTED_LANGUAGE_EVENT, fromShell);
  win.addEventListener?.('pageshow', notify);
  win.addEventListener?.('storage', fromStorage);
  observer?.observe(doc.documentElement, { attributes: true, attributeFilter: ['lang'] });
  signal?.addEventListener('abort', dispose, { once: true });
  if (immediate) {
    try { listener(selected); } catch (error) { dispose(); throw error; }
  }
  return dispose;
}

