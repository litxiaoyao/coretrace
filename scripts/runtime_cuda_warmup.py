"""Initialize library workspaces in an existing resident CUDA context."""
import argparse,json

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True)
    parser.parse_args()
    import torch
    # cuBLAS allocates outside the PyTorch cache. Give it physical headroom.
    torch.cuda.empty_cache()
    with torch.inference_mode():
        x=torch.ones((32,32),device='cuda',dtype=torch.bfloat16)
        result=x@x
        torch.cuda.synchronize()
        assert bool((result==32).all())
    print(json.dumps(dict(status='COMPLETE_CUDA_WARMUP',reserved_bytes=torch.cuda.memory_reserved(),free_bytes=torch.cuda.mem_get_info()[0])))

if __name__=='__main__':main()
