"""Plan or sequentially run the fixed paper experiment suite.

Nothing executes without --run. Model paths are supplied separately from the
scientific configuration. Complete stages are reused on subsequent invocations.
"""
import argparse,json,os,shlex,subprocess,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAGES=['discover','train','readout','evaluate','causal','fullft','report']

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--config',default=str(ROOT/'configs/experiments.json'))
 p.add_argument('--models',default=str(ROOT/'configs/models.local.json'))
 p.add_argument('--model',nargs='+',help='Subset of configured model names')
 p.add_argument('--stage',choices=['all']+STAGES,default='all')
 p.add_argument('--output',default=str(ROOT/'outputs'))
 p.add_argument('--resident',help='Optional resident executor state directory')
 p.add_argument('--eval-seeds',nargs='+',type=int,choices=[42,43,44],help='Dispatch only these fixed seeds for the evaluate stage; scientific configuration is unchanged')
 p.add_argument('--run',action='store_true');p.add_argument('--keep-fullft',action='store_true',help='Keep one final FullFT checkpoint per seed; requires substantial disk space')
 a=p.parse_args();cfg=json.loads(Path(a.config).read_text());models=json.loads(Path(a.models).read_text());output=Path(a.output).resolve();stages=STAGES if a.stage=='all'else[a.stage];names=a.model or list(cfg['models']);dataset=(ROOT/cfg['dataset']).resolve();groups=[];plan=[]
 if a.eval_seeds is not None and a.stage!='evaluate':p.error('--eval-seeds is only valid for --stage evaluate')
 if cfg['seeds']!=[42,43,44]:raise ValueError('Use the fixed seeds42/43/44')
 def complete(path):
  if not path.exists():return False
  return json.loads(path.read_text()).get('status','').startswith('COMPLETE')
 def call(stage,name,script,arguments,done,config=None):
  if stage not in stages:return
  command=[sys.executable,str(ROOT/'scripts'/script)]+list(map(str,arguments))
  if config is not None:
   cp=output/'configs'/(name+'.json');command+=['--config',str(cp)]
  else:cp=None
  command+=['--run'];plan.append(dict(stage=stage,name=name,complete=complete(done),command=shlex.join(command)))
  if not a.run or complete(done):return
  if cp:
   if script=='evaluate.py'and done.exists():
    prior=json.loads(done.read_text())
    if prior.get('status')=='RUNNING':config=prior['provenance']['config']
   cp.parent.mkdir(parents=True,exist_ok=True);cp.write_text(json.dumps(config,indent=2)+'\n')
  print(shlex.join(command),flush=True)
  if a.resident:
   from resident_worker import submit_cli
   submit_cli(a.resident,command)
  else:
   subprocess.run(command,cwd=ROOT,check=True,env={**os.environ,'TOKENIZERS_PARALLELISM':'false','OMP_NUM_THREADS':os.environ.get('OMP_NUM_THREADS','16'),'MKL_NUM_THREADS':os.environ.get('MKL_NUM_THREADS','16'),'OPENBLAS_NUM_THREADS':'1'})
 def eval_job(name,family,modelpath,seed,benchmark,methods,destination):
  data=dict(kind='core',path=str(dataset),split='test')if benchmark=='core'else dict(kind=benchmark,path=str(ROOT/'data/benchmarks'/(benchmark+'.jsonl')))
  ec=dict(model=dict(path=str(modelpath),family=family),seed=seed,dataset_version=cfg['dataset_version'],dataset=data,methods=methods,output=str(destination))
  ec['batch_size']=cfg.get('mmlu_batch_size',1)if benchmark=='mmlu'else cfg.get('qa_batch_size',1)if benchmark in ['core','hotpot']else cfg.get('gsm8k_batch_size',1)
  return ec
 def add_groups(model,benchmark,methods,paths):
  for method in methods:
   group=dict(model=model,benchmark=benchmark,method=method,directories=[str(path)for path in paths])
   if method=='native':group.update(deterministic_reference=True,directories=[str(paths[0])])
   groups.append(group)
 for name in names:
  if name not in cfg['models']or name not in models:raise ValueError('Model missing from configuration: '+name)
  settings=cfg['models'][name];family=settings['family'];modelpath=Path(models[name]).expanduser();modelpath=modelpath if modelpath.is_absolute()else ROOT/modelpath
  base=output/name;discovery=base/'discovery';heads=discovery/'SELECTION_FROZEN.json';native_reader=base/'native_readout';scope=settings['scope']
  call('discover',name+'_discovery','discover.py',[],discovery/'manifest.json',dict(model=dict(path=str(modelpath),family=family),dataset=str(dataset),candidate_counts=cfg['candidate_counts'],seed=42,output=str(discovery)))
  # Native-state removal control uses its own train-only readout.
  call('readout',name+'_native_readout','readout.py',['--dataset',dataset,'--model',modelpath,'--family',family,'--heads',heads,'--seed',42,'--output',native_reader],native_reader/'complete.json')
  evaluations={b:[]for b in cfg['benchmarks']};full_evaluations={b:[]for b in cfg['benchmarks']}
  for seed in cfg['seeds']:
   if a.eval_seeds is not None and seed not in a.eval_seeds:continue
   run=base/f'seed{seed}';checkpoint=run/'head_tuning';reader=run/'readout';scopefile=output/'configs'/(name+'_scope.json')
   if a.run and set(stages)&{'readout','evaluate','causal'}:
    scopefile.parent.mkdir(parents=True,exist_ok=True);scopefile.write_text(json.dumps(scope,indent=2)+'\n')
   call('train',f'{name}_{seed}_training','train.py',['--dataset',dataset,'--model',modelpath,'--family',family,'--heads',heads,'--seed',seed,'--output',checkpoint],checkpoint/'training.json')
   call('readout',f'{name}_{seed}_readout','readout.py',['--dataset',dataset,'--model',modelpath,'--family',family,'--heads',heads,'--checkpoint',checkpoint,'--scope',scopefile,'--seed',seed,'--output',reader],reader/'complete.json')
   # Resolve actual discovery heads only at execution; the plan stays model-free.
   headmap=json.loads(heads.read_text())['head_map']if heads.exists()else{}
   boundary='leading_newline' if family=='qwen3' else 'line_start'
   methods=[dict(name='native'),dict(name='native_text',selector='decoded_text',paragraph_boundary=boundary,head_map=headmap,readout=str(native_reader/'address_readout.json')),dict(name='head_tuning',artifact=str(checkpoint)),dict(name='scoped_body',artifact=str(checkpoint),scope=scope),dict(name='graphfirst',artifact=str(checkpoint),scope=scope,selector='graphfirst_text',paragraph_boundary=boundary),dict(name='final',artifact=str(checkpoint),scope=scope,selector='decoded_text',paragraph_boundary=boundary,readout=str(reader/'address_readout.json')),dict(name='final_attention',artifact=str(checkpoint),scope=scope,selector='decoded_text',paragraph_boundary=boundary,readout=str(reader/'attention_readout.json')),dict(name='final_metadata',artifact=str(checkpoint),scope=scope,selector='decoded_text',paragraph_boundary=boundary,readout=str(reader/'metadata_readout.json'))]
   for benchmark in cfg['benchmarks']:
    dest=run/'evaluation'/benchmark;evaluations[benchmark].append(dest)
    active_methods=methods if benchmark=='core' else [m for m in methods if m['name'] in ['native','head_tuning','final']]
    if seed!=cfg['seeds'][0]:active_methods=[m for m in active_methods if m['name']!='native']
    ec=eval_job(name,family,modelpath,seed,benchmark,active_methods,dest)
    call('evaluate',f'{name}_{seed}_{benchmark}','evaluate.py',[],dest/'manifest.json',ec)
   content=run/'causal_content'
   call('causal',f'{name}_{seed}_content','content_causal.py',[],content/'manifest.json',dict(dataset=str(dataset),model=dict(path=str(modelpath),family=family),seed=seed,variants=['native','native_budget','body','final'],heads=str(heads),budget=str(heads),checkpoint=str(checkpoint),scope=str(scopefile),readout=str(reader/'address_readout.json'),output=str(content)))
   ft=run/'fullft';ftmodel=ft/'final_model'
   ft_already_evaluated=all(complete((run/'evaluation_fullft'/b/'manifest.json'))for b in cfg['benchmarks'])
   if not ft_already_evaluated:
    if a.run and 'fullft'in stages and complete(ft/'training.json')and not ftmodel.exists():raise FileNotFoundError('FullFT checkpoint was removed before all evaluations completed')
    call('fullft',f'{name}_{seed}_fullft','fullft_train.py',['--dataset',dataset,'--model',modelpath,'--family',family,'--seed',seed,'--cpu-memory-budget-gib',216,'--output',ft],ft/'training.json')
   for benchmark in cfg['benchmarks']:
    dest=run/'evaluation_fullft'/benchmark;full_evaluations[benchmark].append(dest);ec=eval_job(name,family,ftmodel,seed,benchmark,[dict(name='FullFT')],dest)
    call('fullft',f'{name}_{seed}_fullft_{benchmark}','evaluate.py',[],dest/'manifest.json',ec)
   if a.run and 'fullft'in stages and not a.keep_fullft and all(complete((run/'evaluation_fullft'/b/'manifest.json'))for b in cfg['benchmarks'])and ftmodel.is_dir():shutil.rmtree(ftmodel)
  for benchmark,paths in evaluations.items():add_groups(name,benchmark,[m['name']for m in methods if benchmark=='core' or m['name'] in ['native','head_tuning','final']],paths)
  for benchmark,paths in full_evaluations.items():add_groups(name,benchmark,['FullFT'],paths)
  for script,sub in [('causal.py','causal_access'),('factorized_causal.py','causal_factorization')]:
   dest=base/sub;call('causal',name+'_'+sub,script,[],dest/'manifest.json',dict(dataset=str(dataset),model=dict(path=str(modelpath),family=family),seed=42,budget=str(heads),output=str(dest)))
  dest=base/'causal_necessity';call('causal',name+'_causal_necessity','necessity.py',[],dest/'manifest.json',dict(dataset=str(dataset),model=dict(path=str(modelpath),family=family),ranking=str(discovery/'ranking.json'),output=str(dest)))
 if a.run and 'report'in stages:
  spec=dict(seeds=cfg['seeds'],dataset_version=cfg['dataset_version'],groups=groups);cp=output/'table_inputs.json';cp.parent.mkdir(parents=True,exist_ok=True);cp.write_text(json.dumps(spec,indent=2)+'\n')
  subprocess.run([sys.executable,str(ROOT/'scripts/aggregate.py'),'--manifest',str(cp),'--output',str(output/'tables')],cwd=ROOT,check=True)
  subprocess.run([sys.executable,str(ROOT/'scripts/figures.py'),'--outputs',str(output)],cwd=ROOT,check=True)
 if not a.run:print(json.dumps(dict(status='PLAN_ONLY',models=names,seeds=cfg['seeds'],stages=stages,tasks=plan,report_groups=len(groups),model_weights_loaded=False),indent=2))
if __name__=='__main__':main()
