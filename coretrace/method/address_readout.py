"""Fixed-recipe linear paragraph-address readout; no evaluation-label input."""
import hashlib, json
import torch
from .paragraph_features import feature_matrix

def feature_schema(row):
    heads = [(int(layer), int(head)) for layer in sorted(row['features'], key=int) for head in sorted(row['features'][layer]['heads'])]
    return dict(head_order=heads, modes=['all_question_mean', 'last_question'], extra=['log_paragraph_token_fraction', 'title_mentioned_in_question'], parameters=2 * len(heads) + 2)

def fit_address_readout(train_rows, train_labels, *, seed=42, steps=500, lr=0.03, l2=0.01, feature_set="full"):
    """Accept explicitly training-only feature rows and ID->paragraph labels.

    Standardization, optimization and schema derive solely from these rows.
    Runtime configuration fixes the recipe before any test predictions exist.
    """
    rows = list(train_rows)
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Nonempty unique training feature IDs required')
    if any((r['split'] != 'train' for r in rows)):
        raise ValueError('Only explicitly designated train split may fit the readout')
    if set(train_labels) != {r['id'] for r in rows}:
        raise ValueError('Training labels must match exactly the feature IDs')
    schema = feature_schema(rows[0])
    if feature_set not in ['full', 'attention', 'metadata']:
        raise ValueError('Unknown readout feature set')
    columns = list(range(schema['parameters']))
    if feature_set == 'attention': columns = columns[:-2]
    elif feature_set == 'metadata': columns = columns[-2:]
    xs = []
    for r in rows:
        if feature_schema(r) != schema:
            raise ValueError('Fixed feature head order/schema required')
        x = feature_matrix(r)[:, columns]
        if not 0 <= train_labels[r['id']] < len(x):
            raise ValueError('Training target paragraph outside original context')
        xs.append(x)
    nf = len(columns)
    flat = torch.cat(xs)
    mean = flat.mean(0)
    std = flat.std(0, unbiased=False).clamp_min(0.0001)
    batch = torch.zeros(len(xs), max(map(len, xs)), nf)
    valid = torch.zeros(batch.shape[:2], dtype=torch.bool)
    for i, x in enumerate(xs):
        batch[i, :len(x)] = (x - mean) / std
        valid[i, :len(x)] = True
    y = torch.tensor([train_labels[r['id']] for r in rows])
    torch.manual_seed(seed)
    weight = torch.nn.Parameter(torch.zeros(nf))
    optimizer = torch.optim.Adam([weight], lr=lr)
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        scores = (batch @ weight).masked_fill(~valid, -1000000000.0)
        loss = torch.nn.functional.cross_entropy(scores, y) + l2 * weight.square().sum()
        if not torch.isfinite(loss):
            raise ValueError('Nonfinite readout loss')
        loss.backward()
        optimizer.step()
    return dict(feature_set=feature_set, feature_columns=columns, weight=weight.detach().tolist(), mean=mean.tolist(), std=std.tolist(), schema=schema, training_sources=len(rows), steps=steps, lr=lr, L2=l2, seed=seed, LLM_updates=0)

def address_scores(row, artifact):
    if feature_schema(row) != artifact['schema']:
        if json.dumps(feature_schema(row), sort_keys=True) != json.dumps(artifact['schema'], sort_keys=True):
            raise ValueError('Readout feature schema mismatch')
    x = feature_matrix(row)
    if "feature_columns" in artifact: x = x[:, artifact["feature_columns"]]
    return (x - torch.tensor(artifact['mean'])) / torch.tensor(artifact['std']) @ torch.tensor(artifact['weight'])
