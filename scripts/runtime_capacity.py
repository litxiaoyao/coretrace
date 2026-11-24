"""Resize a resident executor allocation at a request boundary without unloading."""
import argparse,inspect,json,time
from pathlib import Path

def main():
 import torch
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--capacity-gib',type=float,required=True);p.add_argument('--transfer-control',required=True);p.add_argument('--transfer-remaining-gib',type=float,required=True);a=p.parse_args()
 frame=inspect.currentframe().f_back
 while frame is not None:
  if frame.f_code.co_name=='run_preloaded'and frame.f_code.co_filename.endswith('resident_worker.py')and'retain'in frame.f_locals:break
  frame=frame.f_back
 if frame is None:raise RuntimeError('Run this command through the resident executor')
 retain=frame.f_locals['retain'];cells=dict(zip(retain.__code__.co_freevars,retain.__closure__))
 capacity=int(a.capacity_gib*(1<<30));control=Path(a.transfer_control);status=control.with_name('transfer_reservation_status.json')
 temporary=control.with_suffix('.tmp');temporary.write_text(json.dumps({'gib':a.transfer_remaining_gib}));temporary.replace(control)
 while True:
  try:
   state=json.loads(status.read_text())
   if state['held_bytes']<=int(a.transfer_remaining_gib*(1<<30)):break
   if not(Path('/proc')/str(state['pid'])).exists():raise RuntimeError('Transfer reservation process exited before releasing memory')
  except (FileNotFoundError,json.JSONDecodeError):pass
  time.sleep(.1)
 torch.cuda.set_per_process_memory_fraction((capacity+(1<<30))/torch.cuda.get_device_properties(0).total_memory)
 gap=max(0,capacity-torch.cuda.memory_reserved())
 if gap:
  allocation=torch.empty(gap,dtype=torch.uint8,device=next(frame.f_locals['model'].parameters()).device);del allocation
 cells['capacity'].cell_contents=capacity
 print(json.dumps(dict(status='COMPLETE_RESIDENT_CAPACITY_CHANGE',capacity_bytes=capacity,reserved_bytes=torch.cuda.memory_reserved(),model_unloaded=False),indent=2))
if __name__=='__main__':main()
