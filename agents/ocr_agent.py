"""
Agent 2 — OCR Text Extraction

Primary:  EasyOCR (supports Hindi + English, no system binary needed)
Fallback: Tesseract (if installed)

Replaces TrOCR (650 MB model) — EasyOCR is faster, more robust for
full-page Indian documents, and supports Hindi out of the box.

After raw text extraction, regex patterns pull structured fields:
  - Name, DOB, UID (Aadhaar)
  - PAN number (PAN card)
  - Passport number, nationality (Passport)
"""

import re
from loguru import logger


# ── Lazy-loaded readers (initialized on first call) ──
_easyocr_reader = None
_tesseract_available = None


def _get_easyocr_reader():
    """Lazy-init EasyOCR reader (downloads ~40 MB on first use)."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(["en", "hi"], gpu=False)
            logger.info("OCR Agent: EasyOCR reader initialized (en+hi)")
        except ImportError:
            logger.error("OCR Agent: easyocr not installed")
            return None
        except Exception as e:
            logger.error(f"OCR Agent: EasyOCR init failed — {e}")
            return None
    return _easyocr_reader


def _is_tesseract_available():
    """Check if Tesseract is installed and accessible."""
    global _tesseract_available
    if _tesseract_available is None:
        try:
            import pytesseract
            from config import TESSERACT_CMD
            from pathlib import Path

            if Path(TESSERACT_CMD).exists():
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

            # Quick test
            pytesseract.get_tesseract_version()
            _tesseract_available = True
            logger.info("OCR Agent: Tesseract is available")
        except Exception:
            _tesseract_available = False
            logger.info("OCR Agent: Tesseract not available (fallback only)")
    return _tesseract_available


def extract_text(image_path: str) -> dict:
    """
    Extract raw text from a document image.

    Tries EasyOCR first, falls back to Tesseract.

    Returns:
        dict with: raw_text, method, confidence, lines
    """
    # ── Try EasyOCR ──
    reader = _get_easyocr_reader()
    if reader is not None:
        try:
            results = reader.readtext(image_path)
            lines = []
            total_conf = 0.0
            for bbox, text, conf in results:
                lines.append({"text": text, "confidence": round(conf, 3)})
                total_conf += conf

            raw_text = " ".join(item["text"] for item in lines)
            avg_conf = total_conf / len(lines) if lines else 0.0

            logger.info(
                f"OCR Agent [EasyOCR]: Extracted {len(lines)} lines, "
                f"avg_conf={avg_conf:.2f}"
            )
            return {
                "raw_text": raw_text,
                "method": "easyocr",
                "confidence": round(avg_conf, 3),
                "line_count": len(lines),
                "lines": lines,
            }
        except Exception as e:
            logger.warning(f"OCR Agent: EasyOCR failed — {e}")

    # ── Fallback: Tesseract ──
    if _is_tesseract_available():
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            raw_text = pytesseract.image_to_string(img, lang="eng+hin")

            logger.info(f"OCR Agent [Tesseract]: Extracted {len(raw_text)} chars")
            return {
                "raw_text": raw_text.strip(),
                "method": "tesseract",
                "confidence": 0.0,  # Tesseract doesn't return per-line confidence easily
                "line_count": len(raw_text.strip().split("\n")),
                "lines": [],
            }
        except Exception as e:
            logger.error(f"OCR Agent: Tesseract also failed — {e}")

    # ── Both failed ──
    logger.error("OCR Agent: All OCR methods failed")
    return {
        "raw_text": "",
        "method": "none",
        "confidence": 0.0,
        "line_count": 0,
        "lines": [],
        "error": "No OCR engine available",
    }


# ── Field Extraction Patterns ──

_AADHAAR_UID = re.compile(r"\b(\d{4}\s?\d{4}\s?\d{4})\b")
_PAN_NUMBER = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")
_DOB_PATTERNS = [
    re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b"),   # DD/MM/YYYY or DD-MM-YYYY
    re.compile(r"\b(\d{4}[/-]\d{2}[/-]\d{2})\b"),   # YYYY-MM-DD
    re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b"),        # DD.MM.YYYY
]
_PASSPORT_NUMBER = re.compile(r"\b([A-Z]\d{7})\b")
_NAME_LABEL = re.compile(
    r"(?:name|naam)\s*[:\-]?\s*([A-Za-z\s]+)",
    re.IGNORECASE,
)


def extract_fields(raw_text: str, document_type: str = "unknown") -> dict:
    """
    Extract structured fields from raw OCR text based on document type.

    Returns:
        dict with: name, dob, uid, pan_number, passport_number (as applicable)
    """
    fields = {
        "name": None,
        "dob": None,
        "uid": None,
        "pan_number": None,
        "passport_number": None,
    }

    # ── Name ──
    name_match = _NAME_LABEL.search(raw_text)
    if name_match:
        name = name_match.group(1).strip()
        # Clean up: remove trailing garbage
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) > 2:
            fields["name"] = name

    # ── DOB ──
    for pattern in _DOB_PATTERNS:
        dob_match = pattern.search(raw_text)
        if dob_match:
            fields["dob"] = dob_match.group(1)
            break

    # ── UID (Aadhaar) ──
    if document_type in ("aadhaar", "unknown"):
        uid_match = _AADHAAR_UID.search(raw_text)
        if uid_match:
            fields["uid"] = uid_match.group(1).replace(" ", "")

    # ── PAN Number ──
    if document_type in ("pan", "unknown"):
        pan_match = _PAN_NUMBER.search(raw_text)
        if pan_match:
            fields["pan_number"] = pan_match.group(1)

    # ── Passport Number ──
    if document_type in ("passport", "unknown"):
        pp_match = _PASSPORT_NUMBER.search(raw_text)
        if pp_match:
            fields["passport_number"] = pp_match.group(1)

    logger.info(f"OCR Fields: {fields}")
    return fields
