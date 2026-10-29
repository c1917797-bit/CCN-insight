/* Original-site entry must preserve reading context without duplicating facts. */
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'ccn-entry-test-'));
try {
 cp.execFileSync('python',['scripts/build_original_entry.py',temp],{cwd:root,stdio:'pipe'});
 const config=JSON.parse(fs.readFileSync(path.join(temp,'canonical-reader.json'),'utf8'));
 const code=fs.readFileSync(path.join(temp,'canonical-reader.js'),'utf8');
 const run=url=>{
  const current=new URL(url),link={href:''},redirects=[];
  const location={pathname:current.pathname,origin:current.origin,search:current.search,hash:current.hash,replace:next=>redirects.push(next)};
  vm.runInNewContext(code,{URL,URLSearchParams,location,document:{getElementById:()=>link}});
  return {redirects,link};
 };
 for(const file of config.entrypoints){
  const result=run('https://original.example/business_insight/cloud_core/'+file+'?month=2026-10&scope=review&topic=parameters-precision&lang=en&token=do-not-forward&return=https%3A%2F%2Fother.example#research-card-awq');
  assert.equal(result.redirects.length,1);
  const target=new URL(result.redirects[0]);
  assert.equal(target.origin,new URL(config.canonical_reader).origin);
  assert.equal(target.pathname,new URL(config.routes?.[file]?.file||file,config.canonical_reader).pathname);
  assert.equal(target.hash,'#research-card-awq');
  assert.equal(target.searchParams.get('month'),'2026-10');
  assert.equal(target.searchParams.get('scope'),'review');
  assert.equal(target.searchParams.get('topic'),'parameters-precision');
  assert.equal(target.searchParams.get('lang'),'en');
  assert(!target.searchParams.has('token'));assert(!target.searchParams.has('return'));
  assert.equal(result.link.href,target.href);
  assert.equal(run(target.href).redirects.length,0,'Canonical reader must not loop');
  const html=fs.readFileSync(path.join(temp,file),'utf8');
  assert(html.includes('canonical-reader-link'));assert(!html.includes('local-content/'));
  assert(html.includes('lri-shell-v18-cloud-report-navigation'));
 }
 assert.equal(new URL(run('https://original.example/business_insight/cloud_core/').redirects[0]).hash,'#view-topics');
 const archive=new URL(run('https://original.example/business_insight/cloud_core/archive.html?month=2026-10&scope=review').redirects[0]);
 assert.equal(archive.pathname,new URL('index.html',config.canonical_reader).pathname,'Archive entry must use the adopted report archive, not the unmigrated legacy material library');
 assert.equal(archive.hash,'#view-reports');
 assert.equal(archive.searchParams.get('month'),'2026-10');
 assert.equal(run('https://original.example/business_insight/cloud_core/unrelated.html').redirects.length,0);
 const marker=JSON.parse(fs.readFileSync(path.join(root,'dist/business_insight/cloud_core/compression-release.json'),'utf8'));
 const generated=JSON.parse(fs.readFileSync(path.join(root,'dist/original-reader-version.json'),'utf8'));
 assert.equal(marker.content_version,generated.content_version);
 assert.equal(marker.reader_revision,generated.local_revision);
 assert.match(marker.ui_revision,/^[a-f0-9]{20}$/);
 assert.equal(marker.canonical_reader,config.canonical_reader);
 console.log('PASS: five entry routes; query/hash preservation; credential exclusion; loop prevention; release provenance');
} finally {
 assert(path.resolve(temp).startsWith(path.resolve(os.tmpdir())+path.sep));
 fs.rmSync(temp,{recursive:true,force:true});
}
