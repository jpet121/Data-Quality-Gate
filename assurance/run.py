"""Bounded local audit profiles; C requires explicit local-target authorization."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import resource
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def process_limits() -> None:
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(600,600))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def execute(command: list[str], label: str, timeout: int) -> dict:
    start=datetime.now(timezone.utc).isoformat(); before=time.monotonic()
    log=ROOT/'final_evidence'/f'profile_{label}.txt'
    with log.open('w') as output:
        process=subprocess.Popen(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=process_limits)
        try: code=process.wait(timeout=timeout);state='EXECUTED'
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait();code=124;state='TIMEOUT'
    return {'command':command,'started_at':start,'completed_at':datetime.now(timezone.utc).isoformat(),
            'wall_seconds':time.monotonic()-before,'exit_code':code,'state':state,'log':str(log.relative_to(ROOT))}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['A','B','C'],default='A')
    parser.add_argument('--authorized-local-target',action='store_true',help='Authorize only the supplied local validator; never external endpoints')
    args=parser.parse_args()
    if args.profile=='C':
        if not args.authorized_local_target:
            print('BLOCKED: explicit local-target authorization flag required');return 2
        result=execute([sys.executable,'-m','assurance.campaign','--cases','100000','--seed','20261029','--authorized-local-target'],'C_differential',180)
        (ROOT/'continuation_evidence/profile_C.json').write_text(json.dumps({'profile':'C','authorization':'user requested independent high-assurance verification and additional bounded testing of this supplied application; no external targets','results':[result]},indent=2))
        return 0 if result['exit_code']==0 else 1
    commands=[([sys.executable,'tools/build_standalone.py','--check'],'standalone',20),
              ([sys.executable,'-m','pytest','-q','test_suite.py','tests','--hypothesis-seed=20261029',
                '--junitxml=final_evidence/profile_'+args.profile+'.xml']+
               (['--ignore=tests/integration/test_postgres_independent.py'] if args.profile=='A' else []),'tests',120)]
    if args.profile=='B':
        if not os.environ.get('SESV_TEST_DSN'):
            print('BLOCKED: SESV_TEST_DSN must select a disposable PostgreSQL database; tests destroy its public schema.')
            return 2
        commands += [([sys.executable,'-m','assurance.calibration'],'calibration',20),
                     ([sys.executable,'verification/mutation_check.py'],'mutations',600),
                     ([sys.executable,'verification/seeded_boundary_sweep.py','--cases','50000','--seed','20261029'],'boundaries',120)]
    results=[]
    for command,label,timeout in commands:
        result=execute(command,args.profile+'_'+label,timeout);results.append(result)
        if result['exit_code']: break
    (ROOT/'final_evidence'/f'profile_{args.profile}.json').write_text(json.dumps({'profile':args.profile,'scope':'selected automated checks only; acceptance separately evaluated','results':results},indent=2))
    return 0 if all(x['exit_code']==0 for x in results) else 1

if __name__=='__main__':raise SystemExit(main())
