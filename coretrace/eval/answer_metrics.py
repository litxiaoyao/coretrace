"""Official 2Wiki-MultihopQA v1.1 answer metrics (adapted from HotpotQA).
Functions below are verbatim from the original evaluator.
"""
import re, string
from collections import Counter

def normalize_answer(s):

    def remove_articles(text):
        return re.sub('\\b(a|an|the)\\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join((ch for ch in text if ch not in exclude))

    def lower(text):
        return text.lower()
    return white_space_fix(remove_articles(remove_punc(lower(s))))

def f1_score(prediction, ground_truth):
    normalized_prediction = normalize_answer(prediction)
    normalized_ground_truth = normalize_answer(ground_truth)
    ZERO_METRIC = (0, 0, 0)
    if normalized_prediction in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC
    if normalized_ground_truth in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC
    prediction_tokens = normalized_prediction.split()
    ground_truth_tokens = normalized_ground_truth.split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return ZERO_METRIC
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return (f1, precision, recall)

def exact_match_score(prediction, ground_truth):
    return normalize_answer(prediction) == normalize_answer(ground_truth)

def eval_answer(prediction, gold):
    em = exact_match_score(prediction, gold)
    f1, prec, recall = f1_score(prediction, gold)
    return (em, f1, prec, recall)

def update_answer(metrics, prediction, golds):
    max_em, max_f1, max_prec, max_recall = (0, 0, 0, 0)
    for gold in golds:
        em, f1, prec, recall = eval_answer(prediction, gold)
        max_em = max(max_em, em)
        max_f1 = max(max_f1, f1)
        max_prec = max(max_prec, prec)
        max_recall = max(max_recall, recall)
    metrics['em'] += float(max_em)
    metrics['f1'] += max_f1
    metrics['prec'] += max_prec
    metrics['recall'] += max_recall
    return (max_em, max_prec, max_recall)

def score_answer(answer, gold_aliases):
    golds = list(gold_aliases)
    if not golds:
        raise ValueError('At least one fixed gold alias required')
    metrics = dict(em=0.0, f1=0.0, prec=0.0, recall=0.0)
    update_answer(metrics, answer, golds)
    return metrics
