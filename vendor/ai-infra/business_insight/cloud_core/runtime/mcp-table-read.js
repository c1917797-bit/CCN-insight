(() => {
  'use strict';
  // Official server-authorized, read-only transport. No caller impersonation,
  // credentials, copied business records or writes are sent by this module.
  const tables = new Set(['ic_pipeline_runs','ic_source_pipeline','ic_source_route_candidates','ic_source_acquisition_attempts','ic_paper_review_intakes','ic_foundation_lesson_steps','ic_foundation_lesson_values','ic_compression_foundations','ic_insight_reports','ic_insight_report_assets','ic_insight_report_papers','ic_ascend_route_assessments','ic_ascend_validation_probes','ic_current_signals','ic_signal_topics','ic_industry_updates','ic_industry_update_changes','ic_industry_change_topics','ic_industry_topic_assessments','ic_compression_mechanism_steps','ic_compression_research_frames','ic_compression_research_routes','ic_compression_route_assessments','ic_compression_topic_concepts','ic_compression_topic_cards','ic_compression_topic_card_refs','ic_compression_topics','ic_compression_topic_sections','ic_compression_topic_events','ic_map_facets','ic_map_terms','ic_map_assignments','cloud_core_sources', 'cloud_core_documents', 'topic_workbench_profiles', 'topic_workbench_items',
    ...['objects','methods','cells','techniques','placements','trend_periods','tasks','review_notes','evaluation_dimensions','source_refs','flywheel_stages','lineages','lineage_nodes','lineage_relations','lineage_cells','source_scans','source_screenings','channels','source_categories','channel_categories','channel_provenance','channel_checks','findings','finding_evidence','finding_cells','finding_techniques','finding_keywords','finding_scopes','measurements','decisions','collection_runs','channel_retrievals','channel_entries','evidence_items','evidence_placements','evidence_keywords','trend_scopes','trend_reviews'].map(name => 'ic_' + name)]);
  for (const name of ['monthly_route_insights','monthly_route_evidence','paper_summaries','paper_summary_keywords','paper_summary_events','source_families','channel_families','industry_source_scopes','collection_entries','monthly_evidence_cells','monthly_scopes','monthly_cell_reviews','trend_observations']) tables.add('ic_' + name);
  for (const name of ['modules','flywheel_stages','stage_gates','constraints','metrics','experiments','import_runs','measurements','import_issues']) tables.add('cloud_core_' + name);
  let id = 0, contract, revision = '';
  async function call(name, args) {
    const request = {
      method: 'POST', credentials: 'same-origin',
      headers: {'content-type':'application/json', accept:'application/json, text/event-stream', 'MCP-Protocol-Version':'2026-07-28', 'Mcp-Method':'tools/call', 'Mcp-Name':name},
      body: JSON.stringify({jsonrpc:'2.0', id:++id, method:'tools/call', params:{name, arguments:args, _meta:{'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}}}}),
      signal: AbortSignal.timeout(45000),
    };
    let response;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        response = await fetch('/mcp', {...request, signal:AbortSignal.timeout(45000)});
        if (![408,429,502,503,504].includes(response.status) || attempt === 2) break;
      } catch (error) { if (attempt === 2) throw error; }
      await new Promise(resolve => setTimeout(resolve, 400 * (attempt + 1)));
    }
    if (!response.ok) throw new Error(`TableGit MCP read failed: ${response.status}`);
    const envelope = await response.json();
    if (envelope.error) throw new Error(envelope.error.message || 'TableGit MCP request rejected');
    const result = envelope.result;
    const value = result?.structuredContent ?? JSON.parse(result?.content?.find(item => item.type === 'text')?.text || 'null');
    if (result?.isError || !value || value.outcome === 'failed' || value.error) {
      throw Object.assign(new Error(value?.error?.message || 'TableGit read permission or contract unavailable'),{code:value?.error?.code||''});
    }
    return value;
  }
  // Session-scoped, bounded memoization of immutable committed reads only.
  // Latest metadata and permission/contract discovery always use the server.
  const cachePrefix='lri-cloud-read-v3:', memo=new Map(), inflight=new Map();
  const maxBytes=4*1024*1024,maxEntryBytes=256*1024;let cacheEpoch=0;
  function forgetMemo(){memo.clear();try{for(let i=sessionStorage.length-1;i>=0;i--){const key=sessionStorage.key(i);if(key?.startsWith(cachePrefix))sessionStorage.removeItem(key);}}catch(_){}}
  function entryLimit(key){try{return JSON.parse(key.slice(cachePrefix.length))[0].startsWith('semantic:')?1024*1024:maxEntryBytes;}catch(_){return maxEntryBytes;}}
  function restoreMemo(){
    try{for(let i=0;i<sessionStorage.length;i++){const key=sessionStorage.key(i);if(key?.startsWith(cachePrefix)){const text=sessionStorage.getItem(key);if(text&&text.length*2<=entryLimit(key))memo.set(key,{text,bytes:text.length*2});}}}catch(_){}
    trimMemo();
  }
  function trimMemo(){let bytes=[...memo.values()].reduce((n,e)=>n+e.bytes,0);while(memo.size>128||bytes>maxBytes){const key=memo.keys().next().value;bytes-=memo.get(key).bytes;memo.delete(key);try{sessionStorage.removeItem(key);}catch(_){}}}
  function retireOtherRevisions(current){
    cacheEpoch++;
    for(const key of memo.keys()){
      let belongs=false;try{belongs=JSON.parse(key.slice(cachePrefix.length))[1]?.view?.revision===current;}catch(_){}
      if(!belongs){memo.delete(key);try{sessionStorage.removeItem(key);}catch(_){}}
    }
  }
  restoreMemo();
  function immutableRead(table,args,read,maxRows=100,entryBytes=maxEntryBytes){
    const expected=args.view?.kind==='committed'&&args.view.revision;
    if(!expected)return read();
    const key=cachePrefix+JSON.stringify([table,args]),entry=memo.get(key);
    if(entry){try{const value=JSON.parse(entry.text);if(value.revision!==expected||!Array.isArray(value.rows)||value.rows.length>maxRows)throw new Error('invalid cache');memo.delete(key);memo.set(key,entry);return Promise.resolve(value);}catch(_){memo.delete(key);try{sessionStorage.removeItem(key);}catch(_){}}}
    if(inflight.has(key))return inflight.get(key);
    const epoch=cacheEpoch;
    const pending=read().then(value=>{
      if(value.revision!==expected)throw new Error('TableGit cached read revision mismatch');
      const text=JSON.stringify(value),bytes=text.length*2;
      if(epoch===cacheEpoch&&value.rows.length<=maxRows&&bytes<=entryBytes){memo.set(key,{text,bytes});trimMemo();try{if(memo.has(key))sessionStorage.setItem(key,text);}catch(_){}}
      return value;
    }).finally(()=>{if(inflight.get(key)===pending)inflight.delete(key);});
    inflight.set(key,pending);return pending;
  }
  globalThis.LRICloudTableReadInvalidate=()=>{cacheEpoch++;inflight.clear();forgetMemo();};
  function readContract() {
    if(!contract&&globalThis.LRICloudLiveContract)contract=globalThis.LRICloudLiveContract.catch(()=>{globalThis.LRICloudLiveContract=null;contract=null;return readContract();});
    if (!contract) contract = call('skill_get', {skill_id:'table.query', operation:'table_query'}).then(value => {
      const summary = value.skill?.summary;
      if (summary?.skill_id !== 'table.query' || !summary.skill_version || !value.skill.operations?.some(op => op.name === 'table_query' && op.access_lane === 'read')) throw new Error('TableGit read contract unavailable');
      return summary.skill_version;
    }).catch(error => {contract = null; throw error;});
    return contract;
  }
  async function query(table, args) {
    return immutableRead(table,args,async()=>{
    const value = await call('skill_run_read', {skill_id:'table.query', skill_version:await readContract(), operation:'table_query', arguments:{repo:'works', path:'data/tables/' + table, ...args}});
    const result = value.result;
    if (value.outcome !== 'executed' || !result?.revision || !Array.isArray(result.rows)) throw new Error('Invalid TableGit read result');
    return result;
    });
  }
  // A tagged UNION preserves each normalized semantic row and its own table identity.
  // Only fixed reader plans are exposed; arbitrary SQL or repository paths are rejected.
  const coreTables=['objects','methods','cells','map_facets','map_terms','compression_topics','compression_topic_sections','compression_topic_concepts'];
  const referenceTables=['techniques','placements','source_refs','lineages','lineage_nodes','lineage_relations','lineage_cells','map_assignments'];
  const workbenchTables=["objects","methods","cells","techniques","placements","trend_periods","tasks","review_notes","evaluation_dimensions","source_refs","flywheel_stages","lineages","lineage_nodes","lineage_relations","lineage_cells","source_scans","source_screenings","findings","finding_evidence","finding_cells","finding_techniques","finding_keywords","finding_scopes","map_facets","map_terms","map_assignments","compression_topics","compression_topic_sections","compression_topic_concepts"];
  const dossierTables=['compression_topic_cards','compression_topic_card_refs','compression_mechanism_steps','compression_research_frames','compression_research_routes'];
  const eq=(field,value)=>({field,op:'eq',value}),within=(field,value)=>({field,op:'in',value});
  function semanticPlan(mode,options){
    const scoped=name=>({name,table:'ic_'+name,filters:[eq('topic_id','cloud_core')]});
    const profile={name:'profiles',table:'topic_workbench_profiles',filters:[eq('topic_id','cloud_core')]};
    if(mode==='sources'){
      const group=options.group,channels=options.channels;
      if(!['hotspot','industry','academic'].includes(group)||!Array.isArray(channels)||channels.length>400||channels.some(r=>r.topic_id!=='cloud_core'||r.business_id!=='cloud-core'||r.ui_group!==group||!r.channel_id||!r.source_id))throw new Error('Invalid source batch scope');
      const ids=[...new Set(channels.map(r=>r.source_id))],cids=channels.map(r=>r.channel_id);
      if(new Set(cids).size!==cids.length)throw new Error('Duplicate source batch channel');
      return [
        {name:'source_families',table:'ic_source_families',filters:[eq('ui_group',group)]},
        {name:'channel_families',table:'ic_channel_families',filters:[within('channel_id',cids)]},
        {name:'primarySources',table:'cloud_core_sources',filters:[within('source_id',ids)],select:['source_id','business_id','canonical_url','title','external_id']},
        ...(group==='industry'?[scoped('industry_source_scopes')]:[]),profile];
    }
    if(mode==='workbench')return [...workbenchTables.map(scoped),profile,{name:'items',table:'topic_workbench_items',filters:[eq('topic_id','cloud_core')]}];
    if(mode==='synthesis'){
      if(!/^\d{4}-\d{2}$/.test(options.period||'')||!options.scope)throw new Error('Invalid synthesis scope');
      return [
        ...['monthly_route_insights','monthly_route_evidence','ascend_route_assessments','ascend_validation_probes'].map(name=>({name,table:'ic_'+name,filters:[eq('scope_id',options.scope)]})),
        {name:'current_signals',table:'ic_current_signals',filters:[eq('period_id',options.period)]},scoped('signal_topics'),...['insight_reports','insight_report_assets','insight_report_papers'].map(name=>({name,table:'ic_'+name,filters:[eq('scope_id',options.scope)]}))
      ];
    }
    if(mode==='current'){
      const plan=[...coreTables.map(scoped),{name:'map_assignments',table:'ic_map_assignments',filters:[within('subject_kind',['legacy_object','legacy_method'])]},scoped('trend_periods'),profile];
      if(options.period||options.scope){
        if(!/^\d{4}-\d{2}$/.test(options.period||'')||!options.scope)throw new Error('Invalid current reader scope');
        plan.push({name:'monthly_scopes',table:'ic_monthly_scopes',filters:[eq('period_id',options.period)]},...['monthly_cell_reviews','compression_topic_events'].map(name=>({name,table:'ic_'+name,filters:[eq('scope_id',options.scope)]})));
      }
      return plan;
    }
    if(mode==='industry')return ['industry_updates','industry_update_changes','industry_change_topics','compression_topics'].map(scoped);
    if(mode==='references')return referenceTables.map(scoped);
    if(mode==='map')return [...coreTables,...referenceTables.filter(n=>!coreTables.includes(n)),'trend_periods'].map(scoped).concat(profile);
    if(mode==='topic'||mode==='dossier'){
      if(!/^([a-z_]+)-([a-z_]+)$/.test(options.topicId||''))throw new Error('Invalid topic batch scope');
      if(mode==='dossier')return dossierTables.map(name=>({name,table:'ic_'+name,filters:[eq('compression_topic_id',options.topicId)]}));
      return [...coreTables.map(scoped),{name:'map_assignments',table:'ic_map_assignments',filters:[within('subject_kind',['legacy_object','legacy_method'])]},profile,...dossierTables.map(name=>({name,table:'ic_'+name,filters:[eq('compression_topic_id',options.topicId)]}))];
    }
    throw new Error('Unsupported semantic reader plan');
  }
  function decodeSemantic(result,expected,plan,bindings){
    if(result.revision!==expected||!Array.isArray(result.bindings)||result.bindings.length!==bindings.length||!Array.isArray(result.rows)||result.rows.length>1000||JSON.stringify(result.columns)!==JSON.stringify(['kind','key','row_version','row_json'])||!Number.isSafeInteger(result.output_bytes)||result.output_bytes>1048576)throw new Error('Invalid semantic read envelope');
    const resolved=new Map();
    for(const b of result.bindings){if(resolved.has(b.alias))throw new Error('Duplicate semantic binding');resolved.set(b.alias,b);}
    for(const b of bindings){const actual=resolved.get(b.alias);if(!actual||actual.repo!==b.repo||actual.path!==b.path||actual.revision!==expected||actual.include_deleted!==false)throw new Error('Semantic binding revision/identity mismatch');}
    const groups=Object.fromEntries(plan.map(p=>[p.name,[]])),seen=new Set();
    for(const row of result.rows){
      if(!Array.isArray(row)||row.length!==4||row[0]?.type!=='text'||row[1]?.type!=='text'||!row[1].value||row[2]?.type!=='integer'||!Number.isSafeInteger(row[2].value)||row[2].value<1||row[3]?.type!=='text'||!Object.hasOwn(groups,row[0].value))throw new Error('Invalid semantic row');
      const key=row[0].value+'__'+row[1].value;if(seen.has(key))throw new Error('Duplicate semantic row');seen.add(key);
      const record=JSON.parse(row[3].value);
      if(!record||typeof record!=='object'||Array.isArray(record)||record.deleted===true)throw new Error('Invalid semantic record');
      const spec=plan.find(p=>p.name===row[0].value);
      for(const filter of spec.filters){const value=record[filter.field];if(filter.op==='eq'?value!==filter.value:!filter.value.includes(value))throw new Error('Semantic row outside requested scope');}
      if(!['profiles','items'].includes(spec.name)&&record.business_id!=='cloud-core')throw new Error('Foreign semantic business');
      groups[spec.name].push(record);
    }
    return {revision:expected,groups};
  }
  async function materializedRows(plan,expected,bindings){
    // The fallback still reads normalized TableGit tables at the exact same revision.
    // It is used only for the server SQL materialization race; all envelopes are revalidated.
    const rows=[];let bytes=0,total=0;
    for(const spec of plan){let offset=0;
      for(;;){const result=await query(spec.table,{filters:spec.filters,...(spec.select?{select:spec.select}:{}),limit:100,offset,view:{kind:'committed',revision:expected}});
        if(result.revision!==expected||!Array.isArray(result.rows))throw new Error('Exact table fallback revision mismatch');
        total+=result.rows.length;bytes+=JSON.stringify(result.rows).length*2;
        if(total>1000||bytes>2097152)throw new Error('Exact table fallback exceeds source budget');
        for(const record of result.rows)rows.push([{type:'text',value:spec.name},{type:'text',value:record.key},{type:'integer',value:record.row_version},{type:'text',value:JSON.stringify(record.row)}]);
        if(!result.truncated)break;
        if(!result.rows.length)throw new Error('Exact table fallback invalid cursor');offset+=result.rows.length;
      }
    }
    return {outcome:'executed',result:{revision:expected,bindings:bindings.map(b=>({alias:b.alias,repo:b.repo,path:b.path,revision:expected,include_deleted:false})),columns:['kind','key','row_version','row_json'],rows,output_bytes:JSON.stringify(rows).length*2}};
  }
  async function semanticChunk(mode,expected,plan){
    // Bind relation names to the complete query identity, not reusable b0/b1 names.
    // Two hashes separate different scopes/chunks; decoded bindings still enforce exact identity.
    const identity=JSON.stringify([mode,expected,plan]);let h1=2166136261,h2=5381;
    for(let n=0;n<identity.length;n++){h1=Math.imul(h1^identity.charCodeAt(n),16777619);h2=Math.imul(h2,33)^identity.charCodeAt(n);}
    const prefix='r_'+expected.slice(0,16)+'_'+(h1>>>0).toString(16)+'_'+(h2>>>0).toString(16)+'_';
    const bindings=plan.map((p,i)=>({alias:prefix+i,repo:'works',path:'data/tables/'+p.table,revision:expected,source_query:{filters:p.filters,...(p.select?{select:p.select}:{})}}));
    const args={bindings,sql:plan.map((p,i)=>"SELECT '"+p.name+"' AS kind,key,row_version,row_json FROM "+bindings[i].alias).join(' UNION ALL '),limits:{max_source_rows:1000,max_source_bytes:2097152,max_result_rows:1000,max_result_bytes:1048576},wall_time_ms:2000};
    const result=await immutableRead('semantic:'+mode,{...args,view:{kind:'committed',revision:expected}},async()=>{
      let value;
      // Retry only the observed server materialization race, at the same confirmed revision.
      for(let attempt=0;attempt<3;attempt++){
        try{value=await call('skill_run_read',{skill_id:'table.query',skill_version:await readContract(),operation:'table_relation_query',arguments:args});break;}
        catch(error){if(!/SQL relation changed identity while being materialized/i.test(String(error.message)) )throw error;if(attempt===2){value=await materializedRows(plan,expected,bindings);break;}await new Promise(resolve=>setTimeout(resolve,250*(attempt+1)));}
      }
      if(value.outcome!=='executed'||!value.result)throw new Error('Invalid TableGit semantic result');
      const result={...value.result,revision:expected};decodeSemantic(result,expected,plan,bindings);return result;
    },1000,1024*1024);
    return decodeSemantic(result,expected,plan,bindings);
  }
  globalThis.LRICloudSemanticRead=async(mode,expected,options={})=>{
    if(!/^[a-f0-9]{40}$/.test(expected||''))throw new Error('Semantic read requires a confirmed revision');
    const plan=semanticPlan(mode,options),chunks=[];
    // Service SQL has a 16-term compound-SELECT bound; readers use at most two chunks.
    for(let i=0;i<plan.length;i+=16)chunks.push(plan.slice(i,i+16));
    if(chunks.length>2)throw new Error('Semantic reader plan exceeds request budget');
    // Keep chunk concurrency bounded; each chunk has its own relation identity.
    const results=[];for(const chunk of chunks)results.push(await semanticChunk(mode,expected,chunk));
    return {revision:expected,groups:Object.assign({},...results.map(result=>result.groups))};
  };
  // Overlap live permission discovery with the remaining deferred UI scripts.
  readContract().catch(()=>{});
  globalThis.LRICloudTableReadPage=async(table,options)=>{
    if(!tables.has(table))throw new Error('Unsupported cloud-core page');
    const offset=Math.max(0,Number(options.offset)||0),limit=Math.max(1,Math.min(Number(options.limit)||50,100));
    const args={offset,limit,...(options.expectedRevision?{view:{kind:'committed',revision:options.expectedRevision}}:{})};
    if(options.filterField)args.filters=[{field:options.filterField,op:'eq',value:options.filterValue}];
    const result=await query(table,args);
    if(options.expectedRevision&&result.revision!==options.expectedRevision)throw new Error('TableGit page revision mismatch');
    const fields=Object.keys(result.definition?.fields||{});
    if(options.filterField&&!fields.includes(options.filterField))throw new Error('TableGit page filter unavailable');
    if(!options.expectedRevision){if(revision!==result.revision)retireOtherRevisions(result.revision);revision=result.revision;}
    return {metadata:{schema:'mcpgit/hosted-table/v1',table,status:{revision:result.revision,row_count:result.row_count,deleted_count:result.deleted_count},max_rows:100,filter_fields:fields,transport:'mcp-read'},page:{...result,total:result.matched_count}};
  };


  // Processing queues join canonical source identity at one confirmed revision.
  // Only fixed plans and typed search/offset inputs cross the transport boundary.
  const pipelineTables=new Set(['ic_pipeline_runs','ic_source_pipeline','ic_source_route_candidates','ic_source_acquisition_attempts','cloud_core_sources']);
  const pipelineStages=['metadata_needed','candidate_direct','candidate_adjacent','needs_relevance_review','reviewed_visible','reviewed_unpublished','reconciliation_needed','blocked_invalid','excluded_manual','retryable_failure'];
  const queueStages={candidates:['candidate_direct','candidate_adjacent'],metadata:['metadata_needed'],manual:['needs_relevance_review'],issues:['blocked_invalid','retryable_failure'],linkage:['reviewed_unpublished','reconciliation_needed'],pending:['metadata_needed','candidate_direct','candidate_adjacent','needs_relevance_review','blocked_invalid','retryable_failure']};
  const authorities=new Map();let statusContract,relationContract;
  function operationContract(operation){
    return call('skill_get',{skill_id:'table.query',operation}).then(value=>{
      const s=value.skill?.summary;
      if(s?.skill_id!=='table.query'||!s.skill_version||!value.skill.operations?.some(o=>o.name===operation&&o.access_lane==='read'))throw Error('Pipeline read contract unavailable');
      return s.skill_version;
    });
  }
  function pipelineAuthority(table,expected){
    if(!pipelineTables.has(table)||!/^[a-f0-9]{40}$/.test(expected||''))throw Error('Invalid pipeline authority request');
    const key=table+':'+expected;
    if(!authorities.has(key))authorities.set(key,(async()=>{
      statusContract ||= operationContract('table_status').catch(e=>{statusContract=null;throw e;});
      const value=await call('skill_run_read',{skill_id:'table.query',skill_version:await statusContract,operation:'table_status',arguments:{repo:'tablegit',path:'data/tables/'+table,view:{kind:'committed',revision:expected}}});
      const r=value.result;
      if(value.outcome!=='executed'||!r||r.revision!==expected||r.path!=='data/tables/'+table||typeof r.repo!=='string'||!r.repo||!r.definition?.key_field)throw Error('Invalid pipeline table authority');
      return {repo:r.repo,path:r.path,revision:expected,keyField:r.definition.key_field};
    })().catch(e=>{authorities.delete(key);throw e;}));
    return authorities.get(key);
  }
  async function pipelineTable(table,args){
    const expected=args.view?.revision,authority=await pipelineAuthority(table,expected);
    return immutableRead('pipeline:'+table,{...args,repo:authority.repo,path:authority.path},async()=>{
      const value=await call('skill_run_read',{skill_id:'table.query',skill_version:await readContract(),operation:'table_query',arguments:{...args,repo:authority.repo,path:authority.path}});
      const r=value.result;
      if(value.outcome!=='executed'||r?.repo!==authority.repo||r?.path!==authority.path||r?.revision!==expected||!Array.isArray(r.rows)||r.rows.length>(args.limit||100))throw Error('Invalid pipeline table read');
      return r;
    },args.limit||100);
  }
  function queueRequest(expected,offset,term){
    if(!/^[a-f0-9]{40}$/.test(expected||'')||!Number.isSafeInteger(offset)||offset<0||offset%10||typeof term!=='string'||term.length>120)throw Error('Invalid paper queue request');
  }
  function sourceURL(value){const url=new URL(value);if(url.protocol!=='https:'||url.username||url.password)throw Error('Unsafe paper queue URL');return url.href;}
  globalThis.LRICloudPaperQueueRead = async ({revision:expected,offset=0,term=''}) => {
    queueRequest(expected,offset,term);
    const filters=[eq('business_id','cloud-core'),eq('source_kind','paper'),eq('verification_status','not_checked')];
    const result=await pipelineTable('cloud_core_sources',{filters,select:['source_id','business_id','source_kind','verification_status','title','canonical_url','external_id'],order_by:[{field:'source_id',direction:'asc'}],limit:10,offset,view:{kind:'committed',revision:expected},...(term.trim()?{text_search:{query:term.trim(),fields:['title','external_id','canonical_url'],term_mode:'all',case_sensitive:false}}:{})});
    if(!Number.isSafeInteger(result.matched_count)||result.matched_count<0||typeof result.truncated!=='boolean')throw Error('Invalid paper queue envelope');
    const seen=new Set(),rows=result.rows.map(e=>{const row=e.row;if(e.deleted||!e.key||e.key!==row?.source_id||seen.has(e.key)||!Number.isSafeInteger(e.row_version)||e.row_version<1||filters.some(f=>row[f.field]!==f.value))throw Error('Invalid paper queue row');seen.add(e.key);let sourceURLValid=false;try{sourceURL(row.canonical_url);sourceURLValid=true;}catch(_){}return {...row,sourceURLValid};});
    if(result.truncated!==(offset+rows.length<result.matched_count)||result.truncated&&!rows.length)throw Error('Invalid paper queue pagination');
    return {revision:expected,rows,total:result.matched_count,truncated:result.truncated};
  };
  globalThis.LRICloudPipelineRunRead=async expected=>{
    queueRequest(expected,0,'');
    let page;
    try{page=await pipelineTable('ic_pipeline_runs',{filters:[eq('business_id','cloud-core'),eq('topic_id','cloud_core')],order_by:[{field:'started_at',direction:'desc'},{field:'run_id',direction:'desc'}],limit:1,offset:0,view:{kind:'committed',revision:expected}});}
    catch(e){if(e.code==='not_found')return {revision:expected,run:null};throw e;}
    if(!page.rows.length)return {revision:expected,run:null};
    const frame=page.rows[0],r=frame.row;
    if(frame.deleted||frame.key!==r?.run_id||r.business_id!=='cloud-core'||r.topic_id!=='cloud_core'||!/^[a-f0-9]{40}$/.test(r.source_revision||''))throw Error('Invalid pipeline run');
    for(const field of ['total_sources','processed_sources','duplicate_refs',...pipelineStages])if(!Number.isSafeInteger(r[field])||r[field]<0)throw Error('Invalid pipeline coverage count');
    if(r.processed_sources>r.total_sources||pipelineStages.reduce((n,k)=>n+r[k],0)!==r.processed_sources)throw Error('Pipeline stage count mismatch');
    return {revision:expected,run:r};
  };
  globalThis.LRICloudPipelineRead=async({revision:expected,queue='candidates',offset=0,term=''})=>{
    queueRequest(expected,offset,term);if(!Object.hasOwn(queueStages,queue))throw Error('Invalid pipeline queue');
    const stages=queueStages[queue],[p,s]=await Promise.all([pipelineAuthority('ic_source_pipeline',expected),pipelineAuthority('cloud_core_sources',expected)]);
    const identity=JSON.stringify([expected,queue,term.trim()]);let h=2166136261;for(let i=0;i<identity.length;i++)h=Math.imul(h^identity.charCodeAt(i),16777619);
    const prefix='pq_'+expected.slice(0,12)+'_'+(h>>>0).toString(16),pa=prefix+'_p',sa=prefix+'_s';
    const bindings=[
      {alias:pa,repo:p.repo,path:p.path,revision:expected,source_query:{filters:[eq('business_id','cloud-core'),eq('topic_id','cloud_core'),within('stage',stages)]}},
      {alias:sa,repo:s.repo,path:s.path,revision:expected,source_query:{filters:[eq('business_id','cloud-core'),eq('source_kind','paper')],select:['source_id','business_id','source_kind','title','canonical_url','external_id'],...(term.trim()?{text_search:{query:term.trim(),fields:['title','external_id','canonical_url'],term_mode:'all',case_sensitive:false}}:{})}}
    ];
    const sql='WITH matched AS (SELECT p.key AS item_key,p.row_json AS pipeline_json,s.row_json AS source_json FROM '+pa+' p LEFT JOIN '+sa+" s ON s.key=json_extract(p.row_json,'$.source_id')"+(term.trim()?' WHERE s.key IS NOT NULL':'')+"), page AS (SELECT * FROM matched ORDER BY CAST(json_extract(pipeline_json,'$.priority') AS INTEGER),item_key LIMIT ? OFFSET ?), total AS (SELECT COUNT(*) AS total FROM matched) SELECT page.item_key,page.pipeline_json,page.source_json,total.total FROM total LEFT JOIN page ON 1=1";
    const args={bindings,sql,parameters:[{type:'integer',value:10},{type:'integer',value:offset}],limits:{max_source_rows:50000,max_source_bytes:33554432,max_result_rows:10,max_result_bytes:131072},wall_time_ms:5000};
    relationContract ||= operationContract('table_relation_query').catch(e=>{relationContract=null;throw e;});
    const result=await immutableRead('pipeline-join:'+queue,{...args,view:{kind:'committed',revision:expected}},async()=>{
      const value=await call('skill_run_read',{skill_id:'table.query',skill_version:await relationContract,operation:'table_relation_query',arguments:args});
      if(value.outcome!=='executed'||!value.result)throw Error('Pipeline relation unavailable');
      return {...value.result,revision:expected};
    },10);
    if(result.revision!==expected||JSON.stringify(result.columns)!==JSON.stringify(['item_key','pipeline_json','source_json','total'])||!Array.isArray(result.rows)||result.rows.length>10||!Array.isArray(result.bindings)||result.bindings.length!==2)throw Error('Invalid pipeline relation envelope');
    for(const b of bindings){const actual=result.bindings.find(x=>x.alias===b.alias);if(!actual||actual.repo!==b.repo||actual.path!==b.path||actual.revision!==expected||actual.include_deleted!==false)throw Error('Mixed pipeline relation authority');}
    let total=null;const seen=new Set(),rows=[];
    for(const cells of result.rows){
      if(!Array.isArray(cells)||cells.length!==4||cells[3]?.type!=='integer'||!Number.isSafeInteger(cells[3].value)||cells[3].value<0||(total!==null&&total!==cells[3].value))throw Error('Invalid pipeline relation count');
      total=cells[3].value;if(cells[0]?.type==='null'){if(cells[1]?.type!=='null'||cells[2]?.type!=='null')throw Error('Invalid empty pipeline row');continue;}
      if(cells[0]?.type!=='text'||cells[1]?.type!=='text'||!['text','null'].includes(cells[2]?.type))throw Error('Invalid pipeline record');
      const row=JSON.parse(cells[1].value),source=cells[2].type==='text'?JSON.parse(cells[2].value):null;
      if(row.source_id!==cells[0].value||seen.has(row.source_id)||row.business_id!=='cloud-core'||row.topic_id!=='cloud_core'||!stages.includes(row.stage)||!Number.isSafeInteger(row.priority))throw Error('Pipeline record outside requested scope');
      if(source&&(source.source_id!==row.source_id||source.business_id!=='cloud-core'||source.source_kind!=='paper'))throw Error('Pipeline source mismatch');
      let sourceURLValid=false;if(source)try{sourceURL(source.canonical_url);sourceURLValid=true;}catch(_){}
      seen.add(row.source_id);rows.push({pipeline:row,source,sourceURLValid});
    }
    if(total===null||rows.length>10||(offset<total&&!rows.length)||offset+rows.length>total)throw Error('Invalid pipeline result pagination');
    return {revision:expected,rows,total,truncated:offset+rows.length<total};
  };

  globalThis.LRICloudTableRead = async (url, options = {}) => {
    const target = new URL(url, location.href);
    const match = /^\/__mcpgit\/tables\/([a-z0-9_]+)(\/rows(?:\/(?:get|by-values))?)?$/.exec(target.pathname);
    if (target.origin !== location.origin || !match || !tables.has(match[1])) throw new Error('Unsupported cloud-core table read');
    const table = match[1], route = match[2] || '';
    if (!route) {
      const expected = target.searchParams.get('expected_revision') || '';
      const result = await query(table, {limit:0, ...(expected ? {view:{kind:'committed',revision:expected}} : {})});
      if (expected && result.revision !== expected) throw new Error('TableGit metadata revision mismatch');
      if(!expected&&revision!==result.revision)retireOtherRevisions(result.revision);
      revision = result.revision;
      return {schema:'mcpgit/hosted-table/v1', table, status:{revision:result.revision,row_count:result.row_count,deleted_count:result.deleted_count}, max_rows:100, filter_fields:Object.keys(result.definition?.fields || {}), transport:'mcp-read'};
    }
    const body = options.body ? JSON.parse(options.body) : {}, args = {limit:100,offset:0,view:{kind:'committed',revision:body.expected_revision || target.searchParams.get('expected_revision') || revision}};
    if (!args.view.revision) throw new Error('TableGit read requires a confirmed revision');
    if (route === '/rows/get') {
      args.keys = body.keys; args.limit = body.keys.length;
      if (body.select) args.select = body.select;
    } else if (route === '/rows/by-values') {
      args.filters = [{field:body.filter_field,op:'in',value:body.filter_values}]; args.offset = body.offset || 0; args.limit = body.limit || 100;
    } else {
      args.offset = Number(target.searchParams.get('offset') || 0); args.limit = Number(target.searchParams.get('limit') || 100);
      if (target.searchParams.has('filter_field')) args.filters = [{field:target.searchParams.get('filter_field'),op:'eq',value:target.searchParams.get('filter_value')}];
    }
    const result = await query(table, args);
    if (result.revision !== args.view.revision) throw new Error('TableGit MCP revision mismatch');
    if (route === '/rows/get') {
      const found = new Set(result.rows.map(row => row.key));
      if (result.truncated) throw new Error('Incomplete TableGit exact-key read');
      return {...result,requested_count:body.keys.length,missing_keys:body.keys.filter(key => !found.has(key)),excluded_deleted_keys:[]};
    }
    return {...result,total:result.matched_count};
  };
})();
