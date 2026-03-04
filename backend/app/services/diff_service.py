"""
Diff service — generates colour-coded HTML diff between OCR and ground truth.
Ported from dashboard.py html_diff().
"""

import difflib
from app.pipeline.ocr import normalise


def html_diff(ocr_text: str, gt_text: str) -> str:
    """
    Word-level diff between OCR output and ground truth.
    Returns HTML with <span class="diff-add"> and <span class="diff-del"> spans.
    """
    ocr_words = normalise(ocr_text).split()
    gt_words = normalise(gt_text).split()
    matcher = difflib.SequenceMatcher(None, ocr_words, gt_words)
    parts = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            parts.append(" ".join(ocr_words[i1:i2]))
        elif tag == "replace":
            parts.append(f'<span class="diff-del">{" ".join(ocr_words[i1:i2])}</span>')
            parts.append(f'<span class="diff-add">{" ".join(gt_words[j1:j2])}</span>')
        elif tag == "delete":
            parts.append(f'<span class="diff-del">{" ".join(ocr_words[i1:i2])}</span>')
        elif tag == "insert":
            parts.append(f'<span class="diff-add">{" ".join(gt_words[j1:j2])}</span>')

    return " ".join(parts)
