// Generated UI assets only; no HTML, table responses, credentials, or business facts.
const CACHE="lri-cloud-ui-a9e0d8b4a067c790";
const ASSETS={"../../assets/insight-executive.css?v=lri-content-contract-v11-compression-foundations":"7b57ab655c581343cebfe036d132a7f3c6996321b658e88ff552475d867db11f","../../assets/lri-shell.js?v=lri-shell-v18-cloud-report-navigation":"a841a5453eecfcb73e2f2835d3e839fc3acd2f180ee0b3c5449bcc5c9a6bc759","reader-entry.js?v=reader-content-f0d5a725082d2c01":"f0d5a725082d2c0138ade72d2cbb7d938107ec931f4956e857764c98b78b81ee","topic-entry.js?v=reader-content-e0eaf508132f3fd7":"e0eaf508132f3fd739f89c980ed46200978d6e807f5a5e29c051826cb11dbff2"};
'use strict';
// A strict immutable UI-code cache. Permission checks and all TableGit data stay on the network.
const allowed=new Map(Object.entries(ASSETS).map(([path,digest])=>[new URL(path,self.registration.scope).href,digest]));
function assetKey(request){return request.method==='GET'&&new URL(request.url).origin===self.location.origin&&allowed.has(request.url)?request.url:null;}
async function verified(response,key){if(!response.ok||response.redirected)return false;const bytes=await response.clone().arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');return hash===allowed.get(key);}
async function refresh(key){const response=await fetch(key,{credentials:'same-origin',cache:'no-store'});if(await verified(response,key))(await caches.open(CACHE)).put(key,response.clone());return response;}
self.addEventListener('install',event=>event.waitUntil(Promise.all([...allowed.keys()].map(key=>refresh(key).catch(()=>{}))).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('lri-cloud-ui-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const key=assetKey(event.request);if(!key)return;event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(cached=>cached||refresh(key)));});

