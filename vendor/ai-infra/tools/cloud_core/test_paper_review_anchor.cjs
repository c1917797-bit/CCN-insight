'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('business_insight/cloud_core/paper-review.js','utf8');
const code=source.slice(source.indexOf('function scrollReviewTarget(){'),source.indexOf('function reset(){'));
function fixture(canceled=false){
 let now=0,y=1000,ready=false,hidden=false;const timers=[],scrolls=[];
 const navigation={hash:'#supplementary-paper-reviews',canceled};
 const target={closest:()=>hidden?{}:null,getBoundingClientRect:()=>({top:y-sandbox.window.scrollY}),querySelector:()=>({})};
 const sandbox={performance:{now:()=>now},location:{hash:navigation.hash},LRICloudInitialNavigation:navigation,setTimeout:f=>timers.push(f),
 document:{addEventListener:()=>{},querySelector:selector=>selector==='lri-site-shell'?({shadowRoot:{querySelector:()=>({getBoundingClientRect:()=>({bottom:64})})}}):null,getElementById:id=>id==='supplementary-paper-reviews'?target:id==='monthly-route-report'?{querySelector:()=>ready?{}:null}:null},
 window:{scrollY:0,scrollTo:o=>{scrolls.push(o.top);sandbox.window.scrollY=o.top;}}};
 vm.createContext(sandbox);vm.runInContext(code,sandbox);
 return {sandbox,navigation,scrolls,setY:v=>y=v,setHidden:v=>hidden=v,setReady:()=>ready=true,step:ms=>{now+=ms;const work=timers.splice(0);work.forEach(f=>f());}};
}
const f=fixture();f.sandbox.settleInitialAnchor();f.step(900);assert.equal(f.scrolls.length,0,'no alignment before upper content is ready');
f.setY(2000);f.setReady();f.step(150);f.step(700);assert.deepEqual(f.scrolls,[1916],'wait for stable layout and leave header clearance');
f.setY(2500);f.step(150);f.step(700);assert.deepEqual(f.scrolls,[1916,2416],'late content layout is corrected while untouched');
f.navigation.canceled=true;f.setY(3000);f.step(800);assert.equal(f.scrolls.length,2,'never pull the reader back after user interaction');
const untouched=fixture(true);untouched.sandbox.settleInitialAnchor();untouched.step(900);assert.equal(untouched.scrolls.length,0);
const changed=fixture();changed.sandbox.settleInitialAnchor();changed.sandbox.location.hash='#view-topics';changed.setReady();changed.step(1000);assert.equal(changed.scrolls.length,0);
const hidden=fixture();hidden.setHidden(true);hidden.setReady();hidden.sandbox.settleInitialAnchor();hidden.step(900);assert.equal(hidden.scrolls.length,0);hidden.setHidden(false);hidden.step(150);hidden.step(700);assert.deepEqual(hidden.scrolls,[916],'a temporarily hidden router panel must not end the anchor watcher');
const crypto=require('node:crypto'),base='business_insight/cloud_core/';
for(const page of ['index.html','monthly.html','topic.html']){
 const html=fs.readFileSync(base+page,'utf8'),url=html.match(/data-lri-reader="([^"]+)"/)[1],bundle=url.split('?')[0],hash=crypto.createHash('sha256').update(fs.readFileSync(base+bundle)).digest('hex').slice(0,16);
 assert.equal(url,bundle+'?v=reader-content-'+hash,'every consumer must address its exact bundle, bypassing a previously installed immutable-cache worker');
 assert.notEqual(url,bundle+'?v=reader-content-v180-paper-review');
}
console.log(JSON.stringify({pass:true,tests:10,fixture_only:true,stable_initial_anchor:true,user_scroll_respected:true}));
