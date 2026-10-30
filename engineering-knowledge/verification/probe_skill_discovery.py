from pathlib import Path
import json,subprocess,selectors,time
out=Path('/workspace/Structured_Event_Schema_Validator/engineering-knowledge/verification')
cwd=Path('/workspace/knowledge_capture_work/fresh-session');cwd.mkdir(exist_ok=True)
commands=[]
with (out/'fresh_discovery_stderr.txt').open('w') as errors:
 p=subprocess.Popen(['codex','app-server','--listen','stdio://'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1)
 selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ)
 def request(data):p.stdin.write(json.dumps(data)+'\n');p.stdin.flush();commands.append(data)
 def response(identifier):
  deadline=time.monotonic()+40
  while time.monotonic()<deadline:
   if not selector.select(timeout=1):
    if p.poll()is not None:raise RuntimeError('Fresh app-server exited')
    continue
   line=p.stdout.readline()
   if not line:raise RuntimeError('Unexpected app-server EOF')
   message=json.loads(line)
   if message.get('id')==identifier:return message
  raise TimeoutError('Skill discovery response timed out')
 try:
  request({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'clientInfo':{'name':'engineering_knowledge_validator','version':'1.0'}}})
  initialized=response(1)
  request({'jsonrpc':'2.0','method':'initialized','params':{}})
  request({'jsonrpc':'2.0','id':2,'method':'skills/list','params':{'cwds':[str(cwd)],'forceReload':True}})
  found=response(2)
  (out/'fresh_process_skill_discovery.json').write_text(json.dumps({'initialize':initialized,'skills_list':found},indent=2)+'\n')
  entries=found['result']['data']
  skill=next(s for entry in entries for s in entry['skills'] if s['name']=='evidence-driven-python-build')
  assert skill['enabled'] and skill['scope']=='user'
  assert Path(skill['path']).resolve()==Path('/home/agent/.agents/skills/evidence-driven-python-build/SKILL.md')
  assert not any(entry['errors'] for entry in entries)
  (out/'fresh_process_discovery_summary.json').write_text(json.dumps({'passed':True,'method':'fresh codex app-server process, native skills/list forceReload','cwd':str(cwd),'skill':skill,'parser_errors':[],'claim':'Native user-skill discovery verified; model execution is a separate check'},indent=2)+'\n')
  print('PASS: fresh Codex app-server discovered enabled user skill at',skill['path'])
 finally:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
