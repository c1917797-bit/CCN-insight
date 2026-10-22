"""Exercise edit fencing, rollback and protected identifiers using disposable data."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import compression_maintenance as editor

class EditSafety(unittest.TestCase):
    def setUp(self):
        fixture_parent=Path(__file__).resolve().parents[2]/'.tmp/maintenance-tests'
        fixture_parent.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=fixture_parent)
        self.root=Path(self.tmp.name);self.data=self.root/'data/compression';folder=self.data/'tables/example';folder.mkdir(parents=True)
        self.file=folder/'rows.jsonl'
        self.file.write_text(json.dumps({'key':'card-1','row_version':1,'row':{'id':'card-1','business_id':'cloud-core','title_zh':'Original'}})+'\n',encoding='utf-8')
        definition={'key_field':'id','fields':{'id':{'type':'string','required':True},'business_id':{'type':'string','required':True},'title_zh':{'type':'text','required':True}}}
        (folder/'definition.json').write_text(json.dumps(definition),encoding='utf-8')
        self.version=lambda:'v-'+hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.patches=[patch.object(editor,'ROOT',self.root),patch.object(editor,'DATA',self.data),patch.object(editor,'content_version',self.version),patch.object(editor,'table_info',return_value={'rows_file':'data/compression/tables/example/rows.jsonl'})]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_stale_version_does_not_write(self):
        before=self.file.read_bytes()
        with self.assertRaises(ValueError):editor.apply_change('example','card-1',{'title_zh':'New'},'stale')
        self.assertEqual(self.file.read_bytes(),before)
        self.assertFalse((self.data/'.edit.lock').exists())
    def test_key_changes_rejected(self):
        with self.assertRaises(ValueError):editor.apply_change('example','card-1',{'id':'other'},self.version())
    def test_validation_failure_restores_exact_bytes(self):
        before=self.file.read_bytes()
        with patch.object(editor.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='broken reference')):
            with self.assertRaises(ValueError):editor.apply_change('example','card-1',{'title_zh':'New'},self.version())
        self.assertEqual(self.file.read_bytes(),before)
    def test_success_has_backup_and_new_version(self):
        before=self.file.read_bytes();version=self.version()
        with patch.object(editor.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='')):
            result=editor.apply_change('example','card-1',{'title_zh':'New'},version)
        self.assertNotEqual(result['version'],version)
        self.assertEqual(json.loads(self.file.read_text())['row']['title_zh'],'New')
        self.assertEqual((self.root/'.maintenance/backups'/result['change_id']/'rows.jsonl').read_bytes(),before)

if __name__=='__main__':unittest.main()
