import contextlib,io,json,subprocess,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/l4/tnsm_revision/matched_ablation'))
import launch
class LaunchTests(unittest.TestCase):
    def test_credentials_use_private_stdin_and_new_container_has_no_gateway_data_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=SimpleNamespace(gateway_container='gateway',workspace=Path(tmp),command='preflight',name='pilot_01')
            env={k:('test-model' if k.endswith('_MODEL') else 'fixture-secret-key-123456') for k in launch.CONFIG};calls=[]
            def run(cmd,**kw):
                calls.append((cmd,kw))
                if cmd[:2]==['docker','inspect']:return SimpleNamespace(returncode=0,stdout='sha256:'+'0'*64+'\n')
                if cmd[:2]==['docker','exec']:return SimpleNamespace(returncode=0,stdout=json.dumps(env))
                return SimpleNamespace(returncode=0)
            with patch.object(launch.subprocess,'run',side_effect=run),contextlib.redirect_stdout(io.StringIO()) as captured:
                with self.assertRaises(SystemExit) as e:launch.launch(args)
            self.assertEqual(e.exception.code,0)
            self.assertNotIn('fixture-secret',captured.getvalue())
            cmd,kw=calls[-1];self.assertIn('--read-only',cmd)
            self.assertNotIn('fixture-secret',' '.join(cmd));self.assertNotIn('--env-file',cmd)
            self.assertIn('fixture-secret',kw['input'].decode())
            mounts=[cmd[i+1] for i,x in enumerate(cmd) if x=='--mount']
            self.assertEqual(len(mounts),2);self.assertTrue(any('dst=/study,readonly' in m for m in mounts))
            self.assertTrue(any('dst=/results' in m for m in mounts))
            self.assertFalse(list(Path(tmp).rglob('*')))
    def test_inspect_failure_does_not_dump_environment(self):
        args=SimpleNamespace(gateway_container='gateway')
        with patch.object(launch.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='private')):
            with self.assertRaises(SystemExit) as e:launch.launch(args)
        self.assertNotIn('private',str(e.exception))
if __name__=='__main__':unittest.main()
