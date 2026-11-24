"""Temporarily apply selected-head slices and an optional role-specific rollback."""
import gc
import json
from pathlib import Path
from contextlib import nullcontext
from .head_slices import HeadSliceQKVO
from .scoped_rollback import SavedProjectionUpdateReversionLayersSession

class DeploymentBody:
    def __init__(self, model, directory, *, scope=None, expected_dataset_version=None,
                 expected_model_identity=None):
        self.model = model
        self.directory = Path(directory)
        self.scope = scope
        self.expected_dataset = expected_dataset_version
        self.adapter = None
        self.restore_report = None

    def __enter__(self):
        from safetensors.torch import load_file
        if getattr(self.model, '_headslice_qkvo_merged_owner', None) is not None:
            raise ValueError('Enter with the unmodified base model')
        self.manifest = json.loads((self.directory / 'training.json').read_text())
        if self.manifest['status'] != 'COMPLETE_SELECTED_HEAD_TRAINING':
            raise ValueError('Training is incomplete')
        if self.expected_dataset and self.manifest['dataset_version'] != self.expected_dataset:
            raise ValueError('Checkpoint and dataset versions differ')
        self.model.eval().requires_grad_(False)
        try:
            self.adapter = HeadSliceQKVO(self.model, self.manifest['head_map'])
            self.adapter.load_state_dict(load_file(str(self.directory / 'slices_final.safetensors'), device='cpu'))
            self.adapter.requires_grad_(False)
            self.adapter.merge()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def session(self, entry):
        if self.adapter is None or not self.adapter.merged:
            raise ValueError('Enter deployment context first')
        if not self.scope or not self.scope.get('role'):
            return nullcontext()
        layers = self.scope.get('layers', 'selected')
        if layers == 'selected':
            layers = list(map(int, self.adapter.head_map))
        return SavedProjectionUpdateReversionLayersSession(
            self.adapter, prompt_length=len(entry['prompt_ids']),
            question_positions=entry['question_positions'], components=self.scope['components'],
            layers=layers, role=self.scope['role'])

    def __exit__(self, *args):
        if self.adapter is not None:
            self.adapter.unmerge()
            self.adapter.remove()
        self.adapter = None
        gc.collect()
        self.restore_report = dict(slices_unmerged=True)
        return False

    def batch_session(self, entries, *, padded_length):
        """Optional independent left-padded prefill rollback for batched MCQ."""
        from .scoped_rollback import BatchedProjectionUpdateReversionLayersSession
        if self.adapter is None or not self.adapter.merged:
            raise ValueError('Enter deployment context first')
        if not self.scope or not self.scope.get('role'):
            return nullcontext()
        layers = self.scope.get('layers', 'selected')
        if layers == 'selected':
            layers = list(map(int, self.adapter.head_map))
        return BatchedProjectionUpdateReversionLayersSession(
            self.adapter, prompt_lengths=[len(e['prompt_ids']) for e in entries],
            question_positions=[e['question_positions'] for e in entries],
            padded_length=padded_length, components=self.scope['components'],
            layers=layers, role=self.scope['role'])
