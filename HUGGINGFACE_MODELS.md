# 🧠 SECUREAI-KYC — Hugging Face Models & Python Packages Guide

> Complete list of every AI model and Python package needed from Hugging Face for each pipeline stage.

---

## 📥 How to Download All Models

All models below can be downloaded using the `transformers` or `speechbrain` library. Install the base packages first:

```bash
pip install transformers torch torchvision huggingface_hub speechbrain
```

To pre-download ALL models at once (so they work offline):

```python
from huggingface_hub import snapshot_download

models = [
    "microsoft/dit-base-finetuned-rvlcdip",
    "google/vit-base-patch16-224-in21k",
    "microsoft/trocr-base-printed",
    "microsoft/trocr-base-handwritten",
    "microsoft/layoutlmv3-base",
    "dima806/deepfake_vs_real_image_detection",
    "prithivMLmods/Deep-Fake-Detector-v2-Model",
    "speechbrain/spkrec-ecapa-voxceleb",
    "google/flan-t5-base",
]

for model_id in models:
    print(f"Downloading {model_id}...")
    snapshot_download(repo_id=model_id)
    print(f"✅ {model_id} downloaded!")
```

---

## 🔷 STAGE 0 — Document Type Classification

> **Goal**: Detect if the uploaded document is Aadhaar, PAN, Passport, or Salary Slip

### Primary Model

| Field | Value |
|-------|-------|
| **Model** | `microsoft/dit-base-finetuned-rvlcdip` |
| **HF Link** | https://huggingface.co/microsoft/dit-base-finetuned-rvlcdip |
| **Type** | Image Classification (Document Image Transformer) |
| **Size** | ~340 MB |
| **Why** | Pre-trained on 400K documents (RVL-CDIP), classifies 16 doc types. Fine-tune on Indian ID dataset for Aadhaar/PAN/Passport. |

### Alternative / Specialized Models

| Model | HF Link | Purpose |
|-------|---------|---------|
| `logasanjeev/indian-id-validator` | https://huggingface.co/logasanjeev/indian-id-validator | 🔥 **Indian-specific** — classifies Aadhaar (front/back), PAN, Passport |
| `arnabdhar/YOLOv8-nano-aadhar-card` | https://huggingface.co/arnabdhar/YOLOv8-nano-aadhar-card | YOLOv8 for detecting fields on Aadhaar cards |
| `foduucom/pan-card-detection` | https://huggingface.co/foduucom/pan-card-detection | YOLO for PAN card field detection |

### Python Code (Stage 0)

```python
from transformers import pipeline

# Option A: General document classifier
classifier = pipeline("image-classification", model="microsoft/dit-base-finetuned-rvlcdip")
result = classifier("aadhaar_card.jpg")
# result: [{'label': 'letter', 'score': 0.85}, ...]

# Option B: Indian-specific (RECOMMENDED)
# Uses logasanjeev/indian-id-validator pipeline
from transformers import AutoModelForImageClassification, AutoFeatureExtractor
model = AutoModelForImageClassification.from_pretrained("logasanjeev/indian-id-validator")
```

### Pip Packages Required

```bash
pip install transformers torch torchvision pillow ultralytics
```

---

## 🔷 STAGE 1 — Input Quality Gate

> **Goal**: Blur detection, resolution check, brightness/contrast

### No Hugging Face Model Needed ✅

This stage uses **pure OpenCV** — no AI model required.

### Python Code (Stage 1)

```python
import cv2
import numpy as np

def check_quality(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur detection (Laplacian variance)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Resolution check
    h, w = img.shape[:2]
    resolution_ok = (h >= 500 and w >= 500)

    # Brightness check
    brightness = np.mean(gray)
    brightness_ok = (40 < brightness < 220)

    return {
        "quality_pass": blur_score > 100 and resolution_ok and brightness_ok,
        "blur_score": round(blur_score, 2),
        "resolution_ok": resolution_ok,
        "brightness": round(brightness, 2)
    }
```

### Pip Packages Required

```bash
pip install opencv-python numpy
```

---

## 🔷 STAGE 2 — Preprocessing

> **Goal**: Normalize input for all agents

### No Hugging Face Model Needed ✅

Pure OpenCV/Pillow operations.

### Python Code (Stage 2)

```python
import cv2
from PIL import Image

def preprocess(image_path, output_path="clean.jpg"):
    img = cv2.imread(image_path)

    # Resize to standard size
    img = cv2.resize(img, (1024, 768))

    # Bilateral filter (reduce noise, keep edges)
    img = cv2.bilateralFilter(img, 9, 75, 75)

    # Convert to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Re-encode as JPEG (strip adversarial noise)
    pil_img = Image.fromarray(img)
    pil_img.save(output_path, "JPEG", quality=95)

    return output_path
```

