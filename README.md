
# 🛡️ SECUREAI-KYC — AI-Powered KYC Document Fraud Detection System

> **An intelligent, multi-agent KYC verification pipeline** that uses AI models for document classification, OCR, deepfake detection, voice verification, and explainable fraud scoring.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Pipeline Stages](#-pipeline-stages)
- [Tech Stack](#-tech-stack)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Dependency Status](#-dependency-status)
- [Known Issues & Workarounds](#-known-issues--workarounds)
- [Environment Configuration](#-environment-configuration)
- [Running the Project](#-running-the-project)
- [Frontend Integration Guide](#-frontend-integration-guide)
- [HF Models Reference](#-hf-models-reference)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🔍 Overview

**SecureAI-KYC** is a document fraud detection system designed for Indian KYC documents (Aadhaar, PAN, Passport, Salary Slip). It uses a multi-agent AI pipeline that performs:

- **Document Type Classification** — Rule-based heuristic classifier (QR + regex + keywords)
- **Image Quality Gate** — Blur, resolution, brightness, and contrast validation
- **Error Level Analysis** — Detect photoshopped/tampered regions with visual heatmap
- **OCR Text Extraction** — Extract Name, DOB, UID, Address using EasyOCR (Hindi + English)
- **QR Code Decoding** — Validate embedded Aadhaar QR data
- **EXIF Metadata Analysis** — Flag documents edited in Photoshop/GIMP
- **Deepfake Face Detection** — Detect AI-generated/pasted faces (secondary signal, weight ≤ 0.10)
- **Voice Verification** — Optional speaker recognition for biometric matching
- **Cross-Validation** — Match OCR text against QR data with fuzzy matching (**killer feature**)
- **Fraud Scoring** — Weighted multi-signal fraud score computation
- **Explainable Output** — Generate human-readable fraud explanations via Gemini API or templates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React / Next.js)                   │
│                   Document Upload + Results UI                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI + Uvicorn)                   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Stage 0      │  │ Stage 1-2    │  │ Stage 3 (6 Agents)    │ │
│  │ Rule-Based   │→ │ Quality +    │→ │ ELA │ OCR │ QR │ EXIF │ │
│  │ Classifier   │  │ Preprocess   │  │ Face│Voice│    │      │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
│                                              │                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────▼───────────────┐ │
│  │ Stage 7      │  │ Stage 5-6    │  │ Stage 4               │ │
│  │ Gemini API / │← │ Scoring +    │← │ Cross-Validation      │ │
│  │ Template     │  │ Decision     │  │ (fuzzy matching)      │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Stage 8: Audit Logger (SQLAlchemy + SQLite/PostgreSQL)   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔷 Pipeline Stages

| Stage | Name | Technology | Purpose |
|-------|------|-----------|---------|
| **0** | Document Classification | Rule-based (QR + regex + keywords) | Detect Aadhaar/PAN/Passport |
| **1** | Input Quality Gate | OpenCV | Blur, resolution, brightness checks |
| **2** | Preprocessing | OpenCV + Pillow | Normalize, denoise, re-encode |
| **3.1** | ELA Forensics | Custom Python (recompress + diff) | Detect tampered regions + heatmap |
| **3.2** | OCR Extraction | EasyOCR (en + hi) | Extract text from documents |
| **3.3** | QR Decoder | pyzbar / OpenCV | Decode Aadhaar QR XML data |
| **3.4** | EXIF Analyzer | exifread | Flag Photoshop-edited docs |
| **3.5** | Deepfake Detection | `dima806/deepfake_vs_real_image_detection` | Detect fake/AI faces (weight ≤ 0.10) |
| **3.6** | Voice Verification | `speechbrain/spkrec-ecapa-voxceleb` | Speaker biometric matching (OPTIONAL) |
| **4** | Cross-Validation | fuzzywuzzy | Match OCR text vs QR data |
| **5-6** | Scoring + Decision | Pure Python (weighted signals) | Weighted fraud score |
| **7** | Explainer | Gemini API / structured templates | Human-readable explanation |
| **8** | Audit Logger | SQLAlchemy | Tamper-proof audit trail |

### ⚖️ Fraud Score Signal Weights

| Signal | Weight | Rationale |
|--------|--------|-----------|
| QR-OCR mismatch | **0.35** | Strongest, most unique signal |
| ELA tampering | **0.25** | Visual + reliable |
| EXIF flag | **0.15** | Binary, reliable |
| Deepfake | **0.10** | Noisy on small faces |
| ML forgery | **0.05** | Optional, redundant with ELA |
| Voice mismatch | **0.10** | Optional, skip-safe |

---

## 🛠️ Tech Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.13.12 |
| Web Framework | FastAPI | 0.135.2 |
| ASGI Server | Uvicorn | 0.42.0 |
| Database ORM | SQLAlchemy | 2.0.48 |
| AI Framework | PyTorch | 2.11.0 (CPU) |
| Model Hub | Hugging Face Transformers | 5.4.0 |
| Explainability | Gemini API (google-genai) | Latest |
| OCR Engine | EasyOCR | 1.7.2 |

### Frontend (To Connect)
| Component | Technology |
|-----------|-----------|
| Framework | React / Next.js |
| Runtime | Node.js v22.16.0 |
| Package Manager | npm 10.9.2 |

---

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 10+ | Windows 11 |
| **Python** | 3.10+ | 3.13+ |
| **RAM** | 4 GB | 8 GB |
| **Disk Space** | 1 GB (with models) | 2 GB |
| **GPU** | Not required | NVIDIA CUDA GPU (faster inference) |
| **Node.js** | v18+ (for frontend) | v22+ |

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/ZeroTrace7/Ai_KYC.git
cd Ai_KYC
```

### Step 2: Install All Python Packages (One Command)

```bash
pip install -r requirements.txt
```

Or individually:
```bash
pip install transformers torch torchvision torchaudio huggingface_hub opencv-python pillow scikit-image numpy scipy easyocr pytesseract pyzbar piexif exifread fuzzywuzzy python-Levenshtein pymupdf fastapi uvicorn python-multipart sqlalchemy python-dotenv loguru google-genai safetensors requests speechbrain resemblyzer librosa sounddevice webrtcvad-wheels
```

### Step 3 (Optional): Install Tesseract OCR (Fallback OCR)

> ⚠️ **EasyOCR is the primary OCR engine and needs no system binary.** Tesseract is an optional fallback.

1. **Download** from: https://github.com/UB-Mannheim/tesseract/wiki
2. **Run the installer** and check "Add to PATH"
3. Verify: `tesseract --version`

### Step 4 (Optional): Fix pyzbar — Install Visual C++ 2013 Runtime

> ⚠️ If pyzbar fails, the system automatically falls back to OpenCV's QR decoder.

1. **Download** VC++ 2013 x64: https://aka.ms/highdpimfc2013x64enu
2. **Install** and **restart** your terminal

### Step 5 (Optional): Set Up Gemini API Key

For AI-powered fraud explanations (free tier: 15 RPM):

1. Get an API key from https://aistudio.google.com/app/apikey
2. Add to your `.env` file: `GEMINI_API_KEY=your_key_here`
3. If no key is set, the system uses structured templates (also effective!)

### Step 6 (Optional): Pre-Download AI Models (~400 MB)

```bash
python scripts/precache_ai_models.py
```

---

## ✅ Dependency Status

> Last verified: 2026-03-29

### Python Packages — All Installed ✅

| Package | Version | Stage | Status |
|---------|---------|-------|--------|
| `easyocr` | 1.7.2 | OCR (3.2) — **PRIMARY** | ✅ |
| `transformers` | 5.4.0 | Deepfake (3.5) | ✅ |
| `torch` | 2.11.0 | Core AI | ✅ |
| `torchvision` | 0.26.0 | Vision models | ✅ |
| `torchaudio` | 2.11.0 | Voice (3.6) | ✅ |
| `huggingface_hub` | 1.8.0 | Model downloads | ✅ |
| `google-genai` | Latest | Explainer (7) | ✅ |
| `opencv-python` | 4.13.0.92 | Stages 1, 2, 3.3, 3.5 | ✅ |
| `pillow` | 12.1.1 | Image processing | ✅ |
| `numpy` | 2.4.2 | Numeric ops | ✅ |
| `scipy` | 1.17.1 | Scientific computing | ✅ |
| `scikit-image` | 0.26.0 | Image analysis | ✅ |
| `pytesseract` | 0.3.13 | OCR fallback (3.2) | ⚠️ Needs Tesseract binary |
| `pyzbar` | 0.1.9 | QR decode (3.3) | ⚠️ Auto-fallback to OpenCV |
| `piexif` | 1.1.3 | EXIF (3.4) | ✅ |
| `exifread` | 3.5.1 | EXIF (3.4) | ✅ |
| `fuzzywuzzy` | 0.18.0 | Cross-validation (4) | ✅ |
| `python-Levenshtein` | 0.27.3 | Fuzzy speed boost (4) | ✅ |
| `speechbrain` | 1.0.3 | Voice (3.6, optional) | ⚠️ Needs workaround |
| `fastapi` | 0.135.2 | Backend API | ✅ |
| `uvicorn` | 0.42.0 | ASGI server | ✅ |
| `python-multipart` | 0.0.22 | File uploads | ✅ |
| `sqlalchemy` | 2.0.48 | Audit logging (8) | ✅ |
| `loguru` | 0.7.3 | Logging | ✅ |
| `python-dotenv` | 1.2.2 | Env config | ✅ |
| `safetensors` | 0.7.0 | Model loading | ✅ |
| `requests` | 2.33.0 | HTTP client | ✅ |

### Models — Optimized (91% reduction)

| Model | Size | Status | Notes |
|-------|------|--------|-------|
| `dima806/deepfake_vs_real_image_detection` | 350 MB | ✅ Required | Single deepfake model |
| EasyOCR English + Hindi | ~40 MB | ✅ Required | Auto-downloads on first use |
| ~~`microsoft/dit-base-finetuned-rvlcdip`~~ | ~~340 MB~~ | ❌ Removed | → Rule-based classifier |
| ~~`microsoft/trocr-base-printed`~~ | ~~650 MB~~ | ❌ Removed | → EasyOCR |
| ~~`microsoft/trocr-base-handwritten`~~ | ~~650 MB~~ | ❌ Removed | → EasyOCR |
| ~~`microsoft/layoutlmv3-base`~~ | ~~500 MB~~ | ❌ Removed | Not needed |
| ~~`prithivMLmods/Deep-Fake-Detector-v2-Model`~~ | ~~350 MB~~ | ❌ Removed | Redundant |
| ~~`google/flan-t5-base`~~ | ~~990 MB~~ | ❌ Removed | → Gemini API + templates |

**Total download: ~400 MB** (down from ~4 GB)

---

## ⚠️ Known Issues & Workarounds

### 1. SpeechBrain + TorchAudio Compatibility

**Problem**: `speechbrain 1.0.3` calls `torchaudio.list_audio_backends()` which was removed in `torchaudio 2.11`.

**Workaround**: Already handled automatically in `utils/compat.py`. The voice agent applies the patch before importing SpeechBrain.

### 2. pyzbar QR Decoder on Windows

**Problem**: `libzbar-64.dll` fails to load without VC++ 2013 redistributable.

**Workaround**: Automatic fallback to OpenCV's built-in QR decoder. No action needed.

### 3. Tesseract OCR Not Found

**Problem**: `pytesseract` requires the Tesseract engine binary.

**Fix**: EasyOCR is the primary OCR engine and doesn't need Tesseract. Install Tesseract only if you need it as a fallback.

### 4. First-Run Model Downloads

**Problem**: First API call downloads the deepfake model (~350 MB).

**Fix**: Pre-download: `python scripts/precache_ai_models.py`

### 5. Deepfake False Positives on Document Photos

**Problem**: Aadhaar card photos are small (~100x120px) and low quality. The model gives noisy outputs.

**Mitigation**: Deepfake signal weight is capped at 0.10. Faces smaller than 80x80px are automatically skipped.

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# === Server ===
HOST=0.0.0.0
PORT=8000
DEBUG=true

# === Paths ===
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
UPLOAD_DIR=./uploads
MODEL_CACHE_DIR=./models

# === Database ===
DATABASE_URL=sqlite:///./audit.db

# === CORS (Frontend URL) ===
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# === Thresholds ===
BLUR_THRESHOLD=100
ELA_THRESHOLD=0.35
DEEPFAKE_THRESHOLD=0.5
FRAUD_SCORE_THRESHOLD=60
NAME_MATCH_THRESHOLD=85

# === Feature Flags ===
ENABLE_DEEPFAKE=true
ENABLE_VOICE=false
ENABLE_ML_FORGERY=false

# === Gemini API (Explainability) ===
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# === Hugging Face ===
HF_HOME=./models
TRANSFORMERS_CACHE=./models
```

---

## 🚀 Running the Project

### Start the Backend

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with Python
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs (Swagger)**: http://localhost:8000/docs
- **Docs (ReDoc)**: http://localhost:8000/redoc

### API Endpoints

```
POST /api/verify          →  Full KYC verification pipeline
POST /api/classify        →  Classify document type only
POST /api/ocr             →  Extract text from document
POST /api/deepfake        →  Check if face is deepfake
POST /api/voice/verify    →  Compare voice samples
GET  /api/audit/{id}      →  Get audit trail for verification
GET  /api/health          →  Health check endpoint
```

### Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at http://localhost:3000 (or :5173 for Vite).

---

## 🔗 Frontend Integration Guide

### Frontend Upload Example (React/Next.js)

```javascript
const verifyDocument = async (file) => {
  const formData = new FormData();
  formData.append('document', file);
  
  const response = await fetch('http://localhost:8000/api/verify', {
    method: 'POST',
    body: formData,
  });
  
  const result = await response.json();
  return result;
  
  // Expected response:
  // {
  //   "document_type": "aadhaar",
  //   "quality": { "quality_pass": true, ... },
  //   "ela": { "ela_score": 0.12, "heatmap_path": "..." },
  //   "ocr": { "fields": { "name": "...", "dob": "...", "uid": "..." } },
  //   "qr": { "qr_name": "...", "qr_dob": "..." },
  //   "exif": { "exif_flag": "clean" },
  //   "cross_validation": { "name_similarity": 95, "dob_match": true },
  //   "fraud_score": 15,
  //   "decision": "GENUINE",
  //   "explanation": "Document appears authentic...",
  //   "processing_time_seconds": 2.3
  // }
};
```

### CORS Configuration

Already configured in `main.py`. Add your frontend URL to `CORS_ORIGINS` in `.env`.

---

## 🧠 HF Models Reference

See **[HUGGINGFACE_MODELS.md](./HUGGINGFACE_MODELS.md)** for detailed model documentation.

### Required Models (~400 MB total)

| Model | Size | Purpose |
|-------|------|---------|
| `dima806/deepfake_vs_real_image_detection` | 350 MB | Deepfake detection |
| EasyOCR (en + hi) | ~40 MB | OCR text extraction |

### Optional Models

| Model | Size | Purpose |
|-------|------|---------|
| `speechbrain/spkrec-ecapa-voxceleb` | 80 MB | Voice verification |
| `kumaran-0188/image_forgery_detector` | 90 MB | ML forgery detection |

---

## 📁 Project Structure

```
secureai-kyc/
├── README.md                    # This file
├── HUGGINGFACE_MODELS.md        # Detailed model reference
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
│
├── main.py                      # FastAPI app + pipeline orchestration
├── config.py                    # Configuration loader + feature flags
│
├── agents/                      # Stage 3 AI agents
│   ├── __init__.py
│   ├── ela_agent.py             # Agent 1: ELA forensics + heatmap
│   ├── ocr_agent.py             # Agent 2: EasyOCR + field extraction
│   ├── qr_agent.py              # Agent 3: QR decoder (pyzbar/OpenCV)
│   ├── exif_agent.py            # Agent 4: EXIF metadata analysis
│   ├── deepfake_agent.py        # Agent 5: Deepfake detection (weight ≤ 0.10)
│   └── voice_agent.py           # Agent 6: Voice verification (OPTIONAL)
│
├── pipeline/                    # Pipeline stages
│   ├── __init__.py
│   ├── classifier.py            # Stage 0: Rule-based classifier
│   ├── quality_gate.py          # Stage 1: Input quality check
│   ├── preprocessor.py          # Stage 2: Image preprocessing
│   ├── cross_validator.py       # Stage 4: Cross-validation (killer feature)
│   ├── scorer.py                # Stage 5-6: Weighted fraud scoring
│   ├── explainer.py             # Stage 7: Gemini API / template explainer
│   └── audit_logger.py          # Stage 8: Audit logging
│
├── utils/                       # Utilities
│   ├── __init__.py
│   └── compat.py                # Compatibility patches + safe imports
│
├── scripts/                     # Setup scripts
│   ├── precache_ai_models.py    # Download AI models (~400 MB)
│   └── download_tools.py        # Download system tools
│
├── tools/                       # System tool installers
├── models/                      # Downloaded HF models cache
├── uploads/                     # Uploaded documents (temp)
├── frontend/                    # React/Next.js frontend
│
└── tests/                       # Unit tests
    ├── test_agents.py
    └── test_pipeline.py
```

---

## 🔧 Troubleshooting

### "Model not found" on first run
The deepfake model auto-downloads (~350 MB). Pre-download with `python scripts/precache_ai_models.py`.

### "CUDA out of memory"
The system defaults to CPU. If you have a GPU with limited VRAM, models fall back to CPU automatically.

### pytesseract "TesseractNotFoundError"
EasyOCR is the primary OCR — Tesseract is optional. If you want Tesseract, install the binary.

### pyzbar "Could not find module libzbar-64.dll"
Automatic fallback to OpenCV QR detector. No action required.

### speechbrain AttributeError
The compatibility patch is applied automatically in `utils/compat.py`.

### Slow inference
Target: 2-4 sec on CPU. If slower, ensure no other heavy processes are running.

### "Connection refused" from frontend
Check CORS config in `.env`. Backend must be running on port 8000.

---

## ⚡ Performance Comparison

| Metric | Before (Original) | After (Optimized) |
|--------|-------------------|-------------------|
| Model download | ~4 GB | **~400 MB** (91% reduction) |
| Startup time | ~30 sec | **~5 sec** |
| Per-document | 5-15 sec | **2-4 sec** |
| RAM usage | ~4 GB | **~1.5 GB** |
| Crash risk | High (many models) | **Low (graceful fallbacks)** |

---

## 📄 License

MIT License — See `LICENSE` file.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-agent`)
3. Commit changes (`git commit -m "Add new verification agent"`)
4. Push to branch (`git push origin feature/new-agent`)
5. Open a Pull Request

---

## 👤 Author

- **GitHub**: [@ZeroTrace7](https://github.com/ZeroTrace7)
- **Email**: shreyashgupta999@gmail.com
- **Project Link**: [https://github.com/ZeroTrace7/Ai_KYC](https://github.com/ZeroTrace7/Ai_KYC)

---

> **Built with** 🐍 Python, 🤗 Hugging Face, ⚡ FastAPI, 🔥 PyTorch, ✨ Gemini API
