"""Refresh evaluation helpers between resident jobs without reloading weights."""
import argparse
import importlib
import json
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.parse_args()
    names = ['coretrace.models.scoped_rollback',
             'coretrace.models.deployment',
             'coretrace.eval.summarize',
             'coretrace.eval.batched_inference',
             'coretrace.eval.batched_mmlu',
             'coretrace.eval.batched_qa']
    for name in names:
        if name in sys.modules:
            importlib.reload(sys.modules[name])
        else:
            importlib.import_module(name)
    from coretrace.models.deployment import DeploymentBody
    assert hasattr(DeploymentBody, 'batch_session')
    print(json.dumps({'status': 'COMPLETE_RUNTIME_REFRESH', 'modules': names,
                      'model_weights_reloaded': False}))

if __name__ == '__main__':
    main()
