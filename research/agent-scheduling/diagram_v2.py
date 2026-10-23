"""Compact entity map. Runtime motion is driven by local draft.js, not a GIF."""
from html import escape as e

def node(key, x, y, w, h, title, note='', point=None, kind=''):
    point = point or key
    text = f'<text x="{x+16}" y="{y+30}" class="map-node-title">{e(title)}</text>'
    if note:
        text += f'<text x="{x+16}" y="{y+57}" class="map-node-note">{e(note)}</text>'
    icon = ''
    if key in ('gpu','cpu'):
        icon = f'<g transform="translate({x+w-62} {y+24})" class="resource-chip" aria-hidden="true"><rect x="0" y="0" width="34" height="34" rx="5"/><rect x="8" y="8" width="18" height="18" rx="2"/><path d="M8-6V0 M17-6V0 M26-6V0 M8 34V40 M17 34V40 M26 34V40 M-6 8H0 M-6 17H0 M-6 26H0 M34 8H40 M34 17H40 M34 26H40"/></g>'
    return f'<a href="#point-{point}" data-map-node="{key}" data-map-point="{point}" class="map-node {kind}" aria-label="{e(title)}，查看技术说明"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>{text}{icon}</a>'

def path(key, d, kind='call'):
    return f'<path id="route-{key}" data-map-edge="{key}" class="map-edge {kind}" d="{d}" marker-end="url(#map-{kind})"/>'

