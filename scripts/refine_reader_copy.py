"""Refine reader UI source modules and rebuild delivery bundles reproducibly."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'original-reader/site'
BASE=SITE/'business_insight/cloud_core'

COPY={
 'monthly_help':'按所选月份阅读新发表或实质更新的成果。每条进展说明解决的问题、关键方法、实验条件与业务启示。',
 'updates_help':'从挑战看进展：本月哪些方法提供了新证据，哪些工程变化改善了落地条件？',
 'sources_help':'按学术、产业与热点查找资料，了解每个来源的用途。产业来源分为昇腾生态与跨平台生态；新闻帮助发现线索，技术判断依据论文原文和官方实现。',
 'topics_help':'先选择压缩对象，再进入研究专题。共同原理集中在“压缩基础”，专题重点解释具体挑战、实现路线和采用条件。',
 'map_help':'技术地图连接压缩对象与方法。各专题沉淀原理和路线，本期动态追踪新增证据，洞察报告给出取舍和验证建议。',
 'analysis_intro':'从业务瓶颈出发，选择值得投入的具体技术：为什么选、需要适配什么、用什么实验判断是否继续。',
 'analysis_route_title':'技术取舍与验证计划',
 'analysis_route_note':'结合报告比较候选路线，说明采用条件、适配工作与继续投入的门槛。',
 'analysis_report_hint':'在本页阅读，可翻页或放大查看细节',
 'analysis_focus_help':'每项重点研究对应具体论文或实现，说明目标瓶颈、候选机制和验证方法。尚未完成业务实测的收益，保留为待验证假设。',
 'analysis_focus_reason':'选择理由',
 'analysis_focus_probe':'验证内容',
 'analysis_focus_action':'建议行动',
 'analysis_focus_probe_pending':'尚缺可执行的实验设计，暂不作为立项依据。',
 'industry_general_title':'跨平台生态',
 'industry_general_help':'跟踪跨平台项目及其他硬件生态的压缩方法、推理运行时和计算内核，为昇腾适配提供工程参照。具体支持按项目和版本核对。',
 'industry_ascend_help':'沿“压缩工具—模型格式—推理框架—计算算子”查看昇腾实现，重点检查版本配套及尚需适配的环节。',
 'industry_scope_help':'先区分昇腾生态与跨平台生态，再按压缩工具、推理运行时、计算内核和评测用途查找；同一项目的多个入口合并展示。',
 'current_signal_help':'关注改变业务需求或技术优先级的事件，说明它影响了哪个瓶颈，以及为什么值得调整研究投入。',
 'current_industry_help':'查看版本新增了什么、对应哪项技术挑战、还缺什么适配条件。正式发布、主干变更与既有能力分别标注。',
 'current_papers_help':'按技术地图组织本月已研读论文，保留具体模型、数据集、基线和效果，说明机制如何回应挑战。',
 'reports_help':'归档从 2026 年 10 月开始，保留各期报告及当时的判断。更早的论文作为专题基础文献，不单列为往期洞察。',
 'paper_pipeline_help':'这是采集与研读工作台。按处理阶段查看候选、待补资料和已读记录；正式技术判断请阅读专题或洞察报告。',
 'paper_pipeline_direct':'压缩相关候选',
 'paper_pipeline_machine':'标题初筛 · 尚待原文研读',
 'paper_pipeline_run':'最近处理时间',
 'paper_pipeline_processed':'已记录处理阶段；论文研读进度单独统计。',
 'paper_pipeline_key':'资料编号',
 'research_scope_help':'面向 LLM（以 Qwen3.8-27B 为例）及降噪、翻译等领域模型，筛选能改善容量、吞吐或时延的压缩技术。精度损失小于 1% 是待验证的业务目标。',
 'industry_research_check':'部署前检查',
 'industry_research_details':'实现条件与证据说明',
 'industry_research_impact':'对昇腾适配的意义',
 'validation_help':'每项实验围绕具体方法设计，给出对照、指标和停止条件。验证结果用于决定采用、调整或暂缓。',
 'ascend_decision_help':'依据已读证据提出技术取舍；区分可直接复现的路径、需要适配的候选和暂缓路线。实际收益仍需目标设备验证。',
 'source_grouping_help':'每个机构或项目保留一条介绍；主页、代码、文档和发布记录作为不同入口列在条目内。',
}

def main():
 p=BASE/'data/focus-ui.zh.json';pack=json.loads(p.read_text(encoding='utf-8'));pack['strings'].update(COPY);p.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 p=BASE/'compression.js';text=p.read_text(encoding='utf-8')
 text=text.replace("root.hidden=topicPage()||document.body.dataset.compressionMonthly==='true';if(root.hidden)return;","root.hidden=topicPage()||document.body.dataset.compressionMonthly==='true'||state.view!=='sources';if(root.hidden)return;")
 for old,new in {
  '阅读指南':'如何使用这份洞察',
  '信息来源：了解信源定位与选择理由。':'信息来源：查找原始资料与跟踪入口。',
  '技术地图：查阅各专题的背景、挑战、原理与技术路线。':'技术地图：理解原理、挑战与解决路线。',
  '本期动态：查看当月论文、产业进展与热点事件。':'本期动态：了解本月新增了哪些证据。',
  '洞察报告：阅读综合判断、技术取舍与业务落地建议。':'洞察报告：判断哪些技术值得验证。',
  '洞察归档：回看历月报告与判断变化。':'洞察归档：回看各期判断及其变化。',
  '研究分析 · 待验证':'研究建议 · 尚未实测',
  '技术原理 · 原文依据':'技术原理',
  '参考章节与图表':'参考位置',
  '当前分类信源已加载 · 其他类别按需读取':'',
 }.items():text=text.replace(old,new)
 # Imported-corpus samples have per-paper provenance, rather than a fictitious single channel.
 text=text.replace("typeof scan.channel_source_id==='string'&&scan.channel_source_id&&countKeys.every", "typeof scan.channel_source_id==='string'&&(scan.channel_source_id||scan.origin_kind==='imported_corpus_regression_sample')&&countKeys.every")
 text=text.replace("external(detail,sourceById(scan.channel_source_id).canonical_url,label('original_source'));", "if(scan.channel_source_id)external(detail,sourceById(scan.channel_source_id).canonical_url,label('original_source'));else detail.append(element('p',mapText('跨来源样本，各条论文的原始链接见下方。','Cross-source sample. Each paper links to its original source below.'),'meta'));")
 text=text.replace("scans.map(row=>row.channel_source_id)","scans.map(row=>row.channel_source_id).filter(Boolean)") if 'scans.map(row=>row.channel_source_id).filter(Boolean)' not in text else text
 text=text.replace("collected.source_scans.map(row=>row.channel_source_id)","collected.source_scans.map(row=>row.channel_source_id).filter(Boolean)") if 'collected.source_scans.map(row=>row.channel_source_id).filter(Boolean)' not in text else text
 text=text.replace("if(id!=='parameters-precision')paragraph(scope,'problem');", "if(id!=='parameters-precision'&&!dossier?.frames?.length)paragraph(scope,'problem');")
 text=text.replace("if(id!=='parameters-precision')renderResearchFraming(mechanism,'challenge');", "")
 # Citations retain full titles and review locators without competing with the prose.
 old="for(const ref of references){const source=dossier.sources.find(item=>item.source_id===ref.source_id),shortName=source.title.split(':')[0].slice(0,48),sourceUrl=new URL(source.canonical_url),paperId=sourceUrl.hostname==='arxiv.org'?sourceUrl.pathname.split('/').filter(Boolean).at(-1):'',link=element('a',shortName+(paperId?' ['+paperId+']':''));"
 new="for(const ref of references){const source=dossier.sources.find(item=>item.source_id===ref.source_id),referenceNumber=dossier.sources.findIndex(item=>item.source_id===ref.source_id)+1,link=element('a','['+referenceNumber+']');link.setAttribute('aria-label',source.title);"
 assert old in text or new in text,'Citation renderer changed unexpectedly'
 text=text.replace(old,new)
 # Put a concise conclusion before the detailed argument on every topic.
 if 'function renderEditorialTakeaway(' not in text:
  helper="""function renderEditorialTakeaway(hero){
 const row=topicSectionRow('implication');if(!row)return;
 const sentence=textOf(row,'body').split(state.locale==='en'?/(?<=\\.)\\s/:/。/)[0];
 if(sentence)hero.append(element('p',sentence+(state.locale==='en'?'':'。'),'topic-takeaway'));
}
"""
  text=text.replace('function renderWeightQuantizationTopic(',helper+'function renderWeightQuantizationTopic(',1)
  text=text.replace("parent.append(hero);renderFoundationLink(hero,'precision');","renderEditorialTakeaway(hero);parent.append(hero);renderFoundationLink(hero,'precision');",1)
  text=text.replace("const stats=element('div','','direction-stats topic-report-meta');","renderEditorialTakeaway(hero);\n const stats=element('div','','direction-stats topic-report-meta');",1)
 # Keep the left outline at chapter level. Subsections remain visible in the article.
 marker="function renderTopicReportOutline(parent,sections){"
 if 'function simplifyTopicOutline(' not in text:
  helper="""function simplifyTopicOutline(parent){
 for(const node of parent.querySelectorAll('section[id]')){
  const chapter=node.classList.contains('research-overview-section')&&node.id.startsWith('research-overview-');
  node.dataset.sectionOutline=String(chapter);
 }
}
"""
  text=text.replace(marker,helper+marker,1)
  text=text.replace("host.append(node);\n  }\n }\n}\nfunction simplifyTopicOutline", "host.append(node);\n  }\n }\n simplifyTopicOutline(parent);\n}\nfunction simplifyTopicOutline",1)
 p.write_text(text,encoding='utf-8')
 p=BASE/'current-synthesis.js';text=p.read_text(encoding='utf-8')
 heading="function mapHeading(tag,title,ids,contextOnly=false){const h=el(tag,title),labels=[...new Set(ids)].map(id=>{const topic=current.topics.find(x=>x.compression_topic_id===id);check(topic,'Unresolved map topic');return pick(topic,'title');});if(labels.length)h.append(el('span',(current.locale==='en'?' (':'（')+(contextOnly?(current.locale==='en'?'Context: ':'相关背景：'):'')+labels.join(' · ')+(current.locale==='en'?')':'）'),'monthly-route-map-label'));return h;}"
 text=re.sub(r'function mapHeading\([^\n]+',lambda _:heading,text,count=1)
 text=text.replace("mapHeading('h3',pick(r,'title'),mappings.map(l=>l.compression_topic_id))", "mapHeading('h3',pick(r,'title'),mappings.map(l=>l.compression_topic_id),mappings.every(l=>l.relation_kind==='research_context'))")
 text=text.replace("family.open=opened.has(familyId);","family.open=true;")
 text=text.replace("d.open=opened.has(r.update_id);","d.open=true;")
 anchor="}card.append(links);\n  const detail=el('a',ui('analysis_focus_argument')"
 replacement="}card.append(links);\n  field(card,'analysis_focus_reason',pick(a,'rationale'));\n  field(card,'analysis_focus_probe',pick(a,'recommendation'));\n  const detail=el('a',ui('analysis_focus_argument')"
 if anchor in text:text=text.replace(anchor,replacement,1)
 p.write_text(text,encoding='utf-8')

 # A small shared style layer: restrained typography, space between ideas, no second tab bar.
 css='''/* Reader editorial layer: shared by all five views and topic pages. */
.compression-research-workbench{--reading-ink:#183447;--reading-muted:#536778}
.compression-research-workbench .wb-view-tabs{display:none!important}
.compression-research-workbench #topic-title{font-size:clamp(26px,2.5vw,38px);line-height:1.3;letter-spacing:-.025em;margin:8px 0 16px}
.compression-research-workbench #runtime-status:empty{display:none}
.compression-research-workbench #reading-guide{margin:0 0 24px;background:#f5f8f9;box-shadow:none;border:1px solid #e1e9ed;border-radius:10px}
.compression-research-workbench #reading-guide li{line-height:1.75}
.compression-research-workbench p{line-height:1.85;overflow-wrap:anywhere}
.compression-research-workbench .direction-section>p,.compression-research-workbench .topic-dossier-card>p:not(.meta):not(.topic-dossier-type){max-width:76ch}
.compression-research-workbench .research-overview-section{margin:0 0 44px}
.compression-research-workbench .direction-section{margin:24px 0}
.compression-research-workbench .research-overview-section>h2{padding:0 0 12px;border-bottom:1px solid #dce7eb;font-size:clamp(23px,2vw,30px);color:var(--reading-ink)}
.compression-research-workbench .topic-dossier-card{box-shadow:none;border-color:#dfe8ed;border-radius:12px;padding:22px 26px;background:#fff}
.compression-research-workbench .topic-dossier-card h3,.compression-research-workbench .topic-dossier-card h4{line-height:1.55;font-size:20px;margin:8px 0 14px}
.compression-research-workbench .topic-dossier-type{font-size:12px;letter-spacing:.04em;color:var(--reading-muted);margin:0 0 8px}
.compression-research-workbench .topic-dossier-citations{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;font-size:12px}
.compression-research-workbench .topic-dossier-citations a{border:0!important;background:transparent!important;padding:2px!important;box-shadow:none!important;font-weight:600}
.compression-research-workbench [data-source-family]{box-shadow:none!important;transition:border-color .15s ease}
.compression-research-workbench [data-source-family] p{font-size:15px;line-height:1.85;max-width:80ch}
.compression-research-workbench #channel-cards h5{font-size:18px;line-height:1.55}
.compression-research-workbench #channel-cards h4{font-size:14px;color:#647786;margin:22px 0 12px}
.compression-research-workbench .meta{font-size:13px;line-height:1.7;color:var(--reading-muted)}
.compression-research-workbench .topic-takeaway{font-size:18px;line-height:1.8;color:#173f4d;background:#edf6f5;border-left:3px solid #0d817f;border-radius:0 8px 8px 0;padding:16px 20px;max-width:76ch;margin:20px 0}
@media(min-width:1051px){.compression-research-workbench .research-reader-tabs,.compression-research-workbench .topic-report-actions{display:none}}
@media(max-width:760px){.compression-research-workbench .topic-dossier-card{padding:18px}.compression-research-workbench #reading-guide ul{grid-template-columns:1fr}.compression-research-workbench .topic-dossier-card h3{font-size:18px}}
'''
 (BASE/'reader-editorial.css').write_text(css,encoding='utf-8')
 for name in ['index.html','topic.html','monthly.html','foundations.html']:
  p=BASE/name;t=p.read_text(encoding='utf-8')
  if 'reader-editorial.css' not in t:t=t.replace('</head>','<link rel="stylesheet" href="reader-editorial.css?v=20261022">\n</head>',1)
  p.write_text(t,encoding='utf-8')
 rebuild()

def rebuild():
 helper=ROOT/'vendor/ai-infra/tools/cloud_core/build_reader_entry.py'
 spec=importlib.util.spec_from_file_location('reader_build',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=SITE;module.BASE=BASE
 for topic,name in [(False,'reader-entry.js'),(True,'topic-entry.js')]:
  (BASE/name).write_bytes(module.build(topic).encode('utf-8'))
 # Foundations have their own entry bundle. Rebuild it alongside the readers so
 # source edits cannot silently leave the public formula reference stale.
 packs={lang:json.loads((BASE/f'data/foundations-ui.{lang}.json').read_text(encoding='utf-8')) for lang in ['zh','en']}
 foundation='// Generated shared foundations UI; facts remain in canonical compression tables.\n'+'globalThis.LRICloudFoundationUIPacks='+json.dumps(packs,ensure_ascii=False,separators=(',',':'))+';\n'+'\n'.join((BASE/name).read_text(encoding='utf-8') for name in ['runtime/mcp-table-read.js','runtime/tablegit.js','foundations.js'])
 (BASE/'foundations-entry.js').write_bytes(foundation.encode('utf-8'))
 path=BASE/'foundations.html';text=path.read_text(encoding='utf-8');digest=hashlib.sha256(foundation.encode('utf-8')).hexdigest()[:16]
 text=re.sub(r'foundations-entry\.js(?:\?[^"\s]*)?',lambda _:'foundations-entry.js?v='+digest,text);path.write_bytes(text.encode('utf-8'))
 for name in ['index.html','topic.html','monthly.html']:
  path=BASE/name;t=path.read_text(encoding='utf-8');reader=re.search(r'data-lri-reader="([^"]+)"',t)[1].split('?')[0];digest=hashlib.sha256((BASE/reader).read_bytes()).hexdigest()[:16]
  bootstrap=(BASE/'reader-bootstrap.js').read_text(encoding='utf-8').rstrip()
  t=re.sub(r'<script data-lri-reader-bootstrap>[\s\S]*?</script>',lambda _:'<script data-lri-reader-bootstrap>\n'+bootstrap+'\n</script>',t)
  t=re.sub(r'data-lri-reader="[^"]+"',lambda _:'data-lri-reader="'+reader+'?v=reader-content-'+digest+'"',t);path.write_bytes(t.encode('utf-8'))
 # Navigation and stylesheet fixes must invalidate the same URLs on every entry
 # page, including the extension-free URLs used by static hosting.
 shell_hash=hashlib.sha256((SITE/'assets/lri-shell.js').read_bytes()).hexdigest()[:16]
 for name in ['index.html','topic.html','monthly.html','foundations.html']:
  path=BASE/name;t=path.read_text(encoding='utf-8')
  t=re.sub(r'lri-shell\.js\?v=[^"\s]+',lambda _:'lri-shell.js?v='+shell_hash,t)
  for asset in ['reader-atlas.css','foundations-quickref.css','source-directory.css']:
   digest=hashlib.sha256((BASE/asset).read_bytes()).hexdigest()[:16]
   t=re.sub(re.escape(asset)+r'\?v=[^"\s]+',lambda _:asset+'?v='+digest,t)
  t=t.replace('正在连接 TableGit…','正在读取研究资料…').replace('<title>压缩基础 · 云核 · LRI</title>','<title>压缩基础 · 极智 AI Infra</title>')
  path.write_bytes(t.encode('utf-8'))
 # Rebuild UI cache from its tracked manifest, retaining shell asset ownership and policy.
 worker=BASE/'reader-ui-cache.js';text=worker.read_text(encoding='utf-8');match=re.search(r'const ASSETS=(.*);',text);assets=json.loads(match[1]);updated={}
 for url in assets:
  clean=url.split('?')[0];path=(BASE/clean).resolve()
  if clean in ['reader-entry.js','topic-entry.js']:
   digest=hashlib.sha256(path.read_bytes()).hexdigest();url=clean+'?v=reader-content-'+digest[:16]
  updated[url]=hashlib.sha256(path.read_bytes()).hexdigest()
 text=text[:match.start(1)]+json.dumps(updated,separators=(',',':'))+text[match.end(1):]
 digest=hashlib.sha256(json.dumps(updated,sort_keys=True).encode()).hexdigest()[:16];text=re.sub(r'const CACHE="[^"]+";',lambda _:'const CACHE="lri-cloud-ui-'+digest+'";',text);worker.write_bytes(text.encode('utf-8'))
 print('UI copy and reader bundles rebuilt')

if __name__=='__main__':main()