### Pip Packages Required

```bash
pip install opencv-python pillow
```

---

## 🔷 STAGE 3 — AGENT 1: ELA (Image Forensics)

> **Goal**: Detect tampered regions via Error Level Analysis + AI classifier

### Primary Model (AI-enhanced ELA)

| Field | Value |
|-------|-------|
| **Model** | `kumaran-0188/image_forgery_detector` |
| **HF Link** | https://huggingface.co/kumaran-0188/image_forgery_detector |
| **Type** | Image Classification (Real vs Forged) |
| **Size** | ~90 MB |
| **Why** | Trained to detect image manipulation / forgery patterns |

### Alternative Models

| Model | HF Link | Purpose |
|-------|---------|---------|
| `umm-maybe/AI-image-detector` | https://huggingface.co/umm-maybe/AI-image-detector | Detects AI-generated images (ViT-based) |
| `FakeShield` (Research) | https://huggingface.co/papers/FakeShield | Multi-modal forgery detection + localization |

### Python Code (Stage 3 - Agent 1)

```python
from PIL import Image, ImageChops
import numpy as np

def compute_ela(image_path, quality=90):
    """Traditional ELA — recompress and compute difference"""
    original = Image.open(image_path).convert("RGB")

    # Re-save at lower quality
    original.save("temp_ela.jpg", "JPEG", quality=quality)
    resaved = Image.open("temp_ela.jpg")

    # Compute pixel difference
    ela_image = ImageChops.difference(original, resaved)

    # Amplify differences
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff if max_diff != 0 else 1

    ela_enhanced = ela_image.point(lambda x: x * scale)
    ela_enhanced.save("heatmap.png")

    # Score: average intensity of ELA image
    ela_array = np.array(ela_enhanced)
    ela_score = np.mean(ela_array) / 255.0

    return {
        "ela_score": round(ela_score, 4),
        "heatmap": "heatmap.png"
    }

# AI-based forgery detection
from transformers import pipeline
forgery_detector = pipeline("image-classification",
                            model="kumaran-0188/image_forgery_detector")
result = forgery_detector("document.jpg")
```

### Pip Packages Required

```bash
pip install pillow numpy transformers torch
```

---

## 🔷 STAGE 3 — AGENT 2: OCR (Text Extraction)

> **Goal**: Extract Name, DOB, UID, Address from documents

### Primary Model

| Field | Value |
|-------|-------|
| **Model** | `microsoft/trocr-base-printed` |
| **HF Link** | https://huggingface.co/microsoft/trocr-base-printed |
| **Type** | Vision Encoder-Decoder (OCR) |
| **Size** | ~650 MB |
| **Why** | Microsoft's Transformer OCR — best for printed text on documents |

### Additional OCR Models

| Model | HF Link | Purpose |
|-------|---------|---------|
| `microsoft/trocr-base-handwritten` | https://huggingface.co/microsoft/trocr-base-handwritten | For handwritten text on documents |
| `microsoft/trocr-large-printed` | https://huggingface.co/microsoft/trocr-large-printed | Higher accuracy, larger model (~1.3 GB) |
| `EasyOCR` (Python lib) | N/A (pip install) | Lightweight fallback, supports Hindi + English |

### Layout-Aware Model (For Structured Extraction)

| Field | Value |
|-------|-------|
| **Model** | `microsoft/layoutlmv3-base` |
| **HF Link** | https://huggingface.co/microsoft/layoutlmv3-base |
| **Type** | Document Understanding (layout + text) |
| **Size** | ~500 MB |
| **Why** | Understands document layout — knows WHERE each field is (name, DOB, UID position). Critical for Stage 4 cross-validation. |

### Python Code (Stage 3 - Agent 2)

```python
# Option A: TrOCR (Hugging Face — high accuracy)
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")

image = Image.open("aadhaar_cropped_line.jpg").convert("RGB")
pixel_values = processor(images=image, return_tensors="pt").pixel_values
generated_ids = model.generate(pixel_values)
text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(text)  # "Rajesh Kumar"

# Option B: EasyOCR (fallback — supports Hindi)
import easyocr
reader = easyocr.Reader(['en', 'hi'])
results = reader.readtext("aadhaar.jpg")
for (bbox, text, confidence) in results:
    print(f"{text} ({confidence:.2f})")

# Option C: Tesseract (system-level OCR)
import pytesseract
text = pytesseract.image_to_string(Image.open("aadhaar.jpg"), lang='eng+hin')
```

