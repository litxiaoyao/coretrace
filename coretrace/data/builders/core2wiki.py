"""Reconstruct CoRe-2Wiki from official 2Wiki data_ids.zip, without a model.

The fixed selection records source IDs and document/support indices only. All
questions, contexts, graph triples and answer aliases come from the archive.
"""
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
import zipfile

INSTRUCTION = ('Use only the evidence below. Each title, when present, identifies its paragraph. '
               'Return only the answer using the original entity spelling, without explanation.')
TEMPLATE = 'core2wiki-v1-native-official-context-template1'
QUERY_TYPES = ('composed', 'direct_first', 'direct_target')
SELECTION = Path(__file__).with_name('selection.json')


def stream_array(binary):
    """Stream the original top-level JSON arrays instead of loading the archive."""
    stream = io.TextIOWrapper(binary, encoding='utf-8')
    buffer = ''; position = 0; decoder = json.JSONDecoder(); started = False; eof = False
    while True:
        while position >= len(buffer) and not eof:
            buffer = stream.read(1 << 20); position = 0; eof = not buffer
        if not started:
            while position < len(buffer) and buffer[position].isspace(): position += 1
            if position >= len(buffer) or buffer[position] != '[':
                raise ValueError('Expected a top-level JSON array')
            position += 1; started = True
        while position < len(buffer) and (buffer[position].isspace() or buffer[position] == ','):
            position += 1
        if position < len(buffer) and buffer[position] == ']': return
        try:
            value, end = decoder.raw_decode(buffer, position)
        except json.JSONDecodeError:
            more = stream.read(1 << 20)
            if not more: raise
            buffer = buffer[position:] + more; position = 0; continue
        yield value; position = end
        if position > 1 << 20:
            buffer = buffer[position:]; position = 0


def display(text):
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), str(text))
    return re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), text).replace('\\"', '"')


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', display(text)).casefold().split())


def title_key(text):
    return re.sub(r'\s*\([^)]*\)', '', norm(text)).strip()


def direct(relation, subject):
    templates = {'director': 'Who directed {}?', 'composer': 'Who composed {}?',
                 'father': 'Who is the father of {}?', 'mother': 'Who is the mother of {}?',
                 'spouse': 'Who is the spouse of {}?', 'place of birth': 'Where was {} born?',
                 'place of death': 'Where did {} die?'}
    return templates[relation].format(subject) if relation in templates else f'According to the evidence, for {subject}, what is the value of the relation "{relation}"?'


def edge(triple, row):
    subject, relation, obj = triple; context = dict(row['context']); found = []
    for title, index in row['supporting_facts']:
        if title not in context or not 0 <= index < len(context[title]) or title_key(title) != title_key(subject):
            continue
        text = context[title][index]
        if re.search(r'(?<!\w)' + re.escape(norm(obj)) + r'(?!\w)', norm(text)):
            found.append((len(text), title, index, text))
    if not found: return None
    _, title, index, text = min(found)
    return dict(subject=subject, relation=relation, object=obj, title=title, sent_id=index, text=text,
                support_basis='Official relation triple plus official supporting_facts, matching subject paragraph title, whole object mention in exact sentence. No hardcoded four-relation or profession/predicate heuristic.', source_id=row['_id'])


def chain(row):
    triples = row['evidences']
    if len(triples) != 2: return None
    paths = [(a, b) for a, b in [triples, triples[::-1]] if norm(a[2]) == norm(b[0])]
    if len(paths) != 1: return None
    a, b = paths[0]
    if norm(b[2]) != norm(row['answer']) or len({norm(a[0]), norm(a[2]), norm(b[2])}) != 3: return None
    e1, e2 = edge(a, row), edge(b, row)
    if not e1 or not e2 or (e1['title'], e1['sent_id']) == (e2['title'], e2['sent_id']): return None
    return a, b, e1, e2


