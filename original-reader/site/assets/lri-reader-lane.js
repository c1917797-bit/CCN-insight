// One replaceable read lane. A lane owns no records, rendering, or shared-provider cache.
// Cancellation fences non-abortable providers; it does not claim to stop their transport.
export function createReaderLane({timeoutMs=15000}={}) {
  if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new RangeError('Positive finite read timeout required');
  let current=null,closed=false;
  function cancel(reason=new DOMException('Read superseded','AbortError')) {
    current?.abort(reason);
  }
  function run(work) {
    if(closed)return Promise.reject(new DOMException('Reader disposed','AbortError'));
    if(typeof work!=='function')return Promise.reject(new TypeError('Read callback required'));
    cancel();
    const controller=new AbortController();current=controller;
    return new Promise((resolve,reject)=>{
      let done=false,timer;
      const finish=(error,value)=>{
        if(done)return;done=true;clearTimeout(timer);
        controller.signal.removeEventListener('abort',aborted);
        if(current===controller)current=null;
        error?reject(error):resolve(value);
      };
      const aborted=()=>finish(controller.signal.reason||new DOMException('Aborted','AbortError'));
      controller.signal.addEventListener('abort',aborted,{once:true});
      timer=setTimeout(()=>controller.abort(new DOMException('Reader deadline exceeded','TimeoutError')),timeoutMs);
      // Attach a rejection handler even when work ignores cancellation.
      Promise.resolve().then(()=>{
        controller.signal.throwIfAborted();
        return work(controller.signal);
      }).then(value=>{
        if(controller.signal.aborted)aborted();else finish(null,value);
      },error=>finish(error));
    });
  }
  return Object.freeze({run,cancel,dispose(){closed=true;cancel();},get pending(){return current!==null;}});
}

// Validate declarative navigation before a filename is assigned to a player.
export function validateSceneManifest(value) {
  if(!value||!Array.isArray(value.scenes)||value.scenes.length>32)throw new Error('Invalid scene manifest');
  const ids=new Set();
  for(const item of value.scenes){
    if(!item||typeof item.id!=='string'||!item.id||ids.has(item.id)||!item.locales)throw new Error('Invalid or duplicate scene');
    ids.add(item.id);
    for(const lang of ['zh','en']){
      const choice=item.locales[lang];
      if(!choice)continue; // A missing translation is a visible local diagram error, not a data error.
      if(typeof choice.title!=='string'||typeof choice.file!=='string'||!/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.svg$/.test(choice.file))throw new Error('Invalid scene file');
      const box=typeof choice.mobile_viewbox==='string'?choice.mobile_viewbox.trim().split(/[ ,]+/).map(Number):[];
      if(box.length!==4||!box.every(Number.isFinite)||box[2]<=0||box[3]<=0)throw new Error('Invalid mobile scene bounds');
    }
  }
  return value;
}