### Pip Packages Required

```bash
pip install transformers torch torchvision pillow easyocr pytesseract
```

> ⚠️ **Tesseract** must also be installed as a system binary (see main implementation plan).

---

## 🔷 STAGE 3 — AGENT 3: QR Decoder

> **Goal**: Decode QR code from Aadhaar and extract embedded fields

### No Hugging Face Model Needed ✅

Uses `pyzbar` library directly.

### Python Code (Stage 3 - Agent 3)

```python
from pyzbar.pyzbar import decode
from PIL import Image
import xml.etree.ElementTree as ET

def decode_aadhaar_qr(image_path):
    img = Image.open(image_path)
    decoded = decode(img)

    for obj in decoded:
        data = obj.data.decode('utf-8')
        # Aadhaar QR contains XML data
        try:
            root = ET.fromstring(data)
            return {
                "qr_name": root.attrib.get("name", ""),
                "qr_dob": root.attrib.get("dob", ""),
                "qr_gender": root.attrib.get("gender", ""),
                "qr_uid": root.attrib.get("uid", "")[-4:]  # Last 4 digits
            }
        except ET.ParseError:
            return {"qr_raw": data}

    return {"error": "No QR code found"}
```

### Pip Packages Required

```bash
pip install pyzbar pillow
```

> ⚠️ **Windows**: You need `zbar` DLL. Download from https://sourceforge.net/projects/zbar/

---

## 🔷 STAGE 3 — AGENT 4: EXIF Analysis

> **Goal**: Extract metadata and flag Photoshop-edited documents

### No Hugging Face Model Needed ✅

Uses `piexif` / `exifread` libraries.

### Python Code (Stage 3 - Agent 4)

```python
import exifread

def analyze_exif(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)

    software = str(tags.get("Image Software", "Unknown"))
    make = str(tags.get("Image Make", "Unknown"))
    date = str(tags.get("EXIF DateTimeOriginal", "Unknown"))

    # Flag suspicious software
    suspicious_keywords = ["photoshop", "gimp", "paint", "editor", "canva"]
    exif_flag = "suspicious" if any(
        kw in software.lower() for kw in suspicious_keywords
    ) else "clean"

    return {
        "software": software,
        "camera_make": make,
        "date_taken": date,
        "exif_flag": exif_flag,
        "has_exif": len(tags) > 0
    }
```

### Pip Packages Required

```bash
pip install exifread piexif
```

---

## 🔷 STAGE 3 — AGENT 5: Face / Deepfake Detection

> **Goal**: Detect if face on document is a deepfake or pasted

### Primary Model

| Field | Value |
|-------|-------|
| **Model** | `dima806/deepfake_vs_real_image_detection` |
| **HF Link** | https://huggingface.co/dima806/deepfake_vs_real_image_detection |
| **Type** | Image Classification (ViT) |
| **Base** | `google/vit-base-patch16-224-in21k` |
| **Size** | ~350 MB |
| **Why** | Fine-tuned ViT for Real vs Deepfake binary classification |

### Alternative Models

| Model | HF Link | Purpose | Size |
|-------|---------|---------|------|
| `prithivMLmods/Deep-Fake-Detector-v2-Model` | https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model | Updated deepfake detector V2 | ~350 MB |
| `google/vit-base-patch16-224-in21k` | https://huggingface.co/google/vit-base-patch16-224-in21k | Base ViT (fine-tune yourself on face data) | ~330 MB |

### Face Detection (Crop Face First)

| Library | Purpose |
|---------|---------|
| `deepface` | Detect + crop face from document image |
| `opencv-python` (Haar cascades) | Lightweight face detection fallback |

### Python Code (Stage 3 - Agent 5)

```python
# Step 1: Crop face from document
from deepface import DeepFace

def extract_face(image_path):
    """Extract face region from document"""
    faces = DeepFace.extract_faces(image_path, detector_backend="retinaface")
    if faces:
        face_img = faces[0]["face"]
        return face_img  # numpy array
    return None

# Step 2: Run deepfake detection
from transformers import pipeline

deepfake_detector = pipeline(
    "image-classification",
    model="dima806/deepfake_vs_real_image_detection"
)

result = deepfake_detector("cropped_face.jpg")
# result: [{'label': 'fake', 'score': 0.81}, {'label': 'real', 'score': 0.19}]

deepfake_score = next(r['score'] for r in result if r['label'] == 'fake')
print(f"Deepfake score: {deepfake_score}")  # 0.81
```

### Pip Packages Required

```bash
pip install transformers torch torchvision deepface pillow
```

---

