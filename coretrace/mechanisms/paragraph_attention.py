"""Architecture-resolved native eager paragraph observer and mass adapter.
No model loading, weights, projection hooks, lifecycle or dataset assumptions.
Tested Llama/Qwen3 API: Q/K after native normalization/RoPE, receiver V/O intact.
"""
import importlib, threading
import torch
_LOCK = threading.Lock()

def _backend(model):
    layers = model.model.layers
    module = importlib.import_module(type(layers[0].self_attn).__module__)
    if not callable(getattr(module, 'eager_attention_forward', None)) or not callable(getattr(module, 'repeat_kv', None)):
        raise ValueError('Native eager/repeat_kv backend required')
    if model.training or model.config._attn_implementation != 'eager':
        raise ValueError('Eval eager attention required')
    if any((type(l.self_attn).__module__ != module.__name__ for l in layers)):
        raise ValueError('Homogeneous native attention backend required')
    return module

def set_source_mass(row, keys, target):
    """FP32 mass rescale, one native cast; preserve both conditional distributions."""
    keys = torch.as_tensor(keys, device=row.device, dtype=torch.long)
    a = row.float()
    total = a.sum(-1, keepdim=True)
    src = a.index_select(-1, keys)
    mass = src.sum(-1, keepdim=True)
    tau = torch.as_tensor(target, device=a.device, dtype=torch.float32)
    if bool(((tau < 0) | (tau > 1) | ~torch.isfinite(tau)).any()):
        raise ValueError('Finite budget in[0,1]')
    goal = tau * total
    outside = a.clone()
    outside[..., keys] = 0
    om = total - mass
    valid = (total > 0) & ((mass > 0) | (goal == 0)) & ((om > 0) | ((total - goal).abs() < 1e-12))
    new = outside * ((total - goal) / om.clamp_min(1e-30))
    new[..., keys] = src * (goal / mass.clamp_min(1e-30))
    new = torch.where(valid, new, a)
    cast = new.to(row.dtype)
    return (cast, dict(valid=valid.squeeze(-1), before_mass=(mass / total.clamp_min(1e-30)).squeeze(-1), target_mass=torch.broadcast_to(tau, (row.shape[0],)), fp32_total_error=(new.sum(-1) - total.squeeze(-1)).abs(), cast_total_error=(cast.float().sum(-1) - total.squeeze(-1)).abs(), alpha_delta_l2=(cast.float() - a).norm(dim=-1)))

class NativeEagerHeadChunks:
    """Optional serialized backend context. Enter before observer/budget; exit after."""

    def __init__(self, model, chunk_heads=4):
        self.backend = _backend(model)
        self.chunk = int(chunk_heads)

    def __enter__(self):
        if self.chunk <= 0:
            raise ValueError('Positive chunk size')
        self.original = self.backend.eager_attention_forward
        backend = self.backend
        chunk = self.chunk

        def attention(module, query, key, value, attention_mask, scaling, dropout=0.0, **kwargs):
            if torch.is_grad_enabled() or dropout or module.training:
                raise ValueError('Inference-only chunk backend')
            k = backend.repeat_kv(key, module.num_key_value_groups)
            v = backend.repeat_kv(value, module.num_key_value_groups)
            outputs = []
            for lo in range(0, query.shape[1], chunk):
                hi = min(lo + chunk, query.shape[1])
                logits = query[:, lo:hi] @ k[:, lo:hi].transpose(2, 3) * scaling
                if attention_mask is not None:
                    logits += (attention_mask if attention_mask.shape[1] == 1 else attention_mask[:, lo:hi])[..., :key.shape[-2]]
                alpha = torch.softmax(logits, dim=-1, dtype=torch.float32).to(query.dtype)
                outputs.append(alpha @ v[:, lo:hi])
            return (torch.cat(outputs, 1).transpose(1, 2).contiguous(), None)
        self.backend.eager_attention_forward = attention
        return self

    def __exit__(self, *args):
        self.backend.eager_attention_forward = self.original

