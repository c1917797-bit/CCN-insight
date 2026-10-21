"""Typed normalized TableGit model and clearly labelled design proposals."""
import json
from pathlib import Path
from build_migration import stable, BATCH_ID, NOW, ROOTS, MODULES

BASE = {'business_id': 'string'}
SPECS = {
 'modules': ('module_id', {'name_zh':'string','name_en':'string','order':'integer','logical_prefix':'string','purpose':'text','stage_id':'string'}, ['business_id','order']),
 'folders': ('folder_id', {'module_id':'string','parent_id':'string','name':'string','logical_path':'path'}, ['module_id','parent_id']),
 'documents': ('document_id', {'module_id':'string','folder_id':'string','title':'string','document_kind':'string','logical_path':'path','body':'markdown','body_sha256':'string','source_date':'string','source_status':'string','review_status':'string','batch_id':'string'}, ['module_id','document_kind','review_status','batch_id']),
 'sources': ('source_id', {'canonical_url':'string','title':'string','source_kind':'string','provider':'string','external_id':'string','verification_status':'string','update_policy':'string','last_checked_at':'string','batch_id':'string'}, ['canonical_url','source_kind','provider','external_id','verification_status','batch_id']),
 'source_refs': ('reference_id', {'source_id':'string','document_id':'string','module_id':'string','origin_note':'path','origin_title':'string','observed_url':'string','observed_version':'string','discovered_at':'string','source_status':'string','reference_kind':'string','batch_id':'string'}, ['source_id','document_id','module_id','reference_kind','batch_id']),
 'links': ('link_id', {'from_document_id':'string','target_name':'string','to_document_id':'string','link_kind':'string','resolution_status':'string','batch_id':'string'}, ['from_document_id','to_document_id','resolution_status']),
 'scenarios': ('scenario_id', {'name':'string','description':'text','origin':'string','source_document_id':'string','review_status':'string'}, ['review_status','origin']),
 'constraints': ('constraint_id', {'scenario_id':'string','name':'string','requirement':'text','source_document_id':'string','source_section':'string','origin':'string','review_status':'string'}, ['scenario_id','source_document_id','review_status']),
 'metrics': ('metric_id', {'scenario_id':'string','name':'string','unit':'string','direction':'string','measurement_contract':'text','target_rule':'text','origin':'string','source_document_id':'string','review_status':'string'}, ['scenario_id','direction','review_status']),
 'benchmarks': ('benchmark_id', {'metric_id':'string','source_id':'string','scenario_id':'string','version':'string','hardware':'string','model':'string','workload':'string','observed_at':'string','valid_until':'string','value':'number','unit':'string','review_status':'string'}, ['metric_id','scenario_id','valid_until','review_status']),
 'experiments': ('experiment_id', {'scenario_id':'string','hypothesis':'text','metric_id':'string','baseline_id':'string','acceptance_rule':'text','owner_person_id':'string','status':'string','decision_id':'string','due_at':'string'}, ['scenario_id','status','metric_id']),
 'measurements': ('measurement_id', {'experiment_id':'string','metric_id':'string','benchmark_id':'string','value':'number','unit':'string','sample_count':'integer','percentile':'string','measured_at':'string','evidence_source_id':'string','review_status':'string'}, ['experiment_id','metric_id','review_status']),
 'decisions': ('decision_id', {'experiment_id':'string','decision':'string','rationale':'text','reviewer_person_id':'string','decided_at':'string','status':'string','next_stage_id':'string'}, ['experiment_id','status','next_stage_id']),
 'flywheel_stages': ('stage_id', {'order':'integer','name_zh':'string','name_en':'string','inputs':'text','outputs':'text','cadence':'string','feedback_stage_id':'string','origin':'string','review_status':'string'}, ['order','review_status']),
 'stage_gates': ('gate_id', {'stage_id':'string','gate_order':'integer','rule':'text','failure_action':'text','status':'string'}, ['stage_id','gate_order']),
 'entity_refs': ('entity_ref_id', {'source_id':'string','target_table':'string','target_key':'string','relation_type':'string','verification_status':'string'}, ['source_id','target_table','target_key']),
 'import_issues': ('issue_id', {'batch_id':'string','subject_id':'string','issue_type':'string','status':'string','description':'text'}, ['batch_id','issue_type','status']),
 'import_runs': ('batch_id', {'status':'string','source_policy':'text','started_at':'string','completed_at':'string','scanned_notes':'integer','document_count':'integer','source_count':'integer','reference_count':'integer','excluded_name_count':'integer','excluded_content_count':'integer','retained_local_count':'integer','payload_audit':'string'}, ['status','completed_at']),
}


def definitions():
    result = {}
    for name, (key, fields, indexes) in SPECS.items():
        types = {key:'string', **BASE, **fields}
        definition = {'key_field':key,'description':f'Cloud Core {name}: typed rows, stable keys and explicit relationships; no whole-domain JSON blob. Persistent history.',
                      'fields':{field:{'type':type_, 'role':'key' if field == key else 'value', 'required':True,
                                       'projection':'deferred' if field == 'body' else 'default'} for field,type_ in types.items()},
                      'required_fields':list(types), 'indexes':[{'name':'idx_'+field,'field':field} for field in dict.fromkeys(['business_id',*indexes])]}
        result['cloud_core_'+name] = definition
    return result


