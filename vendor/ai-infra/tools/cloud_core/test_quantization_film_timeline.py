"""Causal-time checks complement independent arithmetic and browser geometry checks."""
from pathlib import Path
import re,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]/'business_insight/cloud_core/assets'
COUNTS={'purpose':1,'precision':1,'concept':1,'tradeoff':1,'idea':5,'formula':7,'worked':6,'error':3,'groups':4,'execution':3}
checked=0
def frames(css,name):
 match=re.search(r'@keyframes '+re.escape(name)+r'\{(.*?)(?=</style>|@keyframes|$)',css,re.S)
 assert match,name
 return match.group(1)
def translations(css,name):
 body=frames(css,name)
 return [(float(p),float(x),float(y)) for p,x,y in re.findall(r'([\d.]+)%\{transform:translate\(([-\d.]+)(?:px)?,([-\d.]+)(?:px)?\)',body)]

for p in ROOT.glob('quantization-class-*.svg'):
 root=ET.parse(p).getroot();key=root.get('data-scene')
 assert root.get('data-style')=='quantization-teaching-film-v4'
 assert float(root.get('data-cycle'))==COUNTS[key]*4
 assert not any(n.tag.rsplit('}',1)[-1] in ('script','foreignObject','iframe') for n in root.iter())
 css=p.read_text(encoding='utf-8')
 assert 'opacity:' not in ''.join(n.text or '' for n in root.iter() if n.tag.endswith('style')),'semantic groups must not fade'
 if '.static.' in p.name:
  assert '@keyframes' not in css
  continue
 if key=='purpose':
  t=translations(css,'purposeRead')
  assert any(0<pct<100 and x>0 for pct,x,y in t),'reading packet must travel inside the four-second scene'
 if key=='concept':
  for i in range(4):
   t=translations(css,'conceptWeight'+str(i))
   assert any(abs(pct-(23+i*20))<.01 and y>0 for pct,x,y in t),'each weight must reach its approximation in sequence'
 if key=='tradeoff':
  assert all('id="tradeoff-code-'+str(i)+'"' in css for i in range(4))
 if key=='idea':
  for i in range(2):
   t=translations(css,'ideaMap'+str(i))
   assert len(t)>=3
   assert all(x==0 and y==0 for pct,x,y in t if pct<40),'originals must remain at source for the first two steps'
   arrivals=[pct for pct,x,y in t if x!=0 or y!=0]
   assert min(arrivals)>40 and min(arrivals)<60,'both values must map during step two'
   assert not any(60<pct<99.9 for pct,x,y in t),'storage and decode steps retain the selected level'
  assert '16 bit' in css and 'data-stored-bit="0"' in css and 'data-stored-bit="1"' in css
 if key=='formula':
  t=translations(css,'formulaPacket')
  assert sum(1 for pct,_,_ in t if 0<pct<100)>=13
 if key=='worked':
  for col,step in enumerate([0,2,3,4]):
   body=frames(css,'workedColumn'+str(col))
   match=re.search(r'([\d.]+)%,([\d.]+)%\{stroke:#6ef3e2;stroke-width:3\}',body)
   assert match and abs(float(match.group(1))-step/6*100)<.01,'worked column emphasis must match its explanation step'
  assert 'workedLevels' in css and 'workedFirstError' in css
 if key=='error':
  old=translations(css,'output0');new=translations(css,'output1')
  assert any(x>0 for pct,x,y in old if pct<33.33)
  assert all(x==0 for pct,x,y in new if pct<33.33),'quantized output must wait for step one'
 if key=='groups':
  t=translations(css,'scaleToken0_0')
  assert all(x==0 and y==0 for pct,x,y in t if pct<25),'one scale must remain through per-tensor step'
  assert any(x!=0 for pct,x,y in t if 25<pct<50)
  assert any(y!=0 for pct,x,y in t if 50<pct<75)
 if key=='execution':
  t=translations(css,'packedPacket')
  assert len(t)>=7,'read, decode and output require distinct arrivals'
  assert 'Inside the kernel' in css or '核内示意' in css
 checked+=1
print({'pass':True,'animated_variants':checked,'step_seconds':4,'causal_scenes':list(COUNTS),'semantic_text_fades':0})

