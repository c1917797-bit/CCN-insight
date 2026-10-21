// DOM-independent evidence transport. This cache is disposable, never fact authority.
// Browser and Node tests execute the same implementation.
export const HOSTED_BOOTSTRAP = '<script src="/__mcpgit/ui/bootstrap.js" defer></script>';
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', {fatal:true, ignoreBOM:true});

function error(code, message=code) {
  const e = new Error(message);
  e.name = code === 'ABORTED' ? 'AbortError' : code === 'TIMEOUT' ? 'TimeoutError' : 'EvidenceError';
  e.code = code;
  return e;
}
function aborted(signal) { if (signal?.aborted) throw signal.reason || error('ABORTED'); }
export function sourceIdentity(d) {
  if (!d || typeof d.path !== 'string' || !d.path || /[\\%?#:\x00-\x20]/.test(d.path) ||
      d.path.split('/').some(p => !p || p === '.' || p === '..') ||
      !['html','md'].includes(d.kind) || !d.path.endsWith('.'+d.kind) ||
      !/^[a-f0-9]{64}$/.test(d.sha256) || !Number.isSafeInteger(d.bytes) || d.bytes < 0) {
    throw error('DESCRIPTOR', 'Invalid evidence source descriptor');
  }
  return JSON.stringify([d.path, d.kind, d.sha256, d.bytes]);
}
export async function sha256(bytes) {
  return Array.from(new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', bytes)),
    b => b.toString(16).padStart(2,'0')).join('');
}
export async function verifyEvidenceBytes(d, bytes, digest=sha256) {
  sourceIdentity(d);
  let text, actual = await digest(bytes);
  if (actual === d.sha256) {
    if (bytes.byteLength !== d.bytes) throw error('INTEGRITY');
    return decoder.decode(bytes);
  }
  // Only one exact, documented transport wrapper is removable. Never strip arbitrary HTML.
  if (d.kind === 'html') {
    text = decoder.decode(bytes);
    if (text.split(HOSTED_BOOTSTRAP).length === 2) {
      text = text.replace(HOSTED_BOOTSTRAP, '');
      const original = encoder.encode(text);
      if (original.byteLength === d.bytes && await digest(original) === d.sha256) return text;
    }
  }
  throw error('INTEGRITY', 'Source bytes differ from the pinned catalog');
}
async function boundedBody(response, limit, signal) {
  if (!response.body?.getReader) {
    const bytes = new Uint8Array(await response.arrayBuffer());
    aborted(signal);
    if (bytes.byteLength > limit) throw error('SIZE_LIMIT');
    return bytes;
  }
  const reader = response.body.getReader(), chunks = [];
  let total = 0;
  try {
    while (true) {
      aborted(signal);
      const {done, value} = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > limit) throw error('SIZE_LIMIT', 'Evidence response exceeds its declared size');
      chunks.push(value);
    }
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk,offset); offset += chunk.byteLength; }
    return bytes;
  } catch (e) {
    await reader.cancel(e).catch(()=>{});
    throw e;
  } finally { reader.releaseLock(); }
}
function raceAbort(promise, signal) {
  return new Promise((resolve,reject) => {
    const cancel = () => reject(signal.reason || error('ABORTED'));
    if (signal.aborted) { promise.catch(()=>{}); cancel(); return; }
    signal.addEventListener('abort', cancel, {once:true});
    promise.then(resolve,reject).finally(()=>signal.removeEventListener('abort',cancel));
  });
}