## 🔷 STAGE 3 — AGENT 6: Voice Verification

> **Goal**: Compare user's voice with stored voice embedding

### Primary Model

| Field | Value |
|-------|-------|
| **Model** | `speechbrain/spkrec-ecapa-voxceleb` |
| **HF Link** | https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb |
| **Type** | Speaker Verification (ECAPA-TDNN) |
| **Size** | ~80 MB |
| **Why** | State-of-the-art speaker recognition model. Extracts voice embeddings and compares speakers. Trained on VoxCeleb dataset. |

### Alternative Models

| Model | HF Link | Purpose |
|-------|---------|---------|
| `speechbrain/spkrec-xvect-voxceleb` | https://huggingface.co/speechbrain/spkrec-xvect-voxceleb | X-vector based speaker verification |
| `Resemblyzer` (Python lib) | N/A (pip install) | Lightweight voice embedding extraction |

### Python Code (Stage 3 - Agent 6)

```python
# Option A: SpeechBrain (RECOMMENDED — higher accuracy)
from speechbrain.inference.speaker import SpeakerRecognition

verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

# Compare two audio files
score, prediction = verification.verify_files(
    "user_voice.wav",
    "reference_voice.wav"
)

print(f"Score: {score.item():.4f}")       # 0.85
print(f"Same speaker: {prediction.item()}")  # True

# Option B: Resemblyzer (lightweight fallback)
from resemblyzer import VoiceEncoder, preprocess_wav

encoder = VoiceEncoder()
wav1 = preprocess_wav("user_voice.wav")
wav2 = preprocess_wav("reference_voice.wav")

embed1 = encoder.embed_utterance(wav1)
embed2 = encoder.embed_utterance(wav2)

similarity = np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))
print(f"Voice similarity: {similarity:.4f}")  # 0.65
```

### Pip Packages Required

```bash
pip install speechbrain torchaudio resemblyzer librosa sounddevice
```

---

## 🔷 STAGE 4 — Cross-Validation

> **Goal**: Match OCR text vs QR data using fuzzy matching

### No Hugging Face Model Needed ✅

Uses `fuzzywuzzy` for string matching.

### Python Code (Stage 4)

```python
from fuzzywuzzy import fuzz

def cross_validate(ocr_data, qr_data):
    name_score = fuzz.ratio(ocr_data["name"].lower(), qr_data["qr_name"].lower())
    dob_match = ocr_data.get("dob") == qr_data.get("qr_dob")

    qr_ocr_match = name_score >= 85 and dob_match
    boost_applied = not qr_ocr_match

    return {
        "qr_ocr_match": qr_ocr_match,
        "name_similarity": name_score,
        "dob_match": dob_match,
        "boost_applied": boost_applied,
        "confidence": round(name_score / 100, 2)
    }
```

### Pip Packages Required

```bash
pip install fuzzywuzzy python-Levenshtein
```

---

## 🔷 STAGE 7 — Explainable Output (RAG)

> **Goal**: Generate human-readable fraud explanation

### Primary Model

| Field | Value |
|-------|-------|
| **Model** | `google/flan-t5-base` |
| **HF Link** | https://huggingface.co/google/flan-t5-base |
| **Type** | Text-to-Text Generation |
| **Size** | ~990 MB |
| **Why** | Lightweight instruction-following model. Can generate fraud explanations from structured signals. No GPU required. |

### Alternative Models

| Model | HF Link | Purpose | Size |
|-------|---------|---------|------|
| `google/flan-t5-small` | https://huggingface.co/google/flan-t5-small | Smaller, faster (hackathon mode) | ~300 MB |
| `microsoft/Phi-3-mini-4k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct | More powerful, needs GPU | ~7.6 GB |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | Small chat LLM | ~2.2 GB |

### Python Code (Stage 7)

```python
from transformers import pipeline

explainer = pipeline("text2text-generation", model="google/flan-t5-base")

def generate_explanation(signals):
    prompt = f"""You are a KYC fraud analyst. Based on the following signals, generate a clear explanation for the fraud decision.

Signals:
- OCR Name: {signals['ocr_name']}
- QR Name: {signals['qr_name']}
- Name Match: {signals['name_match']}%
- ELA Score: {signals['ela_score']}
- EXIF Software: {signals['exif_software']}
- Deepfake Score: {signals.get('deepfake_score', 'N/A')}
- Final Fraud Score: {signals['fraud_score']}
- Decision: {signals['decision']}

Write a 2-3 sentence explanation for a compliance officer:"""

    result = explainer(prompt, max_length=200)
    return result[0]['generated_text']

