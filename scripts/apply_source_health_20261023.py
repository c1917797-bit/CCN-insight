# -*- coding: utf-8 -*-
"""Record bounded endpoint checks independently of content collection status."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables';DAY='2026-10-23'
def read(t):return [json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def save(t,data):(BASE/t/'rows.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in data),encoding='utf-8')
audit=json.loads((ROOT/'research/source-audits/2026-10-23/source-health-after-refresh.json').read_text(encoding='utf-8'))
data=read('ic_channels');by={r['channel_id']:r for r in audit['records']};checks=read('ic_channel_checks');ci={x['key']:i for i,x in enumerate(checks)}
for entry in data:
 r=entry['row'];check=by.get(r['channel_id'])
 if not check:continue
 ok=check['status']=='entrypoint_fetched';code=check.get('http_status')
 if ok:zh='入口样本可读取；未据此确认所有内容或分页均已采集。';en='Endpoint sample retrieved; not a complete content or pagination check.'
 elif code in [403,429,412,468]:zh='本轮自动访问受限（HTTP '+str(code)+'）；不据此判定来源停更或失效。';en='Automated access restricted (HTTP '+str(code)+'); not evidence of discontinuation.'
 elif code==404:zh='本轮请求返回404，具体替代入口尚待确认。';en='Endpoint returned 404; a replacement remains unconfirmed.'
 else:zh='本轮读取未完成；需进一步核对网络、动态加载或跳转条件。';en='Fetch incomplete; network, dynamic rendering or redirects need checking.'
 patch=dict(entrypoint_checked_at=DAY,entrypoint_status='sample_readable' if ok else 'access_restricted' if code in [403,429,412,468] else 'needs_check',entrypoint_note_zh=zh,entrypoint_note_en=en)
 if any(r.get(k)!=v for k,v in patch.items()):r.update(patch);entry['row_version']+=1
 key='registry-health-'+r['channel_id']+'-20261023'
 row=dict(business_id='cloud-core',topic_id='cloud_core',channel_id=r['channel_id'],check_id=key,source_id=r['source_id'],checked_at=DAY,captured_research_items=0,observed_title=check.get('observed_title',''),performance_verified=False,reason_zh=zh,reason_en=en,result='checked' if ok else 'fetch_incomplete',retrieval_method='bounded_public_https_sample',verification_scope='entrypoint_sample_only_not_content_coverage')
 if key in ci:
  old=checks[ci[key]]
  if old['row']!=row:checks[ci[key]]={**old,'row':row,'row_version':old['row_version']+1}
 else:checks.append(dict(key=key,row=row,row_version=1,deleted=False,text_match=None))
save('ic_channels',data);save('ic_channel_checks',checks)
p=BASE/'ic_channels/definition.json';d=json.loads(p.read_text(encoding='utf-8'))
for k in ['entrypoint_checked_at','entrypoint_status','entrypoint_note_zh','entrypoint_note_en']:d['fields'][k]=dict(projection='default',required=False,role='value',source=None,type='string')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded endpoint checks:',len(by),audit['counts'])
