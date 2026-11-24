"""Optional serial executor reusing one resident native model.

The public CLI also starts a fresh executor. run_preloaded supports an existing
caller-owned model without depending on that caller's implementation or files.
"""
import argparse,contextlib,gc,importlib,json,os,runpy,signal,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def run_preloaded(model,tokenizer,request):
 import torch
 from transformers import AutoModelForCausalLM,AutoTokenizer
 os.chdir(ROOT);sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
 for name,module in list(sys.modules.items()):
  if name=='coretrace'or name.startswith('coretrace.'):
   origin=getattr(module,'__file__',None)
   if origin and not Path(origin).resolve().is_relative_to(ROOT):del sys.modules[name]
 state=Path(request['state']).resolve();state.mkdir(parents=True,exist_ok=True)
 for sub in ['requests','responses']:(state/sub).mkdir(exist_ok=True)
 capacity=int(request.get('capacity_bytes',torch.cuda.memory_reserved()));current=str(Path(request['model_path']).resolve());base_snapshot=None;fullft_path=None;stop=[False]
 def status(phase,**kw):atomic(state/'status.json',dict(pid=os.getpid(),phase=phase,model_path=current,capacity_bytes=capacity,**kw))
 def retain():
  if torch.cuda.is_available():
   gap=capacity-torch.cuda.memory_reserved()
   if gap>0:
    reservation=torch.empty(gap,device=next(model.parameters()).device,dtype=torch.uint8);del reservation
 def restore():
  nonlocal base_snapshot,fullft_path
  if base_snapshot is not None:
   with torch.no_grad():
    for name,parameter in model.named_parameters():parameter.copy_(base_snapshot[name])
   base_snapshot=None;fullft_path=None;gc.collect()
  model.eval().requires_grad_(False);model.config.use_cache=True
 def replace(path):
  nonlocal current
  restore();status('LOADING_NEXT_MODEL_ON_CPU',next_model=str(path))
  from coretrace.models.native import load_native
  new,tok=load_native(str(path),family=importlib.import_module('transformers').AutoConfig.from_pretrained(path,local_files_only=True).model_type,device='cpu')
  model.__dict__.clear();model.__class__=type(new);model.__dict__.update(new.__dict__)
  tokenizer.__dict__.clear();tokenizer.__class__=type(tok);tokenizer.__dict__.update(tok.__dict__)
  del new,tok;gc.collect();model.to('cuda:0');current=str(path);retain()
 def halt(*_):stop[0]=True
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
 if request.get('handoff_response'):atomic(request['handoff_response'],dict(status='COMPLETE',result=dict(status='RESIDENT_EXECUTOR_READY',state=str(state),pid=os.getpid())))
 status('READY',active_job=None);retain()
 while not stop[0]:
  for jobfile in sorted((state/'requests').glob('*.json')):
   response=state/'responses'/jobfile.name
   if response.exists():continue
   job=json.loads(jobfile.read_text());argv=list(job['argv']);script=Path(argv[0]).resolve();started=time.monotonic();status('RUNNING',active_job=jobfile.name,script=str(script))
   try:
    if not script.is_relative_to(ROOT/'scripts'):raise ValueError('Only repository CLI scripts are supported')
    if '--config'in argv:
     cfg=json.loads(Path(argv[argv.index('--config')+1]).read_text());requested=Path(cfg['model']['path']).resolve()
    else:requested=Path(argv[argv.index('--model')+1]).resolve()
    training_full=script.name=='fullft_train.py'
    is_current_fullft=fullft_path is not None and requested==fullft_path
    if not is_current_fullft:
     restore()
     if str(requested)!=current:replace(requested)
    status('RUNNING',active_job=jobfile.name,script=str(script))
    if training_full:
     base_snapshot={name:parameter.detach().cpu().clone()for name,parameter in model.named_parameters()}
     fullft_path=(Path(argv[argv.index('--output')+1])/'final_model').resolve()
    original_model=AutoModelForCausalLM.from_pretrained;original_tokenizer=AutoTokenizer.from_pretrained
    def borrowed_model(*args,**kwargs):return model
    def borrowed_tokenizer(*args,**kwargs):return tokenizer
    AutoModelForCausalLM.from_pretrained=borrowed_model;AutoTokenizer.from_pretrained=borrowed_tokenizer
    previous_argv=sys.argv;torch.set_num_threads(int(job.get('cpu_threads',request.get('cpu_threads',16))))
    log=state/(jobfile.stem+'.log')
    try:
     sys.argv=argv
     with log.open('a',buffering=1)as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):runpy.run_path(str(script),run_name='__main__')
    finally:
     sys.argv=previous_argv;AutoModelForCausalLM.from_pretrained=original_model;AutoTokenizer.from_pretrained=original_tokenizer
    result=dict(status='COMPLETE',seconds=time.monotonic()-started,log=str(log))
   except BaseException as exc:
    result=dict(status='FAILED',error=repr(exc),traceback=traceback.format_exc(),seconds=time.monotonic()-started)
    restore()
   atomic(response,result);gc.collect();retain();status('READY',active_job=None,last_job=jobfile.name,last_status=result['status'])
  time.sleep(.2)
 restore();status('STOPPED');raise SystemExit(0)

def submit_cli(state,command):
 """Submit and wait; the caller may run as a detached experiment controller."""
 import fcntl
 state=Path(state)
 # Reattach after a controller restart instead of submitting the same active
 # training request twice. The CUDA executor and its optimizer stay untouched.
 with (state/'submit.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  pending=[p for p in sorted((state/'requests').glob('*.json'))
           if not(state/'responses'/p.name).exists()
           and json.loads(p.read_text()).get('argv')==command[1:]]
  if pending:name=pending[0].name
  else:
   counter=max([int(p.name.split('_',1)[0])for p in(state/'requests').glob('*.json')]+[0])+1
   name=f'{counter:05d}_{Path(command[1]).stem}.json'
   atomic(state/'requests'/name,dict(argv=command[1:]))
  response=state/'responses'/name
 while not response.exists():
  record=json.loads((state/'status.json').read_text())
  if not (Path('/proc')/str(record['pid'])).exists():raise RuntimeError('Resident executor exited')
  time.sleep(2)
 result=json.loads(response.read_text())
 if result['status']!='COMPLETE':raise RuntimeError(json.dumps(result,indent=2))
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--family',required=True);p.add_argument('--state',required=True);p.add_argument('--capacity-gib',type=float,default=18.4);a=p.parse_args();sys.path.insert(0,str(ROOT))
 import torch
 capacity=int(a.capacity_gib*(1<<30))
 free,_=torch.cuda.mem_get_info()
 capacity=min(capacity,max(0,free-(1<<30)))
 if capacity<(20<<30):raise MemoryError('Insufficient available memory for an additional 8B research worker')
 # Initialize cuBLAS before the allocator cache reserves the working floor.
 scratch=torch.ones((32,32),device='cuda',dtype=torch.bfloat16)
 product=scratch@scratch;torch.cuda.synchronize();del scratch,product
 # Reserve the declared working allocation before CPU model loading.
 reservation=torch.empty(capacity,device='cuda',dtype=torch.uint8);del reservation
 from coretrace.models.native import load_native
 model,tok=load_native(a.model,family=a.family,device='cuda');run_preloaded(model,tok,dict(state=a.state,model_path=a.model,capacity_bytes=capacity,cpu_threads=int(os.environ.get('OMP_NUM_THREADS','8'))))
if __name__=='__main__':main()
