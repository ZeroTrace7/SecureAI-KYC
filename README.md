# 🛡️ SecureAI-KYC — Intelligent Document Verification & Fraud Detection

**SecureAI-KYC** is a comprehensive, multi-agent forensic verification platform built to detect sophisticated document fraud. Developed for the **Document Forgery Detection Blue Team Challenge** at the National Hackathon, 2026.

Instead of relying on a single "black-box" machine learning model, SecureAI-KYC uses a deterministic, **stage-gated pipeline** that cross-validates visual, spatial, textual, and immutable data across **14 independent modules**, outputting an explainable fraud score and a downloadable PDF compliance report.

---

## 💻 Complete Technology Stack & Deep Dive

### Frontend (UI & Real-time Visualization)
| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 16 | React meta-framework with App Router for SSR and instant dashboard loading |
| **React** | 19 | Component-based UI with state management via Context API |
| **Tailwind CSS** | v4 | Utility-first CSS for rapid, consistent UI theming (light-mode SaaS design) |
| **Framer Motion** | 12.x | Spring-physics animations for real-time pipeline progression and micro-interactions |
| **jsPDF** | 4.x | Client-side PDF generation for XAI compliance reports (zero backend load) |
| **Lucide React** | 1.7 | Icon system for the dashboard UI |
| **TypeScript** | 5.x | Type-safe frontend with strict mode enabled |

### Backend (Core Logic & API)
| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.135 | High-performance async Python API with automatic OpenAPI docs |
| **Uvicorn** | 0.42 | ASGI server running the FastAPI application |
| **Python** | 3.11+ | Core language for AI/ML pipeline logic |
| **ThreadPoolExecutor** | stdlib | Fires all 8 forensic agents concurrently (cuts latency from ~40s to <5s) |
| **SQLite + SQLAlchemy** | 2.0 | Zero-dependency database for the Blockchain Hash Ledger and Audit Trail |
| **PyMuPDF (fitz)** | 1.27 | PDF-to-image conversion for uploaded PDF documents |
| **Loguru** | 0.7 | Structured, color-coded logging for pipeline debugging |

### AI, Machine Learning & Computer Vision
| Technology | Version | Purpose |
|---|---|---|
| **PyTorch** | 2.11 | Deep learning framework powering Deepfake and OCR models |
| **Hugging Face Transformers** | 5.4 | Model hub for loading pre-trained `.safetensors` checkpoints |
| **EasyOCR** | 1.7 | PyTorch-based OCR engine (locked to English-only for 40% speed boost) |
| **PyTesseract** | 0.3 | Fallback OCR engine if EasyOCR is unavailable |
| **OpenCV** | 4.13 | Image processing: blur detection (Laplacian), ELA computation, face extraction (Haar cascades), HSV segmentation, Hough circles |
| **Pillow (PIL)** | 12.x | Image I/O and perceptual hash computation |
| **Scikit-image** | 0.26 | Structural similarity (SSIM) for ELA variance mapping |
| **SciPy** | 1.17 | DCT (Discrete Cosine Transform) for double-JPEG compression detection |
| **NumPy** | 2.4 | Matrix operations for pixel-level forensic analysis |
| **FuzzyWuzzy + Levenshtein** | 0.18 | Fuzzy string matching for QR-OCR cross-validation (handles OCR noise) |
| **PyZbar** | 0.1.9 | 1D/2D barcode and QR code decoding from document images |
| **ImageHash** | 4.3+ | Perceptual hashing (pHash) for visual similarity resubmission detection |
| **Google Gemini API** | 2.0 Flash | LLM-powered Explainable AI (XAI) for plain-English compliance reports |

---

## 🏗️ Full System Pipeline (14 Modules, 7 Stages)

