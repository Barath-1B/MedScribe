"""
OCR utilities: TrOCR (handwriting), Tesseract (fallback), ground-truth extraction.
Supports HF-MedicalRecords and DoctorHandwritingBD (handwritten prescriptions).
"""

import csv
import os
import re
import json
import logging
from pathlib import Path

# ── Set HuggingFace cache to D: drive BEFORE importing transformers ──────────
_PROJECT_ROOT = Path(__file__).parents[3]
os.environ.setdefault("HF_HOME", str(_PROJECT_ROOT / ".hf_cache"))

import cv2
import numpy as np
from PIL import Image

import pytesseract

log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_LOCAL_TESSERACT = _PROJECT_ROOT / "Tesseract" / "tesseract.exe"
if _LOCAL_TESSERACT.is_file():
    pytesseract.pytesseract.tesseract_cmd = str(_LOCAL_TESSERACT)

# Primary dataset: handwritten medical records (100 images)
DS_HF_IMAGES = _PROJECT_ROOT / "ds-HF-MedicalRecords" / "images"
DS_HF_GT     = _PROJECT_ROOT / "ds-HF-MedicalRecords" / "ground_truth.json"

# Secondary dataset: doctor handwriting (89 images)
DS_DOC_IMAGES = _PROJECT_ROOT / "ds-DoctorHandwritingBD" / "img" / "img"
DS_DOC_LABELS = _PROJECT_ROOT / "ds-DoctorHandwritingBD" / "doctor_handwriting_labels.csv"

# Legacy dataset: FUNSD printed forms
DS1_IMAGES      = _PROJECT_ROOT / "ds-FUNSD" / "dataset" / "testing_data" / "images"
DS1_ANNOTATIONS = _PROJECT_ROOT / "ds-FUNSD" / "dataset" / "testing_data" / "annotations"


# ── TrOCR model (lazy-loaded) ────────────────────────────────────────────────

_trocr_processor = None
_trocr_model = None


def _load_trocr():
    """Lazy-load TrOCR model and processor (downloads ~1GB on first use)."""
    global _trocr_processor, _trocr_model
    if _trocr_processor is not None:
        return

    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    model_name = "microsoft/trocr-base-handwritten"
    log.info("Loading TrOCR model: %s (first run downloads ~1GB)", model_name)
    _trocr_processor = TrOCRProcessor.from_pretrained(model_name)
    _trocr_model = VisionEncoderDecoderModel.from_pretrained(model_name)
    _trocr_model.eval()
    log.info("TrOCR model loaded successfully")


# ── Line segmentation ────────────────────────────────────────────────────────

def _segment_lines(image: np.ndarray, min_line_height: int = 15) -> list[np.ndarray]:
    """
    Segment a page image into individual text line crops using
    horizontal projection profile.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Binarize (invert so text is white)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Horizontal projection: sum of white pixels per row
    h_proj = np.sum(binary, axis=1)

    # Find line boundaries: rows where projection > threshold
    threshold = np.max(h_proj) * 0.02
    in_line = h_proj > threshold

    lines = []
    start = None
    for i, val in enumerate(in_line):
        if val and start is None:
            start = i
        elif not val and start is not None:
            if i - start >= min_line_height:
                # Add some padding
                y0 = max(0, start - 5)
                y1 = min(image.shape[0], i + 5)
                lines.append(image[y0:y1, :])
            start = None

    # Handle last line
    if start is not None and len(image) - start >= min_line_height:
        y0 = max(0, start - 5)
        lines.append(image[y0:, :])

    # If no lines found, return the whole image as one line
    if not lines:
        lines = [image]

    return lines


# ── OCR engines ──────────────────────────────────────────────────────────────

def run_trocr(image_path: str) -> str:
    """
    Run TrOCR on a full-page image:
    1. Segment into text lines using horizontal projection
    2. Feed each line through TrOCR
    3. Join results
    """
    _load_trocr()

    img_cv = cv2.imread(str(image_path))
    if img_cv is None:
        raise ValueError(f"Cannot read image: {image_path}")

    line_crops = _segment_lines(img_cv)
    recognized_lines = []

    for crop in line_crops:
        # Convert BGR to RGB PIL image
        pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

        # Run TrOCR
        pixel_values = _trocr_processor(images=pil_img, return_tensors="pt").pixel_values
        import torch
        with torch.no_grad():
            generated_ids = _trocr_model.generate(pixel_values, max_new_tokens=128)
        text = _trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        text = text.strip()
        if text:
            recognized_lines.append(text)

    return "\n".join(recognized_lines)


def run_tesseract(image_path: str, psm: int = 6) -> str:
    """Run Tesseract OCR on an image (fallback for printed text)."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, config=f"--psm {psm}")


def run_ocr(image_path: str, psm: int = 6, engine: str = "trocr") -> str:
    """
    Run OCR on an image.
    engine: 'trocr' (default, best for handwriting) or 'tesseract' (fallback)
    """
    if engine == "trocr":
        try:
            return run_trocr(image_path)
        except Exception as e:
            log.warning("TrOCR failed, falling back to Tesseract: %s", e)
            return run_tesseract(image_path, psm)
    else:
        return run_tesseract(image_path, psm)


# ── Text utilities ───────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    """Collapse whitespace and lowercase."""
    return re.sub(r"\s+", " ", text.strip().lower())


def tokenise(text: str) -> list:
    """Split on whitespace."""
    return text.split()


# ── Ground truth loaders ─────────────────────────────────────────────────────

def gt_from_funsd_json(json_path: Path) -> str:
    """Extract ground-truth text from a FUNSD annotation JSON."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    fields = data.get("form", [])
    fields_sorted = sorted(fields, key=lambda item: (item["box"][1], item["box"][0]))
    tokens = [
        field.get("text", "").strip()
        for field in fields_sorted
        if field.get("text", "").strip()
    ]
    return " ".join(tokens)


def load_hf_ground_truth() -> list[dict]:
    """Load HF-MedicalRecords ground truth JSON."""
    if not DS_HF_GT.exists():
        return []
    with open(DS_HF_GT, encoding="utf-8") as f:
        return json.load(f)


def load_doctor_handwriting_gt() -> list[dict]:
    """Load DoctorHandwritingBD CSV labels → same format as HF ground truth."""
    if not DS_DOC_LABELS.exists():
        return []
    entries = []
    with open(DS_DOC_LABELS, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row.get("filename", "").strip()
            label = row.get("label", "").strip()
            if fname and label:
                entries.append({"filename": fname, "medicines": label})
    return entries
