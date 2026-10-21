import pathlib,json,hashlib,re
root=pathlib.Path(__file__).parent
manifest=json.loads((root/'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
missing=[]; mismatches=[]; findings=[]
pattern=re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|(?:password|basic_verify|person_verify|api_key)\s*[:=]\s*[\x22\x27][^\x22\x27]{8,}[\x22\x27]',re.I)
for item in manifest['files']:
    path=root/item['path']
    if not path.exists():missing.append(item['path']);continue
    data=path.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if blob!=item['blob']:mismatches.append(item['path'])
    if pattern.search(data):findings.append(item['path'])
result={'files':len(manifest['files']),'missing':missing,'hash_mismatches':mismatches,'possible_credentials_files':findings}
(root/'COPY-VERIFICATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
