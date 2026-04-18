# 🛡️ SecureAI-KYC — Intelligent Document Verification & Fraud Detection

**SecureAI-KYC** is a comprehensive, multi-agent forensic verification platform built to detect sophisticated document fraud. Developed for the **Document Forgery Detection Blue Team Challenge** at the National Hackathon, 2026.

Instead of relying on a single "black-box" machine learning model, SecureAI-KYC uses a deterministic, **stage-gated 8-signal pipeline** that cross-validates visual, spatial, textual, and immutable data, outputting an explainable fraud score and PDF report.

---

## 💻 Complete Technology Stack

### Frontend (UI & Real-time Visualization)
*   **Framework:** Next.js 16, React 19 (App Router)
*   **Styling:** Tailwind CSS v4, CSS Modules
*   **Animations:** Framer Motion (Real-time pipeline progression & micro-interactions)
*   **Reporting:** jsPDF (Client-side localized PDF report generation)
*   **Icons:** Lucide React

### Backend (Core Logic & API)
*   **Framework:** FastAPI, Uvicorn, Python 3.11
*   **Concurrency:** Built-in `ThreadPoolExecutor` (Runs 8 Python ML agents in parallel for sub-5 second responses)
*   **Database:** SQLite, SQLAlchemy (Used for the Blockchain Hash Ledger)
*   **PDF Parsing:** PyMuPDF (`fitz`)

### AI, Machine Learning & Computer Vision
*   **Deep Learning Frameworks:** PyTorch, Hugging Face Transformers
*   **Optical Character Recognition (OCR):** EasyOCR (locked to EN for 40% speed boost), PyTesseract (Fallback)
*   **Image Processing & Forensics:** OpenCV (`cv2`), Pillow (PIL), Scikit-image (Used for Error Level Analysis & Edge Detection)
*   **Deepfake & Manipulation Models:** ViT / MobileNetV2 architectures for synthetic face detection
*   **Data Validation:** FuzzyWuzzy, Levenshtein (Semantic similarity matching)
*   **Barcode/QR Decoding:** PyZbar
*   **Explainable AI (XAI):** Google Gemini API (`google-genai`) for plain-English compliance reporting
*   **Perceptual Hashing:** ImageHash (Prevents visually identical resubmission attacks)

---

## ⚙️ How It Works (The 8-Signal Pipeline)

When a document is uploaded, it passes through our parallel execution engine:

1.  **Quality Gate:** OpenCV verifies blur, glare, and resolution constraints.
2.  **Classification & OCR:** EasyOCR extracts bounding boxes and text.
3.  **ELA Pixel Forensics:** Detects Photoshop/editing compression artifacts.
4.  **EXIF Metadata:** Scans for impossible timestamps and known editing software footprints.
5.  **Signature & Seal Analysis:** Uses HSV segmentation and Hough circles to detect digitally pasted elements.
6.  **Deepfake Detection:** Analyzes the extracted face for GAN/Diffusion artifacts.
7.  **Text & Structural Integrity:** Detects character-class manipulation (e.g., hidden letters in money fields) and broken arithmetic checksums (especially on Payslips).
8.  **QR ↔ OCR Cross-Validation:** The most heavily weighted signal. It cryptographically decrypts the Aadhaar/PAN QR code and string-matches it against the printed text.

**Final Verdict:** The system computes a weighted average. However, we use a **Safety Net Architecture**—if any single critical signal scores incredibly high for fraud, the document is mathematically overridden and forced into `MANUAL_REVIEW` by a human agent.

---

## 🎤 Pitch Guide for Judges 
*How to present this project to technically advanced judges.*

### 1. The Hook (The Problem)
> *"Most KYC systems rely on simple OCR or a single image classification model. The problem? Single models are easily bypassed by localized edits, and standard OCR cannot tell if text was digitally pasted. Our solution is **SecureAI-KYC**, an architectural approach to fraud detection that acts as a multi-agent forensic laboratory."*

### 2. Explain the Tech Stack (The "Why")
> *"For the frontend, we used **Next.js and Framer Motion** to create a highly responsive, modern SaaS dashboard that visualizes the pipeline in real-time. But the magic is in the backend.* 
>
> *We built a high-performance **FastAPI** server that runs 8 independent forensic agents concurrently using a ThreadPoolExecutor. We use **OpenCV and Scikit-image** for Error Level Analysis and visual segmentation. For text extraction, we optimized **EasyOCR**, and for deepfake detection, we implemented **PyTorch/Transformers**. Finally, we use the **Gemini API** as an Explainability Agent to convert the complex mathematical scores into a plain-English compliance report."*

### 3. The Demo Flow (Show, Don't Tell)
**Demo 1: The Identity Card Fake (QR-OCR Cross-Validation)**
1.  Upload a forged Aadhaar card where the printed name was altered using Photoshop, but the original QR code remains.
2.  **Point out to judges:** *"Visually, this looks perfect. A standard ML model might pass it. But look at our pipeline—our QR decoder extracted the hidden payload, ran a Fuzzy text search against the printed OCR, detected the mismatch, and instantly rejected it. Deterministic security beats probabilistic guessing."*

**Demo 2: The Salary Slip Fake (Structural Semantic Validation)**
1.  Upload an altered salary slip (e.g., where a `0` was changed to an `O` or the Gross Pay arithmetic doesn't match the deductions).
2.  **Point out to judges:** *"This is a NaviDoMass-style forgery. The pixel manipulation is too subtle for standard filters. But our **Structured Document Validator** agent doesn't just read pixels; it reads semantics. It caught the invalid character class and the broken arithmetic checksum."*

### 4. Anticipated Q&A
*   **Q: "Is your system too slow with 8 ML models?"**
    *   **A:** *"No. We heavily optimized it. We downscale images to 800px max-width before deep learning sweeps, we hardcoded EasyOCR to English to drop 40% of the neural weights, and we run the agents concurrently. Processing takes under 5 seconds."*
*   **Q: "How do you handle 'black-box' ML trust issues for compliance?"**
    *   **A:** *"We implemented a Safety Net Architecture and an XAI (Explainable AI) stage. The pipeline generates a localized PDF report (using jsPDF) that gives a specific reason for rejection based on the exact agent that flagged it, tying it back to RBI KYC master directions."*

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
