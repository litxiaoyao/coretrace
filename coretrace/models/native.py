"""Explicit local native model loading with a pre-load parameter-size check."""

def load_native(path, *, family, device, dtype='bfloat16'):
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    config = AutoConfig.from_pretrained(path, local_files_only=True)
    if config.model_type != family or family not in ['qwen3', 'llama']:
        raise ValueError('Explicit supported model family required')
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(config, attn_implementation='eager')
    count = sum((p.numel() for p in probe.parameters()))
    del probe
    if count > 14000000000:
        raise ValueError('Model exceeds the14B experiment limit')
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, torch_dtype=getattr(torch, dtype), attn_implementation='eager').to(device).eval().requires_grad_(False)
    if sum((p.numel() for p in model.parameters())) != count:
        raise ValueError('Loaded model size mismatch')
    return (model, tokenizer)
