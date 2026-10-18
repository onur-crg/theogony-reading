#!/usr/bin/env python3
"""Tool-disabled, source-tracked CLI review or note regeneration. Never edits source text."""
import argparse,hashlib,json,subprocess,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('prompt',type=Path);p.add_argument('schema',type=Path);p.add_argument('output',type=Path);p.add_argument('--version',required=True);a=p.parse_args()
 assert not a.output.exists(),a.output
 prompt=a.prompt.read_text();a.output.parent.mkdir(parents=True,exist_ok=True)
 saved=a.output.with_suffix('.prompt.txt')
 if saved.resolve()!=a.prompt.resolve():saved.write_text(prompt)
 record={'run_id':str(uuid4()),'created_at_utc':datetime.now(timezone.utc).isoformat(),'prompt_version':a.version,'prompt_file':saved.name,'prompt_sha256':digest(saved),'source_sha256':digest(ROOT/'sources/tlg0020.tlg001.perseus-grc2.xml'),'section_boundaries_sha256':digest(ROOT/'content/leseabsaetze.md'),'schema_sha256':digest(a.schema),'runner_sha256':digest(Path(__file__)),'codex_cli_version':subprocess.check_output(['codex','--version'],text=True).strip(),'model':'gpt-6.1-sol','effort':'high','range':[1,1022]}
 with tempfile.TemporaryDirectory(prefix='theogony-notes-') as isolated:
  last=Path(isolated)/'last.json'
  command=['codex','exec','--ignore-user-config','--strict-config','--skip-git-repo-check','--ephemeral','--cd',isolated,'--model',record['model'],'--config','default_permissions="translation"','--config','permissions.translation.filesystem={ ":minimal" = "read", ":workspace_roots" = { "." = "read" }, "/opt/homebrew/bin" = "read", "/opt/homebrew/Caskroom/codex" = "read" }','--config','model_reasoning_effort="high"','--config','web_search="disabled"','--config','skills.include_instructions=false','--output-schema',str(a.schema.resolve()),'--output-last-message',str(last),'--json']
  for flag in ['shell_tool','unified_exec','code_mode','apps','plugins','memories','browser_use','computer_use','multi_agent','image_generation','goals']:command+=['--disable',flag]
  command+=['-'];start=time.monotonic();c=subprocess.run(command,input=prompt,text=True,capture_output=True)
  events=[]
  for line in c.stdout.splitlines():
   try:events.append(json.loads(line))
   except json.JSONDecodeError:pass
  kinds={e.get('item',{}).get('type','') for e in events if e.get('type','').startswith('item.')}
  tools=[k for k in kinds if k.endswith('tool_call') or k in ['command_execution','web_search_call','function_call','computer_call']]
  errors=[e for e in events if e.get('type')=='error' or e.get('item',{}).get('type')=='error']
  record.update(seconds=round(time.monotonic()-start,2),cli_exit=c.returncode,tool_event_count=len(tools),item_types=sorted(kinds),usage_events=[e for e in events if 'usage' in e],error_events=errors)
  if c.returncode or tools or errors or not last.exists():
   print(c.stderr[-2000:]);print(record);raise SystemExit('Constrained run failed')
  result=json.loads(last.read_text())
  from jsonschema import validate
  validate(result,json.loads(a.schema.read_text()))
  a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');record['output_sha256']=digest(a.output)
  a.output.with_suffix('.metrics.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({k:v for k,v in record.items() if k!='usage_events'}))
if __name__=='__main__':main()
