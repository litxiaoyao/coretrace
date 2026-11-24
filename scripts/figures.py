"""Generate all paper figures from formal experiment outputs."""
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def read(path):return json.loads(path.read_text())

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--outputs',default=str(ROOT/'outputs'));p.add_argument('--destination');args=p.parse_args();base=Path(args.outputs).resolve();out=Path(args.destination).resolve()if args.destination else base/'figures';out.mkdir(parents=True,exist_ok=True)
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 import numpy as np
 from coretrace.eval.ledgers import read_complete
 plt.rcParams.update({'font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
 def save(fig,name):
  fig.tight_layout();fig.savefig(out/(name+'.pdf'),bbox_inches='tight');fig.savefig(out/(name+'.png'),dpi=200,bbox_inches='tight');plt.close(fig)
 def bars(values,title,name,ylabel='Accuracy'):
  fig,ax=plt.subplots(figsize=(max(5,len(values)*1.1),3.6));ax.bar(list(values),list(values.values()));ax.set(ylabel=ylabel,title=title);ax.tick_params(axis='x',rotation=30);save(fig,name)
 def necessity(report,model):
  by={(r['method'],r['query']):r['accuracy']for r in report['summary']}
  queries=['composed','direct_first','direct_target']
  fig,axes=plt.subplots(1,3,figsize=(10,3.3),sharey=True)
  for ax,query in zip(axes,queries):
   baseline=by['native',query]
   for method,label,color in [('selected','Localized heads','#245a81'),('random','Layer-matched random heads','#a36a32')]:
    ax.plot([0,20,40,80],[0]+[100*(by[f'{method}_{n}',query]-baseline)for n in [20,40,80]],marker='o',label=label,color=color)
   ax.axhline(0,color='gray',linewidth=.6);ax.set(title=query.replace('_',' '),xlabel='Heads removed at question prefill')
  axes[0].set_ylabel('Accuracy change (percentage points)');axes[-1].legend(fontsize=7)
  save(fig,model+'_causal_necessity')
 def factorization(report,model,source):
  by={r['method']:r for r in report['summary']if r['query']=='composed'}
  fig,ax=plt.subplots(figsize=(5.2,3.8))
  for methods,label,color in [(['native','mass_only'],'Receiver conditional','#355e86'),(['conditional_only','both'],'Direct-target conditional','#268c84')]:
   ax.plot([0,1],[100*by[m]['accuracy']for m in methods],marker='o',linewidth=2,color=color,label=label)
  ax.scatter([0],[100*by['identity']['accuracy']],s=100,facecolors='none',edgecolors='gray',label='Identity control',zorder=4)
  ax.set(xticks=[0,1],xticklabels=['Native paragraph mass','Fixed paragraph mass'],ylabel='Composed accuracy (%)',title=model+' access × local reading')
  ax.set_xlim(-.12,1.12);ax.legend(fontsize=8)
  if 'factorial_accuracy'in report:
   item=report['factorial_accuracy']['contrasts']['interaction'];lo,hi=item['paired_cluster_CI95']
   ax.text(.02,.98,f"Interaction: {100*item['estimate']:+.1f} pp\n95% cluster CI [{100*lo:+.1f}, {100*hi:+.1f}]",transform=ax.transAxes,va='top',fontsize=8)
  save(fig,model+'_causal_factorization')
  with(out/(model+'_causal_factorization_data.csv')).open('w',newline='')as stream:
   writer=csv.DictWriter(stream,fieldnames=['model','method','n','accuracy','source_summary']);writer.writeheader()
   writer.writerows(dict(model=model,method=method,n=row['n'],accuracy=row['accuracy'],source_summary=str(source))for method,row in by.items())
 models=sorted(p.name for p in base.iterdir()if p.is_dir()and(p/'discovery/manifest.json').exists())
 if not models:raise ValueError('No completed formal model outputs; run experiments first')
 phenomena={};example_records=[]
 corpus={r['source_id']:r for r in map(json.loads,(ROOT/'data/CoRe-2Wiki-v1.0/corpus.jsonl').open())}
 for model in models:
  root=base/model
  for sub in ['causal_access','causal_factorization','causal_necessity']:
   path=root/sub/'summary.json'
   if path.exists():
    report=read(path)
    if sub=='causal_necessity':necessity(report,model)
    elif sub=='causal_factorization':factorization(report,model,path)
    else:
     values={r['method']:r['accuracy']for r in report['summary']if r['query']=='composed'};bars(values,model+' '+sub,model+'_'+sub)
  path=root/'discovery/ranking.json'
  if path.exists():
   ranking=read(path)['ranking'];layers=max(r['layer']for r in ranking)+1;heads=max(r['head']for r in ranking)+1;matrix=np.full((layers,heads),np.nan)
   for r in ranking:matrix[r['layer'],r['head']]=r['score']
   fig,ax=plt.subplots(figsize=(8,6));im=ax.imshow(matrix,aspect='auto',cmap='coolwarm');ax.set(xlabel='Attention head',ylabel='Layer',title=model+' direct-target minus composed access');fig.colorbar(im,ax=ax,label='Paragraph attention mass difference');save(fig,model+'_head_localization')
  native_reader=root/'native_readout/complete.json'
  if native_reader.exists():
   d=read(native_reader)['diagnostics'];bars({k:v['test']['correct']/v['test']['n']for k,v in d.items()},model+' native bridge-address readout',model+'_address_readout')
  content={};application={}
  for seed in [42,43,44]:
   run=root/f'seed{seed}';core=run/'evaluation/core'
   if (core/'summary.json').exists():
    summary=read(core/'summary.json')
    for r in summary['summary']:
     if r['query']=='composed':application.setdefault(r['method'],[]).append(r['accuracy'])
    if seed==42:
     row=next(r for r in summary['conditional_composition']if r['method']=='native');phenomena[model]=row['conditional_failure_rate']
     manifest,rows=read_complete(core);by={(r['method'],r['query'],r['source_id']):r for r in rows};sources=sorted({r['source_id']for r in rows})
     candidates=[sid for sid in sources if by['native','direct_first',sid]['correct']and by['native','direct_target',sid]['correct']and not by['native','composed',sid]['correct']and by['final','composed',sid]['correct']]
     if candidates:
      sid=candidates[0];example_records.append(dict(model=model,source_id=sid,source=corpus[sid],selection='First source ID with native constituent success, composition failure and final repair success',predictions=[r for r in rows if r['source_id']==sid]))
   cp=run/'causal_content/summary.json'
   if cp.exists():
    for r in read(cp)['summary']:
     if r['pool']=='actual_swaps':content.setdefault(r['variant'],[]).append(r['edited_new_follow']/r['n'])
  if application and all(len(v)==(1 if k=='native'else 3)for k,v in application.items()):
   labels=list(application);fig,ax=plt.subplots(figsize=(9,3.6));ax.bar(labels,[np.mean(application[k])for k in labels],yerr=[np.std(application[k],ddof=1)if len(application[k])>1 else 0 for k in labels],capsize=3);ax.set(ylabel='Composed accuracy',title=model+' composition and components');ax.tick_params(axis='x',rotation=35);save(fig,model+'_application_ablations')
  if content:
   fig,ax=plt.subplots(figsize=(6,3.6));labels=list(content);means=[np.mean(content[k])for k in labels];errors=[np.std(content[k],ddof=1)if len(content[k])>1 else 0 for k in labels];ax.bar(labels,means,yerr=errors,capsize=3);ax.set(ylabel='Edited-value following rate',title=model+' reciprocal fact exchange');save(fig,model+'_content_reading')
 if phenomena:bars(phenomena,'Composition failure despite both correct constituent hops','phenomenon',ylabel='Failure rate | both constituent answers correct')
 table=base/'tables/tables.json'
 if table.exists():
  rows=read(table)['rows']
  for benchmark in ['core','hotpot','mmlu','gsm8k']:
   fig,axes=plt.subplots(1,len(models),figsize=(6*len(models),3.7),squeeze=False)
   for ax,model in zip(axes[0],models):
    rs=[r for r in rows if r['model']==model and r['benchmark']==benchmark and(benchmark!='core'or r['query']=='composed')];ax.bar([r['method']for r in rs],[r['mean_accuracy']for r in rs],yerr=[r['sample_std_accuracy']or 0 for r in rs],capsize=2);ax.set(title=model,ylabel='Accuracy');ax.tick_params(axis='x',rotation=60)
   save(fig,'comparison_'+benchmark)
 if example_records:(out/'worked_examples.json').write_text(json.dumps(example_records,ensure_ascii=False,indent=2)+'\n')
 print('Figures written to',out)
if __name__=='__main__':main()
