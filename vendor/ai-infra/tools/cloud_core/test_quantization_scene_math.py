"""Independently verify the common four-weight example, bit payloads and rendered teaching cases."""
from pathlib import Path
import math,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2]/'business_insight/cloud_core/assets'
WEIGHTS=[-.9,-.6,.2,.4];S=.5;Z=2;QMIN=0;QMAX=3
Q=[min(QMAX,max(QMIN,round(w/S)+Z)) for w in WEIGHTS]
RESTORED=[S*(q-Z) for q in Q]
assert Q==[0,1,2,3] and RESTORED==[-1.,-.5,0.,.5]
assert all(abs(a-b)<=S/2 for a,b in zip(WEIGHTS,RESTORED))
documents=0;weight_cases=0
for p in ROOT.glob('quantization-class-*.svg'):
 root=E.parse(p).getroot();documents+=1
 nodes={e.get('id'):e for e in root.iter() if e.get('id')}
 assert root.get('viewBox').split()[2] in ['360','800']
 for e in root.iter():
  tag=e.tag.rsplit('}',1)[-1].lower()
  assert tag not in ['script','foreignobject','iframe']
  if e.get('font-size'):assert float(e.get('font-size')) >= (24 if '.mobile.' in p.name else 20)
 if '-purpose.' in p.name:
  n=nodes['purpose-capacity'];params=int(n.get('data-parameters'));bits=int(n.get('data-bits-per-weight'));payload=int(n.get('data-weight-bytes'))
  assert params==27_000_000_000 and bits==16
  assert params*bits//8==payload==54_000_000_000 and payload/1_000_000_000==54
 if '-precision.' in p.name:
  n=nodes['precision-code-count'];assert int(n.get('data-bits'))==2 and int(n.get('data-code-count'))==2**2
  for width in [16,2]:assert len([e for e in root.iter() if e.get('data-precision-width')==str(width)])==width
 if '-concept.' in p.name:
  for i,(w,q,r) in enumerate(zip(WEIGHTS,Q,RESTORED)):
   original=nodes['concept-original-'+str(i)];level=nodes['concept-level-'+str(i)];moving=nodes['concept-moving-'+str(i)]
   assert original.get('fill')=='#fff' and float(original.get('data-input'))==w
   assert float(level.get('data-level'))==r and int(level.get('data-code'),2)==q
   assert float(moving.get('data-input'))==w and float(moving.get('data-reconstructed'))==r
   assert min(RESTORED,key=lambda x:abs(x-w))==r
   if '.static.' in p.name:assert moving.get('cx')==level.get('cx') and moving.get('cy')==level.get('cy')
 if '-tradeoff.' in p.name:
  payload=nodes['tradeoff-payload']
  assert int(payload.get('data-weight-count'))==4
  assert int(payload.get('data-before'))==4*int(payload.get('data-original-bits'))==64
  assert int(payload.get('data-after'))==4*int(payload.get('data-code-bits'))==8
  assert len([e for e in root.iter() if e.get('data-bit-sketch')=='int2'])==8
  assert ''.join(e.get('data-stored-bit') for e in root.iter() if e.get('data-stored-bit') is not None)=='00011011'
  for i,r in enumerate(RESTORED):
   code=nodes['tradeoff-code-'+str(i)];out=nodes['tradeoff-restored-'+str(i)]
   assert int(code.get('data-code'),2)==i and float(out.get('data-reconstructed'))==r
 if '-formula.' in p.name:
  stages={int(e.get('data-formula-stage')):float(e.get('data-value')) for e in root.iter() if e.get('data-formula-stage') is not None}
  assert [stages[i] for i in range(7)]==[.4,.8,1,3,3,.5,.5]
  assert .4/S==stages[1] and round(stages[1])+Z==stages[3]
  assert S*(stages[4]-Z)==stages[5]
 if '-worked.' in p.name:
  for i,(w,q,r) in enumerate(zip(WEIGHTS,Q,RESTORED)):
   values=[nodes[f'worked-value-{i}-{j}'] for j in range(4)]
   assert [e.text for e in values]==[f'{w:g}',str(q),format(q,'02b'),f'{r:g}']
   for n in values:
    assert float(n.get('data-input'))==w and int(n.get('data-q'))==q and int(n.get('data-code'),2)==q and float(n.get('data-reconstructed'))==r
   weight_cases+=1
  n=nodes['worked-first-error']
  assert math.isclose(float(n.get('data-reconstructed'))-float(n.get('data-input')),float(n.get('data-error')),abs_tol=1e-12)
  assert math.isclose(float(n.get('data-error')),-.1,abs_tol=1e-12)
 if '-error.' in p.name:
  n=nodes['error-case'];x=float(n.get('data-input'));w=float(n.get('data-original-weight'));r=float(n.get('data-reconstructed-weight'))
  assert w==.4 and r==.5 and x==10
  assert w*x==float(n.get('data-original-output'))==4
  assert r*x==float(n.get('data-reconstructed-output'))==5
  assert math.isclose((r-w)*x,float(n.get('data-output-error')),abs_tol=1e-12)
 if '-idea.' in p.name:
  nodes={e.get('id'):e for e in root.iter() if e.get('id')}
  choices=[nodes['idea-level-'+str(i)] for i in range(4)]
  assert [float(n.get('data-level')) for n in choices]==[0.0,0.3,0.6,0.9]
  assert [n.get('data-code') for n in choices]==['00','01','10','11']
  assert math.ceil(math.log2(len(choices)))==2
  assert len([e for e in root.iter() if e.get('data-bit-sketch')=='fp16'])==16
  assert len([e for e in root.iter() if e.get('data-bit-sketch')=='int2'])==2
  assert ''.join(e.get('data-stored-bit') for e in root.iter() if e.get('data-stored-bit') is not None)=='01'
  for i,value in enumerate([.26,.34]):
   original=nodes['idea-input-'+str(i)]
   moving=nodes['idea-moving-'+str(i)]
   nearest=min(range(4),key=lambda j:abs(value-[0.0,0.3,0.6,0.9][j]))
   assert nearest==1 and original.get('fill')=='#fff'
   assert math.isclose(float(moving.get('data-reconstructed')),.3)
   assert moving.get('data-code')=='01'
   err=next(e for e in root.iter() if e.get('data-original')==f'{value:.2f}' and e.get('data-error'))
   assert math.isclose(float(err.get('data-error')),.3-value,abs_tol=1e-12)
   if '.static.' in p.name:
    assert moving.get('cx')==choices[1].get('cx') and moving.get('cy')==choices[1].get('cy')
  assert nodes['idea-restored-value'].get('data-code')=='01'
 if '-groups.' in p.name:
  assert len([e for e in root.iter() if e.get('data-weight-row') is not None])==32
  assert len([e for e in root.iter() if (e.get('data-scale-scope') or '').startswith('group')])==16
 if '-execution.' in p.name:
  bits=''.join(e.get('data-packed-bit') for e in root.iter() if e.get('data-packed-bit') is not None)
  assert bits=='00011011'
  assert [int(bits[i:i+2],2) for i in range(0,8,2)]==Q
  assert [int(e.get('data-unpacked-code')) for e in root.iter() if e.get('data-unpacked-code') is not None]==Q
  restore=next(e for e in root.iter() if e.get('data-kernel-stage')=='restore')
  assert [float(x) for x in restore.get('data-restored-values').split(',')]==RESTORED
  kernel=nodes['fused-kernel'];x,y,w,h=[float(kernel.get(a)) for a in ['x','y','width','height']]
  for e in root.iter():
   if e.get('data-kernel-stage'):assert x<float(e.get('x'))<x+w and y<float(e.get('y'))<y+h
print({'pass':True,'weight_cases':weight_cases,'weights':WEIGHTS,'codes':Q,'reconstructed':RESTORED,
       'svg_documents':documents,'matrix_weights':32,'per_group_scales':16,'packed_byte':'00011011','payload_bits':[64,8]})
