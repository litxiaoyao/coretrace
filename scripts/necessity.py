"""Head-output necessity dose curves with layer-matched random controls."""
import argparse,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from coretrace.mechanisms.paragraph_attention import _Session

class QuestionHeadKnockout(_Session):
 def apply(self,layer,module,q,k,v,mask,scale,output):
  import torch
  changed=output[0].clone();rows=torch.tensor(self.rows,device=changed.device);heads=torch.tensor(self.maps[layer],device=changed.device)
  changed[0,rows[:,None],heads[None,:]]=0
  return changed,None

def run_loaded(model,tokenizer,entries,ranking,output,provenance,*,family,eos_token_ids):
 from coretrace.data.tokenization import tokenize_prompt
 from coretrace.eval.ledgers import EvaluationLedger
 from coretrace.eval.inference import greedy_answer
 from coretrace.eval.answer_metrics import score_answer
 from coretrace.eval.summarize import summarize
 arms={'native':None};controls={}
 for n in [20,40,80]:
  selected={}
  for head in ranking[:n]:selected.setdefault(head['layer'],[]).append(head['head'])
  rng=random.Random(42+n);random_map={layer:sorted(rng.sample(range(model.config.num_attention_heads),len(heads)))for layer,heads in selected.items()}
  arms[f'selected_{n}']=selected;arms[f'random_{n}']=random_map
  controls[str(n)]=dict(selected=selected,random_layer_matched=random_map,overlap_heads=sum(len(set(heads)&set(random_map[layer]))for layer,heads in selected.items()),random_seed=42+n)
 ledger=EvaluationLedger(output,provenance=provenance,entry_ids=[e['id']for e in entries],methods=list(arms))
 pad=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
 model.eval().requires_grad_(False)
 for raw in entries:
  entry=dict(raw,**tokenize_prompt(tokenizer,raw['prompt'],family=family))
  for method,heads in arms.items():
   if method+':'+entry['id']in ledger.rows:continue
   session=QuestionHeadKnockout(model,entry,heads)if heads else None
   result=greedy_answer(model,tokenizer,entry,eos_token_ids=eos_token_ids,pad_token_id=pad,session=session)
   score=score_answer(result['answer'],entry['gold_aliases']);ledger.append(dict(result,id=entry['id'],source_id=entry['source_id'],query=entry['query'],cluster_id=entry['cluster_id'],method=method,correct=bool(result['eos_complete']and score['em']),text_f1=score['f1']))
 ledger.finish();summary=summarize(output,seed=42);summary.update(controls=controls,intervention='Zero selected attention-head output only at question prefill rows before O; cached decode untouched. Layer counts matched in random controls; their random overlap is disclosed.',interpretation='Question-prefill contribution necessity and dose response; not proof of an exclusive complete circuit.')
 (Path(output)/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 return summary

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--run',action='store_true');p.add_argument('--plan',action='store_true');a=p.parse_args();cp=Path(a.config).resolve();cfg=json.loads(cp.read_text())
 def path(s):
  x=Path(s);return x if x.is_absolute()else cp.parent/x
 from coretrace.data.frozen_loader import FrozenDataset
 data=FrozenDataset(path(cfg['dataset']));entries=data.queries('test');aliases={e['source_id']:e for e in data.aliases('test')};sources={e['source_id']:e for e in data.sources('test')}
 for entry in entries:entry.update(gold_aliases=aliases[entry['source_id']]['queries'][entry['canonical_query']]['golds'],cluster_id=sources[entry['source_id']]['cluster_id'])
 if not a.run:print(json.dumps(dict(status='PLAN_ONLY',sources=1000,queries=len(entries),arms=7,expected_generations=7*len(entries),model_weights_loaded=False),indent=2));return
 from coretrace.models.native import load_native
 model,tok=load_native(path(cfg['model']['path']),family=cfg['model']['family'],device=cfg['model'].get('device','cuda'));eos=model.generation_config.eos_token_id or tok.eos_token_id;eos=[eos]if isinstance(eos,int)else eos
 result=run_loaded(model,tok,entries,json.loads(path(cfg['ranking']).read_text())['ranking'],path(cfg['output']),dict(model_identity=cfg['model'],seed=42,dataset_version=data.version),family=cfg['model']['family'],eos_token_ids=eos);print(json.dumps(dict(status=result['status']),indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'manifest.json')