### STAGE 1–2 · INTAKE
| Module | File | How It Works |
|---|---|---|
| **Quality Gate** | `pipeline/quality_gate.py` | Pure OpenCV — no AI. Runs 4 checks: `Laplacian variance` for blur, `min resolution` (300px), `mean brightness` range (40–245), and `std deviation` for contrast. If any check fails, the document is instantly rejected before wasting GPU resources. |
| **Document Classifier** | `pipeline/classifier.py` | Rule-based regex engine. Scans OCR text for document-specific keywords (e.g., "UNIQUE IDENTIFICATION" → Aadhaar, "INCOME TAX" → PAN). Includes a `is_payslip_like()` fallback to catch misclassified salary slips using keywords like "basic pay", "gross", "deductions". |

### STAGE 3 · FORENSIC AGENTS (Run in Parallel)
All 8 agents below are fired **concurrently** inside a `ThreadPoolExecutor(max_workers=8)`. While the OCR is scanning text, PyTorch is simultaneously running deepfake inference, ELA is computing pixel differences, and the blockchain is querying the hash ledger.

| Agent | File | How It Works |
|---|---|---|
| **OCR Engine** | `agents/ocr_agent.py` | Uses a singleton `EasyOCR` reader pre-loaded at server startup (eliminates cold-start). Images are **downscaled to 800px max-side** via `cv2.resize` before OCR to exponentially reduce inference time. Extracts bounding boxes, text, and per-line confidence scores. Regex post-processing extracts structured fields (Name, DOB, UID, PAN number). |
| **ELA Pixel Analysis** | `agents/ela_agent.py` | Saves the image at JPEG quality 95, then computes the absolute pixel-level difference between the original and re-saved version. Inconsistent compression regions (e.g., a Photoshopped name pasted over an original) light up as bright hotspots on the ELA heatmap. Uses `scikit-image` for structural variance and outputs a normalized 0–1 tampering score. |
| **EXIF Metadata** | `agents/exif_agent.py` | Uses `exifread` to extract IPTC/EXIF headers. Flags: (1) Known editing software signatures (Photoshop, GIMP, Canva, DALL-E, Midjourney) via a curated blocklist, (2) Impossible timestamps (modified date before creation date), (3) Camera make/model metadata from synthetic generators. Outputs `clean`, `notable`, or `suspicious`. |
| **Deepfake Detector** | `agents/deepfake_agent.py` | Extracts the face from the document using OpenCV **Haar cascade classifiers** (`haarcascade_frontalface_default`). The cropped face (minimum 80px) is fed through a HuggingFace `image-classification` pipeline using the `dima806/deepfake_vs_real_image_detection` model (~350 MB, pre-loaded at startup). Outputs a 0–1 probability of synthetic generation. |
| **ML Forgery Engine** | `agents/ml_forgery_agent.py` | MobileNetV2-based classifier trained on forgery datasets. Provides a redundant visual signal alongside ELA. Currently disabled by feature flag (the model `kumaran-0188/image_forgery_detector` is TF/Keras-based, incompatible with the PyTorch pipeline). Re-enable when a PyTorch-native forgery model is available. |
| **Signature & Seal** | `agents/signature_seal_agent.py` | Three-phase analysis: (1) **Seal Detection** — HSV color-space segmentation isolates red/blue circular stamps, then `HoughCircles` validates circularity. (2) **Signature Detection** — Adaptive thresholding detects high-frequency ink strokes. (3) **Edge Forensics** — Sobel gradient analysis measures edge sharpness. Digitally pasted elements have unnaturally sharp, pixel-perfect edges compared to real ink bleeding into paper. |
| **Text Integrity** | `agents/text_integrity_agent.py` | Three-pronged analysis: (1) **Font Consistency** — Measures variance in OCR bounding-box character heights and spacing outliers. (2) **DCT Analysis** — Uses `scipy.fft.dctn` for frequency-domain peak detection to catch double-JPEG compression artifacts in text regions. (3) **Copy-Move Detection** — ORB (Oriented FAST and Rotated BRIEF) feature matching to detect duplicated document regions where text was copy-pasted. |
| **Blockchain Ledger** | `pipeline/blockchain_ledger.py` | Dual-hash system: (1) **SHA-256** content hash for exact-match detection. (2) **Perceptual Hash (pHash)** via `imagehash` for visual similarity — catches fraudsters who slightly crop, compress, or resize a previously rejected document to bypass checksums. SQLite-backed immutable chain with genesis block, `prev_block_hash` linking, and full chain integrity validation on every query. |

