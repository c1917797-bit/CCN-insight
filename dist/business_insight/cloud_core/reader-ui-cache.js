// Generated UI assets only; no HTML, table responses, credentials, or business facts.
const CACHE="lri-cloud-ui-82ac2ba1e91a08bb";
const ASSETS={"../../assets/insight-executive.css?v=lri-content-contract-v11-compression-foundations":"7b57ab655c581343cebfe036d132a7f3c6996321b658e88ff552475d867db11f","../../assets/lri-shell.js?v=lri-shell-v18-cloud-report-navigation":"a841a5453eecfcb73e2f2835d3e839fc3acd2f180ee0b3c5449bcc5c9a6bc759","reader-entry.js?v=reader-content-a6ce540b50619d68":"a6ce540b50619d6851f34ae1659bc94c32edbb11bbfbc3f1e931eb994c3da9b3","topic-entry.js?v=reader-content-fd4d19dc2b04384c":"fd4d19dc2b04384cac2672f8a5eb05532bcb55c23a4a37f298b7c531b27e72ef"};
'use strict';
// A strict immutable UI-code cache. Permission checks and all TableGit data stay on the network.
const allowed=new Map(Object.entries(ASSETS).map(([path,digest])=>[new URL(path,self.registration.scope).href,digest]));
function assetKey(request){return request.method==='GET'&&new URL(request.url).origin===self.location.origin&&allowed.has(request.url)?request.url:null;}
async function verified(response,key){if(!response.ok||response.redirected)return false;const bytes=await response.clone().arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');return hash===allowed.get(key);}
async function refresh(key){const response=await fetch(key,{credentials:'same-origin',cache:'no-store'});if(await verified(response,key))(await caches.open(CACHE)).put(key,response.clone());return response;}
self.addEventListener('install',event=>event.waitUntil(Promise.all([...allowed.keys()].map(key=>refresh(key).catch(()=>{}))).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('lri-cloud-ui-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const key=assetKey(event.request);if(!key)return;event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(cached=>cached||refresh(key)));});

