"""Run from the source tree after building and clean-installing the wheel."""
import json,pathlib,subprocess,tempfile,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
WHEEL_PY=pathlib.Path(sys.argv[1]).absolute()
results=[]
with tempfile.TemporaryDirectory() as d:
 d=pathlib.Path(d)
 shutil.copy2(ROOT/'main.py',d/'main.py'); shutil.copytree(ROOT/'examples',d/'examples')
 def run(label,args,expected=0):
  p=subprocess.run(args,cwd=d,text=True,capture_output=True)
  results.append({'label':label,'command':list(map(str,args)),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
  assert p.returncode==expected,(label,p.stdout,p.stderr)
  return p
 loc=run('wheel import location',[WHEEL_PY,'-I','-c','import event_validator; print(event_validator.__file__)'])
 assert 'site-packages' in loc.stdout and '/source/' not in loc.stdout
 args=['--matrix','examples/matrix_v1.json','--input','examples/replay.jsonl']
 cli=WHEEL_PY.parent/'event-validate'
 a=run('installed wheel CLI',[cli,*args])
 b=run('standalone isolated',[WHEEL_PY,'-I','main.py',*args])
 aa=[json.loads(x) for x in a.stdout.splitlines()]; bb=[json.loads(x) for x in b.stdout.splitlines()]
 assert aa==bb and len(aa)==3 and [x['status'] for x in aa].count('ACCEPTED')==2
 for label,command in [('wheel',[cli]),('standalone',[WHEEL_PY,'-I','main.py'])]:
  c=run(label+' SQLite creation',[*command,*args,'--db',label+'.sqlite'])
  assert all(x['storage_state']=='CREATED' for x in map(json.loads,c.stdout.splitlines()))
  c=run(label+' SQLite repeat',[*command,*args,'--db',label+'.sqlite'])
  assert all(x['storage_state']=='DUPLICATE' for x in map(json.loads,c.stdout.splitlines()))
  run(label+' bad config',[*command,'--matrix','absent'],2)
(ROOT/'final_evidence/distribution_results.json').write_text(json.dumps(results,indent=2))
print('PASS: wheel import, CLI, isolated standalone parity, SQLite creation/replay, config exit codes')
