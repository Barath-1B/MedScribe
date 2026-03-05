"""
OCR utilities: Tesseract setup, FUNSD ground-truth extraction, text normalisation.
"""

import re
import json
from pathlib import Path

from PIL import Image
import pytesseract

# ── Paths (relative to project root, 3 levels up from backend/app/pipeline/) ─
_PROJECT_ROOT = Path(__file__).parents[3]
_LOCAL_TESSERACT = _PROJECT_ROOT / "Tesseract" / "tesseract.exe"
if _LOCAL_TESSERACT.is_file():
    pytesseract.pytesseract.tesseract_cmd = str(_LOCAL_TESSERACT)

DS1_IMAGES      = _PROJECT_ROOT / "ds-FUNSD" / "dataset" / "testing_data" / "images"
DS1_ANNOTATIONS = _PROJECT_ROOT / "ds-FUNSD" / "dataset" / "testing_data" / "annotations"


def normalise(text: str) -> str:
    """Collapse whitespace and lowercase."""
    return re.sub(r"\s+", " ", text.strip().lower())


def tokenise(text: str) -> list:
    """Split on whitespace."""
    return text.split()


def gt_from_funsd_json(json_path: Path) -> str:
    """
    Extract ground-truth text from a FUNSD annotation JSON.
    Fields are sorted top-to-bottom, left-to-right by bounding box.
    """
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


def run_ocr(image_path) -> str:
    """Run Tesseract on an image and return the extracted text."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, config="--psm 6")
