"""Account aggregate host memory before allocating FullFT optimizer states."""
import contextlib
import errno
import fcntl
import json
import os
import shutil
from pathlib import Path
import time

GIB = 1 << 30


def wait_for_checkpoint_space(runtime, output, parameters, reserve_bytes=2 * GIB):
    """Keep the live job/weights while shared checkpoint storage is unavailable."""
    ancestor = Path(output).resolve()
    while not ancestor.exists():
        ancestor = ancestor.parent
    required = 2 * parameters + (64 << 20) + reserve_bytes
    waiting = False
    while True:
        free = shutil.disk_usage(ancestor).free
        if free >= required:
            return
        wait_status(runtime, 'WAITING_CHECKPOINT_DISK', free_bytes=free,
                    required_bytes=required)
        if not waiting:
            print(json.dumps(dict(status='WAITING_CHECKPOINT_DISK', free_bytes=free,
                                  required_bytes=required)), flush=True)
            waiting = True
        time.sleep(30)


def reclaim_unused_host_cache():
    """At a training boundary, release free host buffers, retaining GPU cache."""
    import ctypes
    import gc
    import torch
    gc.collect()
    if torch.cuda.is_initialized():
        release = getattr(torch._C, '_host_emptyCache', None)
        if release is not None:
            release()
    trim = getattr(ctypes.CDLL(None), 'malloc_trim', None)
    if trim is not None:
        trim(0)


def reclaim_clean_file_cache(group, wanted):
    """Reclaim this service's unused file cache; require swapping disabled."""
    group = Path(group)
    swap = group / 'memory.swap.max'
    reclaim = group / 'memory.reclaim'
    if not swap.exists() or swap.read_text().strip() != '0' or not reclaim.exists():
        return 0
    stats = dict(line.split() for line in (group / 'memory.stat').read_text().splitlines())
    clean = max(0, int(stats.get('file', 0)) - sum(int(stats.get(k, 0))
                for k in ['shmem', 'file_mapped', 'file_dirty', 'file_writeback']))
    amount = min(max(0, wanted), clean, 8 * GIB)
    if amount < 256 << 20:
        return 0
    before = int((group / 'memory.current').read_text())
    try:
        reclaim.write_text(str(amount))
    except OSError as error:
        if error.errno not in [errno.EAGAIN, errno.EACCES, errno.EPERM]:
            raise
    return max(0, before - int((group / 'memory.current').read_text()))


def projected_memory(usage, leases):
    """Include both resident memory and admitted states not allocated yet."""
    return sum(usage.values()) + sum(max(
        0, x['baseline_bytes'] + x['extra_bytes'] - usage.get(x['cgroup'], 0))
        for x in leases)


def system_memory():
    values = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        values[key] = int(value.split()[0]) * 1024
    return values['MemTotal'], values['MemAvailable']


def wait_status(runtime, phase, **fields):
    path = Path(runtime) / 'fullft_host_status' / (str(os.getpid()) + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    value = dict(pid=os.getpid(), phase=phase, updated=time.time(), **fields)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def project_usage():
    relative = Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1]
    own = Path('/sys/fs/cgroup') / relative.lstrip('/')
    if own.name.endswith('.service'):
        usage = {}
        for group in own.parent.iterdir():
            if group.name.startswith(('coretrace-', 'mechanism-gpu2-', 'partial-agent')):
                path = group / 'memory.current'
                if path.exists():
                    usage[str(group)] = int(path.read_text())
        return str(own), usage
    # Standalone CLI: at least account the complete current user cgroup.
    path = own / 'memory.current'
    return str(own), {str(own): int(path.read_text())}