export function createEvidenceSourceStore({baseURL, fetcher=globalThis.fetch, digest=sha256,
  concurrency=4, timeoutMs=15000, maxCacheBytes=4*1024*1024, maxDocumentBytes=2*1024*1024,
  maxEntries=256}={}) {
  const base = new URL(baseURL);
  if (!['http:','https:'].includes(base.protocol) || !base.pathname.endsWith('/') || base.search || base.hash || base.username || base.password) throw error('BASE_URL');
  for (const v of [concurrency,timeoutMs,maxCacheBytes,maxDocumentBytes,maxEntries]) {
    if (!Number.isSafeInteger(v) || v < 1) throw error('CONFIG');
  }
  const cache = new Map(), flights = new Map();
  let catalog=null, queue=[], running=0, retainedBytes=0;
  const counters={requests:0,cacheHits:0,coalesced:0,peakActive:0};
  function check(d) {
    const key=sourceIdentity(d);
    if (d.bytes>maxDocumentBytes) throw error('SIZE_LIMIT');
    if (catalog && !catalog.has(key)) throw error('STALE_CATALOG');
    return key;
  }
  function removeCache(key) {
    const item=cache.get(key);
    if (item) { retainedBytes-=item.cost; cache.delete(key); }
  }
  function remember(key,text) {
    // Charge retained UTF-16 text, not compressed transfer size.
    const cost=text.length*2;
    if (cost>maxCacheBytes) return;
    removeCache(key);
    while (cache.size && (cache.size>=maxEntries || retainedBytes+cost>maxCacheBytes)) removeCache(cache.keys().next().value);
    cache.set(key,{text,cost});retainedBytes+=cost;
  }
  function peek(d) {
    const key=check(d), item=cache.get(key);
    if (!item) return undefined;
    cache.delete(key);cache.set(key,item);
    return item.text;
  }
  function settle(f,issue,text) {
    if (f.settled) return;
    f.settled=true;clearTimeout(f.timer);
    if (flights.get(f.key)===f) flights.delete(f.key);
    for (const waiter of [...f.waiters]) waiter.finish(issue,text);
  }
  function cancelFlight(f,issue=error('ABORTED')) {
    f.controller.abort(issue);
    queue=queue.filter(q=>q!==f);
    settle(f,issue);
  }
  async function transfer(f) {
    const {d,controller}=f, signal=controller.signal;
    aborted(signal);
    const url=new URL(d.path,base);
    if (url.origin!==base.origin || !url.pathname.startsWith(base.pathname)) throw error('SOURCE_SCOPE');
    url.searchParams.set('source',d.sha256);
    counters.requests++;
    const response=await fetcher(url,{credentials:'same-origin',cache:'no-cache',signal});
    if (!response.ok) throw error('HTTP', `HTTP ${response.status}: ${d.path}`);
    if (response.url && new URL(response.url).origin!==base.origin) throw error('SOURCE_SCOPE');
    const extra=d.kind==='html'?encoder.encode(HOSTED_BOOTSTRAP).byteLength:0;
    const bytes=await boundedBody(response,d.bytes+extra,signal);
    const text=await verifyEvidenceBytes(d,bytes,digest);
    aborted(signal);
    if (catalog && !catalog.has(f.key)) throw error('STALE_CATALOG');
    remember(f.key,text);
    return text;
  }
  function drain() {
    while (running<concurrency && queue.length) {
      const f=queue.shift();if(f.settled||!f.waiters.size)continue;
      f.started=true;running++;counters.peakActive=Math.max(counters.peakActive,running);
      f.timer=setTimeout(()=>f.controller.abort(error('TIMEOUT','Evidence read timed out')),timeoutMs);
      raceAbort(transfer(f),f.controller.signal).then(text=>settle(f,null,text),issue=>settle(f,issue))
        .finally(()=>{running--;drain();});
    }
  }
  function read(d,{signal}={}) {
    let key;
    try {aborted(signal);key=check(d);}catch(e){return Promise.reject(e);}
    const cached=peek(d);
    if (cached!==undefined) {counters.cacheHits++;return Promise.resolve(cached);}
    let f=flights.get(key);
    if (!f) {
      f={key,d:{...d},controller:new AbortController(),waiters:new Set(),started:false,settled:false};
      flights.set(key,f);queue.push(f);
    } else counters.coalesced++;
    const promise=new Promise((resolve,reject)=>{
      const waiter={finish(issue,text){
        if (!f.waiters.delete(waiter)) return;
        signal?.removeEventListener('abort',onAbort);
        issue?reject(issue):resolve(text);
      }};
      const onAbort=()=>{
        waiter.finish(signal.reason||error('ABORTED'));
        // One consumer cannot cancel another consumer's foreground or search read.
        if (!f.waiters.size) cancelFlight(f);
      };
      f.waiters.add(waiter);signal?.addEventListener('abort',onAbort,{once:true});
      if(signal?.aborted)onAbort();
    });
    queueMicrotask(drain);
    return promise;
  }
  function setCatalog(documents) {
    const next=new Set(),paths=new Set();
    for(const d of documents) {
      const key=sourceIdentity(d);
      if(d.bytes>maxDocumentBytes||paths.has(d.path))throw error('CATALOG');
      paths.add(d.path);next.add(key);
    }
    catalog=next;
    for(const key of cache.keys())if(!next.has(key))removeCache(key);
    for(const f of [...flights.values()])if(!next.has(f.key))cancelFlight(f,error('STALE_CATALOG'));
  }
  return Object.freeze({read,peek,setCatalog,
    evict(d){const key=sourceIdentity(d);removeCache(key);const f=flights.get(key);if(f)cancelFlight(f);},
    abortAll(){for(const f of [...flights.values()])cancelFlight(f);},
    stats(){return {...counters,active:running,queued:queue.length,inflight:flights.size,entries:cache.size,retainedBytes};}
  });
}