### STAGE 4–7 · VALIDATION & OUTPUT

| Module | File | How It Works |
|---|---|---|
| **QR Cross-Validator** | `pipeline/cross_validator.py` | The **strongest signal** (weight: 0.25). Decodes the embedded QR payload using `pyzbar`, then runs `fuzz.token_sort_ratio()` (Levenshtein distance) against OCR-extracted fields (Name, DOB, UID). If a fraudster changes the printed name on an Aadhaar but leaves the original QR intact, the name similarity drops below 85% and the document is instantly flagged. Handles name-order variations (e.g., "Rajesh Kumar" vs "Kumar Rajesh"). |
| **Structured Validator** | `agents/structured_doc_agent.py` | Semantic logic engine for financial documents. Checks: (1) **Character class validation** — detects letters hidden in money fields (e.g., `O` replacing `0`). (2) **Arithmetic checksums** — verifies that Gross Pay - Deductions = Net Pay. (3) **Format validation** — ensures APE/SIRET codes match expected regex patterns. Primary detector for NaviDoMass-style payslip forgeries. |
| **Scoring Engine** | `pipeline/scorer.py` | Document-type-aware weighted average across all signals. Each document type (Aadhaar, PAN, Passport, Salary Slip, Utility Bill) has a unique **weight modifier profile** — e.g., Deepfake weight is 0.3x for Aadhaar (small compressed photos are noisy) but 1.0x for Passports (face swap is the primary attack). Includes a **corroboration check** requiring ≥2 independent signals to fire before marking FORGED. 4-tier decision engine: `GENUINE`, `MANUAL_REVIEW`, `SUSPICIOUS`, `FORGED`. |
| **Explainability AI** | `pipeline/explainer.py` | Tries **Gemini 2.0 Flash** first with a zero-shot RBI-regulation-aware prompt that cites specific KYC Master Direction sections (16, 38c, 56). Falls back to a deterministic template engine if the API is unavailable. Both produce structured, hallucination-free compliance explanations. |

---

## 🔒 The Safety Net Architecture

The weighted average alone is dangerous — a genuine document with bad lighting could score as "suspicious" if a single noisy agent fires. We implemented three safety mechanisms:

1. **Critical Penalty Override:** If a document type *expects* a feature (e.g., Aadhaar expects a seal) and that feature's agent detects severe anomalies (raw_signal > 0.4), a **direct penalty (+15 to +25 points)** is added to the fraud score, bypassing the weighted-average dilution.
2. **Corroboration Requirement:** A single noisy agent cannot push a document to `FORGED` by itself. The scorer requires **≥2 independent signals** firing above 0.3 before issuing a `FORGED` verdict.
3. **Tiered Escalation for Financial Documents:** For salary slips, if the Text Integrity raw score exceeds 0.28 (a calibrated gap — genuine payslips score 0.10–0.18, forged score 0.29–0.39), the document is mathematically escalated to `FORGED` regardless of other clean signals.

---

## 🛠️ Implementation Methodology (How We Built It)

1. **Model Pre-loading at Startup:** EasyOCR (~40 MB), Deepfake ViT (~350 MB), and ML Forgery models are pre-loaded into memory on `@app.on_event("startup")`. This eliminates the 30–60 second cold-start delay that would kill a live demo.
2. **Single-Pass OCR:** OCR runs once, and the extracted bounding boxes + raw text are shared with both the Text Integrity Agent and the Structured Validator. This avoids redundant neural network inference.
3. **Aggressive Downscaling:** Before any deep learning sweep, `cv2.resize` clamps the image to 800px max-side using `INTER_AREA` interpolation. OCR time scales with pixel count — this cut processing from ~15s to ~2s per scan.
4. **Feature Flag System:** Every agent can be toggled on/off via environment variables (`ENABLE_DEEPFAKE`, `ENABLE_ML_FORGERY`, etc.). This allows graceful degradation on machines without GPU support.
5. **Automatic File Cleanup:** The `finally` block in the pipeline deletes all uploaded and generated files (ELA heatmaps, preprocessed images) after each request to prevent disk bloat.

