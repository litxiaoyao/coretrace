"""Load the fixed CoRe-2Wiki dataset and validate its source-level splits."""
from copy import deepcopy
import json
from pathlib import Path

QUERY_TYPES = ('composed', 'direct_first', 'direct_target')

def _json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def _jsonl(path):
    with path.open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]

class FrozenDataset:
    """Fixed text, aliases and source splits; returned records are copies."""
    def __init__(self, root, *, verify=True):
        self.root = Path(root).expanduser().resolve()
        self.metadata = _json(self.root / 'dataset.json')
        self.name = self.metadata['name']
        self.version = self.metadata.get('id', 'CoRe-2Wiki-v1.0')
        self.dataset_id = self.metadata.get('id', 'CoRe-2Wiki-v1.0')
        # Compatibility aliases for the original experiment entry points.
        self.lock = {'dataset_version': self.dataset_id}
        self.splits = {name: _json(self.root / 'splits' / (name + '.json'))
                       for name in ('discovery', 'train', 'test')}
        self._corpus = _jsonl(self.root / 'corpus.jsonl')
        self._queries = _jsonl(self.root / 'queries.jsonl')
        self._aliases = _jsonl(self.root / 'aliases.jsonl')
        if verify:
            self.verify()

    def verify(self):
        """Reject missing, duplicate or inconsistent IDs, splits and answer joins."""
        def need(condition, message):
            if not condition:
                raise ValueError(message)
        corpus = {r['source_id']: r for r in self._corpus}
        aliases = {r['source_id']: r for r in self._aliases}
        queries = {r['id']: r for r in self._queries}
        need(len(corpus) == len(self._corpus), 'Duplicate corpus source IDs')
        need(len(queries) == len(self._queries), 'Duplicate query IDs')
        need(len(aliases) == len(self._aliases) and set(aliases) == set(corpus),
             'Alias source IDs do not match corpus')
        used = set()
        used_queries = set()
        counts = {}
        for name, split in self.splits.items():
            ids = split['source_ids']; qids = split['canonical_query_ids']
            need(split['global_split'] == name, 'Split name mismatch')
            definition = self.metadata['splits'][name]
            expected_count = (definition.get('sources', definition.get('n_sources'))
                              if isinstance(definition, dict) else definition)
            need(len(ids) == len(set(ids)) == expected_count == split['n_sources'],
                 'Split source count mismatch: ' + name)
            need(set(ids) <= set(corpus), 'Unknown source IDs in split: ' + name)
            need(not used.intersection(ids), 'Overlapping split source IDs')
            used.update(ids)
            expected = [sid + '__core2wiki_v1__' + query for sid in ids for query in QUERY_TYPES]
            need(qids == expected, 'Split query order/membership mismatch')
            need(set(qids) <= set(queries), 'Unknown query IDs in split: ' + name)
            used_queries.update(qids)
            for sid in ids:
                need(corpus[sid]['global_split'] == aliases[sid]['global_split'] == name,
                     'Corpus/alias split mismatch')
            for qid in qids:
                q = queries[qid]
                need(q['global_split'] == name and q['source_id'] in ids, 'Query source/split mismatch')
                need(q['canonical_query'] == q['query'].removeprefix('direct_'), 'Query type mismatch')
                need(q['gold'] == aliases[q['source_id']]['queries'][q['canonical_query']]['gold'],
                     'Query/alias gold mismatch')
            counts[name] = dict(sources=len(ids), queries=len(qids))
        need(used == set(corpus), 'Sources absent from split registry')
        need(used_queries == set(queries), 'Queries absent from split registry')
        return dict(status='VALID_DATASET', dataset=self.dataset_id,
                    source_count=len(corpus), query_count=len(queries), splits=counts)

    def split(self, name):
        return deepcopy(self.splits[name])

    def sources(self, split):
        by = {r['source_id']: r for r in self._corpus}
        return [deepcopy(by[sid]) for sid in self.splits[split]['source_ids']]

    def queries(self, split, query=None):
        """Aliases first/target select direct_first/direct_target, respectively."""
        query = {'first': 'direct_first', 'target': 'direct_target'}.get(query, query)
        if query is not None and query not in QUERY_TYPES:
            raise ValueError('Unknown query type: ' + str(query))
        by = {r['id']: r for r in self._queries}
        return [deepcopy(by[qid]) for qid in self.splits[split]['canonical_query_ids']
                if query is None or by[qid]['query'] == query]

    def aliases(self, split):
        by = {r['source_id']: r for r in self._aliases}
        return [deepcopy(by[sid]) for sid in self.splits[split]['source_ids']]
