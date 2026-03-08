# Plan: Switch to Handwritten Dataset + Image Upload + Fix Experiments

## Problem
1. Current dataset (ds-FUNSD) is **printed forms**, not handwritten medical notes
2. Upload page only accepts **text paste** — no image upload
3. Experiment section has **bugs** (chart data keys mismatch, no real OCR mode)

## Solution Overview
- Switch primary analysis to use **ds-HF-MedicalRecords** (100 real handwritten prescriptions)
- Redesign Upload page: **upload image → OCR preview → edit ground truth → save**
- Fix Experiment page to support **real OCR mode** (use actual Tesseract output vs ground truth)

---

## Phase 1: Backend — Model + Storage Changes

### 1a. Update `GroundTruthNote` model (`backend/app/models.py`)
- Add `ocr_text` column (Text, nullable) — stores Tesseract's raw output
- Add `ocr_method` column (String, nullable) — "tesseract" or "manual"
- `image_path` already exists (nullable)

### 1b. Create uploads directory
- `backend/uploads/` for user-uploaded images
- Add to `.gitignore`

---

## Phase 2: Backend — New OCR + Upload Routes

### 2a. Add OCR preview endpoint (`backend/app/routes/notes.py`)
- `POST /api/notes/ocr-preview` — accepts image file, runs Tesseract, returns OCR text (doesn't save)
- Returns `{ocr_text: "...", image_filename: "..."}` so frontend can show preview

### 2b. Update create note endpoint (`backend/app/routes/notes.py`)
- `POST /api/notes` — now accepts optional image file + ocr_text + ground truth
- If image provided: save to `backend/uploads/`, store path
- Saves both `ocr_text` (what Tesseract read) and `true_text` (correct ground truth)

### 2c. Add dataset gallery endpoint (`backend/app/routes/notes.py`)
- `GET /api/datasets/gallery` — returns list of ds-HF-MedicalRecords images with their medicine labels
- Lets frontend show a browsable gallery of handwritten prescriptions

### 2d. Serve uploaded images (`backend/app/routes/documents.py`)
- `GET /api/uploads/{filename}/image` — serves images from `backend/uploads/`
- `GET /api/datasets/{dataset}/{filename}/image` — serves images from any ds-* folder

---

## Phase 3: Backend — Fix Experiments

### 3a. Update experiments route (`backend/app/routes/experiments.py`)
- When running pipeline, check if note has `ocr_text` (real OCR)
- If yes AND error_rate == 0: pass `ocr_text` to `run_pipeline()` for real OCR mode
- If error_rate > 0: still use error injection on `true_text` (simulated degradation)

### 3b. Update notes list to include ocr_text presence
- Notes list should indicate whether a note has real OCR text (for UI display)

---

## Phase 4: Backend — Switch Analysis to Handwritten Dataset

### 4a. Update `backend/app/pipeline/ocr.py`
- Add `DS_HF_IMAGES` and `DS_HF_GT` paths for ds-HF-MedicalRecords
- Keep FUNSD paths as secondary/legacy

### 4b. Update `backend/app/services/analysis_service.py`
- `get_all_documents()` now processes ds-HF-MedicalRecords (100 handwritten images)
- Ground truth = medicine names from `ground_truth.json`
- OCR = Tesseract on each image
- CER/WER computed on medicine name extraction

### 4c. Update `backend/app/routes/documents.py`
- Image serving now points to ds-HF-MedicalRecords images

---

## Phase 5: Frontend — Redesign Upload Page

### 5a. Rewrite `frontend/src/pages/Upload.jsx`
New layout with two sections:

**Section A: Upload New Image**
- File input (accept image/*)
- "Run OCR" button → calls `/api/notes/ocr-preview`
- Shows: uploaded image preview + OCR text result side by side
- Editable ground truth textarea (user types/pastes correct text)
- Title, Topic, Summary fields
- "Save Note" button

**Section B: Browse Dataset Gallery**
- Grid of thumbnails from ds-HF-MedicalRecords
- Click image → auto-fills OCR preview (runs Tesseract on that image)
- Shows known medicine labels as reference ground truth
- "Use This Image" button to populate the upload form

**Section C: Existing Notes (below)**
- List of saved notes with image thumbnails, OCR/GT preview, delete button

---

## Phase 6: Frontend — Fix Experiment Page

### 6a. Fix `frontend/src/pages/Experiment.jsx`
- Fix chart data: currently looks for `error_injection_cer` / `spell_correction_cer` but data has `ocr_cer` / `spell_correction_cer` pattern from stage_results
- Add badge showing "Real OCR" vs "Simulated" for each experiment
- Fix the bar chart to correctly extract CER from stage_results array
- Show snowball data: CER at each stage in a grouped/stacked view

---

## Phase 7: Frontend — Update Other Pages

### 7a. Update Inspector (`frontend/src/pages/Inspector.jsx`)
- Now loads ds-HF-MedicalRecords documents instead of FUNSD

### 7b. Update Overview, Pipeline, PerDocument pages
- These use `/api/analysis` which will now return ds-HF-MedicalRecords data
- No code changes needed if analysis_service returns same shape

---

## Files Changed Summary

| File | Change |
|------|--------|
| `backend/app/models.py` | Add ocr_text, ocr_method columns |
| `backend/app/routes/notes.py` | OCR preview endpoint, image upload, dataset gallery |
| `backend/app/routes/documents.py` | Serve uploaded + dataset images |
| `backend/app/routes/experiments.py` | Pass ocr_text for real OCR mode |
| `backend/app/pipeline/ocr.py` | Add ds-HF-MedicalRecords paths |
| `backend/app/services/analysis_service.py` | Switch to ds-HF-MedicalRecords |
| `frontend/src/pages/Upload.jsx` | Full rewrite: image upload + OCR + gallery |
| `frontend/src/pages/Experiment.jsx` | Fix chart data, add real OCR badge |
| `frontend/src/pages/Inspector.jsx` | Point to new dataset |
| `frontend/src/App.css` | Add gallery grid, image preview styles |
| `.gitignore` | Add backend/uploads/ |
