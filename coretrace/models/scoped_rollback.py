"""Exact learned V/O slice reversion, explicit layer subset and native tokenrole.
New independent session; whole native projection GEMM, O input columns/V output rows.
"""
import torch
from torch.nn import functional as F

class SavedProjectionUpdateReversionLayersSession:

    def __init__(self, adapter, *, prompt_length, question_positions, components, layers, role):
        assert adapter.merged and components in ['v', 'o', 'vo'] and (role in ['prefix_before_question', 'question_prefill'])
        self.a = adapter
        self.P = prompt_length
        self.q = list(question_positions)
        assert self.q and self.q == list(range(min(self.q), max(self.q) + 1))
        self.components = components
        self.layers = set(layers)
        assert all((0 <= l < len(adapter._model().model.layers) for l in layers))
        self.role = role
        self.handles = []

        self.calls = {}
        self.events = []

    def hook(self, key):

        def apply(module, args, output):
            x = args[0]
            self.calls[key] = self.calls.get(key, 0) + 1
            if self.calls[key] != 1:
                assert x.shape[1] == 1
                return output
            assert x.shape[1] == self.P
            rows = list(range(min(self.q))) if self.role == 'prefix_before_question' else self.q
            if not rows:
                return output
            layer, kind, axis = self.a._spec[key]
            idx = getattr(self.a, 'idx_' + key)
            w = module.weight.detach().clone(memory_format=torch.contiguous_format)
            w.index_copy_(axis, idx, self.a._merged_backups[key])
            replacement = F.linear(x, w, module.bias)
            del w
            changed = output.clone()
            ri = torch.tensor(rows, device=output.device)
            if kind == 'o':
                changed[0, ri] = replacement[0, ri]
            else:
                changed[0, ri[:, None], idx[None, :]] = replacement[0, ri[:, None], idx[None, :]]
            delta = changed[0, ri].float() - output[0, ri].float()
            self.events.append(dict(key=key, layer=layer, component=kind, role=self.role, positions_count=len(rows), reverted_weight_axis='inputcolumns' if kind == 'o' else 'outputchannels', selected_channels=int(idx.numel()), delta_norm=float(delta.square().sum().sqrt()), native_norm=float(output[0, ri].float().square().sum().sqrt()), valid=bool(delta.isfinite().all()), cacheddecode_modified=False))
            return changed
        return apply

    def __enter__(self):
        try:
            for key, (layer, kind, axis) in self.a._spec.items():
                if layer not in self.layers or kind not in self.components:
                    continue
                mod = self.a._module(key)
                assert getattr(mod, '_layerrole_reversion_owner', None) is None
                mod._layerrole_reversion_owner = id(self)
                self.handles.append((mod, mod.register_forward_hook(self.hook(key))))
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exc):
        for mod, h in self.handles:
            h.remove()
            if getattr(mod, '_layerrole_reversion_owner', None) == id(self):
                delattr(mod, '_layerrole_reversion_owner')
        self.handles = []


class BatchedProjectionUpdateReversionLayersSession:
    """Independent left-padded prefill rollback; cached decode stays trained.

    Positions supplied by callers are native, unpadded positions for each item.
    Padding is never reverted. This does not change the batch-one session.
    """

    def __init__(self, adapter, *, prompt_lengths, question_positions,
                 padded_length, components, layers, role):
        if not adapter.merged or components not in ('v', 'o', 'vo'):
            raise ValueError('Merged adapter and V/O components required')
        if role not in ('prefix_before_question', 'question_prefill'):
            raise ValueError('Unknown rollback role')
        self.a = adapter
        self.P = int(padded_length)
        self.lengths = list(prompt_lengths)
        self.questions = [list(q) for q in question_positions]
        self.layers = set(layers)
        self.components, self.role = components, role
        self.handles, self.calls, self.events = [], {}, []
        if not self.lengths or len(self.lengths) != len(self.questions):
            raise ValueError('One question geometry per batch item required')
        for length, q in zip(self.lengths, self.questions):
            if type(length) is not int or not 0 < length <= self.P:
                raise ValueError('Invalid native prompt length')
            if not q or q != list(range(min(q), max(q) + 1)) or min(q) < 0 or max(q) >= length:
                raise ValueError('Contiguous unpadded question positions required')
        if any(l < 0 or l >= len(adapter._model().model.layers) for l in layers):
            raise ValueError('Rollback layer outside model')
        self.rows = []
        for length, q in zip(self.lengths, self.questions):
            native = range(min(q)) if role == 'prefix_before_question' else q
            self.rows.append([self.P - length + j for j in native])

    def hook(self, key):
        def apply(module, args, output):
            x = args[0]
            self.calls[key] = self.calls.get(key, 0) + 1
            if x.shape[0] != len(self.lengths):
                raise ValueError('Batch size changed during greedy generation')
            if self.calls[key] > 1:
                if x.shape[1] != 1:
                    raise ValueError('Only cached single-token decode after prefill')
                return output
            if x.shape[1] != self.P:
                raise ValueError('First call must be the complete padded prefill')
            if not any(self.rows):
                return output
            layer, kind, axis = self.a._spec[key]
            idx = getattr(self.a, 'idx_' + key)
            w = module.weight.detach().clone(memory_format=torch.contiguous_format)
            w.index_copy_(axis, idx, self.a._merged_backups[key])
            replacement = F.linear(x, w, module.bias)
            changed = output.clone()
            for b, rows in enumerate(self.rows):
                if not rows:
                    continue
                ri = torch.tensor(rows, device=output.device)
                if kind == 'o':
                    changed[b, ri] = replacement[b, ri]
                else:
                    changed[b, ri[:, None], idx[None, :]] = replacement[b, ri[:, None], idx[None, :]]
            self.events.append(dict(key=key, layer=layer, component=kind,
                                    role=self.role, positions_count=[len(r) for r in self.rows],
                                    cacheddecode_modified=False))
            return changed
        return apply

    def __enter__(self):
        try:
            for key, (layer, kind, axis) in self.a._spec.items():
                if layer not in self.layers or kind not in self.components:
                    continue
                mod = self.a._module(key)
                if getattr(mod, '_layerrole_reversion_owner', None) is not None:
                    raise RuntimeError('Another rollback session owns projection')
                mod._layerrole_reversion_owner = id(self)
                self.handles.append((mod, mod.register_forward_hook(self.hook(key))))
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exc):
        for mod, handle in self.handles:
            handle.remove()
            if getattr(mod, '_layerrole_reversion_owner', None) == id(self):
                delattr(mod, '_layerrole_reversion_owner')
        self.handles = []
        return False
