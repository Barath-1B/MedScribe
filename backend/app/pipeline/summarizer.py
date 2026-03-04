"""Stage 3 — Extractive Summarization (TF-IDF with medical term boosting)."""

import re
import math
import time
from collections import Counter

_STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "to", "of", "in", "for", "on", "with", "at",
    "by", "from", "as", "into", "through", "before", "after", "this",
    "that", "these", "those", "it", "its", "he", "she", "they", "we",
    "you", "i", "and", "or", "but", "not", "so", "if", "about", "up", "out",
}

_BOOST = {
    "diagnosis", "treatment", "patient", "clinical", "symptoms", "disease",
    "medication", "therapy", "prognosis", "etiology", "pathology", "chronic",
    "acute", "syndrome", "contraindication", "dosage", "adverse", "cardiac",
    "renal", "hepatic", "pulmonary", "neurological", "infection",
    "inflammation", "hypertension", "diabetes", "carcinoma", "hemorrhage",
    "fracture",
}


def _split_sents(text):
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    return [s.strip() for s in sents if len(s.strip()) > 10]


def _tw(text):
    return [w for w in re.findall(r'[a-z][a-z0-9-]*', text.lower())
            if w not in _STOP and len(w) > 1]


def extractive_summarize(text: str, n_sentences: int = 5) -> dict:
    """Summarize text by extracting top-N highest-scoring sentences."""
    start = time.time()
    sents = _split_sents(text)
    if not sents:
        return {"text": "", "num_input_sentences": 0,
                "num_output_sentences": 0, "processing_time_ms": 0}

    n_sentences = min(n_sentences, len(sents))
    sw = [_tw(s) for s in sents]
    all_w = [w for ws in sw for w in ws]
    n_s = len(sw)

    tf = Counter(all_w)
    total = max(len(all_w), 1)
    tf = {w: c / total for w, c in tf.items()}

    df = Counter()
    for words in sw:
        for w in set(words):
            df[w] += 1
    idf = {w: math.log(n_s / (1 + c)) for w, c in df.items()}

    scores = []
    for i, (s, words) in enumerate(zip(sents, sw)):
        if not words:
            scores.append((i, 0.0, s))
            continue
        score = sum(tf.get(w, 0) * idf.get(w, 0) * (1.5 if w in _BOOST else 1.0)
                    for w in words) / len(words)
        if i == 0:
            score *= 1.3
        elif i == len(sents) - 1:
            score *= 1.1
        scores.append((i, score, s))

    top = sorted(scores, key=lambda x: x[1], reverse=True)[:n_sentences]
    top = sorted(top, key=lambda x: x[0])

    return {
        "text": "\n".join(f"* {t[2].strip()}" for t in top),
        "num_input_sentences": len(sents),
        "num_output_sentences": n_sentences,
        "processing_time_ms": round((time.time() - start) * 1000, 2),
    }