def diagram():
    edges = [
        ('intake','M120 177 V226','call'),
        ('agent-entry','M208 263 H244','call'),
        ('dag-menu','M368 208 L398 184','call'),
        ('dag-offer','M368 208 L398 258','call'),
        ('menu-join','M502 184 L532 208','call'),
        ('offer-join','M502 258 L532 208','call'),
        ('compare-confirm','M636 208 L666 184','call'),
        ('authorize-effect','M718 208 V234','call'),
        ('dag-ready','M718 282 V315','call'),
        ('model-call','M430 377 V467','call'),
        ('tool-call','M788 377 V467','call'),
        ('model-batch','M462 535 V563','call'),
        ('tool-api','M952 535 V563','call'),
        ('model-result','M670 597 H710 V403 H622 V377','return'),
        ('tool-result','M1152 597 H1182 V403 H842 V377','return'),
        ('user-result','M895 150 H950','return'),
        ('gpu-support','M468 681 V650','deploy'),
        ('cpu-tools','M954 681 V650','deploy'),
        ('cpu-agent','M1176 723 H1194 V208 H895','deploy'),
        ('placement','M208 480 H228 V793 H954 V765','deploy'),
        ('placement-gpu','M954 793 H468 V765','deploy'),
        ('status-feedback','M740 650 V664 H228 V632 H208','feedback'),
        ('feedback-agent','M208 620 H218 V345 H244','feedback'),
    ]
    parts = ['''<svg class="agent-map" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1220 820" role="group" aria-labelledby="map-title map-description">
<title id="map-title">咖啡任务：Agent、服务与资源的调度关系</title><desc id="map-description">从左侧用户任务进入Agent。Agent内部为咖啡任务DAG与工作流调度；向下调用模型或工具，绿色连线写回结果。底层GPU或NPU支撑模型，CPU与容器支撑Agent及工具。左侧部署和恢复为独立控制点。六步演示通过移动光点显示调用，不代表真实下单。</desc>
<defs>
<linearGradient id="console-canvas" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b182c"/><stop offset="1" stop-color="#070f20"/></linearGradient>
<linearGradient id="console-panel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#152d46"/><stop offset="1" stop-color="#0c1c32"/></linearGradient>
<linearGradient id="console-agent" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#102c41"/><stop offset="1" stop-color="#101d37"/></linearGradient>
<pattern id="console-grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#4b718c" stroke-width=".5" opacity=".14"/></pattern>
<marker id="map-call" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#4a7e9d"/></marker>
<marker id="map-return" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#228b76"/></marker>
<marker id="map-deploy" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#b99b5b"/></marker>
<marker id="map-feedback" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#b57c94"/></marker>
</defs>
<rect x="12" y="12" width="1196" height="796" rx="22" class="map-canvas"/>
<rect x="12" y="12" width="1196" height="796" rx="22" fill="url(#console-grid)" pointer-events="none"/>
<path d="M22 54V22H54 M1166 22H1198V54 M22 766V798H54 M1166 798H1198V766" class="console-corners" fill="none" pointer-events="none"/>
<text x="32" y="53" class="map-layer">01 任务与编排</text>
<text x="244" y="53" class="map-caption">任务交给Agent，Agent按依赖推进任务图</text>
<rect x="244" y="85" width="651" height="309" rx="18" class="map-container agent-container"/>
<text x="267" y="119" class="map-container-title">Agent B · 任务运行时</text>
<text x="267" y="143" class="map-caption">任务依赖＋共享状态 · 调度依据</text>
<rect x="265" y="157" width="607" height="139" rx="12" class="map-dag-area"/>
<text x="784" y="143" class="map-mini-label">咖啡DAG</text>
<text x="950" y="99" class="map-return-label">验收后返回用户</text>
<g class="console-status" aria-label="教学动画状态">
<rect x="950" y="221" width="226" height="157" rx="14" class="console-status-box"/>
<text x="969" y="247" class="console-status-label">SIMULATION / 教学演示</text>
<circle cx="1134" cy="281" r="20" class="console-orbit"/>
<path d="M1127 277L1134 273L1141 277V285L1134 289L1127 285Z M1127 277L1134 281L1141 277 M1134 281V289" class="console-core" fill="none"/>
<text x="969" y="291" data-map-svg-status="true" class="console-status-value">等待播放</text>
<text x="969" y="318" class="console-status-label">光点表示请求与结果流转</text>
''']
    parts.extend(f'<rect x="{970+i*31}" y="344" width="23" height="4" rx="2" data-phase-bit="{i}" class="console-phase-bit"/>' for i in range(6))
    parts += ['''</g>
<text x="32" y="431" class="map-mini-label">独立控制面</text>
<text x="244" y="443" class="map-layer">02 模型服务</text>
<text x="728" y="443" class="map-layer">02 工具服务</text>
<rect x="244" y="457" width="448" height="193" rx="16" class="map-container"/>
<rect x="728" y="457" width="448" height="193" rx="16" class="map-container"/>
<text x="32" y="785" class="map-mini-label">03 资源支撑</text>
<text x="622" y="421" class="map-return-label">结果写回 ↑</text>
<text x="894" y="421" class="map-return-label">结果写回 ↑</text>
<text x="440" y="418" class="map-line-label">模型调用 ↓</text>
<text x="788" y="418" class="map-line-label">工具调用 ↓</text>
''']
    parts.extend(path(key,d,kind) for key,d,kind in edges)
    parts.extend([
        node('user',32,103,176,74,'用户任务','买咖啡 · 演示实例','access','entry-node'),
        node('access',32,226,176,74,'Agent接入调度','能力匹配＋实例选择'),
        node('result',950,113,226,80,'任务结果','有效订单与支付回执','workflow','result-node'),
        node('shop',274,184,94,48,'查门店',point='workflow',kind='dag-node'),
        node('menu',398,160,104,48,'查菜单',point='workflow',kind='dag-node'),
        node('offers',398,234,104,48,'查优惠',point='workflow',kind='dag-node'),
        node('compare',532,184,104,48,'模型比较',point='model-route',kind='dag-node'),
        node('confirm',666,160,104,48,'用户授权',point='tools',kind='dag-node'),
        node('purchase',666,234,104,48,'下单支付',point='tools',kind='dag-node'),
        node('workflow',265,315,607,62,'工作流任务调度 → 执行器','依赖满足＋获得授权 → 派发就绪任务'),
        node('model-route',266,467,404,68,'模型路由调度 → 推理实例2','选择已部署副本，进入实例队列'),
        node('batch',266,563,404,68,'推理批次调度 → 本轮推理','按token与KV预算推进请求'),
        node('tools',750,467,404,68,'工具调用调度＋限流','取得额度；副作用操作核验授权'),
        node('tool-worker',750,563,404,68,'工具执行器 → 外部API','查询／订单／支付，返回业务状态','tools'),
        node('gpu',244,681,448,84,'GPU／NPU 设备组','模型计算、显存与KV缓存','placement','resource-node'),
        node('cpu',728,681,448,84,'CPU／容器／网络','支撑Agent与工具；外部API独立','placement','resource-node'),
        node('placement',32,450,176,92,'资源放置调度','部署／扩容时决策'),
        node('feedback',32,594,176,118,'运行重调度','失败／超时反馈'),
    ])
    parts.append('<text x="48" y="680" class="map-control-note">检查点 · 重试 · 接管</text>')
    # Only request/result edges receive moving packets. Resource support is static.
    parts.extend(f'<g data-flow-token="{key}" class="flow-token {kind}" aria-hidden="true"><circle r="3" data-packet-trail="1" class="token-tail tail-one"/><circle r="2" data-packet-trail="2" class="token-tail tail-two"/><circle r="10" class="token-halo"/><circle r="4" class="token-core"/></g>' for key,_,kind in edges if kind in ('call','return'))
    parts.append('</svg>')
    return ''.join(parts)
