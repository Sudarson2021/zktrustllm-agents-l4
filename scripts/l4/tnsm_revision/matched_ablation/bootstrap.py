"""Read provider configuration from stdin in an isolated container; never log it."""
import json, os, runpy, sys
from pathlib import Path
keys={p+'_'+suffix for p in ['OPENAI','ANTHROPIC','DEEPSEEK','MISTRAL'] for suffix in ['MODEL','API_KEY']}
payload=json.load(sys.stdin)
if set(payload) != {'environment','argv','program'} or set(payload['environment']) != keys:
    raise SystemExit('invalid bootstrap contract')
for name,value in payload['environment'].items():
    if not isinstance(value,str) or any(ord(c)<32 for c in value):
        raise SystemExit('invalid provider configuration')
    os.environ[name]=value
program=payload['program']
if program not in {'study.py','analyze.py'}:raise SystemExit('invalid program')
sys.path.insert(0,str(Path(__file__).parent))
sys.argv=[program]+payload['argv']
runpy.run_path(str(Path(__file__).parent/program),run_name='__main__')