def resolve_chain(row, mapping):
    strict = chain(row)
    if strict: return strict, dict(kind='strict_subject_title_and_support', flags=[])
    sid = row['_id']; selection = mapping[sid]; context = dict(row['context'])
    # These fixed support indices resolve original annotations whose subject
    # surface differs from its paragraph title; never invent or rewrite facts.
    supports = selection['supports']; triples = row['evidences']
    paths = [(a, b) for a, b in [triples, triples[::-1]] if norm(a[2]) == norm(b[0]) and norm(b[2]) == norm(row['answer'])]
    if len(paths) != 1: raise ValueError('Ambiguous annotated chain: ' + sid)
    a, b = paths[0]; edges = []; flags = []
    for i, triple in enumerate([a, b]):
        found = edge(triple, row)
        if found is None:
            title = supports[i]['title']; index = supports[i]['sentence_index']
            if [title, index] not in row['supporting_facts']:
                raise ValueError('Selected support is not official: ' + sid)
            found = dict(subject=triple[0], relation=triple[1], object=triple[2], title=title, sent_id=index,
                         text=context[title][index], source_id=sid,
                         support_basis='Exact frozen grid edge mapping, official triple, official supporting_facts title/index and original sentence verified; subject-title alias mismatch retained, no new trainingcandidate relaxation.')
            flags.append(dict(edge=i, subject=triple[0], support_title=title,
                              subject_entity_id=row['evidences_id'][row['evidences'].index(triple)][0],
                              issue='literal subjecttitle mismatch in strict helper; verified fixed original support provenance'))
        edges.append(found)
    return (a, b, *edges), dict(kind='fixed_official_grid_provenance_verified', flags=flags)


def clusters(samples):
    parent = {r['source_id']: r['source_id'] for r in samples}; owner = {}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        a, b = find(x), find(y)
        if a != b: parent[max(a,b)] = min(a,b)
    for row in samples:
        for entity in {title_key(row['root']), title_key(row['bridge'])}:
            if entity in owner: union(row['source_id'], owner[entity])
            else: owner[entity] = row['source_id']
    groups = defaultdict(list)
    for sid in parent: groups[find(sid)].append(sid)
    assignments = {}; sizes = {}
    for members in groups.values():
        # Stable opaque cluster identifiers, not file-integrity checks.
        cid = hashlib.sha256(('CoRe-2Wiki-v1-cluster:' + ','.join(sorted(members))).encode()).hexdigest()[:24]
        sizes[cid] = len(members)
        for sid in members: assignments[sid] = cid
    return assignments, sizes


def make_queries(row, resolved, split, parent):
    a, b, _, _ = resolved
    evidence = '\n\n'.join('Title: '+title+'\n'+'\n'.join(sentences) for title, sentences in row['context'])
    prefix = INSTRUCTION + '\n\nEvidence:\n' + evidence + '\n\nFinal question: '
    queries = []
    for query, question, gold in [('composed', row['question'], row['answer']),
                                  ('direct_first', direct(a[1],a[0]), a[2]),
                                  ('direct_target', direct(b[1],b[0]), row['answer'])]:
        queries.append(dict(id=row['_id']+'__core2wiki_v1__'+query, source_id=row['_id'], global_split=split,
                            official_parent_split=parent, query=query, canonical_query=query.removeprefix('direct_'),
                            question=question, question_origin='unchanged_official' if query=='composed' else 'explicit_diagnostic_direct_probe',
                            prompt=prefix+question, gold=gold, bridge=a[2], relation1=a[1], relation2=b[1], template_id=TEMPLATE))
    return queries


