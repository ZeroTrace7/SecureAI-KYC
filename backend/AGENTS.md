# 🤖 SecureAI-KYC Forensic Agent Suite

SecureAI-KYC utilizes a multi-layered, 10-signal forensic pipeline where each agent specializes in a specific domain of document verification. 

---

## 🧭 Pipeline Orchestration
All agents are coordinated by `backend/main.py` using a **Phase 1 Parallelization** model. Independent agents execute concurrently in a thread pool to minimize end-to-end latency (~14s total).

---

## 🛠️ The 10 Forensic Agents

### 1. ELA Agent (`agents/ela_agent.py`)
- **Domain**: Pixel-level forensics.
- **Logic**: Performs **Error Level Analysis** by resaving the image at a known quality (95%) and computing the absolute pixel difference. 
- **Output**: Generates a heatmap where bright spots indicate inconsistent compression levels—a hallmark of digital splicing.

### 2. OCR Agent (`agents/ocr_agent.py`)
- **Domain**: Text extraction.
- **Logic**: Utilizes **EasyOCR** (singleton) with English and Hindi support. 
- **Output**: Extracts raw text and uses regex for field-level identification (Name, DOB, UID, PAN, Passport).

### 3. QR Agent (`agents/qr_agent.py`)
- **Domain**: Encrypted data validation.
- **Logic**: Uses `pyzbar` to decode 1D/2D barcodes (Aadhaar QR, etc.).
- **Output**: Decodes embedded JSON/XML data for deterministic cross-validation against OCR text.

### 4. EXIF Agent (`agents/exif_agent.py`)
- **Domain**: Metadata forensics.
- **Logic**: Extracts EXIF/IPTC headers using `exifread`.
- **Alerts**: Flags impossible timestamps (e.g., modified date before creation) and software signatures from AI generators (DALL-E, Midjourney) or editors (Photoshop, Canva).

### 5. Deepfake Agent (`agents/deepfake_agent.py`)
- **Domain**: Facial biometrics.
- **Logic**: Runs a HuggingFace Transformers pipeline (`dima806/deepfake_vs_real_image_detection`) on detected faces.
- **Output**: Probability score (0-1) of the face being synthetically generated.

### 6. Signature/Seal Agent (`agents/signature_seal_agent.py`)
- **Domain**: Document integrity.
- **Logic**: 
  - **Seals**: HSV color-space segmentation for red/blue circular stamps + contour validation.
  - **Signatures**: Adaptive thresholding to detect high-frequency ink strokes.
  - **Edge Forensics**: Sobel edge sharpness analysis to detect "digital pasting" (unusually sharp edges compared to paper background).

### 7. Text Integrity Agent (`agents/text_integrity_agent.py`)
- **Domain**: Typography & Frequency analysis.
- **Logic**:
  - **Font Consistency**: Measures variance in character heights and spacing outliers.
  - **DCT Analysis**: Frequency domain peak detection for double-JPEG compression (spectral markers).
  - **Copy-Move**: ORB (Oriented FAST and Rotated BRIEF) feature matching to detect duplicated document regions.

### 8. Blockchain Agent (`pipeline/blockchain_ledger.py`)
- **Domain**: Global immutability.
- **Logic**: Computes a SHA-256 binary hash + a **Perceptual Hash (pHash)** of every document.
- **Output**: Checks an immutable SQLite chain for previous submissions. If a document was previously rejected, the blockchain signal triggers an immediate fraud alert.

### 9. ML Forgery Agent (`agents/ml_forgery_agent.py`)
- **Domain**: Deep learning forensics.
- **Logic**: MobileNetV2-based classification trained on forgery datasets (NaviDoMass, DocTamper).
- **Note**: Acts as a redundant visual signal to ELA for high-confidence forgery detection.

### 10. Cross-Validator (`pipeline/cross_validator.py`)
- **Domain**: Logical consistency.
- **Logic**: A "Killer Feature" that performs **Fuzzy String Matching** (Levenshtein distance) between OCR-extracted text and QR-embedded metadata.
- **Output**: Detects field-level tampering (e.g., a renamed Aadhaar card where the QR still points to the original owner).

---

## ⚖️ Scoring Engine (`pipeline/scorer.py`)
The signals are aggregated into a weighted score (0-100). The current configuration prioritizes high-confidence deterministic signals:

| Signal | Weight |
|--------|--------|
| QR-OCR Match | 0.25 |
| Text Integrity | 0.20 |
| ELA Forensics | 0.18 |
| Blockchain | 0.15 |
| Signature/Seal | 0.12 |
| EXIF Flag | 0.10 |
| ML Forgery | 0.08 |
| Deepfake | 0.07 |
