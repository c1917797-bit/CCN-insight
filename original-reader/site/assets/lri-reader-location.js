// Pure URL state helpers; no DOM, global listener, storage or research narrative.
export function readReaderLocation(href,{views,defaultView,aliases={}}) {
  const url=new URL(href), allowed=new Set(views);
  if(!allowed.has(defaultView))throw new Error('Reader default view is not registered');
  let hash='';try{hash=decodeURIComponent(url.hash.slice(1));}catch{}
  const requested=url.searchParams.get('view');
  const view=allowed.has(requested)?requested:(allowed.has(aliases[hash])?aliases[hash]:defaultView);
  const chosen=url.searchParams.get('lang');
  return {view,doc:url.searchParams.get('doc')||'',anchor:url.searchParams.get('anchor')||'',
    q:url.searchParams.get('q')||'',locale:chosen==='zh'||chosen==='en'?chosen:null};
}
export function patchReaderURL(href,patch) {
  const url=new URL(href);
  for(const key of ['view','doc','anchor','q','lang']) {
    if(!Object.hasOwn(patch,key))continue;
    const value=patch[key];
    if(value===null||value==='')url.searchParams.delete(key);
    else {
      if(typeof value!=='string'||(key==='lang'&&!['zh','en'].includes(value)))throw new Error('Invalid reader URL state');
      url.searchParams.set(key,value);
    }
  }
  if(Object.hasOwn(patch,'view')||Object.hasOwn(patch,'doc')||Object.hasOwn(patch,'anchor'))url.hash='';
  return url;
}

