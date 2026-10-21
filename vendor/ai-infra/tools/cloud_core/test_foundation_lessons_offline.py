"""Offline lesson integration: exact repository modules and explicit scientific fixtures.
No production network, credentials or live-page acceptance claims.
"""
from pathlib import Path
import argparse,json,os,shutil,tempfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--fixture',required=True,type=Path);ap.add_argument('--output',type=Path);args=ap.parse_args()
data=json.loads(args.fixture.read_text());checks=[]
ui={lang:json.loads((ROOT/f'business_insight/cloud_core/data/foundations-ui.{lang}.json').read_text())['strings'] for lang in ['zh','en']}
markup='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:12px}main{max-width:820px;margin:auto}.gap{height:700px}</style></head><body><main id="root"></main><script type="module">
import '/business_insight/cloud_core/foundation-player.js';
const fixture=FIXTURE, ui=UI;
window.testFixture=fixture;
for(const method of ['quantization','pruning_sparsity','low_rank','distillation']){
 const e=document.createElement('lri-foundation-lesson');e.id=method;
 e.lesson={method,steps:fixture.steps.filter(r=>r.method_id===method),values:fixture.values.filter(r=>r.method_id===method),locale:'zh',ui:ui.zh,referenceNumbers:Object.fromEntries(fixture.steps.map(r=>[r.source_url,1]))};
 root.append(e);const gap=document.createElement('div');gap.className='gap';root.append(gap);
}
window.lessonReady=true;
</script></body></html>'''.replace('FIXTURE',json.dumps(data,ensure_ascii=False)).replace('UI;',json.dumps(ui,ensure_ascii=False)+';')
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1200,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  from urllib.parse import urlparse
  path=urlparse(r.request.url).path
  if path=='/':r.fulfill(status=200,content_type='text/html',body=markup)
  else:
   p=ROOT/path.lstrip('/')
   if p.is_file() and p.resolve().is_relative_to(ROOT.resolve()):r.fulfill(status=200,content_type='text/javascript' if p.suffix=='.js' else 'application/json',body=p.read_text())
   else:r.abort()
 page.route('**/*',route);page.goto('https://lesson.test.invalid/')
 page.wait_for_function("window.lessonReady && document.querySelector('#quantization').shadowRoot.querySelector('lri-motion-scene').shadowRoot.querySelector('svg')")
 first=page.locator('#quantization')
 assert first.locator('select').input_value()=='1';assert first.evaluate('e=>e.playbackRate')==1
 assert first.get_attribute('data-lesson-state')=='paused';checks.append('default paused and speed UI/API both 1x')
 first.locator('[data-action=next]').click();assert first.get_attribute('data-lesson-step')=='1'
 first.locator('[data-action=prev]').click();assert first.get_attribute('data-lesson-step')=='0';checks.append('ordinary previous/next clicks')
 first.locator('[data-action=play]').click();page.wait_for_timeout(150);before=first.evaluate('e=>e.currentTime');assert before>80
 first.locator('[data-action=play]').click();before=first.evaluate('e=>e.currentTime');page.wait_for_timeout(120);assert first.evaluate('e=>e.currentTime')==before
 first.locator('select').select_option('2');first.locator('[data-action=play]').click();page.wait_for_timeout(150);assert first.evaluate('e=>e.currentTime')-before>200;checks.append('play pause and playback rate use one clock')
 page.locator('#pruning_sparsity').scroll_into_view_if_needed();page.wait_for_timeout(90);assert first.get_attribute('data-lesson-state')=='paused';checks.append('offscreen pause')
 first.scroll_into_view_if_needed();first.locator('[data-action=restart]').click();assert first.evaluate('e=>e.currentTime')==0
 page.emulate_media(reduced_motion='reduce');assert first.locator('[data-action=play]').is_disabled();first.locator('[data-action=next]').click();assert first.get_attribute('data-lesson-step')=='1';page.emulate_media(reduced_motion='no-preference');assert first.locator('[data-action=play]').is_enabled();checks.append('reduced motion retains manual complete stages and re-enables motion')
 # Actual causal properties must change when the same scene is sought.
 for method,index,selector,property in [('quantization',3,'.pack0','transform'),('quantization',5,'.clip-probe','transform'),('pruning_sparsity',1,'.removed-connection','strokeDashoffset'),('low_rank',2,'.intermediate','transform'),('distillation',3,'.student0','width')]:
  e=page.locator('#'+method);e.evaluate('(e,index)=>e.go(index)',index)
  page.wait_for_function("x=>{const e=document.getElementById(x.method),s=e.shadowRoot.querySelector('lri-motion-scene');return s.shadowRoot.querySelector(x.selector)}",arg={'method':method,'selector':selector})
  a=e.evaluate("(e,o)=>{const scene=e.shadowRoot.querySelector('lri-motion-scene');scene.seek(0);return getComputedStyle(scene.shadowRoot.querySelector(o.selector))[o.property]}",{'selector':selector,'property':property})
  b=e.evaluate("(e,o)=>{const scene=e.shadowRoot.querySelector('lri-motion-scene');scene.seek(8000);return getComputedStyle(scene.shadowRoot.querySelector(o.selector))[o.property]}",{'selector':selector,'property':property})
  assert a!=b,(method,index,a,b);checks.append('causal property changes: '+method+'/'+str(index))
 # All real storyboard stages produce valid, finite diagrams.
 count=0
 for method in ['quantization','pruning_sparsity','low_rank','distillation']:
  e=page.locator('#'+method);steps=[r for r in data['steps'] if r['method_id']==method]
  for i,row in enumerate(steps):
   e.evaluate('(e,i)=>e.go(i)',i)
   page.wait_for_function("x=>document.getElementById(x.method).shadowRoot.querySelector('lri-motion-scene').shadowRoot.querySelector('svg > g')?.id===x.kind",arg={'method':method,'kind':row['scene_kind']})
   text=e.locator('svg').inner_text();assert not any(x in text for x in ['undefined','NaN','Infinity']);count+=1
 checks.append('all '+str(count)+' canonical stages render')
 # Real mobile clicks must select the intended stage, never a right-side floating dock.
 page.evaluate("""() => {const d=document.createElement('button');d.id='test-dock';d.textContent='Dock';d.style.cssText='position:fixed;right:10px;top:45vh;width:56px;height:56px;z-index:9999';d.onclick=()=>window.dockClicked=true;document.body.append(d);window.dockClicked=false;}""")
 for width in [320,390]:
  page.set_viewport_size({'width':width,'height':844})
  for method in ['quantization','pruning_sparsity','low_rank','distillation']:
   e=page.locator('#'+method)
   for i in range(len([r for r in data['steps'] if r['method_id']==method])):
    e.locator('.steps button').nth(i).click()
    assert e.get_attribute('data-lesson-step')==str(i),(width,method,i)
    assert not page.evaluate('window.dockClicked'),(width,method,i,'floating dock intercepted click')
    page.wait_for_timeout(60)
  checks.append(str(width)+'px: all 18 normal step clicks select intended stage with floating dock')
 page.evaluate("document.getElementById('test-dock').remove()")
 page.set_viewport_size({'width':1200,'height':1000})
 # Both fetched and inline sources use the same admission. Reject before insertion.
 e=first
 for bad in ['<script>alert(1)</script>','<g onload="alert(1)"/>','<foreignObject/>','<image href="https://evil.example/x"/>','<style>@import "https://evil.example/x";</style>']:
  e.evaluate('(e,bad)=>{e.shadowRoot.querySelector("lri-motion-scene").sceneMarkup=\'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200">\'+bad+\'</svg>\'}',bad)
  page.wait_for_function("document.querySelector('#quantization').shadowRoot.querySelector('lri-motion-scene').dataset.sceneState==='error'")
  assert e.locator('svg').count()==0
 checks.append('five active SVG/CSS vectors rejected before insertion')
 first.evaluate('e=>e.go(0)');page.wait_for_function("!!document.querySelector('#quantization').shadowRoot.querySelector('lri-motion-scene').shadowRoot.querySelector('svg')")
 assert not errors,errors
 checks.append('valid scene recovers and no page errors')
 browser.close()
report={'pass':True,'network':'blocked; route-fed repository modules and explicit fixtures','checks':checks}
if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
