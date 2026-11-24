"""Human-readable links from paper table cells to predictions and training logs."""
import csv,json
from pathlib import Path
from .ledgers import read_complete

def write_csv(path,rows):
    if not rows:return
    with Path(path).open('w',newline='')as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def export_sources(result,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    cells=[]
    for row in result['rows']:
        source_rows=[s for s in result['sources']if all(s[k]==row[k]for k in ['model','benchmark','method'])]
        for source in source_rows:
            directory=Path(source['directory'])
            cells.append(dict(model=row['model'],benchmark=row['benchmark'],method=row['method'],query=row['query'],metric=row['metric'],seed=source['seed'],n=row['n'],predictions=str(directory/'predictions.jsonl'),configuration=str(directory/'manifest.json'),filter=dict(method=row['method'],query=['composed','direct_first','direct_target']if row['query']=='all3'else row['query']),statistic='Join all three queries on source_id, logical AND of correct, sum/n'if row['query']=='all3'else f"Sum boolean {row['metric']} over matching rows / n"))
    (out/'sources.json').write_text(json.dumps(dict(table='tables.csv',dataset_version=result['dataset_version'],cells=cells,seed_aggregation='Mean and sample standard deviation across42/43/44; deterministic references measured once.'),indent=2)+'\n')
    inference=[];training=[];inference_sources=[];training_sources=[];seen=set();training_seen=set()
    for source in result['sources']:
        directory=Path(source['directory']);key=(str(directory),source['method'])
        if key not in seen:
            seen.add(key);manifest,rows=read_complete(directory);rs=[r for r in rows if r['method']==source['method']]
            inference.append(dict(model=source['model'],seed=source['seed'],benchmark=source['benchmark'],method=source['method'],questions=len(rs),generation_batch_sizes=','.join(map(str,sorted({r.get('batch_size',1)for r in rs}))),seconds=sum(r.get('total_inference_seconds',r['seconds'])for r in rs),input_tokens=sum(r['input_tokens']for r in rs),generated_tokens=sum(r['generated_tokens']for r in rs),address_prefills=sum(r.get('selection',{}).get('address_prefills',0)for r in rs)))
            inference_sources.append(dict(row=len(inference)-1,predictions=str(directory/'predictions.jsonl'),method=source['method'],formula='Select matching method; count rows and sum total_inference_seconds (generation seconds fallback), input_tokens, generated_tokens and selection.address_prefills.'))
        # The directory is model/seed/evaluation[_fullft]/benchmark.
        seedroot=directory.parent.parent
        for method,folder in [('head_tuning','head_tuning'),('FullFT','fullft')]:
            path=seedroot/folder/'training.json'
            if not path.exists()or str(path)in training_seen:continue
            training_seen.add(str(path));record=json.loads(path.read_text())
            training.append(dict(model=source['model'],seed=source['seed'],method=method,sources=record['actual_sources'],optimizer_steps=record['actual_steps'],trainable_parameters=record.get('parameter_count',record.get('all_parameter_elements')),seconds=record['seconds']))
            training_sources.append(dict(row=len(training)-1,training=str(path),fields=dict(sources='actual_sources',optimizer_steps='actual_steps',trainable_parameters='parameter_count for selected heads; all_parameter_elements for FullFT',seconds='seconds'),scope='LLM training wall time; final and component methods share the selected-head checkpoint.'))
    write_csv(out/'inference_costs.csv',inference);write_csv(out/'training_costs.csv',training)
    (out/'cost_sources.json').write_text(json.dumps(dict(inference_table='inference_costs.csv',inference_rows=inference_sources,training_table='training_costs.csv',training_rows=training_sources),indent=2)+'\n')
    from ..data.frozen_loader import FrozenDataset
    root=Path(__file__).resolve().parents[2];data=FrozenDataset(root/'data/CoRe-2Wiki-v1.0');statistics=[];data_sources=[]
    for split,role in [('discovery','Mechanism localization'),('train','Composed-question LLM training; constituent queries are diagnostic'),('test','Paired main-task evaluation')]:
        statistics.append(dict(dataset=data.version,split=split,sources=len(data.sources(split)),queries=len(data.queries(split)),LLM_gradient_queries=len(data.queries(split,'composed'))if split=='train'else 0,role=role))
        data_sources.append(dict(row=len(statistics)-1,files=[str(data.root/'dataset.json'),str(data.root/'splits'/f'{split}.json'),str(data.root/'queries.jsonl')],formula='Count source_ids in split and its canonical_query_ids. Only composed train queries update LLM weights.'))
    external=root/'data/benchmarks/datasets.json';definitions=json.loads(external.read_text())['datasets']
    for key,info in definitions.items():
        source=root/'data/benchmarks'/f'{key}.jsonl';n=sum(1 for line in source.open()if line.strip())
        statistics.append(dict(dataset=info['name'],split=info['split'],sources=n,queries=n,LLM_gradient_queries=0,role='General capability retention'))
        data_sources.append(dict(row=len(statistics)-1,files=[str(external),str(source)],formula='All rows in the complete official evaluation split.'))
    write_csv(out/'dataset_statistics.csv',statistics)
    (out/'data_sources.json').write_text(json.dumps(dict(table='dataset_statistics.csv',rows=data_sources),indent=2)+'\n')

