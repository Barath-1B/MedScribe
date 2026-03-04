"""
Evaluation metrics: CER, WER (with edit-op breakdown), error recovery rate, ROUGE.
"""

import re
import math
from collections import Counter

import Levenshtein as _lev

from app.pipeline.ocr import normalise, tokenise


# ── Detailed CER / WER ────────────────────────────────────────────────────────

def cer(reference: str, hypothesis: str) -> tuple:
    """
    Character Error Rate with full edit-op breakdown.
    Returns (rate_pct, info_dict).
    """
    ref_norm = normalise(reference)
    hyp_norm = normalise(hypothesis)
    if not ref_norm:
        return 0.0, {}

    ops = _lev.editops(hyp_norm, ref_norm)
    ins = sum(1 for o in ops if o[0] == "insert")
    dlt = sum(1 for o in ops if o[0] == "delete")
    sub = sum(1 for o in ops if o[0] == "replace")
    rate = len(ops) / len(ref_norm) * 100
    return rate, {
        "edit_dist": len(ops), "ins": ins, "del": dlt, "sub": sub,
        "ref_len": len(ref_norm),
    }


def wer(reference: str, hypothesis: str) -> tuple:
    """
    Word Error Rate with full edit-op breakdown.
    Returns (rate_pct, info_dict).
    """
    ref_words = tokenise(normalise(reference))
    hyp_words = tokenise(normalise(hypothesis))
    if not ref_words:
        return 0.0, {}

    ops = _lev.editops(hyp_words, ref_words)
    ins = sum(1 for o in ops if o[0] == "insert")
    dlt = sum(1 for o in ops if o[0] == "delete")
    sub = sum(1 for o in ops if o[0] == "replace")
    rate = len(ops) / len(ref_words) * 100
    return rate, {
        "edit_dist": len(ops), "ins": ins, "del": dlt, "sub": sub,
        "ref_words": len(ref_words),
    }


# ── Scalar helpers ────────────────────────────────────────────────────────────

def error_recovery_rate(cer_before: float, cer_after: float) -> float:
    """Fraction of OCR errors recovered by spell correction, as %."""
    if cer_before == 0:
        return 1.0
    return round((cer_before - cer_after) / cer_before * 100, 2)


# ── ROUGE ─────────────────────────────────────────────────────────────────────

def _tok(text: str) -> list:
    return re.findall(r'[a-z0-9]+', text.lower())

def _ngrams(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def _f1(p, r):
    return 2 * p * r / (p + r) if p + r else 0.0

def _rouge_n(ref, hyp, n):
    rt, ht = _tok(ref), _tok(hyp)
    rng, hng = _ngrams(rt, n), _ngrams(ht, n)
    if not rng or not hng:
        return 0.0
    rc, hc = Counter(rng), Counter(hng)
    overlap = sum(min(v, rc.get(k, 0)) for k, v in hc.items())
    return round(_f1(overlap / len(hng), overlap / len(rng)) * 100, 4)

def _lcs_len(x, y):
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = (dp[i-1][j-1] + 1
                        if x[i-1] == y[j-1]
                        else max(dp[i-1][j], dp[i][j-1]))
    return dp[m][n]

def _rouge_l(ref, hyp):
    rt, ht = _tok(ref), _tok(hyp)
    if not rt or not ht:
        return 0.0
    lcs = _lcs_len(rt, ht)
    return round(_f1(lcs / len(ht), lcs / len(rt)) * 100, 4)

def compute_rouge(reference: str, hypothesis: str) -> dict:
    """Compute ROUGE-1, ROUGE-2, ROUGE-L as percentage scores."""
    if not reference or not hypothesis:
        return {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0}
    return {
        "rouge_1": _rouge_n(reference, hypothesis, 1),
        "rouge_2": _rouge_n(reference, hypothesis, 2),
        "rouge_l": _rouge_l(reference, hypothesis),
    }
