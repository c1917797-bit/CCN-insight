"""Local maintenance workbench. Serves loopback only; has no publish operation."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, DATA, rows, records, manifest, content_version, clear_cache
from compression_maintenance import table_info, apply_change

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
    def trusted(self,write=False):
        host=self.headers.get('Host','')
        expected={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
        if host not in expected:raise ValueError('Loopback Host required')
        if write and self.headers.get('Origin')!='http://'+host:raise ValueError('Same-origin browser request required')
    def answer(self,data,status=200):
        content=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    def do_GET(self):
        try:
            self.trusted();request=urlsplit(self.path);query=parse_qs(request.query);clear_cache()
            if request.path=='/':
                content=(ROOT/'content/compression-maintenance.html').read_bytes()
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content);return
            if request.path=='/api/status':
                staged=json.loads((DATA/'staged-release.json').read_text(encoding='utf-8')) if (DATA/'staged-release.json').exists() else None
                version=content_version();return self.answer({'version':version,'import_revision':manifest()['revision'],'staged':staged,'needs_build':not staged or staged['content_version']!=version,'published':False,'source':'data/compression/tables/'})
            if request.path=='/api/catalog':
                return self.answer({'topics':rows('ic_compression_topics'),'tables':[{'name':t['name'],'count':len(records(t['name']))} for t in manifest()['tables']]})
            if request.path=='/api/records':
                table=query.get('table',['ic_compression_topic_cards'])[0];table_info(table)
                topic=query.get('topic',[''])[0];search=query.get('q',[''])[0].lower()
                data=[r for r in records(table) if not r.get('deleted')]
                if topic:data=[r for r in data if r['row'].get('compression_topic_id')==topic]
                if search:data=[r for r in data if search in json.dumps(r['row'],ensure_ascii=False).lower()]
                result=[]
                for r in data[:100]:
                    row=r['row'];label=next((row[k] for k in ('title_zh','title','label_zh','one_sentence_zh','name_zh') if row.get(k)),r['key'])
                    result.append({'key':r['key'],'label':str(label)[:180]})
                return self.answer({'records':result,'total':len(data),'limited':len(data)>100})
            if request.path=='/api/record':
                table=query['table'][0];info=table_info(table);key=query['key'][0]
                record=next(r for r in records(table) if r['key']==key)
                definition=json.loads((ROOT/info['rows_file']).with_name('definition.json').read_text(encoding='utf-8'))
                return self.answer({'row':record['row'],'key_field':info['key_field'],'version':content_version(),'definition':definition})
            if request.path.startswith('/api/'):return self.answer({'error':'Unknown endpoint'},404)
            if not request.path.startswith(('/ai-infra/','/business_insight/cloud_core/','/assets/')) and request.path not in ('/sources.html','/sources.csv'):return self.answer({'error':'Not served'},404)
            return super().do_GET()
        except Exception as error:self.answer({'error':str(error)},400)
    def do_POST(self):
        try:
            self.trusted(write=True)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('JSON required')
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1024*1024:raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
            if path=='/api/save':
                return self.answer(apply_change(data['table'],data['key'],data['updates'],data['expected_version']))
            if path=='/api/build':
                if data['expected_version']!=content_version():raise ValueError('Content changed. Refresh before building.')
                result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/stage_compression.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
                if result.returncode:raise ValueError((result.stdout+'\n'+result.stderr)[-4000:])
                return self.answer(json.loads((DATA/'staged-release.json').read_text(encoding='utf-8')))
            return self.answer({'error':'Unknown endpoint'},404)
        except FileExistsError:self.answer({'error':'Another edit or build is in progress. Try again when it finishes.'},409)
        except Exception as error:self.answer({'error':str(error)},400)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8785);args=parser.parse_args()
    print('Local maintenance: http://127.0.0.1:'+str(args.port)+'/',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