class _Session:

    def __init__(self, model, entry, head_map, rows=None):
        self.backend = _backend(model)
        self.model = model
        self.e = entry
        self.P = len(entry['prompt_ids'])
        self.rows = list(entry['question_positions'] if rows is None else rows)
        self.maps = {int(l): list(hs) for l, hs in head_map.items()}
        self.layers = {id(model.model.layers[l].self_attn): l for l in self.maps}
        self.events = []
        self.calls = {}
        self.features = {}
        self.owner = False
        if len(set(self.rows)) != len(self.rows) or any((type(i) is not int or i < 0 or i >= self.P for i in self.rows)):
            raise ValueError('Explicit unique native prompt rows')
        for l, hs in self.maps.items():
            if not hs or len(set(hs)) != len(hs) or any((h < 0 or h >= model.config.num_attention_heads for h in hs)):
                raise ValueError('Actual unique queryhead IDs')

    def __enter__(self):
        if not _LOCK.acquire(False):
            raise RuntimeError('Serialized native paragraph attention sessions')
        self.owner = True
        self.original = self.backend.eager_attention_forward

        def wrapped(module, q, k, v, attention_mask, scaling, dropout=0.0, **kwargs):
            if torch.is_grad_enabled() or dropout or module.training:
                raise ValueError('Inference eval/no dropout only')
            output = self.original(module, q, k, v, attention_mask, scaling, dropout=dropout, **kwargs)
            layer = self.layers.get(id(module))
            if layer is None:
                return output
            self.calls[layer] = self.calls.get(layer, 0) + 1
            if self.calls[layer] > 1:
                if q.shape[-2] != 1:
                    raise ValueError('Only cached single-token decoding after prefill')
                return output
            if q.shape[0] != 1 or q.shape[-2] != self.P:
                raise ValueError('Batch1 full native prefill required')
            if not self.rows:
                return output
            return self.apply(layer, module, q, k, v, attention_mask, scaling, output)
        self.backend.eager_attention_forward = wrapped
        return self

    def alpha(self, layer, module, q, k, mask, scale):
        kk = self.backend.repeat_kv(k, module.num_key_value_groups)
        hs = self.maps[layer]
        qs = q[:, hs][:, :, self.rows]
        logits = qs @ kk[:, hs].transpose(2, 3) * scale
        if mask is not None:
            logits += (mask if mask.shape[1] == 1 else mask[:, hs])[:, :, self.rows, :k.shape[-2]]
        return torch.softmax(logits, dim=-1, dtype=torch.float32).to(q.dtype)[0]

    def __exit__(self, *args):
        if hasattr(self, 'original'):
            self.backend.eager_attention_forward = self.original
        if self.owner:
            _LOCK.release()
            self.owner = False
        return False

class NativeParagraphObserver(_Session):
    """Read-only features: numericlayer/head order retained, no labels required."""

    def apply(self, l, module, q, k, v, mask, scale, output):
        alpha = self.alpha(l, module, q, k, mask, scale).float()
        ps = self.e['paragraphs']
        for p in ps:
            if not p['keys'] or max(p['keys']) >= min(self.rows):
                raise ValueError('Paragraph source before query rows')
        masses = torch.stack([alpha[..., p['keys']].sum(-1) for p in ps], -1)
        self.features[str(l)] = dict(heads=self.maps[l], all_question_mean=masses.mean(1).tolist(), last_question=masses[:, -1].tolist())
        return output

class NativeParagraphBudget(_Session):

    def __init__(self, model, entry, head_map, budgets, *, rows=None, identity=False):
        super().__init__(model, entry, head_map, rows)
        self.keys = list(entry['second_source_keys'])
        self.budgets = budgets
        self.identity = bool(identity)
        if len(set(self.keys)) != len(self.keys) or any((i < 0 or i >= self.P for i in self.keys)) or (self.keys and self.rows and (max(self.keys) >= min(self.rows))):
            raise ValueError('Unique evidence keys before selected query rows')

    def apply(self, l, module, q, k, v, mask, scale, output):
        if self.identity or not self.keys:
            return output
        alpha = self.alpha(l, module, q, k, mask, scale)
        vv = self.backend.repeat_kv(v, module.num_key_value_groups)
        changed = output[0].clone()
        for index, h in enumerate(self.maps[l]):
            tau = self.budgets.get(str(l), self.budgets.get(l, {}))
            tau = tau.get(str(h), tau.get(h))
            after, meta = set_source_mass(alpha[index], self.keys, tau)
            z = after @ vv[0, h]
            changed[0, self.rows, h, :] = z
            self.events.append(dict(layer=l, head=h, positions=self.rows, source_key_count=len(self.keys), valid_rows=int(meta['valid'].sum()), invalid_rows=int((~meta['valid']).sum()), before_mass=meta['before_mass'].tolist(), target_mass=meta['target_mass'].tolist(), fp32_total_error_max=float(meta['fp32_total_error'].max()), cast_total_error_max=float(meta['cast_total_error'].max()), alpha_delta_l2=meta['alpha_delta_l2'].tolist(), receiver_V_preserved=True, receiver_O_preserved=True, KV_cache_unmodified=True))
        return (changed, None)
