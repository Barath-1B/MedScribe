"""Stage 4 — Keyword-weighted Topic Classification."""

import re
import time
from collections import Counter

TOPIC_KEYWORDS = {
    "Anatomy": {
        "high": ["anterior","posterior","lateral","medial","superior","inferior",
                 "proximal","distal","dorsal","ventral","cranial","caudal",
                 "femur","tibia","fibula","humerus","radius","ulna","scapula",
                 "clavicle","sternum","vertebra","vertebrae","peritoneum",
                 "pleura","pericardium","meninges","fascia","tendon","ligament",
                 "foramen","fossa","innervation"],
        "medium": ["bone","muscle","nerve","artery","vein","organ","tissue",
                   "joint","cartilage","membrane"],
    },
    "Pharmacology": {
        "high": ["metformin","insulin","atorvastatin","lisinopril","amlodipine",
                 "omeprazole","sertraline","warfarin","amoxicillin","ciprofloxacin",
                 "pharmacokinetics","pharmacodynamics","bioavailability","half-life",
                 "contraindication","dosage","agonist","antagonist","receptor",
                 "inhibitor","therapeutic","toxicity","adverse"],
        "medium": ["drug","medication","dose","tablet","capsule","oral",
                   "intravenous","prescription","enzyme","channel","blocker"],
    },
    "Pathology": {
        "high": ["inflammation","necrosis","apoptosis","hyperplasia","hypertrophy",
                 "atrophy","metaplasia","dysplasia","neoplasia","carcinoma",
                 "sarcoma","lymphoma","leukemia","thrombosis","embolism",
                 "infarction","ischemia","hemorrhage","fibrosis","cirrhosis",
                 "stenosis","aneurysm","atherosclerosis","granuloma","biopsy",
                 "histology","metastasis"],
        "medium": ["tumor","cancer","benign","malignant","lesion","nodule",
                   "mass","cyst","polyp","swelling"],
    },
    "Physiology": {
        "high": ["homeostasis","depolarization","repolarization","neurotransmitter",
                 "acetylcholine","serotonin","glomerular","filtration","reabsorption",
                 "perfusion","ventilation","oxygenation","systolic","diastolic",
                 "preload","afterload","contractility","ejection","baroreceptor",
                 "chemoreceptor","osmolarity","compliance","resistance"],
        "medium": ["heart-rate","respiratory","kidney","liver","hormonal",
                   "feedback","regulation","stimulus","response","reflex"],
    },
    "Microbiology": {
        "high": ["bacteria","bacterial","virus","viral","fungal","fungus",
                 "parasite","gram-positive","gram-negative","staphylococcus",
                 "streptococcus","escherichia","salmonella","mycobacterium",
                 "clostridium","pseudomonas","candida","aspergillus",
                 "antibiotic","antimicrobial","resistance","susceptibility",
                 "biofilm","pathogen","virulence","toxin","endotoxin","exotoxin"],
        "medium": ["infection","colony","growth","medium","agar",
                   "incubation","microscopy","staining"],
    },
    "Biochemistry": {
        "high": ["glycolysis","krebs","citric-acid","electron-transport",
                 "oxidative-phosphorylation","atp","nadh","fadh2",
                 "gluconeogenesis","glycogenolysis","lipolysis","lipogenesis",
                 "beta-oxidation","ketogenesis","urea-cycle","amino-acid",
                 "nucleotide","michaelis-menten","allosteric","competitive",
                 "noncompetitive","denaturation","phosphorylation",
                 "transcription","translation","replication","dna","rna",
                 "mrna","trna","ribosome","polymerase"],
        "medium": ["protein","carbohydrate","lipid","metabolism","pathway",
                   "reaction","catalysis","synthesis"],
    },
}


def classify_topic(text: str) -> dict:
    """Classify text into one of 6 clinical topics using keyword scoring."""
    start = time.time()
    words = re.findall(r'[a-z][a-z0-9-]+', text.lower())
    ws = set(words)
    wc = Counter(words)

    scores = {}
    for topic, kw in TOPIC_KEYWORDS.items():
        score  = sum(3.0 * wc.get(k, 0) for k in kw["high"]   if k in ws)
        score += sum(1.0 * wc.get(k, 0) for k in kw["medium"] if k in ws)
        scores[topic] = round(score, 2)

    total = sum(scores.values())
    if total > 0:
        conf = {t: round(v / total, 4) for t, v in scores.items()}
    else:
        conf = {t: round(1 / len(scores), 4) for t in scores}

    predicted = max(scores, key=scores.get) if total > 0 else "Unknown"
    return {
        "predicted_topic": predicted,
        "confidence": conf.get(predicted, 0.0),
        "all_scores": scores,
        "all_confidences": conf,
        "processing_time_ms": round((time.time() - start) * 1000, 2),
    }
