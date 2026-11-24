"""Full-rank selected Q/K/V/O weight slices, all tokens incl. cached decode.
Frozen native base + FP32 independent selected-slice deltas. Each forward builds
one native-dtype effective projection weight, runs the ORIGINAL full linear GEMM,
and discards its Python reference. No base-output-plus-delta approximation and no
persistent effective dense weights. Caller uses per-layer activation checkpointing
for bounded autograd saved-tensor lifetimes. GQA K/V union affects sibling Q heads.
"""
import json, weakref
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F

class HeadSliceQKVO(nn.Module):

    def __init__(self, model, head_map):
        super().__init__()
        object.__setattr__(self, '_model_ref', weakref.ref(model))
        model.requires_grad_(False)
        c = model.config
        self.hidden = int(c.hidden_size)
        self.query_heads = int(c.num_attention_heads)
        self.kv_heads = int(c.num_key_value_heads)
        self.head_dim = int(c.head_dim)
        assert self.query_heads % self.kv_heads == 0
        self.kv_repeat = self.query_heads // self.kv_heads
        self.head_map = {int(l): sorted(set(hs)) for l, hs in head_map.items() if hs}
        assert self.head_map
        self.kv_map = {l: sorted({h // self.kv_repeat for h in hs}) for l, hs in self.head_map.items()}
        self.deltas = nn.ParameterDict()
        self._spec = {}
        self._installed = {}
        self._merged_backups = {}
        self.merged = False
        for l, hs in self.head_map.items():
            assert 0 <= l < c.num_hidden_layers and all((type(h) is int and 0 <= h < self.query_heads for h in hs))
            attn = model.model.layers[l].self_attn
            for kind in ['q', 'k', 'v', 'o']:
                module = getattr(attn, kind + '_proj')
                dim = 1 if kind == 'o' else 0
                heads = hs if kind in ['q', 'o'] else self.kv_map[l]
                key = f'L{l}_{kind}'
                idx = torch.cat([torch.arange(h * self.head_dim, (h + 1) * self.head_dim, device=module.weight.device) for h in heads])
                expected = (self.hidden, self.query_heads * self.head_dim) if kind == 'o' else ((self.query_heads if kind == 'q' else self.kv_heads) * self.head_dim, self.hidden)
                assert tuple(module.weight.shape) == expected
                shape = list(module.weight.shape)
                shape[dim] = len(idx)
                self.deltas[key] = nn.Parameter(torch.zeros(shape, device=module.weight.device, dtype=torch.float32))
                self.register_buffer('idx_' + key, idx, persistent=False)
                self._spec[key] = (l, kind, dim)

    def _model(self):
        model = self._model_ref()
        if model is None:
            raise RuntimeError('Base model no longer exists')
        return model

    def _module(self, key):
        l, kind, _ = self._spec[key]
        return getattr(self._model().model.layers[l].self_attn, kind + '_proj')

    def _values(self, key, module):
        delta = self.deltas[key]
        assert delta.dtype == torch.float32 and delta.device == module.weight.device, 'FP32 slices must be colocated with base; use adapter.to(device) without dtype conversion'
        idx = getattr(self, 'idx_' + key)
        _, _, dim = self._spec[key]
        return (module.weight.detach().index_select(dim, idx).float() + delta).to(module.weight.dtype)

    def effective_weight(self, key):
        module = self._module(key)
        _, _, dim = self._spec[key]
        weight = module.weight.detach().clone(memory_format=torch.contiguous_format)
        weight.index_copy_(dim, getattr(self, 'idx_' + key), self._values(key, module))
        return weight

    def install(self):
        if self.merged:
            raise RuntimeError('Unmerge before installing trainable slices')
        if self._installed:
            return self
        if getattr(self._model(), '_headslice_qkvo_merged_owner', None) is not None:
            raise RuntimeError('Another adapter is merged into this base')
        try:
            for key in self._spec:
                module = self._module(key)
                if getattr(module, '_headslice_qkvo_owner', None) is not None:
                    raise RuntimeError('Another adapter owns this projection')
                had = 'forward' in module.__dict__
                old = module.__dict__.get('forward')
                self._installed[key] = (had, old)
                module._headslice_qkvo_owner = id(self)

                def forward(input, key=key, module=module):
                    return F.linear(input, self.effective_weight(key), module.bias)
                module.forward = forward
        except BaseException:
            self.remove()
            raise
        return self

    def remove(self):
        for key, (had, old) in list(self._installed.items()):
            module = self._module(key)
            if had:
                module.forward = old
            else:
                delattr(module, 'forward')
            if getattr(module, '_headslice_qkvo_owner', None) == id(self):
                delattr(module, '_headslice_qkvo_owner')
        self._installed.clear()
        return self

    def merge(self):
        if self.merged:
            raise RuntimeError('Already merged')
        self.remove()
        model = self._model()
        if getattr(model, '_headslice_qkvo_merged_owner', None) is not None:
            raise RuntimeError('Another adapter already merged')
        for key in self._spec:
            if getattr(self._module(key), '_headslice_qkvo_owner', None) is not None:
                raise RuntimeError('Another adapter installed')
        with torch.no_grad():
            for key in self._spec:
                module = self._module(key)
                _, _, dim = self._spec[key]
                idx = getattr(self, 'idx_' + key)
                self._merged_backups[key] = module.weight.index_select(dim, idx).detach().clone()
                module.weight.index_copy_(dim, idx, self._values(key, module))
        model._headslice_qkvo_merged_owner = id(self)
        self.merged = True
        return self

    def unmerge(self):
        if not self.merged:
            return self
        with torch.no_grad():
            for key, backup in self._merged_backups.items():
                module = self._module(key)
                module.weight.index_copy_(self._spec[key][2], getattr(self, 'idx_' + key), backup)
        self._merged_backups.clear()
        self.merged = False
        if getattr(self._model(), '_headslice_qkvo_merged_owner', None) == id(self):
            delattr(self._model(), '_headslice_qkvo_merged_owner')
        return self

    def export(self, directory):
        from safetensors.torch import save_file
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=False)
        save_file({k: v.detach().cpu().contiguous().clone() for k, v in self.state_dict().items()}, str(out / 'adapter_final.safetensors'))
        metadata = self.metadata()
        (out / 'adapter_config.json').write_text(json.dumps(metadata, indent=2) + '\n')
        return metadata

    def metadata(self):
        return dict(schema='full_rank_selected_QKVO_weight_slices_v1', head_map=self.head_map, kv_group_union=self.kv_map, query_heads=self.query_heads, kv_heads=self.kv_heads, head_dim=self.head_dim, hidden=self.hidden, trainable_parameters=sum((p.numel() for p in self.parameters())), parameterization='FP32 full selected-slice deltas; effective native weight=(base_selected.float+delta).cast(base_dtype)', token_scope='All training TF/prefill/cached-decode positions', GQA_scope='K/V group union changes shared K/V for all sibling query heads', effective_weights_persistently_cached=False)

    def __enter__(self):
        return self.install()

    def __exit__(self, *exc):
        self.remove()
