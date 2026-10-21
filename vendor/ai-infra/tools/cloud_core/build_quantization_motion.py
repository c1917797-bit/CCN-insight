from pathlib import Path
from xml.sax.saxutils import escape
import json
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'business_insight/cloud_core/assets'
SCALE=.1; ZERO=0; LOW=-8; HIGH=7; VALUES=[.26,.96]; PERIOD=24
labels=[
 ('原始权重','Original weight'),
 ('除以尺度','Divide by scale'),
 ('取最近整数','Round to nearest'),
 ('裁剪并保存整数码','Clip and store'),
 ('反量化得到近似值','Reconstruct weight'),
 ('计算权重误差','Weight error')]
lines=[[],[],[],[],[],[]]
for name,w in zip(['A','B'],VALUES):
 pre=w/SCALE;rounded=int(pre+.5);q=min(HIGH,max(LOW,rounded));restored=SCALE*(q-ZERO);err=restored-w
 for idx,text in enumerate([f'{name}: w = {w:.2f}',f'{name}: w/s = {pre:.1f}',f'{name}: round({pre:.1f}) = {rounded}',f'{name}: q = {q}'+(' (10 → 7)' if rounded!=q else ''),f'{name}: ŵ = {restored:.2f}',f'{name}: e = {err:+.2f}']):
  lines[idx].append(text)
assert lines[3]==['A: q = 3','B: q = 7 (10 → 7)']
def build(lang,animated):
 zh=lang=='zh';L=lambda a,b:a if zh else b
 css='text{font-family:Arial,Microsoft YaHei,sans-serif}.accent{fill:#fff;stroke:#d7e2ee;stroke-width:2}'
 if animated:
  css+='@keyframes focus{0%,16.65%{stroke:#b71c1c;stroke-width:4}16.67%,100%{stroke:#d7e2ee;stroke-width:2}}.accent{animation:focus 24s steps(1,end) infinite}@media(prefers-reduced-motion:reduce){.accent{animation:none}}'
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 580" data-cycle="24" data-mobile-viewbox="0 0 360 1030" role="img" aria-labelledby="title desc">',
 '<title id="title">'+L('权重量化的六个步骤','Six steps of weight quantization')+'</title>',
 '<desc id="desc">'+L('两个教学例子：0.26舍入到0.30；0.96超出范围后裁剪到0.70。所有数字始终可见，红框按顺序指出正在演示的步骤。','Two illustrative cases: 0.26 rounds to 0.30; 0.96 clips to 0.70. Values remain visible; a red outline marks the current stage.')+'</desc>',
 '<style><![CDATA['+css+']]></style>']
 for mobile in [False,True]:
  width=360 if mobile else 860; height=1030 if mobile else 580
  out.append(f'<g data-responsive="{"mobile" if mobile else "desktop"}"'+(' display="none"' if mobile else '')+'>')

  track=width-56;left=28
  out.append(f'<rect width="{width}" height="{height}" fill="#f5f8fc"/>')
  for name,w,recon,low,high,y in [('A',.26,.30,.20,.40,48),('B',.96,.70,0,1,122)]:
   px=lambda value:left+(value-low)/(high-low)*track
   distance=px(recon)-px(w)
   token=name+('Mobile' if mobile else 'Desktop')
   out.append(f'<text x="20" y="{y-22}" font-size="24" fill="#24364b">{name}: {w:.2f} → {recon:.2f}</text>')
   out.append(f'<path d="M{left} {y} H{width-28}" stroke="#9bacc0" stroke-width="3"/>')
   out.append(f'<path d="M{px(w)} {y} H{px(recon)}" stroke="#087f8c" stroke-width="5"/>')
   for val in [low,high]:
    out.append(f'<text x="{px(val)}" y="{y+23}" text-anchor="middle" font-size="22" fill="#526984">{val:.1f}</text>')
   out.append(f'<circle cx="{px(w)}" cy="{y}" r="7" fill="#fff" stroke="#b71c1c" stroke-width="3"/>')
   if animated:
    out.append(f'<style>@keyframes move{token}{{0%,66.66%{{transform:translateX(0)}}83.33%,100%{{transform:translateX({distance}px)}}}}.moving-{token}{{animation:move{token} 24s linear infinite}}@media(prefers-reduced-motion:reduce){{.moving-{token}{{animation:none;transform:translateX({distance}px)}}}}</style>')
   out.append(f'<circle class="moving-{token}" cx="{px(w) if animated else px(recon)}" cy="{y}" r="9" fill="#087f8c"/>')
  out.append('<g transform="translate(0 160)">')

  out.append('<text x="18" y="28" font-size="20" fill="#24364b">s = 0.1 · z = 0 · q ∈ [−8, 7]</text>')
  out.append('<text x="18" y="53" font-size="17" fill="#526984">'+L('教学示例：A = 0.26，B = 0.96','Illustrative: A = 0.26, B = 0.96')+'</text>')
  for i,(zhlabel,enlabel) in enumerate(labels):
   x=18 if mobile else 18+(i%3)*280
   y=74+i*124 if mobile else 74+(i//3)*148
   w=324 if mobile else 264
   out.append(f'<g id="{"mobile" if mobile else "desktop"}-step-{i+1}" data-stage="{i+1}">')
   out.append(f'<rect class="accent" x="{x}" y="{y}" width="{w}" height="112" rx="12"'+(f' style="animation-delay:{-24+i*4}s"' if animated else '')+'/>')
   title=zhlabel if zh else enlabel
   font=24 if mobile else (20 if zh else 18)
   out.append(f'<text x="{x+13}" y="{y+28}" font-size="{font}" font-weight="700" fill="#24364b">{i+1:02d} · {escape(title)}</text>')
   for j,text in enumerate(lines[i]):out.append(f'<text x="{x+13}" y="{y+60+j*27}" font-size="{24 if mobile else 20}" fill="#24364b">{escape(text)}</text>')
   out.append('</g>')
  out.append(f'<text x="18" y="{height-182}" font-size="17" fill="#526984">'+L('e = ŵ − w · 不代表业务精度损失','e = ŵ − w · Not task-quality loss')+'</text></g></g>')
 out.append('</svg>')
 return '\n'.join(out)
OUT.mkdir(parents=True,exist_ok=True)
scenes=[]
for lang in ['zh','en']:
 stem='quantization-principle.'+lang
 (OUT/(stem+'.svg')).write_text(build(lang,True))
 (OUT/(stem+'.static.svg')).write_text(build(lang,False))
 tree=E.fromstring(build(lang,False));tree.set('viewBox','0 0 360 1030')
 for group in list(tree):
  if group.get('data-responsive')=='desktop':tree.remove(group)
  elif group.get('data-responsive')=='mobile':group.attrib.pop('display',None)
 (OUT/(stem+'.mobile.static.svg')).write_text(E.tostring(tree,encoding='unicode'))
 scenes.append({'id':'quantization-principle-'+lang,'source':stem+'.svg','duration_ms':24000,'poster_ms':0,'responsive':{'mobile_strategy':'semantic-groups','detail_mode':'desktop-scroll'},'static_svg':stem+'.static.svg','semantic_steps':6,'claim_kind':'illustrative_arithmetic','authoring_source':'../../../tools/cloud_core/build_quantization_motion.py'})
(OUT/'quantization-motion-scenes.json').write_text(json.dumps({'schema':'lri.motion-scene-set/v2','scenes':scenes},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pass':True,'scenes':2,'steps':6,'static_fallbacks':2}))
