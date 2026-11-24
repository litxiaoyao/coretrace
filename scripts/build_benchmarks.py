"""Build the complete official external benchmarks from original public parquet files."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coretrace.eval.gsm8k import canonical_numeric, extract_official_compatible

QA_INSTRUCTION = 'Use only the evidence below. Each title, when present, identifies its paragraph. Return only the answer using the original entity spelling, without explanation.'
MC_INSTRUCTION = 'Answer the following multiple-choice question. Reply with only the letter A, B, C, or D. Do not give an explanation.'
MATH_INSTRUCTION = 'Solve the math word problem. Show your reasoning step by step. End your response with a separate final line in the format #### NUMBER, where NUMBER is the numerical answer. Do not add text after that final line.'
SOURCES = {
 'hotpot': ('hotpotqa/hotpot_qa', 'distractor/validation-00000-of-00001.parquet', 'main'),
 'mmlu': ('cais/mmlu', 'all/test-00000-of-00001.parquet', 'c30699e8356da336a370243923dbaf21066bb9fe'),
 'gsm8k': ('openai/gsm8k', 'main/test-00000-of-00001.parquet', '740312add88f781978c0658806c59bc2815b9866'),
}

def read_parquet(path):
 import pyarrow.parquet as pq
 return pq.read_table(path, use_threads=False).to_pylist()

def build(hotpot, mmlu, gsm8k):
 hotrows = []
 for r in read_parquet(hotpot):
  ctx = r['context']
  if isinstance(ctx, str):ctx = json.loads(ctx)
  context = list(zip(ctx['title'],ctx['sentences'])) if isinstance(ctx,dict) else ctx
  evidence = '\n\n'.join('Title: '+title+'\n'+'\n'.join(sentences) for title,sentences in context)
  prompt = QA_INSTRUCTION+'\n\nEvidence:\n'+evidence+'\n\nFinal question: '+r['question']
  hotrows.append(dict(id='hotpot_validation_'+r['id'],source_id=r['id'],gold=r['answer'],prompt=prompt,question=r['question']))
 mmrows=[]
 for i,r in enumerate(read_parquet(mmlu)):
  source_id=f'mmlu_test_{i:05d}'
  prompt = MC_INSTRUCTION+'\n\nQuestion:\n'+r['question']+'\n\n'+'\n'.join(f'{label}. {choice}' for label,choice in zip('ABCD',r['choices']))+'\n\nAnswer:'
  mmrows.append(dict(source_id=source_id,official_test_row_index=i,subject=r['subject'],question=r['question'],choices=r['choices'],answer_index=r['answer'],gold='ABCD'[r['answer']],id=source_id,prompt=prompt))
 mathrows=[]
 for i,r in enumerate(read_parquet(gsm8k)):
  value=extract_official_compatible(r['answer']);numeric=canonical_numeric(value)
  if numeric is None:raise ValueError('Original GSM8K answer is not numeric')
  mathrows.append(dict(row_index=i,row_id=f'openai/gsm8k:main:test:{i:04d}',gold_numeric=numeric,question=r['question'],gold_official_extracted=value,prompt=MATH_INSTRUCTION+'\n\nQuestion: '+r['question']))
 if [len(hotrows),len(mmrows),len(mathrows)] != [7405,14042,1319]:raise ValueError('Complete official evaluation splits required')
 return dict(hotpot=hotrows,mmlu=mmrows,gsm8k=mathrows)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in SOURCES:p.add_argument('--'+name,help='Original local parquet; omit with --download')
 p.add_argument('--download',action='store_true');p.add_argument('--output',required=True);a=p.parse_args();paths={}
 for name,(repository,filename,revision) in SOURCES.items():
  value=getattr(a,name)
  if value:paths[name]=value
  elif a.download:
   from huggingface_hub import hf_hub_download
   paths[name]=hf_hub_download(repo_id=repository,repo_type='dataset',filename=filename,revision=revision)
  else:p.error(f'--{name} or --download is required')
 results=build(**paths);out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
 for name,rows in results.items():(out/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows))
 print(json.dumps({name:len(rows)for name,rows in results.items()},indent=2))
if __name__=='__main__':main()
