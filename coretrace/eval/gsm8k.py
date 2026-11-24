"""GSM8K numeric accuracy, strict final-line format and diagnostics."""
import re
from decimal import Decimal, InvalidOperation
NUM = '[+-]?(?:(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?|\\.\\d+)'
FINAL = re.compile('^####\\s+(' + NUM + ')\\s*$')
OFFICIAL = re.compile('#### (\\-?[0-9\\.\\,]+)')

def canonical_numeric(text):
    try:
        x = Decimal(text.replace(',', '').strip())
        if not x.is_finite():
            return None
        return '0' if x == 0 else format(x.normalize(), 'f')
    except InvalidOperation:
        return None

def extract_final(text):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return None
    match = FINAL.fullmatch(lines[-1])
    return canonical_numeric(match.group(1)) if match else None

def extract_official_compatible(text):
    match = OFFICIAL.search(text)
    return match.group(1).strip().replace(',', '') if match else None

def score_answer(text, gold_numeric, *, generated_token_count=None, eos_complete=None, max_new_tokens=512):
    gold = canonical_numeric(gold_numeric)
    assert gold is not None
    pred = extract_final(text)
    official = extract_official_compatible(text)
    return dict(correct=bool(pred is not None and pred == gold), prediction_numeric=pred, gold_numeric=gold, format_failure=pred is None, official_compatible_numeric_correct=bool(official is not None and canonical_numeric(official) == gold), official_compatible_prediction=official, eos_complete=eos_complete, cutoff=bool(generated_token_count is not None and generated_token_count >= max_new_tokens and (eos_complete is False)), generated_token_count=generated_token_count)

def self_test():
    assert score_answer('Reasoning.\n#### 1,200', '1200')['correct']
    assert score_answer('Reasoning.\n#### 72.0', '72')['correct']
    assert score_answer('Reasoning.\n#### -0.5', '-.5')['correct']
    assert score_answer('Reasoning.\n#### +3', '3')['correct']
    assert score_answer('#### 72\nextra', '72')['format_failure']
    assert score_answer('The answer is72.', '72')['format_failure']
    assert not score_answer('#### 7', '72')['correct']
    assert score_answer('#### 72', '72', generated_token_count=512, eos_complete=False)['correct']
    assert score_answer('#### 72', '72', generated_token_count=512, eos_complete=False)['cutoff']
if __name__ == '__main__':
    self_test()
    print('GSM8K numeric/format/cutoff tests PASS')