# Example usage
explanation = generate_explanation({
    "ocr_name": "Rajesh Kumar",
    "qr_name": "Ramesh Kumar",
    "name_match": 72,
    "ela_score": 0.72,
    "exif_software": "Adobe Photoshop",
    "deepfake_score": 0.81,
    "fraud_score": 82,
    "decision": "FORGED"
})
print(explanation)
```

### Pip Packages Required

```bash
pip install transformers torch sentencepiece
```

---

## 📊 MASTER SUMMARY TABLE

| Stage | Agent | Model / Library | HF Model ID | Size | Type |
|-------|-------|----------------|-------------|------|------|
| **0** | Doc Classifier | DiT / Indian ID Validator | `microsoft/dit-base-finetuned-rvlcdip` | 340 MB | HF Model |
| **0** | Aadhaar Detector | YOLOv8-nano | `arnabdhar/YOLOv8-nano-aadhar-card` | 25 MB | HF Model |
| **0** | PAN Detector | YOLO | `foduucom/pan-card-detection` | 25 MB | HF Model |
| **1** | Quality Gate | OpenCV | N/A | 0 MB | Python lib |
| **2** | Preprocessor | OpenCV + Pillow | N/A | 0 MB | Python lib |
| **3.1** | ELA Forensics | Forgery Detector | `kumaran-0188/image_forgery_detector` | 90 MB | HF Model |
| **3.2** | OCR (Printed) | TrOCR | `microsoft/trocr-base-printed` | 650 MB | HF Model |
| **3.2** | OCR (Handwritten) | TrOCR | `microsoft/trocr-base-handwritten` | 650 MB | HF Model |
| **3.2** | Layout Understanding | LayoutLMv3 | `microsoft/layoutlmv3-base` | 500 MB | HF Model |
| **3.2** | OCR (Hindi+English) | EasyOCR | N/A (pip) | 40 MB | Python lib |
| **3.2** | OCR (Fallback) | Tesseract | N/A (system) | 30 MB | System binary |
| **3.3** | QR Decoder | pyzbar | N/A (pip) | 0 MB | Python lib |
| **3.4** | EXIF Analyzer | exifread | N/A (pip) | 0 MB | Python lib |
| **3.5** | Deepfake Detector | ViT | `dima806/deepfake_vs_real_image_detection` | 350 MB | HF Model |
| **3.5** | Deepfake V2 | ViT | `prithivMLmods/Deep-Fake-Detector-v2-Model` | 350 MB | HF Model |
| **3.5** | Face Detection | DeepFace | N/A (pip) | 90 MB | Python lib |
| **3.6** | Voice Verify | ECAPA-TDNN | `speechbrain/spkrec-ecapa-voxceleb` | 80 MB | HF Model |
| **3.6** | Voice Fallback | Resemblyzer | N/A (pip) | 25 MB | Python lib |
| **4** | Cross-Validation | fuzzywuzzy | N/A (pip) | 0 MB | Python lib |
| **5-6** | Scoring + Decision | Pure Python | N/A | 0 MB | Python code |
| **7** | RAG Explainer | Flan-T5 | `google/flan-t5-base` | 990 MB | HF Model |
| **8** | Audit Logger | SQLAlchemy | N/A (pip) | 0 MB | Python lib |

---

## 💾 Total Estimated Download Size

| Category | Size |
|----------|------|
| **HF Models (all)** | ~3.5 GB |
| **HF Models (essential only)** | ~1.8 GB |
| **Python packages** | ~500 MB |
| **Tesseract OCR (system)** | ~30 MB |
| **Total (full)** | **~4 GB** |
| **Total (essential)** | **~2.3 GB** |

---

## 🔧 ONE-SHOT INSTALL COMMAND (All Python Packages)

```bash
pip install transformers torch torchvision torchaudio huggingface_hub speechbrain opencv-python pillow scikit-image numpy scipy pytesseract easyocr pyzbar piexif exifread deepface fuzzywuzzy python-Levenshtein pymupdf fastapi uvicorn python-multipart sqlalchemy python-dotenv loguru resemblyzer librosa sounddevice sentencepiece
```

---

## ⚠️ IMPORTANT NOTES

> **Tesseract**: Must be installed separately as a system binary on Windows.
> Download: https://github.com/UB-Mannheim/tesseract/wiki

> **pyzbar on Windows**: Needs `zbar.dll` manually placed in PATH.
> Download: https://sourceforge.net/projects/zbar/

> **GPU Acceleration**: If you have an NVIDIA GPU, install PyTorch with CUDA:
> ```bash
> pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```

> **First Run**: HF models auto-download on first use. First run will be slow (~5-10 min depending on internet speed).
