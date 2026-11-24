"""Immutable corpus readers and caller-supplied native tokenization."""
from .frozen_loader import FrozenDataset
from .tokenization import tokenize_prompt
__all__ = ['FrozenDataset', 'tokenize_prompt']
