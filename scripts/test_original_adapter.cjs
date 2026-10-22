// Run the static transport with generated files; no HTTP/MCP server is available.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),dist=path.join(root,'dist'),base='http://local/business_insight/cloud_core/';
const meta=JSON.parse(fs.readFileSync(path.join(dist,'business_insight/cloud_core/local-content/manifest.json'),'utf8'));
let backendCalls=0;
const fetchFile=async input=>{const url=new URL(input,base);if(url.pathname==='/mcp'){backendCalls++;throw Error('No backend is available');}const filename=path.join(dist,decodeURIComponent(url.pathname));return new Response(fs.readFileSync(filename),{headers:{'Content-Type':'application/json'}});};
const window={fetch:fetchFile},context={window,document:{currentScript:{src:base+'local-content-adapter.js'}},location:new URL(base+'index.html'),URL,Response,TextEncoder,crypto:require('node:crypto').webcrypto,console};
vm.runInNewContext(fs.readFileSync(path.join(root,'content/original-content-adapter.js'),'utf8'),context);
async function call(operation,args){const response=await window.fetch('/mcp',{body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'skill_run_read',arguments:{skill_id:'table.query',operation,arguments:args}}})});const result=(await response.json()).result;if(result.isError)throw Error(JSON.stringify(result));return result.structuredContent.result;}
(async()=>{
 const result=await call('table_query',{repo:'works',path:'data/tables/ic_compression_topics',filters:[{field:'target_term_id',op:'eq',value:'parameters'}],view:{kind:'committed',revision:meta.revision},limit:100});assert.equal(result.rows.length,4);assert.equal(result.matched_count,4);assert.equal(result.returned_count,4);
 const sourceTable=JSON.parse(fs.readFileSync(path.join(dist,'business_insight/cloud_core/local-content/tables/cloud_core_sources.json'),'utf8'));const key=sourceTable[0].key;
 const exact=await call('table_query',{repo:'works',path:'data/tables/cloud_core_sources',keys:[key],select:['source_id','title'],view:{kind:'committed',revision:meta.revision},limit:1});assert.equal(exact.rows[0].key,key);assert.equal(exact.rows.length,1);assert.ok(exact.rows[0].row.title);
 const bindings=[{alias:'t',repo:'works',path:'data/tables/ic_compression_topics',revision:meta.revision,source_query:{filters:[{field:'target_term_id',op:'eq',value:'parameters'}]}}];
 const union=await call('table_relation_query',{bindings,sql:"SELECT 'topics' AS kind,key,row_version,row_json FROM t",limits:{max_result_rows:100,max_result_bytes:131072}});assert.equal(union.rows.length,4);assert.deepEqual(union.columns,['kind','key','row_version','row_json']);assert.equal(union.rows[0][0].value,'topics');
 assert.equal(backendCalls,0);console.log('PASS: static queries, key-shard lookup, semantic relation; zero backend calls');
})().catch(error=>{console.error(error);process.exitCode=1;});
