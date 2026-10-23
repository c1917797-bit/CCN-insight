"""Small, self-contained SVG explanations for the operator research reader."""
from html import escape
import re


INK = '#d8e9f1'
MUTED = '#8ba9ba'
TEAL = '#55ded0'
BLUE = '#79a9ff'
AMBER = '#f6bf74'


def txt(x, y, value, size=17, color=INK, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(value)}</text>'


def box(x, y, w, h, color='#153449', radius=9, stroke='#2d5368'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{color}" stroke="{stroke}"/>'


def line(x1, y1, x2, y2, color=TEAL, dashed=False, width=2):
    dash = ' stroke-dasharray="5 6"' if dashed else ''
    return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="{width}" fill="none"{dash}/>'


def arrow(x1, y, x2, color=TEAL):
    return line(x1, y, x2, y, color)+f'<path d="M{x2-7} {y-5}l7 5l-7 5" stroke="{color}" stroke-width="2" fill="none"/>'


def circle(x, y, label, color=TEAL, radius=22):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#17364a" stroke="{color}" stroke-width="2"/>'+txt(x, y+6, label, 16, color, 'middle', 600)


def panels(left, right):
    return box(16, 18, 364, 262, '#102b3e')+box(396, 18, 364, 262, '#10313f', stroke='#2e6269')+txt(38, 52, left, 17, BLUE, weight=600)+txt(418, 52, right, 17, TEAL, weight=600)


def matrix(x, y, rows=4, cols=4, step=23, row_colors=False, size=18):
    colors = [TEAL, BLUE, AMBER, '#b197ef']
    return ''.join(box(x+c*step, y+r*step, size, size, colors[(r if row_colors else c) % len(colors)], 3, 'none') for r in range(rows) for c in range(cols))


def route_svg(route_id):
    s=''
    if route_id == 'memory-reuse':
        s=panels('重复加载相同数据', '加载一次，片上重复使用')
        s+=box(39, 100, 86, 95)+txt(82, 140, '外存', 21, anchor='middle')+txt(82, 167, '同一块数据', 12, MUTED, 'middle')
        for y in [107, 160, 213]:
            s+=arrow(135, y, 257, BLUE)+box(265, y-20, 88, 40)+txt(309, y+6, '计算', 16, anchor='middle')
        s+=box(417, 132, 72, 55)+txt(453, 165, '外存', 17, anchor='middle')+arrow(498, 160, 536)
        s+=box(544, 113, 86, 93, '#164c55', stroke=TEAL)+txt(587, 150, '片上', 20, TEAL, 'middle')+txt(587, 178, '可复用块', 13, TEAL, 'middle')
        for y in [102, 160, 218]:
            s+=line(634, 160, 661, y)+box(667, y-18, 67, 36)+txt(700, y+6, '计算', 15, anchor='middle')
        s+=txt(38, 257, '重复访问消耗外存带宽', 14, MUTED)+txt(418, 257, '代价转移到片上容量与复用组织', 14, MUTED)
        caption='相同数据被多次使用的示意。复用减少外存访问，但会占用片上存储；收益取决于原先是否受访存限制。'
    elif route_id == 'tile-parallelism':
        s=panels('搬运与计算串行', '按块推进，交叠独立阶段')
        for x in [51, 147, 243]:
            s+=box(x, 119, 26, 37, BLUE, 4, 'none')+box(x+27, 119, 40, 37, TEAL, 4, 'none')+box(x+68, 119, 22, 37, AMBER, 4, 'none')
        s+=txt(40, 97, '块1              块2              块3', 13, MUTED)
        for i,(label,color,width,offset) in enumerate([('读入',BLUE,26,0),('计算',TEAL,40,28),('写回',AMBER,22,70)]):
            y=97+i*51
            s+=txt(416, y+24, label, 13, MUTED)
            for j in range(3):
                x=468+j*44+offset
                s+=box(x,y,width,30,color,4,'none')+txt(x+width/2,y+21,str(j+1),12,'#102638','middle',600)
        s+=line(458, 246, 733, 246, '#587d90')+txt(38, 257, '总时间包含所有串行阶段', 14, MUTED)+txt(418, 270, '稳态节拍受最慢阶段与共享资源限制', 13, MUTED)
        caption='三块数据的概念流水。横向长度仅用于解释阶段关系；填充、排空、尾块和资源争用均会增加实际耗时。'
    elif route_id == 'fusion-launch':
        s=panels('三个独立操作', '保留依赖，融合共同执行')
        for i, label in enumerate(['MatMul','Bias','GELU']):
            x=40+i*109
            s+=box(x,105,82,58)+txt(x+41,140,label,15,anchor='middle')
            s+=line(x+41,166,x+41,205,AMBER)+txt(x+41,228,'中间写回' if i<2 else '输出',11,MUTED,'middle')
            if i<2:s+=arrow(x+87,134,x+103,BLUE)
        s+=box(427,98,302,90,'#164550',stroke=TEAL)
        for i,label in enumerate(['MM','+b','G']):
            x=460+i*91
            s+=circle(x,143,label,TEAL,22)
            if i<2:s+=arrow(x+26,143,x+64)
        s+=txt(579,219,'中间数据在融合核内部传递',14,TEAL,'middle')+txt(38,260,'启动、同步和中间物化均可能重复',13,MUTED)+txt(418,260,'同时关注寄存器、片上容量和可并行性',13,MUTED)
        caption='以MatMul→Bias→GELU为示意链，融合减少启动或中间物化。具体可融合范围取决于依赖和后端；图捕获减少提交开销，属于另一种手段。'
    elif route_id == 'layout-low-precision':
        s=panels('逻辑张量与物理存放', '生产者与计算核协同布局')
        s+=matrix(48,92)+txt(94,216,'同一逻辑 shape',14,MUTED,'middle')
        s+=arrow(151,137,197,BLUE)+box(207,109,140,63)+txt(277,136,'运行期转换',17,anchor='middle')+txt(277,158,'转置 / 解包',12,MUTED,'middle')
        s+=matrix(430,92,row_colors=True)+arrow(533,137,579)+box(588,104,140,70,'#164550',stroke=TEAL)+txt(658,135,'直接消费',19,TEAL,'middle')+txt(658,160,'匹配布局与数据类型',11,MUTED,'middle')
        s+=txt(38,257,'物理转换可能反复出现',14,MUTED)+txt(418,257,'准备成本按复用次数摊销',14,MUTED)
        caption='颜色表示数据分组，未表示实际数值或位宽。布局匹配、打包格式和低精度算术需要分别核对，文件变小不能证明计算核已使用低精度。'
    elif route_id == 'collectives-topology':
        s=panels('Ring：按环交换与归约', 'Tree：分层汇聚与分发')
        nodes=[(103,117),(260,117),(296,205),(181,245),(66,205)]
        for i,(x,y) in enumerate(nodes):
            nx,ny=nodes[(i+1)%len(nodes)];s+=line(x,y,nx,ny,BLUE)
        for i,(x,y) in enumerate(nodes):s+=circle(x,y,str(i),BLUE,20)
        tree=[(579,94),(478,164),(680,164),(478,235),(680,235)]
        for a,b in [(0,1),(0,2),(1,3),(2,4)]:s+=line(*tree[a],*tree[b])
        for i,(x,y) in enumerate(tree):s+=circle(x,y,str(i),TEAL,18)
        caption='两侧都是5个rank的组织示意。集合语义固定后，再比较通信轮次、关键路径字节与拓扑匹配；图形不预设哪种算法在所有消息规模上更快。'
    elif route_id == 'launch-granularity':
        s=panels('多次独立发送', '聚合后的真实传输')
        for i in range(5):
            y=85+i*33
            s+=box(43,y,31,20,AMBER,3,'none')+box(79,y,74,20,BLUE,3,'none')
        for i in range(2):
            y=109+i*72
            s+=box(425,y,31,30,AMBER,3,'none')
            for j in range(3 if i==0 else 2):
                s+=box(461+j*74,y,72,30,TEAL,3,'none')
        s+=txt(42,267,'固定启动成本 × 实际发送次数',14,MUTED)+txt(418,267,'收益扣除等待、打包和缓冲开销',14,MUTED)
        caption='两侧都是5份相同载荷，右侧按3份和2份聚合；橙色表示启动成本。API分组并不保证消息真的聚合，收益还要扣除等齐消息与打包的时间。'
    elif route_id == 'paths-buffers':
        s=panels('数据准备、拷贝与中转', '可支持的直接路径与缓冲复用')
        for i,(label,sub) in enumerate([('设备 A','源缓冲'),('中转区','准备 / 拷贝'),('设备 B','目标缓冲')]):
            x=35+i*115;s+=box(x,112,98,72)+txt(x+49,141,label,16,anchor='middle')+txt(x+49,164,sub,11,MUTED,'middle')
            if i<2:s+=arrow(x+101,148,x+112,BLUE)
        s+=box(422,109,109,80)+txt(477,142,'设备 A',18,anchor='middle')+txt(477,169,'可复用缓冲',12,MUTED,'middle')
        s+=box(625,109,109,80)+txt(680,142,'设备 B',18,anchor='middle')+txt(680,169,'完成后消费',12,MUTED,'middle')+arrow(541,149,615)
        s+=txt(579,220,'路径、所有权与完成事件共同约束',13,TEAL,'middle')
        caption='抽象传输路径示意。是否支持直达、注册或特定互连，由实际设备与后端决定；首次建立与稳态成本应分列。'
    elif route_id == 'compute-communication-overlap':
        s=panels('串行等待', '独立工作重叠，保留必要等待')
        s+=txt(40,97,'计算',13,MUTED)+box(42,115,167,40,BLUE,5,'none')+txt(127,141,'计算',16,'#102638','middle',600)
        s+=box(210,115,129,40,AMBER,5,'none')+txt(274,141,'通信',16,'#102638','middle',600)
        s+=line(43,214,341,214,'#577d91')+txt(191,242,'模块完成',13,MUTED,'middle')
        s+=box(426,103,181,36,BLUE,5,'none')+box(526,154,129,36,TEAL,5,'none')+box(608,103,47,36,AMBER,4,'none')
        s+=txt(516,128,'可独立计算',15,'#102638','middle',600)+txt(590,179,'通信',15,'#102638','middle',600)+txt(631,127,'等待',12,'#102638','middle')
        s+=line(655,94,655,227,AMBER,True)+arrow(665,212,729,TEAL)+txt(694,239,'消费结果',13,TEAL,'middle')
        caption='关键在于缩短模块完成时间，而非图上出现重叠。并发会争用计算、带宽或缓冲，实际收益需要包含这些减速。'
    elif route_id == 'transfer-compression':
        s=panels('原始传输', '编码、传输、恢复的完整成本')
        s+=matrix(50,90,4,6,step=29,size=22)+txt(140,239,'原始载荷',17,BLUE,'middle')
        s+=box(428,101,74,101)+txt(465,144,'编码',20,anchor='middle')+txt(465,172,'新增计算',11,AMBER,'middle')
        s+=arrow(508,150,539)+box(544,110,93,53,TEAL,5,'none')+txt(590,142,'载荷',16,'#102638','middle',600)
        s+=box(544,169,93,28,AMBER,4,'none')+txt(590,188,'元数据',12,'#102638','middle')
        s+=arrow(643,150,666)+box(673,101,65,101)+txt(705,144,'恢复',19,anchor='middle')+txt(705,172,'误差 / 同步',10,AMBER,'middle')
        s+=txt(418,250,'传输节省必须覆盖编解码与新增同步',13,MUTED)
        caption='消息必须形成实际可传输的编码，元数据也占字节。有损方案还要追踪归约及后续计算中的误差。'
    else:
        raise ValueError(route_id)
    aria=escape(caption,quote=True)
    svg='<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'+aria+'" viewBox="0 0 776 300" class="op-mechanism-svg op-mechanism-wide">'+s+'</svg>'
    # Keep the same topology; omit fine-print labels on narrow screens. The full
    # interpretation stays in selectable HTML below the diagram.
    def mobile_label(match):
        node=match.group(0)
        size=int(re.search(r'font-size="(\d+)"',node)[1])
        if size<13:
            return ''
        return re.sub(r'font-size="\d+"','font-size="'+str(max(15,size))+'"',node)
    mobile_art=re.sub(r'<text\b[^>]*>.*?</text>',mobile_label,s)
    mobile='<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'+aria+'" viewBox="0 0 396 610" class="op-mechanism-svg op-mechanism-mobile"><svg x="0" y="0" width="396" height="300" viewBox="0 0 396 300">'+mobile_art+'</svg><svg x="0" y="310" width="396" height="300" viewBox="386 0 396 300">'+mobile_art+'</svg></svg>'
    return '<figure class="op-figure op-figure-dark"><div class="op-figure-scroll">'+svg+mobile+'</div><figcaption>'+escape(caption)+'</figcaption></figure>'


def hero_svg():
    art='<defs><linearGradient id="atlas-die" x2="1" y2="1"><stop stop-color="#1e6673"/><stop offset="1" stop-color="#102e46"/></linearGradient><radialGradient id="atlas-halo"><stop stop-color="#51dcc5" stop-opacity=".18"/><stop offset="1" stop-color="#51dcc5" stop-opacity="0"/></radialGradient></defs>'
    art+='<circle cx="220" cy="140" r="130" fill="url(#atlas-halo)"/>'
    for radius in [90,115]:
        art+=f'<ellipse cx="220" cy="144" rx="{radius*1.55}" ry="{radius*.9}" fill="none" stroke="#4d9ea5" stroke-opacity=".15" stroke-dasharray="3 8"/>'
    art+='<path d="M134 113L224 66L314 113V182L224 229L134 182Z" fill="#0b2234" stroke="#4ac4bc" stroke-opacity=".65"/>'
    art+='<path d="M134 113L224 160L314 113L224 66Z" fill="url(#atlas-die)" stroke="#6bd8cd" stroke-opacity=".6"/><path d="M134 113L224 160V229L134 182Z" fill="#173e53"/><path d="M224 160L314 113V182L224 229Z" fill="#103346"/>'
    for r in range(4):
        for c in range(4):
            x=224+(c-r)*17;y=94+(c+r)*9
            art+=f'<path class="op-chip-tile" style="--tile:{r+c}" d="M{x} {y}l12 6l-12 6l-12-6Z" fill="{TEAL if (r+c)%3 else BLUE}" opacity=".6"/>'
    for y in [91,128,165]:
        art+=f'<path d="M18 {y}H72L134 {y+22}" fill="none" stroke="#3e748d"/><path class="op-signal" d="M18 {y}H72L134 {y+22}"/>'
        art+=box(18,y-7,32,14,'#274e68',3,BLUE)
    for x,y in [(377,88),(396,175),(335,237)]:
        art+=f'<path d="M286 167Q342 166 {x} {y}" fill="none" stroke="#3a747e"/><path class="op-signal" d="M286 167Q342 166 {x} {y}"/>'
        art+=circle(x,y,'',TEAL,13)
    art+=txt(57,236,'数据搬运',17,BLUE,'middle')+txt(223,262,'计算执行',17,TEAL,'middle')+txt(363,46,'多卡通信',17,TEAL,'middle')
    return '<svg class="op-hero-visual" viewBox="0 0 430 280" role="img" aria-label="数据搬运、片上计算、多卡通信的概念数据流；不代表设备测量">'+art+'</svg>'