def seeds():
    rows = {}
    titles = [('工作台与治理','Workbench & governance','敏感信息检查、质量守门和人工评审','sense'),
              ('一手信源','Primary sources','URL登记、日期与版本核验','sense'),
              ('知识关联','Knowledge graph','来源、论点、方案和业务约束关联','connect'),
              ('时序雷达','Temporal radar','日周月信号、过期与基准变化追踪','sense'),
              ('洞察与课题','Insights & initiatives','双轮驱动、五看三定、反方证据与课题规划','decide'),
              ('学术研究','Academic research','论文原始URL、证据及可复核研究引用','connect')]
    rows['cloud_core_modules']=[dict(module_id=m,business_id='cloud-core',name_zh=z,name_en=e,order=i,logical_prefix=ROOTS[i],purpose=p,stage_id=s) for i,(m,(z,e,p,s)) in enumerate(zip(MODULES,titles))]
    method=stable('note','4_AI情报洞察/方法论/输入/研究方法_业务驱动.md')
    goal=stable('note','4_AI情报洞察/方法论/输入/目标.md')
    call=stable('note','4_AI情报洞察/场景化创新/AI通话助手综合分析.md')
    scenario_data=[('llm','LLM推理','MoE、长上下文与多卡通信约束',method,'imported_template'),('agent','Agent多轮','多轮状态、工具调用和持久化记忆',method,'imported_template'),('multimodal','多模态','图像、视频、音频与文本实时处理',method,'imported_template'),('asr','语音识别','流式窗口、噪声、长音频与说话人分离',method,'imported_template'),('tts','语音合成','首音时延、音质及长文本韵律',method,'imported_template'),('call-assistant','运营商AI通话助手','核心网接入、AI对话、防诈和家庭接管闭环',call,'cloud_core_design')]
    rows['cloud_core_scenarios']=[dict(scenario_id=s,business_id='cloud-core',name=n,description=d,source_document_id=source,origin=origin,review_status='proposed_unverified') for s,n,d,source,origin in scenario_data]
    constraints=[('llm','部署拓扑','记录单卡/多卡、TP/PP/EP及MoE结构；禁止跨硬件直接比较。',method,'§2.1 场景A'),('llm','上下文与并发','记录序列长度分布、并发和KV显存瓶颈。',method,'§2.1 场景A'),('agent','状态连续性','记录轮数、工具频次、状态保留和多Agent协同条件。',method,'§2.1 场景B'),('asr','噪声与流式','分别评估噪声、语种、说话人分离及流式窗口。',method,'§2.1 场景D'),('tts','首音与音质','首音、MOS及长文本韵律需要同时达标；原文阈值属于方案目标。',method,'§2.1 场景E'),('call-assistant','通话链路','核心网信令/媒体接入和AI处理需端到端联调；失败应回退到正常通话。',call,'§3.2 / §3.7'),('call-assistant','误报与漏报','防诈质量分别记录误报、漏报与高风险召回；不能以总准确率替代。',call,'§3.4 / 云核补充设计'),('call-assistant','授权与数据边界','仅使用有授权、已脱敏的验证样本；生产通话内容不进入情报资料库。',call,'§3.7 / 云核补充设计'),('call-assistant','家庭接管','验证跨品牌守护通知与人工接管链路的成功率和时延。',call,'§3.6 / 云核补充设计')]
    rows['cloud_core_constraints']=[dict(constraint_id='constraint-'+str(i+1),business_id='cloud-core',scenario_id=s,name=n,requirement=r,source_document_id=d,source_section=sec,origin='design_grounded_in_source',review_status='proposed_unverified') for i,(s,n,r,d,sec) in enumerate(constraints)]
    metrics=[('ttft','llm','首Token时延','ms','lower','同硬件/模型/输入长度/并发；记录P50/P95','当季可比基准×0.7；源方案目标待复核',goal),('tpot','llm','Token间时延','ms/token','lower','区分Prefill/Decode；固定并发与输出长度','当季可比基准×0.7；源方案目标待复核',goal),('tps','llm','吞吐','token/s','higher','固定模型、精度、并发和统计窗口','可比基准×1.3；源方案目标待复核',goal),('cost','llm','单位推理成本','currency/1M tokens','lower','标注币种、日期、利用率与输入输出比例','同口径基准×0.7；不导入旧示例作实测值',goal),('accuracy-loss','llm','任务精度损失','percentage_point','lower','同任务集、同模型、同版本对照','原方案≤1%；复核百分比/百分点口径',goal),('e2e','call-assistant','通话AI端到端时延','ms','lower','从可观察媒体事件到首个可听响应；记录P95','业务方确认SLO后填写',call),('call-success','call-assistant','接入成功率','ratio','higher','接入成功数/有效尝试数；区分运营商和终端','业务方确认SLO后填写',call),('false-positive','call-assistant','正常通话误报率','ratio','lower','误报正常样本数/全部正常样本数','按场景和风险层级评审阈值',call),('fraud-recall','call-assistant','高风险召回率','ratio','higher','识别高风险数/标注高风险数；锁定数据集版本','与误报率联合验收',call),('takeover','call-assistant','守护接管时延','ms','lower','从授权接管请求到人工接入；记录P95及失败率','先确认可接管链路再填写SLO',call),('availability','call-assistant','业务连续性','ratio','higher','有效窗口内可服务请求数/总有效请求数；包含降级','运行基线和恢复目标待确认',call)]
    rows['cloud_core_metrics']=[dict(metric_id=mid,business_id='cloud-core',scenario_id=s,name=n,unit=u,direction=direction,measurement_contract=c,target_rule=t,origin='source_target_or_cloud_core_design',source_document_id=d,review_status='proposed_unverified') for mid,s,n,u,direction,c,t,d in metrics]
    stages=[('sense','一手溯源与变化侦测','Sense','公开URL、Release、论文版本、业务痛点','候选信号与版本变化','每日/事件触发','scope'),('scope','云核约束与价值筛选','Scope','候选信号、通话链路与推理资源约束','可验证问题与指标口径','每周','sense'),('connect','证据织网与双轮交汇','Connect','业务驱动问题、技术驱动证据、反方资料','来源→约束→技术→机会的可追溯关联','每周','scope'),('decide','五看三定与课题决策','Decide','趋势/市场/竞争/能力/机会；ROI与资源','控制点、目标、策略和实验立项建议','月度/立项','connect'),('validate','云核链路与公平基准验证','Validate','版本锁定的基准、联调实验、授权脱敏样本','测量记录、反方复核、可比性结论','两周实验','scope'),('deliver','灰度验收与运行反馈','Deliver','已通过评审的实验与验收条件','灰度指标、降级策略和正式决策','发布/运行窗口','validate'),('learn','回测复盘与方法更新','Learn','实际结果、误报漏报、成本与预测差异','方法版本、源权重和下一轮问题','月度/季度','sense')]
    rows['cloud_core_flywheel_stages']=[dict(stage_id=s,business_id='cloud-core',order=i+1,name_zh=z,name_en=e,inputs=inp,outputs=out,cadence=c,feedback_stage_id=f,origin='design_grounded_in_obsidian',review_status='proposed') for i,(s,z,e,inp,out,c,f) in enumerate(stages)]
    gates=[('sense','来源URL可复核；发现日期与版本分开存储；变化不自动覆盖既有证据。','保留候选状态，补来源或核验日期。'),('scope','云核场景、链路边界、SLO和成本口径明确；相关性不足不晋升。','退回筛选池，避免泛AI消息污染。'),('connect','至少存在来源及业务约束关联；正反证据分开；缺证据不形成结论。','标记证据缺口。'),('decide','五看完整、三定有依据；资源和ROI是估计时明确标注。','保持建议状态，不能代替立项审批。'),('validate','同硬件/模型/并发/版本可比；误报漏报双验收；授权脱敏样本。','退回实验设计，保留失败与反方结果。'),('deliver','实验通过、人工决策、灰度退出条件及通话降级策略完备。','禁止将未核验方案晋升为运行事实。'),('learn','预测与实测分开记录；过期基准触发重评；复盘更新方法版本。','生成下一轮问题，不静默改写历史。')]
    rows['cloud_core_stage_gates']=[dict(gate_id='gate-'+s,business_id='cloud-core',stage_id=s,gate_order=1,rule=rule,failure_action=action,status='design') for s,rule,action in gates]
    rows['cloud_core_experiments']=[dict(experiment_id='experiment-'+mid,business_id='cloud-core',scenario_id='call-assistant',hypothesis=h,metric_id=mid,baseline_id='',acceptance_rule=a,owner_person_id='',status='proposed',decision_id='',due_at='') for mid,h,a in [('e2e','核心网接入与AI流水线可在业务认可时延下完成响应。','先建立同链路基线及P95阈值；测量通过后评审。'),('false-positive','防诈识别能在可接受误报下保持高风险召回。','锁定脱敏数据集；误报率与召回率联合评审。'),('takeover','跨品牌守护通知和人工接管链路可连续运行。','验证接管成功、P95时延、故障回退与授权边界。')]]
    return rows


if __name__ == '__main__':
    output=Path(__file__).parent/'model-v1'
    output.mkdir(exist_ok=True)
    for table,definition in definitions().items():
        (output/(table+'.schema.json')).write_text(json.dumps(definition,ensure_ascii=False,indent=2),encoding='utf-8')
    for table,rows in seeds().items():
        (output/(table+'.rows.json')).write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'schemas':len(SPECS),'seed_tables':len(seeds()),'seed_rows':sum(map(len,seeds().values()))}))
