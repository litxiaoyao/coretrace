"""Pure readout feature schema. No environment, process, device or model effects."""
import math

def feature_matrix(row):
    import torch
    columns = []
    for mode in ['all_question_mean', 'last_question']:
        for layer in sorted(row['features'], key=int):
            block = row['features'][layer]
            index = {h: i for i, h in enumerate(block['heads'])}
            for head in sorted(index):
                columns.append(torch.tensor(block[mode][index[head]], dtype=torch.float32).clamp_min(1e-08).log())
    columns.append(torch.tensor([math.log(p['key_count'] / row['prompt_tokens']) for p in row['paragraphs']]))
    columns.append(torch.tensor([float(p['title_mentioned_in_question']) for p in row['paragraphs']]))
    x = torch.stack(columns, 1)
    if not torch.isfinite(x).all():
        raise ValueError('Finite paragraph feature matrix required')
    return x
