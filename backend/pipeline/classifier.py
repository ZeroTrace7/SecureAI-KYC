"""
Stage 0 — Rule-Based Document Classifier

Replaces the 340 MB DiT model with fast heuristics:
  1. QR code detected  → Aadhaar
  2. PAN regex matched → PAN
  3. Passport keywords  → Passport
  4. Salary keywords    → Salary Slip
  5. Unknown fallback

Runs in < 200 ms on CPU (vs ~3 sec for DiT).
"""

import re

from loguru import logger

# PAN format: 5 letters, 4 digits, 1 letter  (e.g. ABCDE1234F)
_PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# Aadhaar UID: 12 digits optionally grouped as 4-4-4
_AADHAAR_UID_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")

_PASSPORT_KEYWORDS = [
    "republic of india",
    "passport",
    "nationality",
    "date of issue",
    "date of expiry",
    "place of birth",
    "type p",
    "surname",
    "given name",
]

_SALARY_KEYWORDS = [
    "salary slip",
    "pay slip",
    "gross salary",
    "net salary",
    "basic pay",
    "earnings",
    "deductions",
    "employee id",
]


def classify_document(ocr_text: str, has_qr: bool = False) -> dict:
    """
    Classify an Indian KYC document using rule-based heuristics.

    Args:
        ocr_text: Raw text extracted from the document (via EasyOCR/Tesseract).
        has_qr:   Whether a QR code was detected on the document.

    Returns:
        dict with keys: document_type, confidence, method
    """
    text_lower = ocr_text.lower()

    # ── Rule 1: QR present → strong Aadhaar signal ──
    if has_qr and _AADHAAR_UID_REGEX.search(ocr_text):
        logger.info("Classifier: Aadhaar detected (QR + UID pattern)")
        return {
            "document_type": "aadhaar",
            "confidence": 0.95,
            "method": "rule:qr+uid_pattern",
        }

    if has_qr:
        logger.info("Classifier: Aadhaar detected (QR present)")
        return {
            "document_type": "aadhaar",
            "confidence": 0.85,
            "method": "rule:qr_present",
        }

    # ── Rule 2: PAN pattern ──
    if _PAN_REGEX.search(ocr_text):
        # Double-check with keyword
        if "income tax" in text_lower or "permanent account" in text_lower:
            conf = 0.95
        else:
            conf = 0.80
        logger.info(f"Classifier: PAN detected (confidence={conf})")
        return {
            "document_type": "pan",
            "confidence": conf,
            "method": "rule:pan_regex",
        }

    # ── Rule 3: Passport keywords ──
    passport_hits = sum(1 for kw in _PASSPORT_KEYWORDS if kw in text_lower)
    if passport_hits >= 3:
        conf = min(0.95, 0.60 + passport_hits * 0.07)
        logger.info(f"Classifier: Passport detected (hits={passport_hits})")
        return {
            "document_type": "passport",
            "confidence": round(conf, 2),
            "method": "rule:passport_keywords",
        }

    # ── Rule 4: Salary slip keywords ──
    salary_hits = sum(1 for kw in _SALARY_KEYWORDS if kw in text_lower)
    if salary_hits >= 3:
        conf = min(0.95, 0.60 + salary_hits * 0.07)
        logger.info(f"Classifier: Salary Slip detected (hits={salary_hits})")
        return {
            "document_type": "salary_slip",
            "confidence": round(conf, 2),
            "method": "rule:salary_keywords",
        }

    # ── Rule 5: Aadhaar without QR (UID pattern alone) ──
    if _AADHAAR_UID_REGEX.search(ocr_text):
        if "aadhaar" in text_lower or "unique identification" in text_lower:
            logger.info("Classifier: Aadhaar detected (UID + keyword, no QR)")
            return {
                "document_type": "aadhaar",
                "confidence": 0.75,
                "method": "rule:uid_pattern+keyword",
            }

    # ── Fallback ──
    logger.warning("Classifier: Could not determine document type")
    return {
        "document_type": "unknown",
        "confidence": 0.0,
        "method": "rule:none_matched",
    }
