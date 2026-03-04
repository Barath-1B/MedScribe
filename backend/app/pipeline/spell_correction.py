"""Stage 2 — Medical Spell Correction."""

import re
import time

MEDICAL_DICTIONARY = {
    "anterior", "posterior", "lateral", "medial", "superior", "inferior",
    "proximal", "distal", "dorsal", "ventral", "cranial", "caudal",
    "abdomen", "thorax", "pelvis", "femur", "tibia", "fibula", "humerus",
    "radius", "ulna", "scapula", "clavicle", "sternum", "vertebra",
    "vertebrae", "cervical", "thoracic", "lumbar", "sacral", "diaphragm",
    "peritoneum", "pleura", "pericardium", "meninges", "cerebrum",
    "cerebellum", "brainstem", "thalamus", "hypothalamus", "hippocampus",
    "cortex", "medulla", "pons",
    "metformin", "insulin", "atorvastatin", "lisinopril", "amlodipine",
    "metoprolol", "omeprazole", "levothyroxine", "losartan", "gabapentin",
    "hydrochlorothiazide", "sertraline", "simvastatin", "escitalopram",
    "rosuvastatin", "bupropion", "pantoprazole", "acetaminophen", "ibuprofen",
    "aspirin", "warfarin", "clopidogrel", "heparin", "enoxaparin",
    "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline",
    "cephalosporin", "penicillin", "vancomycin", "fluoxetine", "diazepam",
    "lorazepam", "prednisone", "dexamethasone", "albuterol", "fluticasone",
    "epinephrine", "norepinephrine", "dopamine", "morphine", "fentanyl",
    "naloxone", "pharmacokinetics", "pharmacodynamics", "bioavailability",
    "therapeutic", "contraindication", "dosage", "adverse", "agonist",
    "antagonist", "receptor", "inhibitor", "enzyme",
    "inflammation", "necrosis", "apoptosis", "hyperplasia", "hypertrophy",
    "atrophy", "metaplasia", "dysplasia", "neoplasia", "carcinoma", "sarcoma",
    "lymphoma", "leukemia", "melanoma", "adenoma", "thrombosis", "embolism",
    "infarction", "ischemia", "hemorrhage", "edema", "fibrosis", "cirrhosis",
    "stenosis", "aneurysm", "atherosclerosis", "hypertension", "hypotension",
    "tachycardia", "bradycardia", "arrhythmia", "diabetes", "mellitus",
    "hypothyroidism", "hyperthyroidism", "anemia", "pneumonia", "bronchitis",
    "asthma", "emphysema", "tuberculosis", "hepatitis", "pancreatitis",
    "cholecystitis", "appendicitis", "meningitis", "encephalitis", "nephritis",
    "glomerulonephritis", "cystitis",
    "homeostasis", "metabolism", "catabolism", "anabolism", "mitosis",
    "meiosis", "depolarization", "repolarization", "synapse",
    "neurotransmitter", "acetylcholine", "serotonin", "cortisol",
    "aldosterone", "testosterone", "estrogen", "progesterone", "erythrocyte",
    "leukocyte", "thrombocyte", "platelet", "hemoglobin", "fibrinogen",
    "albumin", "glomerular", "filtration", "reabsorption", "secretion",
    "perfusion", "ventilation", "oxygenation", "cardiac", "systolic",
    "diastolic", "preload", "afterload", "contractility", "ejection",
    "diagnosis", "prognosis", "etiology", "pathogenesis", "symptom",
    "syndrome", "acute", "chronic", "benign", "malignant", "idiopathic",
    "bilateral", "unilateral", "systemic", "peripheral", "central",
    "congenital", "acquired", "hereditary", "prophylaxis", "palliative",
    "curative", "clinical", "subclinical", "asymptomatic", "patient",
    "physician", "prescription", "medication", "treatment",
}

_DICT_LOWER = {w.lower() for w in MEDICAL_DICTIONARY}


def _levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if not s2:
        return len(s1)
    prev = range(len(s2) + 1)
    for c1 in s1:
        curr = [prev[0] + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(curr[-1] + 1, prev[j + 1] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def _find_correction(word: str, max_dist: int = 2) -> str:
    wl = word.lower()
    if wl in _DICT_LOWER:
        return word
    best, best_d = word, max_dist + 1
    for term in _DICT_LOWER:
        if abs(len(term) - len(wl)) > max_dist:
            continue
        d = _levenshtein(wl, term)
        if d < best_d:
            best_d, best = d, term
            if d == 1:
                break
    if best_d <= max_dist:
        return (best[0].upper() + best[1:]) if word and word[0].isupper() else best
    return word


def spell_correct(text: str) -> dict:
    """Apply medical spell correction. Returns corrected text + stats."""
    start = time.time()
    tokens = re.findall(r'\S+|\s+', text)
    corrected, n_fixed, log = [], 0, []

    for tok in tokens:
        if not tok.strip() or not any(c.isalpha() for c in tok):
            corrected.append(tok)
            continue
        pre, suf, core = "", "", tok
        while core and not core[0].isalpha():
            pre += core[0]; core = core[1:]
        while core and not core[-1].isalpha():
            suf = core[-1] + suf; core = core[:-1]
        if len(core) < 3:
            corrected.append(tok)
            continue
        fixed = _find_correction(core)
        if fixed != core:
            n_fixed += 1
            log.append({"original": core, "corrected": fixed})
        corrected.append(pre + fixed + suf)

    return {
        "text": "".join(corrected),
        "corrections_made": n_fixed,
        "corrections_log": log,
        "processing_time_ms": round((time.time() - start) * 1000, 2),
    }
