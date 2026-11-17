// Generated UI assets only; no HTML, table responses, credentials, or business facts.
const CACHE="lri-cloud-ui-3a008f4e7d9591e0";
const ASSETS={"../../assets/insight-executive.css?v=lri-content-contract-v11-compression-foundations":"7b57ab655c581343cebfe036d132a7f3c6996321b658e88ff552475d867db11f","../../assets/lri-shell.js?v=lri-shell-v18-cloud-report-navigation":"a40a085fb62f864e65a96585d910015a1a318d760e4d07c02ae4604a713a6fe1","reader-entry.js?v=reader-content-9c12f4de6cd7b195":"9c12f4de6cd7b1951d6518e78ca7af8b41a2561d2cb65225148f9ab39763a231","topic-entry.js?v=reader-content-d71e55d0f01a4f77":"d71e55d0f01a4f77a683eefc94c6746056bc3852555f91b7b7b5a361b10225e8"};
'use strict';
// A strict immutable UI-code cache. Permission checks and all TableGit data stay on the network.
const allowed=new Map(Object.entries(ASSETS).map(([path,digest])=>[new URL(path,self.registration.scope).href,digest]));
function assetKey(request){return request.method==='GET'&&new URL(request.url).origin===self.location.origin&&allowed.has(request.url)?request.url:null;}
async function verified(response,key){if(!response.ok||response.redirected)return false;const bytes=await response.clone().arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');return hash===allowed.get(key);}
async function refresh(key){const response=await fetch(key,{credentials:'same-origin',cache:'no-store'});if(await verified(response,key))(await caches.open(CACHE)).put(key,response.clone());return response;}
self.addEventListener('install',event=>event.waitUntil(Promise.all([...allowed.keys()].map(key=>refresh(key).catch(()=>{}))).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('lri-cloud-ui-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const key=assetKey(event.request);if(!key)return;event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(cached=>cached||refresh(key)));});

