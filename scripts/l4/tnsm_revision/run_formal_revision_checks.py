#!/usr/bin/env python3
"""Reproduce the original finite TLC run and zero-input sensitivity check."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[3]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--jar',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,default=ROOT/'paper/tnsm_revision_20261015/evidence/formal')
    args=ap.parse_args();jar=args.jar.resolve();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    base=ROOT/'formal/tla';reports=[]
    original=(base/'ZKTrustLLMPolicyGate.tla').read_text()
    cases=[('original','ZKTrustLLMPolicyGate',None,None),('zero_input_probe','ZKTrustLLMPolicyGateZeroProbe',None,None),
      ('mutation_no_admissibility','ZKTrustLLMPolicyGateZeroProbe',('/\\ proofValid = TRUE','/\\ TRUE'),'ProofRequired'),
      ('mutation_no_zero_guard','ZKTrustLLMPolicyGateZeroProbe',('/\\ anchorCommitment # 0','/\\ TRUE'),'NonZeroAnchorRequired'),
      ('mutation_no_human_for_privileged','ZKTrustLLMPolicyGate',('THEN humanApproved /\\ privilegedApproved','THEN privilegedApproved'),'PrivilegedRequiresBoth')]
    for name,module,mutation,expected_violation in cases:
        with tempfile.TemporaryDirectory(prefix='tnsm-tlc-') as temp:
            tmp=Path(temp)
            for file in base.glob('ZKTrustLLMPolicyGate*'):
                if file.suffix in {'.tla','.cfg'}:shutil.copy2(file,tmp/file.name)
            if mutation:
                old,new=mutation
                if old not in original:raise ValueError('mutation target absent')
                (tmp/'ZKTrustLLMPolicyGate.tla').write_text(original.replace(old,new))
            cmd=['java','-XX:+UseParallelGC','-cp',str(jar),'tlc2.TLC','-deadlock','-seed','20261015','-workers','1',module+'.tla']
            r=subprocess.run(cmd,cwd=tmp,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
            log=out/(name+'.log');log.write_text(r.stdout)
            count=re.search(r'(\d+) states generated, (\d+) distinct states found, (\d+) states left on queue',r.stdout)
            violation=re.search(r'Invariant (\w+) is violated',r.stdout)
            ok=(r.returncode==0 and 'No error has been found' in r.stdout) if expected_violation is None else (r.returncode!=0 and violation is not None and violation.group(1)==expected_violation)
            record={'case':name,'expected_invariant_violation':expected_violation,'observed_violation':violation.group(1) if violation else None,
                    'returncode':r.returncode,'check_passed':ok,'generated_states':int(count.group(1)) if count else None,
                    'distinct_states':int(count.group(2)) if count else None,'remaining_states':int(count.group(3)) if count else None,
                    'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
            reports.append(record)
            if not ok:raise RuntimeError(f'formal check failed: {name}; see {log}')
    report={'schema':'zktrustllm.tnsm.formal_revision_checks.v1','tla2tools_jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
            'model_sha256':hashlib.sha256((base/'ZKTrustLLMPolicyGate.tla').read_bytes()).hexdigest(),
            'zero_probe_sha256':hashlib.sha256((base/'ZKTrustLLMPolicyGateZeroProbe.tla').read_bytes()).hexdigest(),
            'model_tool_version':reports and (out/'original.log').read_text().splitlines()[0],
            'checks':reports,'production_implementation_verified':False,'duplicate_anchor_rejection_modelled':False,
            'scope':'Finite safety abstraction and mutation sensitivity. No liveness, deployment, cryptographic proof or code refinement result.'}
    (out/'formal_revision_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
