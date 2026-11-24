"""Factor source access mass from source-internal attention allocation.

The donor is normalized source attention alpha from a direct-target question,
not an answer residual, hidden state, value vector, generated answer, or runtime
repair input. It is privileged causal diagnosis. The caller must align the exact
source-prefix token IDs and source-key positions across donor/receiver prompts.
Mass uses fixed discovery tau, independently of the donor's original mass.
"""
import torch
from .paragraph_attention import _Session, set_source_mass

def factorized_source_row(row, source_keys, tau, donor_conditional, mode):
    """FP32 rearrangement followed by one native cast; invalid rows stay exact.

    A zero source/outside mass makes the conditional undefined and is flagged
    no-op. No uniform or other invented conditional distribution is substituted.
    ``mass_only`` uses the existing NativeParagraphBudget mass mathematics.
    """
    if mode not in ['identity', 'mass_only', 'conditional_only', 'both']:
        raise ValueError('Explicit factorization mode required')
    keys = torch.as_tensor(source_keys, device=row.device, dtype=torch.long)
    if row.ndim != 2 or len(set(source_keys)) != len(source_keys) or any((i < 0 or i >= row.shape[-1] for i in source_keys)):
        raise ValueError('Rows by keys with unique in-range source positions required')
    a = row.float()
    total = a.sum(-1, keepdim=True)
    source = a.index_select(-1, keys)
    mass = source.sum(-1, keepdim=True)
    outside = a.clone()
    outside[..., keys] = 0
    outside_mass = outside.sum(-1, keepdim=True)
    input_valid = torch.isfinite(a).all(-1, keepdim=True) & (a >= 0).all(-1, keepdim=True) & (total > 0)
    source_valid = (mass > 0) & bool(len(source_keys))
    outside_valid = outside_mass > 0
    donor_valid = True
    donor = None
    if mode in ['conditional_only', 'both']:
        if donor_conditional is None:
            donor_valid = False
        else:
            donor = torch.as_tensor(donor_conditional, device=row.device, dtype=torch.float32)
            if donor.ndim != 1 or donor.numel() != len(source_keys):
                donor_valid = False
            else:
                donor_valid = bool(torch.isfinite(donor).all() and (donor >= 0).all() and torch.isclose(donor.sum(), donor.new_tensor(1.0), atol=1e-05, rtol=1e-05))
    valid = input_valid & source_valid & outside_valid & donor_valid
    fp32_error = None
    if mode == 'identity':
        changed = row
        unrounded = a
        valid = input_valid
    elif mode == 'mass_only':
        changed, mass_meta = set_source_mass(row, source_keys, tau)
        changed = torch.where(valid, changed, row)
        unrounded = changed.float()
        fp32_error = torch.where(valid.squeeze(-1), mass_meta['fp32_total_error'], torch.zeros(len(row), device=row.device))
    elif not donor_valid:
        changed = row
        unrounded = a
    else:
        target = mass
        if mode == 'both':
            fixed = torch.as_tensor(tau, device=row.device, dtype=torch.float32)
            if not bool(torch.isfinite(fixed).all() and (fixed >= 0).all() and (fixed <= 1).all()):
                raise ValueError('Fixed finite discovery tau in [0,1] required')
            target = fixed * total
        unrounded = outside * ((total - target) / outside_mass.clamp_min(1e-30))
        unrounded[..., keys] = donor * target
        unrounded = torch.where(valid, unrounded, a)
        changed = unrounded.to(row.dtype)
    return (changed, dict(valid=valid.squeeze(-1), invalid_input=(~input_valid).squeeze(-1), invalid_source=(~source_valid).squeeze(-1), invalid_outside=(~outside_valid).squeeze(-1), invalid_donor=torch.full((len(row),), not donor_valid, device=row.device, dtype=torch.bool), receiver_mass_fraction=(mass / total.clamp_min(1e-30)).squeeze(-1), result_mass_fraction=changed.float().index_select(-1, keys).sum(-1) / total.squeeze(-1).clamp_min(1e-30), fp32_total_error=(unrounded.sum(-1) - total.squeeze(-1)).abs() if fp32_error is None else fp32_error, cast_total_error=(changed.float().sum(-1) - total.squeeze(-1)).abs(), alpha_delta_l2=(changed.float() - a).norm(dim=-1)))

def _source_keys(entry):
    keys = list(entry['second_source_keys'])
    question = entry['question_positions']
    if len(set(keys)) != len(keys) or any((type(i) is not int or i < 0 or i >= len(entry['prompt_ids']) for i in keys)):
        raise ValueError('Unique in-range native source keys required')
    if not question or (keys and max(keys) >= min(question)):
        raise ValueError('Source must precede explicit question rows')
    return keys