def make_quad(selection, official, parents, resolved, original_training):
    queries = []
    for cell in selection['queries']:
        sid = cell['source_id']; row = official[sid]; a,b,_,_ = resolved[sid]
        supports = [dict(title=p['title'], sentence_index=p['sentence_index'], text=dict(row['context'])[p['title']][p['sentence_index']]) for p in cell['supports']]
        queries.append(dict(cell=cell['cell'], id=cell['id'], source_id=sid, source_split=parents[sid], question=row['question'],
                            gold=row['answer'], bridge=a[2], anchor=a[0], first_relation=a[1], second_relation=b[1], support_sentences=supports))
    docs = {}
    for cell in selection['queries']:
        for title, sentences in official[cell['source_id']]['context']: docs[title] = sentences
    shared = [[title, docs[title]] for title in selection['shared_title_order']]
    support_only = [[title, docs[title]] for title in selection['support_titles']]
    by = {q['cell']:q for q in queries}
    return dict(quadruplet_id=selection['quadruplet_id'], first_relation=by['C11']['first_relation'],
                second_relations=[by['C11']['second_relation'], by['C12']['second_relation']],
                anchors=[by['C11']['anchor'], by['C21']['anchor']], bridges=[by['C11']['bridge'], by['C21']['bridge']],
                answers=[[by['C11']['gold'],by['C12']['gold']],[by['C21']['gold'],by['C22']['gold']]], queries=queries,
                support_only_context=support_only, support_titles=selection['support_titles'], distractor_titles=selection['distractor_titles'],
                shared_context=shared, shared_context_text='\n\n'.join('Title: '+title+'\n'+'\n'.join(sentences) for title,sentences in shared),
                four_distinct_answers=len({norm(q['gold']) for q in queries})==4, all_questions_original_official=True,
                training868_source_overlap=sum(q['source_id'] in original_training for q in queries),
                context_policy='Union of complete original supporting paragraphs from the four official rows, padded to exactly10 with original non-support paragraphs from those same rows; identical text for all four questions. Support-only and complete original contexts separately retained.',
                split=selection['split'], split_index=selection['split_index'])