---

## ⚡ Performance Benchmarks

| Metric | Value |
|---|---|
| End-to-end pipeline latency | **< 5 seconds** (CPU-only, no GPU required) |
| Pre-optimization latency | ~80 seconds |
| OCR speed after downscaling | ~2s (down from ~15s at full resolution) |
| EasyOCR weight reduction | 40% (English-only lock) |
| Concurrent agent execution | 8 threads via `ThreadPoolExecutor` |
| Model pre-load time (one-time) | ~45 seconds at server startup |

---

## 🎤 Pitch Guide for Judges

### 1. The Hook (The Problem)
> *"Most KYC systems rely on simple OCR or a single image classification model. The problem? Single models are easily bypassed by localized edits, and standard OCR cannot tell if text was digitally pasted. Our solution is **SecureAI-KYC**, an architectural approach to fraud detection that acts as a multi-agent forensic laboratory."*

### 2. Explain the Tech Stack (The "Why")
> *"For the frontend, we used **Next.js 16 and Framer Motion** to create a real-time SaaS dashboard that visualizes the pipeline as it runs. The backend is a **FastAPI** server (Python 3.11) that runs 8 independent forensic agents concurrently using ThreadPoolExecutor. We use **OpenCV and Scikit-image** for Error Level Analysis, **EasyOCR (PyTorch)** for text extraction, **Hugging Face Transformers** for deepfake detection, **PyZbar** for QR decryption, **FuzzyWuzzy** for cross-validation, **ImageHash** for blockchain ledger matching, and the **Gemini 2.0 Flash API** for Explainable AI compliance reports."*

### 3. The Demo Flow (Show, Don't Tell)
**Demo 1: Identity Card Forgery (QR-OCR Kill Feature)**
1. Upload a forged Aadhaar where the printed name was edited in Photoshop, but the QR code is untouched.
2. *"Our QR decoder extracted the hidden payload, ran a Fuzzy text match against the OCR, detected the mismatch, and instantly rejected it. Deterministic security beats probabilistic guessing."*

**Demo 2: Salary Slip Forgery (Semantic Validation)**
1. Upload a fake payslip where a `0` was changed to `O` or Gross Pay arithmetic doesn't match.
2. *"Standard image filters can't catch this. But our Structured Validator reads the logic — it caught the character-class violation and the broken arithmetic checksum."*

### 4. Anticipated Q&A
* **"Is it too slow with 8 models?"** — *"No. We downscale to 800px, lock OCR to English, pre-load models at startup, and run agents concurrently. Processing takes under 5 seconds."*
* **"How do you handle black-box trust?"** — *"Our Safety Net Architecture combines corroboration checks with a Gemini-powered XAI stage that generates plain-English compliance reports citing specific RBI KYC Master Directions."*
* **"What if a signal is irrelevant?"** — *"Each document type has a unique weight modifier profile. Deepfake is weighted 0.0x for payslips (no face) and 1.0x for passports. Missing seals don't penalize PAN cards because PAN cards don't have seals."*

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- **Python**: 3.11+
- **Node.js**: v20+
- **API Key**: [Get a Gemini API Key](https://aistudio.google.com/) for the Explainability module.

### 2. Environment Variables
In the `backend/` directory, create a `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Start the Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 4. Start the Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:3000` to view the dashboard.

---
*Created for the 2026 AI Hackathon by [@ZeroTrace7](https://github.com/ZeroTrace7).*