class NativeSourceConditionalDonor(_Session):
    """Read-only native last-question-row source-alpha conditional capture."""

    def __init__(self, model, entry, head_map):
        self.keys = _source_keys(entry)
        self.records = {}
        super().__init__(model, entry, head_map, rows=[max(entry['question_positions'])])

    def apply(self, layer, module, q, k, v, mask, scale, output):
        alpha = self.alpha(layer, module, q, k, mask, scale).float()
        for index, head in enumerate(self.maps[layer]):
            row = alpha[index, 0]
            source = row[self.keys]
            mass = source.sum()
            valid = bool(source.numel() and torch.isfinite(source).all() and (source >= 0).all() and (mass > 0))
            self.records.setdefault(str(layer), {})[str(head)] = dict(conditional=(source / mass).cpu().tolist() if valid else None, valid=valid, native_source_mass=float(mass), native_row_total=float(row.sum()))
        return output

    def donor_bank(self):
        if set(self.records) != set(map(str, self.maps)) or any((set(self.records[str(layer)]) != set(map(str, heads)) for layer, heads in self.maps.items())):
            raise ValueError('Complete actual last-row donor capture required')
        return dict(source_id=self.e.get('source_id'), donor_id=self.e.get('id'), head_map={str(layer): heads for layer, heads in self.maps.items()}, second_source_keys=self.keys, source_prefix_ids=self.e['prompt_ids'][:max(self.keys) + 1] if self.keys else [], records=self.records, donor_kind='Normalized last-question source attention alpha only; privileged diagnostic')

def verify_source_alignment(entry, donor):
    """Call before interchange; exact shared native context prefix is required."""
    keys = _source_keys(entry)
    if donor['second_source_keys'] != keys or donor['source_prefix_ids'] != (entry['prompt_ids'][:max(keys) + 1] if keys else []):
        raise ValueError('Donor/receiver native source keys or context prefix differ')
    if entry.get('source_id') != donor.get('source_id'):
        raise ValueError('Source IDs differ')

class NativeFactoredParagraphIntervention(_Session):
    """Native receiver V/O retained; only specified prefill alpha rows change.

    Cached decode is untouched through _Session. KV cache tensors are never edited;
    ordinary downstream causal effects on later-layer activations remain possible.
    """

    def __init__(self, model, entry, head_map, budgets, donor_conditionals=None, *, mode, rows):
        if mode not in ['identity', 'mass_only', 'conditional_only', 'both']:
            raise ValueError('Unknown factorization mode')
        if not rows or not set(rows) <= set(entry['question_positions']):
            raise ValueError('Explicit nonempty prefill question-row subset required')
        self.keys = _source_keys(entry)
        self.budgets = budgets
        self.donor = donor_conditionals
        self.mode = mode
        if mode in ['conditional_only', 'both'] and donor_conditionals is not None:
            verify_source_alignment(entry, donor_conditionals)
        super().__init__(model, entry, head_map, rows=rows)

    def apply(self, layer, module, q, k, v, mask, scale, output):
        if self.mode == 'identity':
            self.events.append(dict(layer=layer, mode='identity', positions=self.rows, identity=True, KV_cache_unmodified=True))
            return output
        alpha = self.alpha(layer, module, q, k, mask, scale)
        values = self.backend.repeat_kv(v, module.num_key_value_groups)
        changed = output[0].clone()
        for index, head in enumerate(self.maps[layer]):
            bank = {} if self.donor is None else self.donor['records'].get(str(layer), {})
            record = bank.get(str(head), {})
            conditional = record.get('conditional') if record.get('valid', False) else None
            tau = self.budgets.get(str(layer), self.budgets.get(layer, {}))
            tau = tau.get(str(head), tau.get(head))
            row, meta = factorized_source_row(alpha[index], self.keys, tau, conditional, self.mode)
            valid = meta['valid']
            if bool(valid.any()):
                replacement = row @ values[0, head]
                valid_rows = torch.as_tensor(self.rows, device=changed.device)[valid]
                changed[0, valid_rows, head, :] = replacement[valid]
            self.events.append(dict(layer=layer, head=head, mode=self.mode, positions=self.rows, valid_rows=int(valid.sum()), invalid_rows=int((~valid).sum()), invalid_source_rows=int(meta['invalid_source'].sum()), invalid_outside_rows=int(meta['invalid_outside'].sum()), invalid_donor_rows=int(meta['invalid_donor'].sum()), receiver_mass_fraction=meta['receiver_mass_fraction'].tolist(), result_mass_fraction=meta['result_mass_fraction'].tolist(), fp32_total_error_max=float(meta['fp32_total_error'].max()), cast_total_error_max=float(meta['cast_total_error'].max()), alpha_delta_l2=meta['alpha_delta_l2'].tolist(), receiver_V_preserved=True, receiver_O_preserved=True, KV_cache_unmodified=True, cacheddecode_modified=False))
        return (changed, None)