def build(archive, output, *, selection=SELECTION):
    """Build a new directory. Existing directories are never overwritten."""
    output = Path(output)
    if output.exists(): raise FileExistsError('Choose a new output directory: '+str(output))
    selected = json.loads(Path(selection).read_text()); splits = selected['splits']
    wanted = {sid for ids in splits.values() for sid in ids}
    if len(wanted)!=3100 or {k:len(v) for k,v in splits.items()} != dict(discovery=100,train=2000,test=1000):
        raise ValueError('Invalid fixed source selection')
    mapping = {q['source_id']:q for quad in selected['discovery_quadruplets'] for q in quad['queries']}
    official = {}; parents = {}
    with zipfile.ZipFile(archive) as zipped:
        for parent in ['dev','train']:
            for row in stream_array(zipped.open('data_ids/'+parent+'.json')):
                sid=row['_id']
                if sid in wanted:
                    if sid in official: raise ValueError('Duplicate official source: '+sid)
                    official[sid]=row; parents[sid]=parent
            print(json.dumps(dict(stage='read_official', split=parent, selected_sources=len(official))),flush=True)
        if set(official)!=wanted: raise ValueError('Missing selected official sources')
        resolved = {}; corpus = []; aliases = []; needed = set(); original_training = set(selected['original_training_sources'])
        for split, ids in splits.items():
            for sid in ids:
                row=official[sid]; c,validation=resolve_chain(row,mapping);resolved[sid]=c;a,b,e1,e2=c
                roles=dict(composed=dict(gold=row['answer'],entity_id=row['answer_id']))
                for role,triple,gold in [('first',a,a[2]),('target',b,row['answer'])]:
                    indices=[i for i,t in enumerate(row['evidences']) if t==triple]
                    entity_ids={row['evidences_id'][i][2] for i in indices}
                    if len(entity_ids)!=1:raise ValueError('Ambiguous answer entity ID')
                    roles[role]=dict(gold=gold,entity_id=next(iter(entity_ids)),official_edge_object=triple[2],official_evidence_triple=triple,
                                     official_evidence_indices=indices,official_evidence_ids=[row['evidences_id'][i] for i in indices])
                root_id=row['evidences_id'][row['evidences'].index(a)][0]
                needed.update(v['entity_id'] for v in roles.values()); needed.add(root_id)
                aliases.append(dict(source_id=sid,global_split=split,official_parent_split=parents[sid],queries=roles))
                corpus.append(dict(source_id=sid,global_split=split,official_parent_split=parents[sid],original_question=row['question'],original_gold=row['answer'],
                                   original_context=row['context'],supporting_facts=row['supporting_facts'],official_evidence_triples=row['evidences'],
                                   official_evidence_ids=row['evidences_id'],official_answer_id=row['answer_id'],official_root_id=root_id,official_type=row.get('type'),
                                   root=a[0],bridge=a[2],relation1=a[1],relation2=b[1],edges=dict(first_target=e1,second_target=e2),
                                   query_ids={q:sid+'__core2wiki_v1__'+q for q in QUERY_TYPES},original868_training_source=sid in original_training,chain_validation=validation))
        amap={}
        for line in zipped.open('data_ids/id_aliases.json'):
            item=json.loads(line)
            if item['Q_id'] in needed:amap[item['Q_id']]=item
    for alias in aliases:
        for value in alias['queries'].values():
            entry=amap.get(value['entity_id'],{})
            value['golds']=sorted(set([value['gold']]+([value['official_edge_object']] if 'official_edge_object' in value else [])+entry.get('aliases',[])+entry.get('demonyms',[])))
            value['official_aliases_present']=value['entity_id'] in amap
    for row in corpus:
        for flag in row['chain_validation']['flags']:
            names=amap.get(flag['subject_entity_id'],{}).get('aliases',[])
            flag.update(official_subject_aliases=names,support_title_matches_official_subject_alias=any(norm(flag['support_title'])==norm(n) for n in names),
                        identity_resolution='Official evidence subject entityID joined to original id_aliases; title alias verified when present, otherwise retained explicit annotationflag, never dropped.')
    global_clusters,_=clusters(corpus); split_clusters={split:clusters([r for r in corpus if r['global_split']==split])[0] for split in splits}
    queries=[]
    for row in corpus:
        sid=row['source_id'];row.update(cluster_id=global_clusters[sid],split_cluster_id=split_clusters[row['global_split']][sid])
        qs=make_queries(official[sid],resolved[sid],row['global_split'],parents[sid])
        for q in qs:q.update(cluster_id=row['cluster_id'],split_cluster_id=row['split_cluster_id'])
        queries.extend(qs)
    quads=[make_quad(q,official,parents,resolved,original_training) for q in selected['discovery_quadruplets']]
    output.mkdir(parents=True);(output/'splits').mkdir();(output/'mechanism_views').mkdir()
    def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    def write_jsonl(path,values):
        with path.open('w') as stream:
            for value in values:stream.write(json.dumps(value,ensure_ascii=False)+'\n')
    write_jsonl(output/'corpus.jsonl',corpus);write_jsonl(output/'queries.jsonl',queries);write_jsonl(output/'aliases.jsonl',aliases)
    write_jsonl(output/'mechanism_views/discovery25_quadruplets.jsonl',quads)
    for split,ids in splits.items():
        write_json(output/'splits'/f'{split}.json',dict(global_split=split,n_sources=len(ids),source_ids=ids,canonical_query_ids=[sid+'__core2wiki_v1__'+q for sid in ids for q in QUERY_TYPES],
                                                       training_query_ids=[sid+'__core2wiki_v1__composed' for sid in ids] if split=='train' else None,
                                                       statistical_unit='25 fixed quadruplets for discovery mechanism view; sourceclusters must be considered for all splits; sources are not assumed independent'))
    metadata=dict(name='CoRe-2Wiki',version='1.0',id='CoRe-2Wiki-v1.0',source='2WikiMultiHopQA official train/development data; real Wikipedia paragraphs and annotated two-hop paths',
                  splits={k:len(v) for k,v in splits.items()},queries=list(QUERY_TYPES),training_queries=['composed'],mechanism_view='25 fixed discovery quadruplets; derived probes keep original source IDs',
                  policy='Fixed source IDs, questions, contexts and official aliases. Pilot overlap is permitted; this test set is not claimed to be never examined.')
    write_json(output/'dataset.json',metadata)
    return dict(dataset='CoRe-2Wiki-v1.0',sources=len(corpus),queries=len(queries),discovery_quadruplets=len(quads),output=str(output))