@contextlib.contextmanager
def admit(runtime, extra_bytes, *, reserve_bytes=4 * GIB):
    runtime = Path(runtime)
    runtime.mkdir(parents=True, exist_ok=True)
    leases_path = runtime / 'fullft_memory_leases.json'
    identity = str(os.getpid())
    start_ticks = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
    # A completed epoch/evaluation may leave multiple GiB in free pinned-host
    # and malloc caches. Do not count these as indispensable model memory or
    # let them block the next seed indefinitely. Live tensors are unaffected.
    reclaim_unused_host_cache()

    def live(lease):
        p = Path('/proc', str(lease['pid']), 'stat')
        try:
            fields = p.read_text().rsplit(')', 1)[1].split()
            return fields[0] != 'Z' and fields[19] == lease['start_ticks']
        except FileNotFoundError:
            return False

    def save(leases):
        tmp = leases_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(leases, indent=2) + '\n')
        tmp.replace(leases_path)

    with (runtime / 'fullft_memory_admission.lock').open('a') as gate:
        waiting = False
        cache_reclaim_attempted = False
        while True:
            fcntl.flock(gate, fcntl.LOCK_EX)
            leases = json.loads(leases_path.read_text()) if leases_path.exists() else {}
            leases = {key: value for key, value in leases.items() if live(value)}
            group, usage = project_usage()
            # Account a pre-existing legacy training job which acquired its
            # mutex before this admission scheme was introduced. Its measured
            # cgroup high-water mark covers the gradient-allocation cycle.
            leased_groups = {x['cgroup'] for x in leases.values()}
            for status in runtime.glob('*/status.json'):
                record = json.loads(status.read_text())
                if (record.get('phase') != 'RUNNING'
                        or Path(record.get('script', '')).name != 'fullft_train.py'):
                    continue
                pid = record.get('pid')
                host_status = runtime / 'fullft_host_status' / (str(pid) + '.json')
                if host_status.exists():
                    phase = json.loads(host_status.read_text()).get('phase', '')
                    if phase.startswith('WAITING_') or phase == 'RELEASED':
                        continue
                try:
                    if Path('/proc', str(pid), 'wchan').read_text().strip() == 'locks_lock_inode_wait':
                        continue
                    rel = Path('/proc', str(pid), 'cgroup').read_text().strip().split('::', 1)[1]
                except FileNotFoundError:
                    continue
                legacy = Path('/sys/fs/cgroup') / rel.lstrip('/')
                if str(legacy) != group and str(legacy) not in leased_groups:
                    peak = legacy / 'memory.peak'
                    if peak.exists():
                        usage[str(legacy)] = max(usage.get(str(legacy), 0), int(peak.read_text()))
            total, available = system_memory()
            lease = dict(pid=os.getpid(), start_ticks=start_ticks, cgroup=group,
                         baseline_bytes=usage.get(group, 0), extra_bytes=extra_bytes)
            projected = projected_memory(usage, list(leases.values()) + [lease])
            allowed = projected <= total // 2 - reserve_bytes
            allowed = allowed and extra_bytes <= available - max(reserve_bytes, total // 20)
            if allowed:
                leases[identity] = lease
                save(leases)
                fcntl.flock(gate, fcntl.LOCK_UN)
                print(json.dumps(dict(status='ADMITTED_FULLFT_HOST_MEMORY',
                                      projected_project_GiB=projected / GIB,
                                      project_limit_GiB=(total // 2) / GIB)), flush=True)
                wait_status(runtime, 'ADMITTED', projected_bytes=projected,
                            limit_bytes=total // 2)
                break
            save(leases)
            fcntl.flock(gate, fcntl.LOCK_UN)
            if not cache_reclaim_attempted:
                cache_reclaim_attempted = True
                wanted = max(0, projected - (total // 2 - reserve_bytes)) + GIB
                reclaimed = reclaim_clean_file_cache(group, wanted)
                if reclaimed:
                    print(json.dumps(dict(status='RECLAIMED_UNUSED_SERVICE_FILE_CACHE',
                                          bytes=reclaimed)), flush=True)
                    continue
            if not waiting:
                print(json.dumps(dict(status='WAITING_PROJECT_HOST_MEMORY',
                                      projected_project_GiB=projected / GIB)), flush=True)
                waiting = True
            wait_status(runtime, 'WAITING_PROJECT_MEMORY', projected_bytes=projected,
                        limit_bytes=total // 2)
            time.sleep(5)
        try:
            yield
        finally:
            fcntl.flock(gate, fcntl.LOCK_EX)
            leases = json.loads(leases_path.read_text()) if leases_path.exists() else {}
            leases.pop(identity, None)
            save(leases)
            fcntl.flock(gate, fcntl.LOCK_UN)
            wait_status(runtime, 'RELEASED')
