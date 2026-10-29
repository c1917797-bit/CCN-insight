// Generated UI assets only; no HTML, table responses, credentials, or business facts.
const CACHE="lri-cloud-ui-91b10a92cfeb8211";
const ASSETS={"../../assets/insight-executive.css?v=lri-content-contract-v11-compression-foundations":"7b57ab655c581343cebfe036d132a7f3c6996321b658e88ff552475d867db11f","../../assets/lri-shell.js?v=lri-shell-v18-cloud-report-navigation":"23a712ebdf5b6609ec97c12cf4b028ea8bc7460862664ad16c19f7bb9d978b5a","reader-entry.js?v=reader-content-d45b974badbc9b1f":"d45b974badbc9b1f5d5ea1a2ab442a7d52f8cf65cb7a2e25269b66ec3236b9de","topic-entry.js?v=reader-content-c2819de77a9f14ec":"c2819de77a9f14ec452ead0073cf2719e10112385f8f11fd77e12292c50c2351"};
'use strict';
// A strict immutable UI-code cache. Permission checks and all TableGit data stay on the network.
const allowed=new Map(Object.entries(ASSETS).map(([path,digest])=>[new URL(path,self.registration.scope).href,digest]));
function assetKey(request){return request.method==='GET'&&new URL(request.url).origin===self.location.origin&&allowed.has(request.url)?request.url:null;}
async function verified(response,key){if(!response.ok||response.redirected)return false;const bytes=await response.clone().arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');return hash===allowed.get(key);}
async function refresh(key){const response=await fetch(key,{credentials:'same-origin',cache:'no-store'});if(await verified(response,key))(await caches.open(CACHE)).put(key,response.clone());return response;}
self.addEventListener('install',event=>event.waitUntil(Promise.all([...allowed.keys()].map(key=>refresh(key).catch(()=>{}))).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('lri-cloud-ui-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const key=assetKey(event.request);if(!key)return;event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(cached=>cached||refresh(key)));});

