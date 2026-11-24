"""Full-parameter AdamW with CPU FP32 masters/states and FP32 gradient sums.

Caller owns model/load/device/resources/data and uses one serial backward stream.
No optimizer step inside hooks: all parameter gradients are summed first, divided
by the exact number of microbatches, optionally globally clipped, then one step.
This matches equal-microbatch mean CE, NOT unequal-token weighted global mean.
Forward/backward parameters retain model dtype/device; no adapter/frozen subset.
CUDA -> CPU transfers remain synchronous, through a reusable pinned FP32 staging
buffer. Each parameter's CPU accumulation completes before reusing that buffer.
When explicitly enabled or admitted by the auto memory check, FP32 gradient
sums remain on GPU across microbatches and are offloaded once before the same
CPU clipping/AdamW update. Model gradients themselves retain native dtype.
Memory lower bound: four FP32 CPU tensors per unique element (master,m,v,grad
when active), plus temporary CPU tensors and native model memory. Resource
preflight belongs to the caller; no model loading occurs in this core.
"""
import math
from collections import OrderedDict
import torch

class CPUOffloadedFullAdamW:

    def __init__(self, model, *, lr=2e-05, betas=(0.9, 0.999), eps=1e-08, weight_decay=0.01, max_grad_norm=1.0, gpu_accumulation=False):
        if not (lr >= 0 and eps > 0 and (0 <= betas[0] < 1) and (0 <= betas[1] < 1) and (weight_decay >= 0)):
            raise ValueError('AdamW hyperparameters')
        if max_grad_norm is not None and max_grad_norm <= 0:
            raise ValueError('Positive clip threshold or None')
        self.model = model
        self.lr = lr
        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        self.max_grad_norm = max_grad_norm
        self.step_count = 0
        self.microbatches = 0
        self.handles = []
        self.closed = False
        self.in_backward = False
        self.params = OrderedDict()
        self.aliases = {}
        seen = {}
        for name, p in model.named_parameters(remove_duplicate=False):
            if id(p) in seen:
                self.aliases[name] = seen[id(p)]
                continue
            if not p.requires_grad:
                raise ValueError('FullFT requires every unique parameter trainable: ' + name)
            if not p.is_floating_point() or not p.is_leaf:
                raise ValueError('Floating leaf parameters required')
            if p.grad is not None:
                raise ValueError('Start without preexisting gradients')
            seen[id(p)] = name
            self.params[name] = p
        if not self.params:
            raise ValueError('Nonempty full parameter set')
        first = next(iter(self.params.values()))
        self.gpu_accumulation = bool(gpu_accumulation is True and first.device.type == 'cuda')
        if gpu_accumulation == 'auto' and first.device.type == 'cuda':
            cached = torch.cuda.memory_reserved(first.device) - torch.cuda.memory_allocated(first.device)
            required = 4 * sum(p.numel() for p in self.params.values())
            # Stay inside this worker's already-retained allocation. Leave8GiB
            # for activations, current parameter gradients and casting workspace.
            self.gpu_accumulation = cached >= required + (8 << 30)
        self.master = {n: p.detach().to(device='cpu', dtype=torch.float32).clone() for n, p in self.params.items()}
        self.m = {n: torch.zeros_like(x) for n, x in self.master.items()}
        self.v = {n: torch.zeros_like(x) for n, x in self.master.items()}
        self.grads = {}
        self.hook_calls = {n: 0 for n in self.params}
        self.last_gradients = None
        self._offload_staging = None
        try:
            for n, p in self.params.items():
                self.handles.append(p.register_post_accumulate_grad_hook(self._hook(n)))
        except BaseException:
            self.close()
            raise

    def _hook(self, name):

        def capture(p):
            if not self.in_backward:
                raise RuntimeError('Use optimizer.backward(loss), not external backward')
            g = p.grad
            if g is None:
                raise RuntimeError('Post-accumulate hook requires gradient')
            if g.is_sparse:
                raise ValueError('Dense fullFT gradients only')
            if self.gpu_accumulation:
                if name in self.grads:
                    self.grads[name].add_(g.detach())
                else:
                    self.grads[name] = g.detach().to(dtype=torch.float32, copy=True)
                self.hook_calls[name] += 1
                p.grad = None
                return
            if g.device.type == 'cuda':
                count = g.numel()
                if self._offload_staging is None or self._offload_staging.numel() < count:
                    self._offload_staging = torch.empty(count, dtype=torch.float32,
                                                       device='cpu', pin_memory=True)
                cpu = self._offload_staging[:count].view(g.shape)
                cpu.copy_(g.detach(), non_blocking=False)
            else:
                cpu = g.detach().to(device='cpu', dtype=torch.float32)
            if name in self.grads:
                self.grads[name].add_(cpu)
            else:
                # Own the accumulation storage: staging is reused by the next hook.
                self.grads[name] = cpu.clone()
            self.hook_calls[name] += 1
            p.grad = None
        return capture

    def backward(self, mean_microbatch_loss):
        if self.closed or self.in_backward:
            raise RuntimeError('Serial open optimizer required')
        if mean_microbatch_loss.ndim != 0:
            raise ValueError('Scalar mean CE per microbatch')
        self.in_backward = True
        try:
            mean_microbatch_loss.backward()
        except BaseException:
            self.zero_grad()
            raise
        finally:
            self.in_backward = False
        self.microbatches += 1

    def averaged_gradients(self):
        if not self.microbatches:
            raise RuntimeError('No completed microbatch')
        return {n: g.detach().cpu() / self.microbatches for n, g in self.grads.items()}

    @torch.no_grad()
    def step(self, *, require_all_gradients=True, retain_gradient_snapshot=False):
        if self.closed or self.in_backward or self.microbatches < 1:
            raise RuntimeError('Complete microbatches before one global step')
        missing = set(self.params) - set(self.grads)
        if require_all_gradients and missing:
            raise ValueError('Missing fullFT gradients: ' + ','.join(sorted(missing)))
        if self.gpu_accumulation:
            # Preserve the original FP32 per-microbatch sum, but transfer it
            # once per optimizer update rather than once per microbatch.
            for n in list(self.grads):
                g = self.grads[n]
                count = g.numel()
                if self._offload_staging is None or self._offload_staging.numel() < count:
                    self._offload_staging = torch.empty(count, dtype=torch.float32,
                                                       device='cpu', pin_memory=True)
                cpu = self._offload_staging[:count].view(g.shape)
                cpu.copy_(g, non_blocking=False)
                self.grads[n] = cpu.clone()
        for g in self.grads.values():
            g.div_(self.microbatches)
        norms = torch.stack([torch.linalg.vector_norm(g, 2) for g in self.grads.values()])
        total = torch.linalg.vector_norm(norms, 2)
        if not torch.isfinite(total):
            raise FloatingPointError('Nonfinite full gradient; no update performed')
        factor = 1.0 if self.max_grad_norm is None else min(1.0, float(self.max_grad_norm / (total + 1e-06)))
        for g in self.grads.values():
            g.mul_(factor)
        self.last_gradients = {n: g.clone() for n, g in self.grads.items()} if retain_gradient_snapshot else None
        self.step_count += 1
        b1, b2 = self.betas
        bc1 = 1 - b1 ** self.step_count
        bc2 = 1 - b2 ** self.step_count
        updated = 0
        changed = 0
        for n, g in self.grads.items():
            w = self.master[n]
            old = w.clone() if retain_gradient_snapshot else None
            if self.weight_decay:
                w.mul_(1 - self.lr * self.weight_decay)
            self.m[n].lerp_(g, 1 - b1)
            self.v[n].mul_(b2).addcmul_(g, g, value=1 - b2)
            denom = self.v[n].sqrt().div_(math.sqrt(bc2)).add_(self.eps)
            w.addcdiv_(self.m[n], denom, value=-self.lr / bc1)
            self.params[n].copy_(w, non_blocking=False)
            updated += 1
            if old is not None:
                changed += int(not torch.equal(old, w))
        report = dict(actual_optimizer_steps=self.step_count, actual_microbatches=self.microbatches, unique_parameter_tensors=len(self.params), unique_parameter_elements=sum((p.numel() for p in self.params.values())), gradient_tensors=len(self.grads), updated_parameter_tensors=updated, master_changed_tensors=changed if retain_gradient_snapshot else None, unclipped_gradient_norm=float(total), clip_factor=factor, missing_gradient_names=sorted(missing), model_gradients_cleared=all((p.grad is None for p in self.params.values())), CPU_master_state=True)
        self.zero_grad()
        return report

    def zero_grad(self):
        self.grads.clear()
        self.microbatches = 0
        for p in self.params.values():
            p.grad = None

    def state_dict(self):
        if self.in_backward:
            raise RuntimeError('Cannot checkpoint inside backward')
        return dict(schema='cpu_fullparameter_adamw_v1', step_count=self.step_count, microbatches=self.microbatches, hyperparameters=dict(lr=self.lr, betas=self.betas, eps=self.eps, weight_decay=self.weight_decay, max_grad_norm=self.max_grad_norm), parameter_names=list(self.params), aliases=self.aliases, master={n: x.detach() for n, x in self.master.items()}, m={n: x.detach() for n, x in self.m.items()}, v={n: x.detach() for n, x in self.v.items()}, grads={n: x.detach().cpu() for n, x in self.grads.items()})

    @torch.no_grad()
    def load_state_dict(self, s):
        if s['schema'] != 'cpu_fullparameter_adamw_v1' or s['parameter_names'] != list(self.params) or s['aliases'] != self.aliases:
            raise ValueError('Exact named unique parameter topology/ties')
        expected = dict(lr=self.lr, betas=self.betas, eps=self.eps, weight_decay=self.weight_decay, max_grad_norm=self.max_grad_norm)
        if s['hyperparameters'] != expected:
            raise ValueError('Same optimizer hyperparameters')
        for field in ['master', 'm', 'v']:
            for n, p in self.params.items():
                x = s[field][n]
                if x.device.type != 'cpu' or x.dtype != torch.float32 or x.shape != p.shape:
                    raise ValueError('CPU FP32 state shape')
            setattr(self, field, {n: x.clone() for n, x in s[field].items()})
        self.step_count = s['step_count']
        self.microbatches = s['microbatches']
        self.grads = {n: x.to(device=self.params[n].device if self.gpu_accumulation else 'cpu',
                              dtype=torch.float32, copy=True) for n, x in s['grads'].items()}
        for n, p in self.params.items():
            p.copy_(self.master[n].to(device=p.device, dtype=p.dtype))

    def close(self):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        self._offload_staging = None
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
