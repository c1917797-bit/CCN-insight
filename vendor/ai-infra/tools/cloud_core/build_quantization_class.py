"""Deterministic 2.5D teaching-film scenes; synthetic data, one four-second shot per step."""
from pathlib import Path
from xml.sax.saxutils import escape
import math,json
OUT=Path(__file__).resolve().parents[2]/'business_insight/cloud_core/assets'
SCENES={'purpose':1,'precision':1,'concept':1,'tradeoff':1,'idea':5,'formula':7,'worked':6,'error':3,'groups':4,'execution':3}
VALUES=[round(.48*math.sin(i*1.71)*math.cos(i*.43),3) for i in range(42)]+[-.91,.96,.26]
INK='#eff8ff';MUTED='#b5cce2';TEAL='#6ef3e2';CORAL='#ffb08d';BLUE='#8fb6ff';GRID='#284761'

def build(key,lang,mobile=False,animated=True):
 zh=lang=='zh';L=lambda a,b:a if zh else b
 W=360 if mobile else 800;H=600 if mobile else 440
 count=SCENES[key];duration=count*4
 o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" data-cycle="{duration}" data-scene="{key}" data-style="quantization-teaching-film-v4" role="img" aria-labelledby="title desc">',
 '<title id="title">'+L('权重量化：逐步机制动画','Weight quantization: a step-by-step teaching film')+'</title>',
 '<desc id="desc">'+L('合成教学数据，非模型实测。立体粒子表示数值，轨道和处理站逐步解释量化；数学坐标、公式和结果始终可读。','Synthetic teaching data, not model measurements. Volumetric particles travel through causal processing stations; mathematical axes, formulas and results remain readable.')+'</desc>',
 '''<defs>
 <linearGradient id="stage" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#183453"/><stop offset=".48" stop-color="#0c2038"/><stop offset="1" stop-color="#071527"/></linearGradient>
 <radialGradient id="spot"><stop stop-color="#1c7d91" stop-opacity=".22"/><stop offset="1" stop-color="#122d45" stop-opacity="0"/></radialGradient>
 <radialGradient id="orbCyan" cx=".28" cy=".22" r=".85"><stop stop-color="#fff"/><stop offset=".18" stop-color="#c1fff3"/><stop offset=".52" stop-color="#54decf"/><stop offset="1" stop-color="#17688c"/></radialGradient>
 <radialGradient id="orbCoral" cx=".28" cy=".22" r=".85"><stop stop-color="#fff4de"/><stop offset=".22" stop-color="#ffd4a5"/><stop offset=".6" stop-color="#fa9b7d"/><stop offset="1" stop-color="#913a61"/></radialGradient>
 <radialGradient id="orbBlue" cx=".28" cy=".22" r=".85"><stop stop-color="#fff"/><stop offset=".2" stop-color="#dae9ff"/><stop offset=".58" stop-color="#86acff"/><stop offset="1" stop-color="#3b509b"/></radialGradient>
 <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#4f7d9b"/><stop offset=".15" stop-color="#284d6a"/><stop offset=".58" stop-color="#17314b"/><stop offset="1" stop-color="#0d2136"/></linearGradient>
 <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#356c87" stop-opacity=".8"/><stop offset=".45" stop-color="#183d59" stop-opacity=".9"/><stop offset="1" stop-color="#132b42"/></linearGradient>
 <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#80b5ff" stop-opacity=".1"/><stop offset="1" stop-color="#79ffe6" stop-opacity=".65"/></linearGradient>
 <linearGradient id="densityFill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#8cb7ff" stop-opacity=".5"/><stop offset="1" stop-color="#67eadf" stop-opacity=".02"/></linearGradient>
 <linearGradient id="errorFill" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#80b5ff" stop-opacity=".05"/><stop offset="1" stop-color="#ffb08d" stop-opacity=".35"/></linearGradient>
 <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#91ffe7"/><stop offset="1" stop-color="#206281"/></linearGradient>
 <pattern id="clipHatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><path d="M0 0 V9" stroke="#c98c88" stroke-width="1"/></pattern>
 <filter id="glow" x="-130%" y="-130%" width="360%" height="360%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 </defs>''',
 '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;font-variant-numeric:tabular-nums}path,line{stroke-linecap:round;stroke-linejoin:round}circle[fill="#fff"]{fill:#0d263d}.decoration{pointer-events:none}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>',
 f'<rect width="{W}" height="{H}" rx="16" fill="url(#stage)"/>',
 f'<ellipse cx="{W*.53}" cy="{H*.46}" rx="{W*.58}" ry="{H*.55}" fill="url(#spot)" class="decoration"/>']
 def add(v):o.append(v)
 def txt(x,y,t,size=22,color=INK,anchor=None,weight=400,extra=''):
  size=max(size,24 if mobile else 20)
  add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}"'+(f' text-anchor="{anchor}"' if anchor else '')+f' {extra}>{escape(str(t))}</text>')
 def path(d,c=GRID,w=1.5,dash=None,extra=''):
  add(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"' if dash else '')+f' {extra}/>')
 def line(x1,y1,x2,y2,c=GRID,w=1.5,dash=None,extra=''):path(f'M{x1} {y1} L{x2} {y2}',c,w,dash,extra)
 def rect(x,y,w,h,fill='none',stroke=None,r=0,extra=''):
  add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+f' {extra}/>')
 def circle(x,y,r=5,color=TEAL,hollow=False,extra=''):
  add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{"#fff" if hollow else color}" stroke="{color}" stroke-width="{2.5 if hollow else 1}" {extra}/>')
 def motion(name,frames,ease='cubic-bezier(.55,0,.2,1)'):
  if animated:add(f'<style>@keyframes {name}{{{frames}}}</style>')
  return f'style="animation:{name} {duration}s {ease} infinite"' if animated else ''
 def phase(name,step,base,focus):
  start=step/count*100;end=(step+1)/count*100-.02
  return motion(name,(f'0%,{start-.01:.3f}%{{{base}}}' if start else '')+f'{start:.3f}%,{end:.3f}%{{{focus}}}{end+.01:.3f}%,100%{{{base}}}','linear')
 def travel(name,x,y,targets):
  """Each target is (step,x,y); arrive inside that lecture step and hold exactly."""
  frames=['0%{transform:translate(0,0)}'];px=x;py=y
  for step,tx,ty in targets:
   p=100*step/count;hold=p+100*.16/count;arrive=p+100*.78/count
   frames += [f'{p:.4f}%,{hold:.4f}%{{transform:translate({px-x}px,{py-y}px)}}',f'{arrive:.4f}%{{transform:translate({tx-x}px,{ty-y}px)}}']
   px,py=tx,ty
  frames += [f'100%{{transform:translate({px-x}px,{py-y}px)}}']
  return motion(name,''.join(frames)),(px,py)
 def orb(name,x,y,r=8,color='cyan',targets=None,extra=''):
  st='';px,py=x,y
  if targets:st,end=travel(name,x,y,targets);px,py=(x,y) if animated else end
  hue=CORAL if color=='coral' else BLUE if color=='blue' else TEAL
  add(f'<ellipse cx="{px+2}" cy="{py+r*1.65}" rx="{r*1.3}" ry="{r*.38}" fill="#020914" opacity=".48" {st} class="decoration"/>')
  grad='orb'+color.title()
  add(f'<circle cx="{px}" cy="{py}" r="{r}" fill="url(#{grad})" stroke="{hue}" stroke-width=".7" {st} {extra}/>')
  add(f'<circle cx="{px-r*.28}" cy="{py-r*.32}" r="{max(1,r*.2)}" fill="#fff" opacity=".78" {st} class="decoration"/>')
 def ring(name,x,y,r,step,color=TEAL):
  st=phase(name,step,'stroke:#365b77;stroke-width:1.5','stroke:'+color+';stroke-width:3.2;filter:drop-shadow(0 0 3px '+color+')')
  circle(x,y,r,'#365b77',True,extra=st)
  # The outer arc reacts; the semantic marker never overshoots a numeric value.
  p=100*step/count;span=100/count
  st2=motion(name+'arc',f'0%,{p:.4f}%{{transform:rotate(0deg);stroke:#4b6c85}}{p+span*.25:.4f}%{{transform:rotate(-18deg);stroke:{color}}}{p+span*.7:.4f}%{{transform:rotate(95deg);stroke:{color}}}{p+span*.99:.4f}%,100%{{transform:rotate(0deg);stroke:#4b6c85}}')
  if st2:st2=st2[:-1]+f';transform-origin:{x}px {y}px"'
  path(f'M{x-r-5} {y} A{r+5} {r+5} 0 0 1 {x} {y-r-5}', '#4b6c85',1.5,extra=st2)
 def platform(x,y,w,h=15):
  add(f'<path d="M{x} {y} H{x+w} L{x+w-13} {y+h} H{x+13} Z" fill="url(#metal)" stroke="#416780" stroke-width="1" class="decoration"/>')
  line(x+12,y+3,x+w-12,y+3,'#6ea3bb',.8)
 def rail(x1,y1,x2,y2):
  line(x1,y1+3,x2,y2+3,'#020e1d',7)
  line(x1,y1,x2,y2,'#446a84',4)
  line(x1,y1-1,x2,y2-1,'#96b9ce',.75)
 def pulse(name,x,y,step,color=TEAL,r=15):
  p=100*step/count;span=100/count
  st=motion(name,f'0%,{p:.4f}%{{transform:scale(1);stroke:#31526c;stroke-width:1}}{p+span*.65:.4f}%{{transform:scale(1.28);stroke:{color};stroke-width:2.5}}{p+span*.82:.4f}%{{transform:scale(.94);stroke:{color}}}{p+span*.99:.4f}%,100%{{transform:scale(1);stroke:#31526c;stroke-width:1}}')
  if st:st=st[:-1]+f';transform-origin:{x}px {y}px"'
  add(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*.33}" fill="none" stroke="#31526c" {st} class="decoration"/>')
 def packet(name,x,y,targets):
  st,end=travel(name,x,y,targets);px,py=(x,y) if animated else end
  add(f'<g {st} class="decoration">')
  add(f'<ellipse cx="{px+2}" cy="{py+19}" rx="23" ry="5" fill="#010815" opacity=".55"/>')
  add(f'<path d="M{px-21} {py-11} L{px+18} {py-11} L{px+24} {py-5} V{py+10} L{px-17} {py+10} L{px-23} {py+4} Z" fill="url(#glass)" stroke="#8cebdc" stroke-width="1.2"/>')
  for n in range(8):rect(px-17+n*4.7,py-6,3.2,11,'url(#orbCyan)',r=1)
  add('</g>')
 def axis(y,lo=-1,hi=1,left=40,right=None,ticks=None):
  right=W-40 if right is None else right
  X=lambda v:left+(v-lo)/(hi-lo)*(right-left)
  rail(left,y,right,y)
  for v in ticks if ticks is not None else [lo,(lo+hi)/2,hi]:
   xx=X(v);line(xx,y-6,xx,y+6,'#95b6ca',1.5)
   txt(xx,y+32,f'{v:g}',20,MUTED,'middle')
  return X
 def foot(a=None,b=None):
  if a:txt(20,H-50,L(a,b or a),20,MUTED)
  txt(20,H-16,L('教学示意 · 非模型实测','Illustrative · not measurements'),20,MUTED)
 # Perspective deck: a restrained cinematic apparatus behind true 2-D mathematical axes.
 for n in range(8):
  xx=W*(n/7);line(W*.5+(xx-W*.5)*.35,H*.52,xx,H-4,'#203b53',.65)
 for yy in [H*.62,H*.73,H*.87]:line(18,yy,W-18,yy,'#1d384f',.6)
 if key=='purpose':
  # A capacity example motivates the research before any quantization vocabulary.
  # GB is decimal and the estimate covers raw weight payload only.
  if mobile:
   txt(20,42,L('为何压缩模型权重','Why compress'),30,INK,weight=600)
   if not zh:txt(20,79,'model weights?',30,INK,weight=600)
   txt(20,145,L('270亿参数 × 16 bit','27B parameters × 16 bit'),26,MUTED)
   txt(20,202,'≈ 54 GB',44,TEAL,weight=600,extra='id="purpose-capacity" data-parameters="27000000000" data-bits-per-weight="16" data-weight-bytes="54000000000"')
   txt(20,235,L('GB = 10⁹ 字节','GB = 10⁹ bytes'),24,MUTED)
   wx=40;wy=300;ww=100;wh=60;mx=225;my=300;mw=95;mh=64
  else:
   txt(32,48,L('为什么要压缩模型权重','Why compress model weights?'),32,INK,weight=600)
   txt(32,90,L('权重需要存下来，推理时还要反复读取。','Weights must be stored and repeatedly read during inference.'),24,MUTED)
   wx=130;wy=153;ww=160;wh=90;mx=520;my=153;mw=145;mh=94
  # A small stack of tensor sheets and a memory store: illustrative apparatus, not a chip claim.
  for d in [12,6,0]:
   rect(wx+d,wy-d,ww,wh,'#17354c','#709ab4',8)
  for r in range(3):
   for c in range(5):
    rect(wx+12+c*(ww-24)/5,wy+10+r*(wh-18)/3,(ww-34)/5,(wh-30)/3,'#537d9a' if (r+c)%2 else '#83b6c5',r=2)
  rect(mx+5,my+7,mw,mh,'#071728',r=10)
  rect(mx,my,mw,mh,'url(#glass)','#79adbf',10)
  for r in range(3):rect(mx+10,my+12+r*(mh-18)/3,mw-20,7,'#5b9fb0',r=3)
  ay=wy+wh/2
  path(f'M{wx+ww+18} {ay} H{mx-17}',TEAL,2)
  path(f'M{mx-25} {ay-6} L{mx-16} {ay} L{mx-25} {ay+6}',TEAL,2)
  orb('purposeRead',wx+ww+18,ay,7,'cyan',[(0,mx-17,ay)],extra='id="purpose-reading-packet"')
  if mobile:
   txt(wx+ww/2,397,L('模型权重','Weights'),24,MUTED,'middle')
   txt(mx+mw/2,397,L('存储 / 读取','Store / read'),24,MUTED,'middle')
   txt(20,470,L('权重占用存储，','Weights occupy storage.'),26,INK)
   txt(20,509,L('推理时还需反复读取。','Inference reads them again.'),26,INK)
   txt(20,563,L('仅估算权重数据','Weight payload only'),24,MUTED)
   txt(20,591,L('不含缓存、激活及运行缓冲','KV and other buffers excluded'),24,MUTED)
  else:
   txt(wx+ww/2,286,L('模型权重','Model weights'),24,MUTED,'middle')
   txt(mx+mw/2,286,L('存储容量与读取流量','Storage and read traffic'),24,MUTED,'middle')
   txt(400,362,L('270亿参数 × 16 bit ≈ 54 GB','27B parameters × 16 bit ≈ 54 GB'),34,TEAL,'middle',weight=600,
       extra='id="purpose-capacity" data-parameters="27000000000" data-bits-per-weight="16" data-weight-bytes="54000000000"')
   txt(32,415,L('十进制GB；仅权重数据，不含KV Cache、激活及运行缓冲。','Decimal GB; weight payload only, excluding KV cache, activations and runtime buffers.'),20,MUTED)
 elif key=='precision':
  # One consistent two-bit teaching example; bits are storage length.
  if mobile:
   txt(20,42,L('先看懂：什么是bit','First: what is a bit?'),30,INK,weight=600)
   txt(20,94,L('每个权重用若干二进制位','A weight uses binary digits.'),24,MUTED)
   txt(20,146,L('16 bit：16个二进制位','16 bit: sixteen binary digits'),24,INK)
   for i in range(16):rect(20+i*20,175,16,35,'#24455f','#81adc2',3,extra=f'data-precision-width="16" data-bit-index="{i}"')
   txt(20,283,L('2 bit：2个二进制位','2 bit: two binary digits'),24,INK)
   for i in range(2):rect(101+i*80,313,64,45,'#205264',TEAL,7,extra=f'data-precision-width="2" data-bit-index="{i}"')
   txt(180,436,L('2² = 4种短码','2² = 4 short codes'),34,TEAL,'middle',weight=600,
       extra='id="precision-code-count" data-bits="2" data-code-count="4"')
   txt(20,511,L('bit是存储长度，','Bit width is storage size,'),26,INK)
   txt(20,554,L('不是保留几位小数。','not decimal places.'),26,CORAL)
   txt(20,591,L('本课用2-bit解释映射','2-bit teaching example.'),24,MUTED)
  else:
   txt(32,48,L('先看懂数值格式：bit是存储长度','Read the format: bits describe storage length'),32,INK,weight=600)
   txt(32,94,L('同样保存一个权重，表示长度可以不同。','The representation of one weight can have different lengths.'),24,MUTED)
   txt(32,158,'16 bit',28,INK)
   for i in range(16):rect(200+i*27,132,20,35,'#24455f','#81adc2',3,extra=f'data-precision-width="16" data-bit-index="{i}"')
   txt(32,258,'2 bit',28,INK)
   for i in range(2):rect(200+i*81,227,66,43,'#205264',TEAL,7,extra=f'data-precision-width="2" data-bit-index="{i}"')
   txt(400,343,L('2 bit → 2² = 4种短码','2 bits → 2² = 4 short codes'),34,TEAL,'middle',weight=600,
       extra='id="precision-code-count" data-bits="2" data-code-count="4"')
   txt(32,409,L('bit不是小数位数；码怎样对应权重，下一幕看映射。','Bits are not decimal places; next we map four codes to weights.'),24,MUTED)
 elif key=='concept':
  # Four weights stay four weights; this small 2-bit example changes their values.
  weights=[-.9,-.6,.2,.4];restored=[-1.,-.5,0.,.5]
  if mobile:
   txt(20,38,L('量化不减少权重个数','Keep the four weights;'),28,INK,weight=600)
   txt(20,76,L('只改用较粗的数值','use coarser values.'),28,INK,weight=600)
   txt(20,123,L('2bit示例：只有4个档位','2-bit example: four levels'),24,MUTED)
   xs=[50,135,220,305];oy=255;ry=365
   txt(20,180,L('原始4个权重','Four original weights'),24,MUTED)
   input_text=226;restored_text=409
  else:
   txt(32,48,L('量化：权重数量不变，改用近似值','Quantization keeps the count, but approximates the values'),30,INK,weight=600)
   txt(32,91,L('本例改用2bit：只允许−1、−0.5、0、0.5四档。','A 2-bit example allows only −1, −0.5, 0 and 0.5.'),24,MUTED)
   xs=[110,300,490,680];oy=190;ry=265
   txt(32,117,L('原始权重','Original weights'),22,MUTED)
   input_text=159;restored_text=316
  for i,(v,r,xx) in enumerate(zip(weights,restored,xs)):
   color=BLUE if i<2 else TEAL
   txt(xx,input_text,f'{v:g}',30 if not mobile else 28,color,'middle',weight=600)
   circle(xx,oy,11,color,True,extra=f'id="concept-original-{i}" data-input="{v:g}"')
   line(xx,oy+15,xx,ry-19,'#6c9ab5',2,'4 6')
   path(f'M{xx-5} {ry-25} L{xx} {ry-18} L{xx+5} {ry-25}',TEAL,2)
   circle(xx,ry,11,TEAL,True,extra=f'id="concept-level-{i}" data-level="{r:g}" data-code="{i:02b}"')
   txt(xx,restored_text,f'{r:g}',30 if not mobile else 28,TEAL,'middle',weight=600)
   # One weight moves at a time within this four-second scene.
   hold=6+i*20;arrive=23+i*20;dy=ry-oy
   st=motion('conceptWeight'+str(i),f'0%,{hold}%{{transform:translate(0,0)}}{arrive}%{{transform:translate(0,{dy}px)}}100%{{transform:translate(0,{dy}px)}}')
   py=oy if animated else ry
   add(f'<ellipse cx="{xx}" cy="{py+13}" rx="12" ry="3.5" fill="#030c1b" opacity=".45" {st}/>')
   circle(xx,py,9,'url(#orbCyan)',extra=st+f' id="concept-moving-{i}" data-input="{v:g}" data-reconstructed="{r:g}" data-q="{i}"')
  if mobile:
   txt(20,459,L('还原为4个近似权重','Four approximate weights'),24,MUTED)
   txt(180,511,L('4个权重，数量不变','Still four weights'),28,INK,'middle',weight=600)
   txt(20,563,L('每个值选择最近的档位','Choose the nearest level.'),24,MUTED)
   txt(20,591,L('教学示例 · 非模型实测','Illustrative, not measured'),24,MUTED)
  else:
   txt(400,379,L('4个权重 → 4个近似值','Four weights → four approximations'),30,INK,'middle',weight=600)
   txt(32,421,L('每个值取最近档位；这是教学示例，不是模型实测。','Each value takes its nearest level; teaching data, not model measurements.'),20,MUTED)
 elif key=='tradeoff':
  # The same four values are represented by four two-bit codes, not by fewer weights.
  values=[-1.,-.5,0.,.5];codes=['00','01','10','11']
  if mobile:
   txt(20,42,L('4个短码，读回近似值','Four shorter codes'),28,INK,weight=600)
   txt(180,101,'64 bit → 8 bit',36,TEAL,'middle',weight=600,
       extra='id="tradeoff-payload" data-weight-count="4" data-original-bits="16" data-code-bits="2" data-before="64" data-after="8"')
   txt(180,142,'4 × 16 bit → 4 × 2 bit',24,MUTED,'middle')
   txt(20,197,L('保存的4个编号','Four stored codes'),24,MUTED)
   xs=[50,135,220,305];cy=241;vy=366
  else:
   txt(32,48,L('同样4个权重：编码载荷从64 bit到8 bit','The same four weights: 64 bits of payload become 8'),30,INK,weight=600)
   txt(400,101,'4 × 16 bit → 4 × 2 bit',30,TEAL,'middle',weight=600,
       extra='id="tradeoff-payload" data-weight-count="4" data-original-bits="16" data-code-bits="2" data-before="64" data-after="8"')
   xs=[110,300,490,680];cy=177;vy=296
   txt(24,177,L('保存','Store'),24,MUTED)
   txt(24,296,L('还原','Read'),24,MUTED)
  for i,(xx,code,value) in enumerate(zip(xs,codes,values)):
   add(f'<g id="tradeoff-code-{i}" data-code="{code}" data-q="{i}" data-level="{value:g}">')
   for j,bit in enumerate(code):
    bx=xx-15+j*30
    rect(bx-12,cy-27,24,35,'#204654',TEAL,5,extra=f'data-bit-sketch="int2" data-code-index="{i}" data-bit-index="{j}"')
    txt(bx,cy,bit,26,TEAL,'middle',extra=f'data-stored-bit="{bit}"')
   add('</g>')
   line(xx,cy+25,xx,vy-41,'#779eb5',2)
   path(f'M{xx-5} {vy-47} L{xx} {vy-40} L{xx+5} {vy-47}',TEAL,2)
   txt(xx,vy,f'{value:g}',30 if not mobile else 28,INK,'middle',weight=600,
       extra=f'id="tradeoff-restored-{i}" data-reconstructed="{value:g}" data-code="{code}"')
  if mobile:
   txt(20,413,L('读回4个近似权重','Four approximated weights'),24,MUTED)
   txt(20,465,L('个数没有减少，','The count stays the same;'),26,INK)
   txt(20,505,L('但不再是原来的精细值。','the fine detail is lost.'),26,INK)
   txt(20,563,L('共享尺度和零点另计','Scale / zero-point cost extra.'),24,MUTED)
   txt(20,591,L('不代表实际运行会更快','Not a speedup guarantee'),24,MUTED)
  else:
   txt(400,350,L('仅权重编码：64 bit → 8 bit','Weight codes only: 64 bit → 8 bit'),28,TEAL,'middle',weight=600)
   txt(32,391,L('读回的是近似值，不是原来的精细权重。','Read back approximate values, not the original fine-grained weights.'),24,INK)
   txt(32,423,L('共享尺度和零点另计；编码更小不代表实际加速。','Shared scale and zero-point cost extra; smaller codes do not guarantee speedup.'),20,MUTED)
 elif key=='idea':
  # A deliberately small nonnegative 2-bit alphabet teaches irreversible rounding.
  # Spatial positions are a flow layout, not an unlabelled numeric axis.
  if mobile:
   txt(20,32,L('量化：把精细数值','Quantization keeps'),26,INK,weight=600)
   txt(20,64,L('归到少数档位','an approximate value'),26,INK,weight=600)
   in_x=[130,270];in_y=128;value_y=105
   level_x=[45,135,225,315];level_y=245;level_text_y=218;code_y=278
   txt(20,105,L('原值','Input'),24,MUTED)
   txt(20,176,L('只留4档','4 levels'),24,MUTED)
  else:
   txt(24,36,L('量化：把精细数值归到少数档位','Quantization: keep only a few representable values'),26,INK,weight=600)
   in_x=[264,448];in_y=108;value_y=87
   level_x=[170,330,490,650];level_y=195;level_text_y=169;code_y=233
   txt(24,87,L('原来的权重','Original weights'),24,MUTED)
   txt(24,134,L('只允许4档近似值','Four allowed levels'),24,MUTED)
  levels=[0.0,0.3,0.6,0.9];codes=['00','01','10','11']
  selected_x=level_x[1]
  for i,(v,code,xx) in enumerate(zip(levels,codes,level_x)):
   st=phase('ideaLevel'+str(i),1,'stroke:#86a5bf;stroke-width:1.5','stroke:'+TEAL+';stroke-width:3')
   circle(xx,level_y,11,TEAL if i==1 else BLUE,True,extra=st+f' id="idea-level-{i}" data-level="{v:.1f}" data-code="{code}"')
   txt(xx,level_text_y,f'{v:.2f}',28,TEAL if i==1 else INK,'middle',weight=600 if i==1 else 400)
   txt(xx,code_y,code,24,TEAL if i==1 else MUTED,'middle',extra=f'id="idea-code-{i}" data-code="{code}" data-level="{v:.1f}"')
  # Always-visible original markers and paths make the many-to-one mapping explicit.
  for i,(v,xx) in enumerate(zip([.26,.34],in_x)):
   color=BLUE if i==0 else CORAL
   st=phase('ideaInput'+str(i),0,'stroke:'+color+';stroke-width:2','stroke:'+color+';stroke-width:4')
   circle(xx,in_y,9,color,True,extra=st+f' id="idea-input-{i}" data-input="{v:.2f}"')
   txt(xx,value_y,f'{v:.2f}',30,color,'middle',weight=600)
   # Route the arrows around the band caption; both end at exactly the same level.
   c1x=xx+20 if mobile and i==0 else xx
   path(f'M{xx} {in_y+12} C{c1x} {in_y+52},{selected_x} {level_y-53},{selected_x} {level_y-17}',color,2,'4 5')
   path(f'M{selected_x-5} {level_y-22} L{selected_x} {level_y-15} L{selected_x+5} {level_y-22}',color,2)
   orb('ideaMap'+str(i),xx,in_y,6,'blue' if i==0 else 'coral',[(2,selected_x,level_y)],
       extra=f'id="idea-moving-{i}" data-input="{v:.2f}" data-code="01" data-reconstructed="0.30"')
  # Bit slots are a width sketch, never a claimed FP16 binary representation.
  if mobile:
   txt(20,326,'FP16',24,MUTED);slot_x=95;slot_y=307;slot_w=8;slot_gap=3
   for i in range(16):rect(slot_x+i*(slot_w+slot_gap),slot_y,slot_w,20,'#1e3b53','#6f91ac',2,extra=f'data-bit-sketch="fp16" data-bit-index="{i}"')
   txt(285,326,'16 bit',24,MUTED)
   txt(20,365,'2 bit',24,INK,weight=600);bit_x=[145,181];bit_y=341
   for i,(bit,xx) in enumerate(zip('01',bit_x)):
    st=phase('ideaStoredBit'+str(i),3,'stroke:#6d9caa;stroke-width:1.5','stroke:'+TEAL+';stroke-width:3')
    rect(xx-15,bit_y,30,32,'#193d50','#6d9caa',5,extra=st+f' data-bit-sketch="int2" data-bit-index="{i}"')
    txt(xx,bit_y+25,bit,26,TEAL,'middle',extra=f'data-stored-bit="{bit}"')
   txt(230,365,L('只存01','code 01'),24,TEAL)
   txt(20,397,L('位数示意 · 未计尺度元数据','Bit sketch · scale costs extra'),24,MUTED)
   txt(20,440,L('读回','Read'),24,MUTED)
   txt(106,440,'01 → 0.30',30,TEAL,weight=600,extra=phase('ideaDecode',4,f'fill:{INK}',f'fill:{TEAL}')+' id="idea-restored-value" data-code="01" data-reconstructed="0.30"')
   txt(20,472,'0.26 → 0.30   +0.04',24,BLUE,extra='data-original="0.26" data-error="0.04"')
   txt(20,503,'0.34 → 0.30   −0.04',24,CORAL,extra='data-original="0.34" data-error="-0.04"')
   txt(20,535,L('原来是哪一个？无法恢复。','Original detail is lost.'),24,INK,weight=600)
   txt(20,563,L('2bit示意 · 非部署建议','2-bit toy · not a recipe'),24,MUTED)
   txt(20,591,L('实际权重可为正或负','Real weights may be ±'),24,MUTED)
  else:
   txt(24,287,L('存储','Store'),24,MUTED)
   txt(100,287,'FP16',24,MUTED);slot_x=176;slot_y=264;slot_w=8;slot_gap=3
   for i in range(16):rect(slot_x+i*(slot_w+slot_gap),slot_y,slot_w,25,'#1e3b53','#6f91ac',2,extra=f'data-bit-sketch="fp16" data-bit-index="{i}"')
   txt(383,287,'16 bit → 2 bit',24,INK)
   for i,(bit,xx) in enumerate(zip('01',[602,638])):
    st=phase('ideaStoredBit'+str(i),3,'stroke:#6d9caa;stroke-width:1.5','stroke:'+TEAL+';stroke-width:3')
    rect(xx-15,260,30,34,'#193d50','#6d9caa',5,extra=st+f' data-bit-sketch="int2" data-bit-index="{i}"')
    txt(xx,286,bit,27,TEAL,'middle',extra=f'data-stored-bit="{bit}"')
   txt(100,319,L('位数示意，非真实FP16编码；未计尺度元数据','Bit-width sketch, not FP16 encoding; scale metadata excluded'),20,MUTED)
   txt(24,360,L('读回','Read'),24,MUTED)
   txt(128,360,'01 → 0.30',30,TEAL,weight=600,extra=phase('ideaDecode',4,f'fill:{INK}',f'fill:{TEAL}')+' id="idea-restored-value" data-code="01" data-reconstructed="0.30"')
   txt(428,360,L('两条误差：+0.04 / −0.04','Errors: +0.04 / −0.04'),23,CORAL)
   # Explicit machine-readable examples are shared with the independent arithmetic gate.
   add('<g data-original="0.26" data-error="0.04"/><g data-original="0.34" data-error="-0.04"/>')
   txt(24,394,L('同一个01：无法知道原来是0.26，还是0.34。','The same 01 cannot tell us whether the original was 0.26 or 0.34.'),22,INK,weight=600)
   txt(24,424,L('2bit教学示意 · 实际权重可为正或负 · 非部署建议','2-bit teaching example · real weights can be ± · not a deployment recipe'),20,MUTED)
 elif key=='formula':
  txt(20 if mobile else 60,43,'q = clip(round(w/s)+z)',24 if mobile else 30,INK,weight=600)
  txt(20 if mobile else 60,82,'ŵ = s(q−z)',26,TEAL)
  if mobile:
   xs=[78,180,282,282,282,180,78];ys=[165,165,165,282,399,399,399]
   labels=[L('原值','Input'),L('缩放','Scale'),L('舍入','Round'),L('平移','Shift'),L('裁剪','Clip'),L('还原','Restore'),L('结果','Result')];values=['0.4','0.8','1','3','3','0.5','0.5']
  else:
   xs=[76,184,292,400,508,616,724];ys=[200]*7
   labels=[L('原值','Input'),L('缩放','Scale'),L('舍入','Round'),L('平移','Shift'),L('裁剪','Clip'),L('还原','Restore'),L('结果','Result')];values=['0.4','0.8','1','3','3','0.5','0.5']
  for i in range(6):rail(xs[i],ys[i],xs[i+1],ys[i+1])
  for i,(xx,yy,label,value) in enumerate(zip(xs,ys,labels,values)):
   platform(xx-35,yy+17,70,13)
   ring('station'+str(i),xx,yy,25,i)
   txt(xx,yy-48,label,22,MUTED,'middle',weight=600)
   txt(xx,yy+8,value,22,INK,'middle',extra=f'data-formula-stage="{i}" data-value="{value}"')
   pulse('stationPulse'+str(i),xx,yy+32,i,r=30)
  # A light-bearing packet follows the code stations without obscuring their numbers.
  orb('formulaPacket',xs[0],ys[0]-30,7,'cyan',[(i,xs[i],ys[i]-30) for i in range(7)])
  if mobile:
   txt(20,465,'s=0.5 · z=2',23,MUTED)
   txt(20,497,'q ∈ [0,3]',23,MUTED)
   txt(20,529,L('无裁剪：|e| ≤ s/2','No clipping: |e| ≤ s/2'),23,CORAL,extra=phase('formulaErrorBound',6,f'fill:{MUTED}',f'fill:{CORAL}'))
  else:
   txt(60,304,'s=0.5 · z=2 · q ∈ [0,3]',23,MUTED)
   txt(60,360,L('无裁剪：|e| ≤ s/2','No clipping: |e| ≤ s/2'),24,CORAL,extra=phase('formulaErrorBound',6,f'fill:{MUTED}',f'fill:{CORAL}'))
  foot()
 elif key=='worked':
  weights=[-.9,-.6,.2,.4];qs=[0,1,2,3];codes=['00','01','10','11'];restored=[-1.,-.5,0.,.5]
  if mobile:
   txt(20,33,L('4个权重','Four weights'),28,INK,weight=600)
   txt(20,72,L('从原值到编码，再还原','Encode and reconstruct'),28,INK,weight=600)
   level_y=118;header_y=168;ys=[220,280,340,400];xs=[52,137,222,307]
   names=[L('原值','Input'),L('编号','Code'),L('2bit','Bits'),L('还原','Read')]
  else:
   txt(32,45,L('同一组4个权重：编码与还原','The same four weights: encode and reconstruct'),30,INK,weight=600)
   level_y=91;header_y=141;ys=[191,236,281,326];xs=[150,315,480,645]
   names=[L('原权重','Original'),L('整数码','Integer code'),L('2-bit码','2-bit code'),L('近似权重','Reconstructed')]
  level_st=phase('workedLevels',1,f'fill:{MUTED}',f'fill:{TEAL}')
  txt(20 if mobile else 32,level_y,L('档位：−1 / −0.5 / 0 / 0.5','Levels: −1 / −0.5 / 0 / 0.5'),24,MUTED,extra=level_st+' id="worked-level-list" data-levels="-1,-0.5,0,0.5"')
  for col,(xx,name,step) in enumerate(zip(xs,names,[0,2,3,4])):
   txt(xx,header_y,name,24,MUTED,'middle')
   st=phase('workedColumn'+str(col),step,'stroke:#42647e;stroke-width:1','stroke:'+TEAL+';stroke-width:3')
   line(xx-(36 if mobile else 65),header_y+12,xx+(36 if mobile else 65),header_y+12,'#42647e',1,extra=st)
  for i,(w,q,code,r,yy) in enumerate(zip(weights,qs,codes,restored,ys)):
   line(20,yy+18,W-20,yy+18,'#29465e',1)
   for col,(xx,value,step) in enumerate(zip(xs,[f'{w:g}',str(q),code,f'{r:g}'],[0,2,3,4])):
    st=phase(f'workedRow{i}Col{col}',step,f'fill:{INK}',f'fill:{TEAL}')
    txt(xx,yy,value,28,INK,'middle',weight=600 if col==3 else 400,
        extra=st+f' id="worked-value-{i}-{col}" data-row="{i}" data-stage="{col}" data-input="{w:g}" data-q="{q}" data-code="{code}" data-reconstructed="{r:g}"')
  err_st=phase('workedFirstError',5,f'fill:{MUTED}',f'fill:{CORAL}')
  if mobile:
   txt(20,469,L('只看第一项','Inspect the first weight'),24,MUTED,extra=err_st)
   txt(20,509,'−0.9 → −1',30,CORAL,weight=600)
   txt(20,548,L('误差：−1−(−0.9)=−0.1','Error: −1−(−0.9)=−0.1'),24,CORAL,
       extra='id="worked-first-error" data-input="-0.9" data-reconstructed="-1" data-error="-0.1"')
   txt(20,591,L('4个权重，数量不变','Still four weights'),24,MUTED)
  else:
   txt(32,385,L('第一项：−0.9 → −1，数值误差−0.1','First weight: −0.9 → −1, numerical error −0.1'),26,CORAL,extra=err_st+
       ' id="worked-first-error" data-input="-0.9" data-reconstructed="-1" data-error="-0.1"')
   txt(32,424,L('教学示例；4个权重的数量不变，近似改变的是数值。','Teaching example: four weights remain four; approximation changes their values.'),20,MUTED)
 elif key=='error':
  left=64;right=W-40;top=145 if mobile else 95;bottom=H-142 if mobile else H-110
  X=lambda x:left+x/10*(right-left);Y=lambda y:bottom-y/5.5*(bottom-top)
  line(24,33,50,33,BLUE,3);txt(60,41,'y=0.4x',24,BLUE)
  line(24,76,50,76,TEAL,3);txt(60,84,'ŷ=0.5x',24,TEAL)
  for v in [0,1,2,3,4,5]:line(left,Y(v),right,Y(v),GRID,1);txt(left-14,Y(v)+7,str(v),20,MUTED,'end')
  rail(left,bottom,right,bottom);line(left,top,left,bottom,'#8eacc2')
  add(f'<path d="M{X(0)} {Y(0)} L{X(10)} {Y(4)} L{X(10)} {Y(5)} Z" fill="url(#errorFill)"/>')
  for i,(weight,color,kind) in enumerate([(.4,BLUE,'blue'),(.5,TEAL,'cyan')]):
   line(X(0),Y(0),X(10),Y(weight*10),color,3)
   orb('output'+str(i),X(0),Y(0),8,kind,[(i,X(10),Y(weight*10))])
   txt(right-12,Y(weight*10)+(28 if i==0 else -16),str(weight*10),22,color,'end')
  st=phase('outputError',2,'stroke:#bc8d89;stroke-width:2','stroke:'+CORAL+';stroke-width:4')
  line(right,Y(4),right,Y(5),CORAL,3,extra=st)
  path(f'M{right-5} {Y(4)} H{right+5} M{right-5} {Y(5)} H{right+5}',CORAL,2)
  txt(left,bottom+32,'0',20,MUTED);txt(right,bottom+32,'x=10',20,MUTED,'end')
  st,end=travel('inputCursor',left,0,[(0,right,0)])
  xx=left if animated else right
  line(xx,top,xx,bottom,'#6dbad8',1.2,'4 6',extra=st)
  add('<g id="error-case" data-input="10" data-original-weight="0.4" data-reconstructed-weight="0.5" data-original-output="4" data-reconstructed-output="5" data-output-error="1"/>')
  foot('Δy=1 ≠ 1%质量损失','Δy=1 ≠ 1% quality loss')
 elif key=='groups':
  cw=32 if mobile else 64;ch=52 if mobile else 55
  mx=(W-8*cw)/2;my=160 if mobile else 108;mw=8*cw;mh=4*ch
  txt(20,55 if mobile else 43,'W[out,in] · group size=2',22,MUTED)
  txt(mx,my-27,L('输入特征 in →','Input features in →'),24,MUTED)
  add(f'<text x="{mx-25}" y="{my+mh/2}" text-anchor="middle" font-size="{24 if mobile else 22}" fill="{MUTED}" transform="rotate(-90 {mx-25} {my+mh/2})">'+L('输出 out','Output out')+'</text>')
  platform(mx-7,my+mh+3,mw+14,16)
  for r in range(4):
   for c in range(8):
    val=math.sin((r*8+c)*1.71)*math.cos(c*.43);strength=abs(val);light=28+strength*33;hue=212-strength*26
    xx=mx+c*cw+3;yy=my+r*ch+3
    # Beveled tensor tiles keep the mathematical row/column geometry strictly frontal.
    rect(xx+2,yy+5,cw-6,ch-6,'#061527',r=6)
    rect(xx,yy,cw-6,ch-9,f'hsl({hue:.1f},66%,{light:.1f}%)',r=6,extra=f'data-weight-row="{r}" data-weight-col="{c}" stroke="#a7ecf3" stroke-opacity=".22"')
    line(xx+5,yy+4,xx+cw-17,yy+4,'#b9f4ff',.7)
  def scope(name,x,y,w,h,step):
   st=phase('scope'+name,step,'stroke:#56758f;stroke-width:1.2;filter:none','stroke:'+TEAL+';stroke-width:3;filter:drop-shadow(0 0 2px #6ef3e2)')
   rect(x,y,w,h,'none','#56758f',7,extra=st+f' data-scale-scope="{name}"')
  scope('tensor',mx-5,my-5,mw+10,mh+10,0)
  for r in range(4):scope('channel'+str(r),mx-2,my+r*ch-2,mw+4,ch+4,1)
  for r in range(4):
   for c in range(0,8,2):scope('group'+str(r)+str(c),mx+c*cw,my+r*ch,2*cw,ch,2)
  # Scale tokens physically split into 4 row tokens, then 16 per-group tokens.
  token0=(mx+mw/2,my-9)
  for r in range(4):
   for g in range(4):
    row=(mx+mw+8,my+r*ch+ch/2)
    group=(mx+g*2*cw+cw,my+r*ch+ch-6)
    orb(f'scaleToken{r}_{g}',*token0,3.5,'cyan',[(1,*row),(2,*group)])
  labels=[L('整张 · 1','per-tensor · 1'),L('逐通道 · 4','per-channel · 4'),L('分组 · 16','per-group · 16')]
  for i,label in enumerate(labels):
   lx=([95,260,180] if mobile else [160,400,640])[i];ly=(425 if i<2 else 465) if mobile else 369
   st=phase('groupLabel'+str(i),i,f'fill:{MUTED}',f'fill:{TEAL}')
   txt(lx,ly,label,22,MUTED,'middle',extra=st)
  st=phase('groupCost',3,f'fill:{MUTED}',f'fill:{CORAL}')
  txt(W/2,H-60 if mobile else H-40,L('分组越细，尺度元数据越多','More groups → more metadata'),20,MUTED,'middle',extra=st)
  foot()
 elif key=='execution':
  # Four 2-bit codes, most-significant pair first, form one illustrative byte.
  bits='00011011';qs=[0,1,2,3];restored=[-1.,-.5,0.,.5]
  if mobile:bx=44;by=85;bw=30;kx=30;ky=238;kw=300;kh=230
  else:bx=40;by=188;bw=25;kx=330;ky=102;kw=300;kh=247
  txt(bx,by-28,L('4个2-bit码打成1字节','Four 2-bit codes → one byte'),24,MUTED)
  platform(bx-8,by+43,bw*8+16,14)
  for n,bit in enumerate(bits):
   rect(bx+n*bw,by,bw-3,39,'url(#glass)','#5892a9',5,extra=f'data-packed-bit-index="{n}" data-packed-bit="{bit}"')
   txt(bx+n*bw+(bw-3)/2,by+28,bit,24 if mobile else 22,TEAL,'middle')
  for i,q in enumerate(qs):txt(bx+(2*i+1)*bw-1.5,by+77,str(q),24,TEAL,'middle',extra=f'data-unpacked-code="{q}"')
  rect(kx+7,ky+9,kw,kh,'#030f20',r=20)
  st=phase('kernelEdge',1,'stroke:#4c819e;stroke-width:2','stroke:'+TEAL+';stroke-width:3')
  rect(kx,ky,kw,kh,'url(#glass)','#4c819e',18,extra='id="fused-kernel" '+st)
  center=kx+kw/2
  txt(center,ky+34,L('核内示意','Inside the kernel'),24,MUTED,'middle')
  txt(center,ky+77,'q=(0,1,2,3)',24,TEAL,'middle',extra='data-kernel-stage="unpack"')
  txt(center,ky+117,'s=0.5 · z=2',24,MUTED,'middle',extra='data-kernel-stage="parameters"')
  txt(center,ky+156,'ŵ=(−1,−0.5,0,0.5)',24,TEAL,'middle',extra='data-kernel-stage="restore" data-restored-values="-1,-0.5,0,0.5"')
  txt(center,ky+205,'Ŷ=ŴX',28,INK,'middle',extra='data-kernel-stage="compute"')
  if mobile:
   rail(180,by+84,180,ky);rail(8,ky+189,kx,ky+189);txt(13,ky+164,'A16',24,MUTED)
   rail(center,ky+kh,center,520);txt(center+20,518,'Ŷ',26,INK)
   start=(180,171);targets=[(0,center,ky+48),(1,center,ky+170),(2,center,520)]
   orb('activation',8,ky+189,6,'blue',[(1,kx+16,ky+189),(2,center,ky+189)])
   for j in range(4):orb('decoded'+str(j),center,ky+48,3.5,'cyan',[(1,center-54+j*36,ky+170),(2,center,520)])
   txt(20,558,L('W2A16仅为教学示意','W2A16 teaching example'),24,MUTED)
   txt(20,590,L('不声明任何硬件已支持','No hardware support claim'),24,MUTED)
  else:
   rail(244,by+20,kx,by+20);rail(center,34,center,ky);txt(center+18,63,'A16',24,MUTED)
   rail(kx+kw,ky+184,752,ky+184);txt(705,ky+152,L('输出Ŷ','Output Ŷ'),24,MUTED,'middle')
   start=(244,208);targets=[(0,kx+18,208),(1,center,ky+170),(2,752,ky+184)]
   orb('activation',center,34,6,'blue',[(1,center,ky+48),(2,center,ky+170)])
   for j in range(4):orb('decoded'+str(j),kx+18,208,3.5,'cyan',[(1,center-54+j*36,ky+170),(2,752,ky+184)])
   txt(20,392,L('s(q−z)还原近似权重；W2A16仅为教学示意。','s(q−z) reconstructs approximate weights; W2A16 is illustrative.'),22,MUTED)
   txt(20,424,L('按显示顺序从高位到低位打包；不声明硬件支持或加速。','Packed high bits first in display order; no hardware support or speedup claim.'),20,MUTED)
  packet('packedPacket',*start,targets)

 o.append('</svg>')
 return '\n'.join(o)

def main():
 scenes=[]
 for key,count in SCENES.items():
  for lang in ['zh','en']:
   stem='quantization-class-'+key+'.'+lang
   for mobile in [False,True]:
    for animated in [False,True]:
     suffix=('.mobile' if mobile else '')+('' if animated else '.static')+'.svg'
     (OUT/(stem+suffix)).write_text(build(key,lang,mobile,animated),encoding='utf-8')
   scenes.append({'id':stem,'source':stem+'.svg','duration_ms':count*4000,'poster_ms':0,'responsive':{'mobile_strategy':'separate-semantic-layout','detail_mode':'desktop-scroll'},'static_svg':stem+'.static.svg','authoring_source':'../../../tools/cloud_core/build_quantization_class.py','claim_kind':'illustrative_mechanism'})
 (OUT/'quantization-class-scenes.json').write_text(json.dumps({'schema':'lri.motion-scene-set/v2','scenes':scenes},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'pass':True,'scenes':len(scenes),'illustrative_only':True,'style':'quantization-teaching-film-v4','clock':'4s per causal shot'}))
if __name__=='__main__':main()

