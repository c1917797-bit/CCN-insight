'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
const selection=code.slice(code.indexOf('function selectScientificFocus('),code.indexOf('function openScientificFocus('));
const reader=code.slice(code.indexOf('async function startCurrentReader('),code.indexOf('async function start(',code.indexOf('async function startCurrentReader(')));
async function run(topic,mapped=true){
 const state={epoch:1,focusTarget:'old',focusMechanism:'old',focusCells:['old']},calls=[],renders=[],persist=[];
 const groups={profiles:[{payload_zh:{title:'Fixture'},payload_en:{title:'Fixture'}}],objects:Array.from({length:7},()=>({})),methods:Array.from({length:6},()=>({})),cells:Array.from({length:42},(_,i)=>({cell_id:'c'+i,object_id:i===0?'W':'other',method_id:i===0?'Q':'other'})),compression_topics:[{compression_topic_id:'parameters-precision'}],map_assignments:mapped?[{subject_kind:'legacy_object',subject_id:'W',term_id:'parameters'},{subject_kind:'legacy_method',subject_id:'Q',term_id:'precision',basis:'canonical'}]:[],trend_periods:[{period_id:'2026-10',month:'2026-10',source_status:'reviewed'}],monthly_scopes:[{scope_id:'scope',period_id:'2026-10'}],monthly_cell_reviews:[],compression_topic_events:[]};
 const box={state,URLSearchParams,Set,location:{search:'?month=2026-10&scope=scope'+(topic?'&topic='+topic:'')},performance:{mark(){}},must:(ok,msg)=>{if(!ok)throw Error(msg);},emptyReaderData:()=>({}),ordered:rows=>rows,assertBusiness(){},validateEvidenceRevision(){},validateScientificTaxonomy(){},validateCompressionTopics(){},validateTopicEvent(){},validateReviews:rows=>rows,mapTerm:id=>id==='parameters'?{facet_id:'target'}:id==='precision'?{facet_id:'mechanism'}:null,scientificDescendants:id=>new Set([id]),render(){renders.push(state.focusTarget+'-'+state.focusMechanism);},persistTopicScope(){persist.push(state.focusTarget+'-'+state.focusMechanism);},renderSelectors(){},renderScope(){},renderMap(){},renderSelection(){},controls(){},loadPeriod:async()=>{throw Error('Unexpected fallback request');},LRICloudSemanticRead:async kind=>{calls.push(kind);return {revision:'r',groups};}};
 vm.createContext(box);vm.runInContext(selection+reader+';globalThis.run=startCurrentReader;',box);
 await box.run(1,{revision:'r'});return {state,calls,renders,persist};
}
(async()=>{
 const focused=await run('parameters-precision');assert.equal(focused.state.focusTarget,'parameters');assert.equal(focused.state.focusMechanism,'precision');assert.equal(focused.state.cell,'c0');assert.equal(focused.state.directionMode,false,'Period entry remains the monthly reader, not a permanent topic view');
 assert(focused.renders.every(x=>x==='parameters-precision'),'Topic is restored before first full render');assert.deepEqual(focused.persist,['parameters-precision'],'Persisting monthly scope cannot remove requested topic');
 assert.deepEqual(focused.calls,['synthesis','current'],'Topic restoration adds no business request');
 const all=await run('');assert.equal(all.state.focusTarget,'');assert.equal(all.state.cell,'');assert(all.state.all,'An unfiltered entry clears a previous focus');
 await assert.rejects(()=>run('unknown-topic'),/Unknown compression topic/);
 await assert.rejects(()=>run('parameters-precision',false),/Unavailable compression topic navigation/);
 console.log(JSON.stringify({pass:true,topicBeforeRender:true,topicPersists:true,noExtraRead:true,unfilteredClearsOldFocus:true,unknownOrUnmappedFailsClosed:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
