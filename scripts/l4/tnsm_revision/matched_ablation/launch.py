#!/usr/bin/env python3
"""Run the ablation in a separate container using the existing gateway image.

Only eight provider configuration values cross a private stdin pipe. No keys
are printed or written to files. Only new output storage is mounted writable.
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
CONFIG={p+'_'+s for p in ['OPENAI','ANTHROPIC','DEEPSEEK','MISTRAL'] for s in ['MODEL','API_KEY']}

def launch(args):
    # Exact fields only: never retrieve docker inspect .Config.Env.
    result=subprocess.run(['docker','inspect','--format','{{.Image}}',args.gateway_container],capture_output=True,text=True)
    if result.returncode:raise SystemExit('Cannot identify the running gateway image.')
    image=result.stdout.strip()
    if not image.startswith('sha256:') or len(image)!=71:raise SystemExit('Invalid gateway image digest.')
    probe='import json,os; print(json.dumps({k:os.getenv(k,"") for k in '+repr(sorted(CONFIG))+'}))'
    result=subprocess.run(['docker','exec',args.gateway_container,'python','-c',probe],capture_output=True,text=True)
    if result.returncode:raise SystemExit('Cannot read the allowlisted provider configuration.')
    try:env=json.loads(result.stdout)
    except ValueError:raise SystemExit('Invalid provider-configuration response.')
    if set(env)!=CONFIG:raise SystemExit('Unexpected provider configuration.')
    workspace=args.workspace.expanduser().resolve()
    workspace.mkdir(parents=True,exist_ok=True)
    if ',' in str(workspace) or ',' in str(HERE):raise SystemExit('Commas in mount paths are unsupported.')
    for model in (env[p+'_MODEL'] for p in ['OPENAI','ANTHROPIC','DEEPSEEK','MISTRAL']):
        if model.startswith(('sk-','ghp_','gho_')):raise SystemExit('Model field resembles a credential; configuration needs correction.')
    cmd=['docker','run','--rm','-i','--read-only','--tmpfs','/tmp:rw,nosuid,size=256m',
      '--user',f'{os.getuid()}:{os.getgid()}','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONUNBUFFERED=1','--env','TNSM_GATEWAY_IMAGE_ID='+image,
      '--mount',f'type=bind,src={HERE},dst=/study,readonly',
      '--mount',f'type=bind,src={workspace},dst=/results',
      '--entrypoint','python',image,'/study/bootstrap.py']
    program='study.py';argv=[]
    if args.command=='preflight':argv=['preflight']
    elif args.command=='freeze':
        argv=['freeze','--output','/results/'+args.name,'--phase',args.phase,
          '--assessor-tokens',str(args.assessor_tokens),'--role-tokens',str(args.role_tokens)]
        if args.synthetic:argv+=['--synthetic']
    elif args.command=='run':
        argv=['run','--output','/results/'+args.name]
        if args.live:argv+=['--live']
    elif args.command=='analyze':
        program='analyze.py';argv=['--input','/results/'+args.name,'--report-dir','/results/'+args.name+'_analysis']
    if args.command!='preflight' and (not args.name or not all(c.isalnum() or c in '-_' for c in args.name)):
        raise SystemExit('Use only letters, digits, hyphens and underscores in the study name.')
    receipt={'gateway_image_id':image,'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'study_code_sha256':hashlib.sha256((HERE/'study.py').read_bytes()).hexdigest(),
      'command':args.command,'study_name':args.name,'recorded_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
      'credentials_logged':False,'new_container':True,'gateway_data_mounted':False}
    if args.command=='freeze':
        target=workspace/(args.name+'_launch_identity.json')
        with target.open('x') as f:json.dump(receipt,f,indent=2)
    if args.command in {'run','analyze'}:
        identity=json.loads((workspace/(args.name+'_launch_identity.json')).read_text())
        if identity['gateway_image_id']!=image:raise SystemExit('Gateway image changed; use a separately frozen study.')
    print('Isolated image:',image,flush=True)
    process=subprocess.run(cmd,input=json.dumps({'environment':env,'argv':argv,'program':program}).encode())
    raise SystemExit(process.returncode)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['preflight','freeze','run','analyze'])
    p.add_argument('--gateway-container',default='zktrustllm-l4-n8n-gateway-1')
    p.add_argument('--workspace',type=Path,default=Path.cwd()/'artifacts/out/tnsm_matched_ablation_20261016')
    p.add_argument('--name',default='pilot_01')
    p.add_argument('--phase',choices=['pilot','full'],default='pilot')
    p.add_argument('--assessor-tokens',type=int,default=5000);p.add_argument('--role-tokens',type=int,default=4500)
    p.add_argument('--live',action='store_true');p.add_argument('--synthetic',action='store_true')
    launch(p.parse_args())
if __name__=='__main__':main()
