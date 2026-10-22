// Generated UI assets only; no HTML, table responses, credentials, or business facts.
const CACHE="lri-cloud-ui-8e276b94044d250a";
const ASSETS={"../../assets/insight-executive.css?v=lri-content-contract-v11-compression-foundations":"4a755026164c9c6075d0702dc41847db797fd4175e6cf44f9ae05d06e5c62c71","../../assets/lri-shell.js?v=lri-shell-v18-cloud-report-navigation":"93d81b1f93dacd9f3650495fcdc21fc3b7eb7824f683543a973c52af720b8471","reader-entry.js?v=reader-content-8e9c1b522d32cda7":"8e9c1b522d32cda7c0d2f3e3f3eadfbd4d2450c7b293dc7c44a1137c6ae799b2","topic-entry.js?v=reader-content-d1140db05b204943":"d1140db05b204943d370b80a8a2147515989d3846ddca32792d024ac2760baa2"};
'use strict';
// A strict immutable UI-code cache. Permission checks and all TableGit data stay on the network.
const allowed=new Map(Object.entries(ASSETS).map(([path,digest])=>[new URL(path,self.registration.scope).href,digest]));
function assetKey(request){return request.method==='GET'&&new URL(request.url).origin===self.location.origin&&allowed.has(request.url)?request.url:null;}
async function verified(response,key){if(!response.ok||response.redirected)return false;const bytes=await response.clone().arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');return hash===allowed.get(key);}
async function refresh(key){const response=await fetch(key,{credentials:'same-origin',cache:'no-store'});if(await verified(response,key))(await caches.open(CACHE)).put(key,response.clone());return response;}
self.addEventListener('install',event=>event.waitUntil(Promise.all([...allowed.keys()].map(key=>refresh(key).catch(()=>{}))).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('lri-cloud-ui-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const key=assetKey(event.request);if(!key)return;event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(cached=>cached||refresh(key)));});

