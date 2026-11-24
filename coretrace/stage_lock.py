"""Serialize writers to the same experiment output when workers run in parallel."""
import fcntl,json,sys
from pathlib import Path

def run_stage(main, completion_file):
    if '--run'not in sys.argv:
        return main()
    if '--config'in sys.argv:
        cp=Path(sys.argv[sys.argv.index('--config')+1]).resolve();cfg=json.loads(cp.read_text());out=Path(cfg['output']);out=out if out.is_absolute()else cp.parent/out
    else:out=Path(sys.argv[sys.argv.index('--output')+1]).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    with(out.parent/('.'+out.name+'.lock')).open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        receipt=out/completion_file
        if receipt.exists()and json.loads(receipt.read_text()).get('status','').startswith('COMPLETE'):
            print(json.dumps(dict(status='COMPLETE_REUSED_STAGE',output=str(out))))
            return
        return main()
