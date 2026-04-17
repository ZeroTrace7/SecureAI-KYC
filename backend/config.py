"""
SecureAI-KYC — Central Configuration
Loads settings from .env file with sensible defaults.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env")


# ─── Server ───────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ─── Paths ────────────────────────────────────────────────
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", "./models"))
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)

# ─── Database ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./audit.db")

# ─── CORS ─────────────────────────────────────────────────
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
]

# ─── Quality Gate Thresholds ──────────────────────────────
BLUR_THRESHOLD = float(os.getenv("BLUR_THRESHOLD", "100"))
MIN_RESOLUTION = int(os.getenv("MIN_RESOLUTION", "300"))
BRIGHTNESS_MIN = float(os.getenv("BRIGHTNESS_MIN", "40"))
BRIGHTNESS_MAX = float(os.getenv("BRIGHTNESS_MAX", "245"))

# ─── Fraud Scoring Thresholds ─────────────────────────────
ELA_THRESHOLD = float(os.getenv("ELA_THRESHOLD", "0.12"))
DEEPFAKE_THRESHOLD = float(os.getenv("DEEPFAKE_THRESHOLD", "0.5"))
FRAUD_SCORE_THRESHOLD = float(os.getenv("FRAUD_SCORE_THRESHOLD", "50"))
NAME_MATCH_THRESHOLD = int(os.getenv("NAME_MATCH_THRESHOLD", "85"))

# ─── Fraud Signal Weights ─────────────────────────────
# Weights are normalized by actual signals present, so they don't need to sum to 1.0.
# Higher weight = more influence when that signal fires.
WEIGHT_QR_OCR_MISMATCH = float(os.getenv("WEIGHT_QR_OCR_MISMATCH", "0.25"))
WEIGHT_ELA = float(os.getenv("WEIGHT_ELA", "0.18"))
WEIGHT_EXIF = float(os.getenv("WEIGHT_EXIF", "0.10"))
WEIGHT_DEEPFAKE = float(os.getenv("WEIGHT_DEEPFAKE", "0.07"))
WEIGHT_SIGNATURE_SEAL = float(os.getenv("WEIGHT_SIGNATURE_SEAL", "0.22"))
WEIGHT_TEXT_INTEGRITY = float(os.getenv("WEIGHT_TEXT_INTEGRITY", "0.10"))
WEIGHT_BLOCKCHAIN = float(os.getenv("WEIGHT_BLOCKCHAIN", "0.05"))
WEIGHT_STRUCTURED_VALIDATION = float(os.getenv("WEIGHT_STRUCTURED_VALIDATION", "0.20"))

# ─── Feature Flags ────────────────────────────────────────
# Toggle optional / risky features
ENABLE_VOICE = os.getenv("ENABLE_VOICE", "false").lower() == "true"
# ML Forgery disabled: kumaran-0188/image_forgery_detector is TF/Keras,
# incompatible with transformers.pipeline() in our PyTorch environment.
# Re-enable when a PyTorch-native forgery model is configured.
ENABLE_ML_FORGERY = os.getenv("ENABLE_ML_FORGERY", "false").lower() == "true"
ENABLE_DEEPFAKE = os.getenv("ENABLE_DEEPFAKE", "true").lower() == "true"
ENABLE_SIGNATURE_SEAL = os.getenv("ENABLE_SIGNATURE_SEAL", "true").lower() == "true"
ENABLE_TEXT_INTEGRITY = os.getenv("ENABLE_TEXT_INTEGRITY", "true").lower() == "true"
ENABLE_BLOCKCHAIN = os.getenv("ENABLE_BLOCKCHAIN", "true").lower() == "true"
ENABLE_STRUCTURED_VALIDATION = os.getenv("ENABLE_STRUCTURED_VALIDATION", "true").lower() == "true"

# ─── Gemini API (Explainability) ──────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ─── Hugging Face ─────────────────────────────────────────
os.environ.setdefault("HF_HOME", str(MODEL_CACHE_DIR))
os.environ.setdefault("TRANSFORMERS_CACHE", str(MODEL_CACHE_DIR))

# ─── Deepfake Model ──────────────────────────────────────
DEEPFAKE_MODEL_ID = "dima806/deepfake_vs_real_image_detection"
MIN_FACE_SIZE = int(os.getenv("MIN_FACE_SIZE", "80"))  # px, skip if smaller

# ─── ML Forgery Model (optional) ─────────────────────────
FORGERY_MODEL_ID = "kumaran-0188/image_forgery_detector"
