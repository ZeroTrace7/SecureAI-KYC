# 🛡️ SECUREAI-KYC — Backend (API & AI Agents)

This directory contains the core intelligence of the SecureAI-KYC system, built with FastAPI and a multi-agent AI pipeline.

---

## 🏗️ Backend Architecture

The backend is organized into stages:
- **Stage 0**: Rule-based document classification.
- **Stage 1-2**: Input quality gate and preprocessing.
- **Stage 3**: Parallel execution of 6 AI agents (ELA, OCR, QR, EXIF, Deepfake, Voice).
- **Stage 4**: Cross-validation (OCR vs QR data matching).
- **Stage 5-6**: Weighted fraud scoring.
- **Stage 7**: Explainable output generation.
- **Stage 8**: Audit logging (SQLAlchemy + SQLite).

---

## 🛠️ Tech Stack (Verified 2026)

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.13.12 |
| Web Framework | FastAPI | 0.135.2 |
| ASGI Server | Uvicorn | 0.42.0 |
| Database ORM | SQLAlchemy | 2.0.48 |
| AI Framework | PyTorch | 2.11.0 (CPU) |
| Model Hub | Hugging Face Transformers | 5.4.0 |
| Explainability | Gemini API (google-genai) | 1.69.0+ |
| OCR Engine | EasyOCR | 1.7.2 |

---

## 📦 Installation

1. **Create Virtual Env**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Pre-download Models**:
   ```bash
   python scripts/precache_ai_models.py
   ```

---

## 🚀 Running the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📁 Directory Structure

- `agents/`: Stage 3 AI implementations.
- `pipeline/`: Core orchestration logic and scoring.
- `utils/`: Compatibility patches and helpers.
- `scripts/`: Maintenance and setup utilities.
- `models/`: Local cache for Hugging Face weights.
- `uploads/`: Temporary storage for processed documents.

---

## 🔍 Agents & Models

Detailed documentation for individual components:
- [AI Agents Documentation](./AGENTS.md)
- [Hugging Face Models Reference](./HUGGINGFACE_MODELS.md)
