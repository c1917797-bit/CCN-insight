import {renderMarkdownReader} from './markdown-reader.js';
const ROOT=new URL('../',import.meta.url);
const TRANSLATION_RUNTIME=new URL('./lri-translation-runtime.js?v=explicit-headings-v2',import.meta.url);
const HEADING_REGISTRY='technology_insight/data/domain-heading-i18n.json';
const esc=s=>String(s??'');
const fetchJson=async path=>{const url=new URL(path,ROOT),r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);const type=String(r.headers.get('content-type')||'').toLowerCase();if(!type.includes('json')){const prefix=(await r.text()).slice(0,48).replace(/\s+/g,' ');throw new Error(`${path}: expected JSON, got ${type||'unknown content type'} (${prefix})`)}return r.json()};
const locale=()=>document.querySelector('lri-site-shell')?.locale||document.documentElement.lang||'zh';
const isEn=()=>String(locale()).toLowerCase().startsWith('en');
const normalizeHeading=value=>String(value??'').replace(/[*_`]+/g,'').replace(/\s+/g,' ').trim();
function bindHeadingI18n(root,domainId,registry){
  const headings=registry?.domains?.[domainId]?.headings||{};
  root?.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(element=>{
    const source=normalizeHeading(element.getAttribute('data-i18n-zh')||element.textContent);
    const translated=headings[source];
    if(!translated)return;
    element.setAttribute('data-i18n-zh',source);
    element.setAttribute('data-i18n-en',translated);
  });
}
function selectBinding(registry,domainId){
  const q=new URLSearchParams(location.search),period=q.get('period')||registry.current_period,view=q.get('view')||'current';
  let row=(registry.periods||[]).find(p=>p.period===period);
  if(view==='latest'&&registry.latest_official_period)row=(registry.periods||[]).find(p=>p.period===registry.latest_official_period&&p.state==='published');
  if(!row)throw new Error('No matching publication period');
  const binding=(row.domains||[]).find(d=>d.domain_id===domainId);
  return {binding,period:row.period,state:row.state,view};
}
async function resolveContribution({registry,catalogDomain,binding,domainId,period,view}){
  if(binding?.contribution_uri){
    return {contribution:await fetchJson(binding.contribution_uri),authority:'release_registry'};
  }
  const allowExpertProjection=(view==='current'||view==='review')&&period===registry.current_period;
  if(!allowExpertProjection)throw new Error(`Domain ${domainId} is not registered for ${period}`);
  const prefix=String(catalogDomain.context_prefix||'').replace(/^\/+|\/+$/g,'');
  if(!prefix)throw new Error(`Domain ${domainId} has no context_prefix for expert projection fallback`);
  const contribution=await fetchJson(`${prefix}/data/domain-contribution.json`);
  if(contribution.domain_id!==domainId)throw new Error(`Domain ${domainId} expert projection identity mismatch`);
  const baselinePeriod=contribution.period||null;
  if(baselinePeriod&&baselinePeriod>period)throw new Error(`Domain ${domainId} expert projection baseline ${baselinePeriod} is newer than requested period ${period}`);
  return {contribution,authority:'expert_projection',baselinePeriod};
}
function applyMeta(catalogDomain,contribution,period){
  const zh=catalogDomain.report_title,en=catalogDomain.report_title_en;
  document.title=`${isEn()?en:zh} · LRI`;
  document.querySelectorAll('[data-domain-title]').forEach(el=>{el.textContent=isEn()?en:zh});
  document.querySelectorAll('[data-domain-period]').forEach(el=>{el.textContent=isEn()?`${period} · ${en}`:`${period.replace('-', '年')}月 · ${zh}`});
}
export async function renderDomainReport({domainId,host='[data-markdown-reader]'}={}){
  if(!domainId)throw new Error('domainId is required');
  const [registry,catalog,headingRegistry]=await Promise.all([
    fetchJson('technology_trends/data/release-registry.json'),
    fetchJson('technology_insight/data/domain-catalog.json'),
    fetchJson(HEADING_REGISTRY),
  ]);
  const cat=(catalog.domains||[]).find(d=>d.domain_id===domainId);if(!cat)throw new Error(`Unknown Domain ${domainId}`);
  const {binding,period,view}=selectBinding(registry,domainId);
  const {contribution,authority,baselinePeriod}=await resolveContribution({registry,catalogDomain:cat,binding,domainId,period,view});
  if(!contribution.report_uri)throw new Error(`Domain ${domainId} has no report_uri`);
  document.documentElement.dataset.domainProjectionAuthority=authority;
  if(baselinePeriod)document.documentElement.dataset.domainExpertBaselinePeriod=baselinePeriod;else delete document.documentElement.dataset.domainExpertBaselinePeriod;
  applyMeta(cat,contribution,period);
  const result=await renderMarkdownReader({host,src:'/'+contribution.report_uri.replace(/^\/+/,''),shellOutline:true});
  const contentRoot=typeof host==='string'?document.querySelector(host):host;
  const apply=async()=>{
    bindHeadingI18n(contentRoot,domainId,headingRegistry);
    applyMeta(cat,contribution,period);
    const shell=document.querySelector('lri-site-shell');
    if(shell?.applyPageLocale)await shell.applyPageLocale(shell.locale);
    const runtime=await import(TRANSLATION_RUNTIME.href);
    await runtime.applyDocumentLocale(locale(),{
      root:contentRoot||document.querySelector('main')||document.body,
      priorityRoot:document.body,
      sourceLanguage:runtime.sourceLanguageForDocument(document),
      concurrency:8,
    });
  };
  const onLocaleChange=()=>{apply().catch(error=>console.warn('Domain report locale update unavailable',error))};
  await apply();document.addEventListener('lri:locale-change',onLocaleChange);
  return {domain:cat,contribution,binding,period,authority,baselinePeriod,headingRegistry,result};
}
