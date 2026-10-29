(() => {
  'use strict';
  const kinds = new Set(['stable','candidate','project_progress','main_change','version_documentation']);
  function requireThat(value, message) { if (!value) throw new Error(message); }
  function validate(snapshot, directory) {
    const updates = new Map(), changes = new Map(), sources = new Map(snapshot.sources.map(row => [row.source_id,row]));
    const topics = new Map(snapshot.topics.map(row => [row.compression_topic_id,row]));
    const families = new Set(directory.source_families.map(row => row.family_id));
    const channels = new Map(directory.channels.map(row => [row.channel_id,row]));
    const sourceExists = id => { const source=sources.get(id); requireThat(source && /^https:\/\//.test(source.canonical_url), 'Unresolved industry source: '+id); };
    for (const row of [...snapshot.updates,...snapshot.changes,...snapshot.links,...snapshot.assessments]) requireThat(row.topic_id==='cloud_core' && row.business_id==='cloud-core', 'Industry business scope mismatch');
    for (const row of snapshot.updates) {
      requireThat(!updates.has(row.update_id) && families.has(row.family_id) && channels.has(row.channel_id), 'Invalid industry update identity');
      requireThat(directory.channel_families.some(link => link.family_id===row.family_id && link.channel_id===row.channel_id), 'Industry channel family mismatch');
      requireThat(kinds.has(row.release_kind), 'Unknown industry release kind');
      requireThat(['release_note_heading','official_publication','month_only','unknown'].includes(row.release_date_kind), 'Unknown release date provenance');
      requireThat(row.release_date_kind==='unknown' ? row.release_date==='' : row.release_date_kind==='month_only' ? /^\d{4}-\d{2}$/.test(row.release_date) : /^\d{4}-\d{2}-\d{2}$/.test(row.release_date), 'Invalid release date precision');
      requireThat(/^\d{4}-\d{2}-\d{2}$/.test(row.checked_at), 'Invalid industry review date');
      for (const field of ['title','summary','scope','dependencies','boundary']) for (const locale of ['zh','en']) requireThat(row[field+'_'+locale]?.trim(), 'Incomplete localized industry update');
      sourceExists(row.source_id);updates.set(row.update_id,row);
    }
    for (const row of snapshot.changes) {
      const update=updates.get(row.update_id);
      requireThat(update && row.family_id===update.family_id && !changes.has(row.change_id) && Number.isSafeInteger(row.position), 'Orphan industry change');
      for (const field of ['title','fact','conditions']) for (const locale of ['zh','en']) requireThat(row[field+'_'+locale]?.trim(), 'Incomplete localized industry change');
      sourceExists(row.source_id);changes.set(row.change_id,row);
    }
    const links=new Set();
    for (const row of snapshot.links) {
      requireThat(!links.has(row.link_id) && changes.get(row.change_id)?.update_id===row.update_id && topics.has(row.compression_topic_id), 'Orphan industry technical-map link');
      requireThat(['compression_direct','deployment_adjacent'].includes(row.relation_kind), 'Invalid industry relation');
      links.add(row.link_id);
    }
    const assessed=new Set(), linkIndex=new Map(snapshot.links.map(row=>[row.link_id,row]));
    for(const row of snapshot.assessments){
      const link=linkIndex.get(row.link_id),change=changes.get(row.change_id);
      requireThat(link && !assessed.has(row.link_id) && row.change_id===link.change_id && row.update_id===link.update_id && row.compression_topic_id===link.compression_topic_id, 'Industry assessment identity mismatch');
      requireThat(row.relation_kind===link.relation_kind && row.source_id===change.source_id, 'Industry assessment provenance mismatch');
      requireThat(['verified','excluded','pending'].includes(row.review_status) && row.claim_kind==='evidence_based_analysis' && row.review_method==='primary_passage_topic_causality_review', 'Invalid industry assessment review');
      requireThat(row.source_locator?.trim() && /^\d{4}-\d{2}-\d{2}$/.test(row.reviewed_at) && Number.isSafeInteger(row.position), 'Missing industry assessment evidence locator');
      for(const field of ['title','fact_focus','relevance','impact','boundary','check'])for(const locale of ['zh','en'])requireThat(row[field+'_'+locale]?.trim(), 'Incomplete localized industry assessment');
      sourceExists(row.source_id);assessed.add(row.link_id);
    }
    requireThat(assessed.size===links.size, 'Unreviewed industry topic mapping');
    for (const row of updates.values()) requireThat([...changes.values()].some(change=>change.update_id===row.update_id), 'Industry update has no concrete changes');
    return snapshot;
  }
  async function scoped(table, revision) {
    const rows=[];
    for (let offset=0; offset<1000;) {
      const result=await LRITableGit.loadTablePage(table,{filterField:'topic_id',filterValue:'cloud_core',offset,limit:100,expectedRevision:revision});
      requireThat(result.revision===revision && result.page.total<=1000, 'Industry revision or bounded scope unavailable');
      rows.push(...result.records);
      if (!result.page.truncated) return rows;
      requireThat(result.page.nextOffset===offset+result.records.length && result.records.length>0, 'Industry paging did not advance');
      offset=result.page.nextOffset;
    }
    throw new Error('Industry scope exceeds reviewed reader bound');
  }
  async function exact(table, ids, revision) {
    const records=[], keys=[...new Set(ids)];
    for (let index=0;index<keys.length;index+=50) {
      const chunk=keys.slice(index,index+50), result=await LRITableGit.loadRowsByKeys(table,chunk,revision);
      requireThat(result.revision===revision && result.records.length===chunk.length, 'Industry reference hydration incomplete');
      records.push(...result.records);
    }
    return records;
  }
  async function readSnapshot(revision) {
    requireThat(Boolean(revision),'Industry read requires a confirmed revision');
    const [batch,assessments]=await Promise.all([
      typeof globalThis.LRICloudSemanticRead==='function'?LRICloudSemanticRead('industry',revision):Promise.resolve(null),
      scoped('ic_industry_topic_assessments',revision)
    ]);
    requireThat(!batch||batch.revision===revision,'Industry batch revision mismatch');
    const [updates,changes,links]=batch?[batch.groups.industry_updates,batch.groups.industry_update_changes,batch.groups.industry_change_topics]:await Promise.all(['ic_industry_updates','ic_industry_update_changes','ic_industry_change_topics'].map(table=>scoped(table,revision)));
    const [sources,topics]=await Promise.all([
      exact('cloud_core_sources',[...updates,...changes,...assessments].map(row=>row.source_id),revision),
      batch?Promise.resolve(batch.groups.compression_topics):exact('ic_compression_topics',links.map(row=>row.compression_topic_id),revision)
    ]);
    return {revision,updates,changes,links,assessments,sources,topics};
  }
  async function load(revision,directory) {return validate(await readSnapshot(revision),directory);}
  const readers=new Map();
  function loadReader(revision) {
    if(readers.has(revision))return readers.get(revision);
    const pending=(async()=>{
      const snapshot=await readSnapshot(revision);
      const familyIds=[...new Set(snapshot.updates.map(row=>row.family_id))],channelIds=[...new Set(snapshot.updates.map(row=>row.channel_id))];
      const [families,channels,scopes,memberships]=await Promise.all([
        exact('ic_source_families',familyIds,revision),exact('ic_channels',channelIds,revision),exact('ic_industry_source_scopes',familyIds,revision),
        channelIds.length?LRITableGit.loadRowsByValues('ic_channel_families','channel_id',channelIds,revision):Promise.resolve({revision,records:[]})
      ]);
      requireThat(memberships.revision===revision,'Industry membership revision mismatch');
      for(const row of [...families,...channels,...scopes,...memberships.records])requireThat(row.topic_id==='cloud_core'&&row.business_id==='cloud-core','Industry directory scope mismatch');
      const directory={source_families:families,channels,industry_source_scopes:scopes,channel_families:memberships.records};
      return {snapshot:validate(snapshot,directory),directory};
    })().catch(error=>{readers.delete(revision);throw error;});
    readers.set(revision,pending);while(readers.size>2)readers.delete(readers.keys().next().value);return pending;
  }
  function forFamily(snapshot, familyId) {
    return snapshot.updates.filter(row=>row.family_id===familyId).sort((a,b)=>(b.platform_published_date||b.release_date||'').localeCompare(a.platform_published_date||a.release_date||''));
  }
  function reviewedLinks(snapshot) {
    const verified=new Set(snapshot.assessments.filter(row=>row.review_status==='verified').map(row=>row.link_id));
    return snapshot.links.filter(row=>verified.has(row.link_id));
  }
  function forTopic(snapshot,topicId) {
    const links=new Map(reviewedLinks(snapshot).filter(row=>row.compression_topic_id===topicId).map(row=>[row.link_id,row]));
    return snapshot.assessments.filter(row=>links.has(row.link_id)).sort((a,b)=>a.position-b.position||a.link_id.localeCompare(b.link_id)).map(assessment=>({
      assessment,link:links.get(assessment.link_id),change:snapshot.changes.find(row=>row.change_id===assessment.change_id),
      update:snapshot.updates.find(row=>row.update_id===assessment.update_id),source:snapshot.sources.find(row=>row.source_id===assessment.source_id)
    }));
  }
  globalThis.LRIIndustryUpdates=Object.freeze({load,loadReader,validate,forFamily,reviewedLinks,forTopic});
})();


