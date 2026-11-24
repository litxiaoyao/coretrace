"""Input-only paragraph policy, independent of model loading and answer labels."""
import re
from .title_graph import single_root_graph

def select_text(prompt, titles, rank_candidates=None, *, paragraph_boundary='line_start'):
    """Keep root plus chosen outgoing-title paragraph, otherwise preserve input.

    rank_candidates takes the candidate indices and returns one of them. The
    model-facing caller supplies the frozen attention readout under its actual
    deployment body. Unique-candidate cases require no extra model prefill.
    """
    markers = ['\n\nQuestion: ', '\n\nFinal question: ']
    marker = max(markers, key=prompt.rfind)
    cut = prompt.rfind(marker)
    if cut < 0:
        return dict(prompt=prompt, graph=dict(root=None, neighbors=[], reason='unrecognized_question_marker'), chosen=None, address_prefills=0)
    parse_prompt = prompt[:cut] + '\n\nFinal question: ' + prompt[cut + len(marker):]
    graph = single_root_graph(parse_prompt, titles)
    candidates = graph['neighbors']
    if not candidates:
        return dict(prompt=prompt, graph=graph, chosen=None, address_prefills=0)
    if len(candidates) == 1:
        chosen = candidates[0]
    else:
        if rank_candidates is None:
            raise ValueError('Ambiguous title neighbors require an explicit fixed policy')
        chosen = rank_candidates(tuple(candidates))
        if chosen not in candidates:
            raise ValueError('Chosen paragraph must be an outgoing-title candidate')
    if paragraph_boundary not in ['line_start', 'leading_newline']:
        raise ValueError('Explicit legacy-compatible paragraph boundary required')
    pattern = '^Title: ([^\\n]+)\\n' if paragraph_boundary == 'line_start' else '(?:^|\\n)Title: ([^\\n]+)\\n'
    matches = list(re.finditer(pattern, prompt[:cut], re.MULTILINE))
    if [m.group(1) for m in matches] != list(titles):
        raise ValueError('Paragraph title order must match the original prompt')
    keep = {graph['root'], chosen}
    blocks = [prompt[m.start():matches[i + 1].start() if i + 1 < len(matches) else cut].strip() for i, m in enumerate(matches) if i in keep]
    if len(blocks) != 2:
        raise ValueError('Exactly root and selected original paragraphs required')
    selected = prompt[:matches[0].start()] + '\n\n'.join(blocks) + prompt[cut:]
    return dict(prompt=selected, graph=graph, chosen=chosen, address_prefills=int(len(candidates) > 1))
