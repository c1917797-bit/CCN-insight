// Generated UI assets only; no HTML, table responses, credentials, or business facts.
const CACHE="lri-cloud-ui-64c24bb1e5d47bb5";
const ASSETS={"../../assets/insight-executive.css?v=lri-content-contract-v11-compression-foundations":"7b57ab655c581343cebfe036d132a7f3c6996321b658e88ff552475d867db11f","../../assets/lri-shell.js?v=lri-shell-v18-cloud-report-navigation":"616c07f4c5f09c572da3baa0d6288e63a8169e023d4501b49fc46e1c72caf871","reader-entry.js?v=reader-content-80661fa000c45be1":"80661fa000c45be18783ff5ae9c081bb9655c821a2cad5ddab6f9eebd3094f65","topic-entry.js?v=reader-content-fc5012eb05a923ab":"fc5012eb05a923ab04e3f94d34e9f19824b1d2f0aecd343196b09beb1e01d16e"};
'use strict';
// A strict immutable UI-code cache. Permission checks and all TableGit data stay on the network.
const allowed=new Map(Object.entries(ASSETS).map(([path,digest])=>[new URL(path,self.registration.scope).href,digest]));
function assetKey(request){return request.method==='GET'&&new URL(request.url).origin===self.location.origin&&allowed.has(request.url)?request.url:null;}
async function verified(response,key){if(!response.ok||response.redirected)return false;const bytes=await response.clone().arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');return hash===allowed.get(key);}
async function refresh(key){const response=await fetch(key,{credentials:'same-origin',cache:'no-store'});if(await verified(response,key))(await caches.open(CACHE)).put(key,response.clone());return response;}
self.addEventListener('install',event=>event.waitUntil(Promise.all([...allowed.keys()].map(key=>refresh(key).catch(()=>{}))).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('lri-cloud-ui-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const key=assetKey(event.request);if(!key)return;event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(cached=>cached||refresh(key)));});

