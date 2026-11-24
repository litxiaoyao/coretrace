"""Execute a saved experiment queue, with independent workers and dependencies."""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--worker', required=True)
    parser.add_argument('--retry-failed', action='store_true')
    args = parser.parse_args()
    planpath = Path(args.plan).resolve()
    plan = json.loads(planpath.read_text())
    jobs = plan['jobs']
    ids = [job['id'] for job in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError('Queue job IDs must be unique')
    for job in jobs:
        if not set(job.get('requires', [])) <= set(ids):
            raise ValueError('Unknown queue dependency')
    state = planpath.parent / (planpath.stem + '_state')
    state.mkdir(exist_ok=True)
    import fcntl
    with (state / (args.worker + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        heartbeat = state / (args.worker + '_heartbeat.json')
        def pulse(phase, **fields):
            write(heartbeat, dict(worker=args.worker, controller_pid=os.getpid(),
                                  phase=phase, updated=time.time(), **fields))
        def status(identifier):
            path = state / (identifier + '.json')
            return json.loads(path.read_text()).get('status') if path.exists() else 'PENDING'
        for job in jobs:
            if job['worker'] != args.worker or status(job['id']) == 'COMPLETE':
                continue
            if status(job['id']) == 'FAILED' and not args.retry_failed:
                raise RuntimeError('Inspect failed job before retrying: ' + job['id'])
            dependencies = job.get('requires', [])
            waiting = False
            while not all(status(dependency) == 'COMPLETE' for dependency in dependencies):
                if any(status(dependency) == 'FAILED' for dependency in dependencies):
                    raise RuntimeError('Dependency failed for ' + job['id'])
                if not waiting:
                    print('WAITING', job['id'], dependencies, flush=True)
                    waiting = True
                pulse('WAITING_DEPENDENCIES', job=job['id'], requires=dependencies)
                time.sleep(2)
            path = state / (job['id'] + '.json')
            record = dict(job, status='RUNNING', controller_pid=os.getpid(), started=time.time())
            write(path, record)
            print('RUNNING', job['id'], flush=True)
            try:
                with subprocess.Popen(job['command'], cwd=plan['cwd']) as child:
                    while True:
                        pulse('RUNNING', job=job['id'], child_pid=child.pid)
                        try:
                            code = child.wait(timeout=10)
                            break
                        except subprocess.TimeoutExpired:
                            pass
                    if code:
                        raise subprocess.CalledProcessError(code, job['command'])
            except BaseException as error:
                record.update(status='FAILED', error=repr(error), finished=time.time())
                write(path, record)
                pulse('FAILED', job=job['id'], error=repr(error))
                raise
            record.update(status='COMPLETE', finished=time.time())
            write(path, record)
            print('COMPLETE', job['id'], flush=True)
        pulse('COMPLETE')

if __name__ == '__main__':
    main()
