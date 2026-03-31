"""
Stage 0 — Rule-Based Document Classifier

Replaces the 340 MB DiT model with fast heuristics:
  1. QR code detected  → Aadhaar
  2. PAN regex matched → PAN
  3. Passport keywords  → Passport
  4. Salary keywords    → Salary Slip (English + French, OCR-resilient)
  5. Unknown fallback

Runs in < 200 ms on CPU (vs ~3 sec for DiT).
"""

import re
import unicodedata

from loguru import logger

# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════

def _strip_accents(text: str) -> str:
    """Remove accents/diacritics so 'sécurité' matches 'securite'."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ═══════════════════════════════════════════════════════════
#  Patterns
# ═══════════════════════════════════════════════════════════

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

# ── English salary/payslip keywords ──
_SALARY_KEYWORDS_EN = [
    "salary slip",
    "pay slip",
    "payslip",
    "gross salary",
    "net salary",
    "basic pay",
    "earnings",
    "deductions",
    "employee id",
    "provident fund",
    "take home pay",
]

# ── French payslip keywords (accent-stripped for OCR resilience) ──
# These are matched against accent-stripped OCR text
_SALARY_KEYWORDS_FR = [
    "bulletin de paie",
    "bulletin de paye",
    "salaire brut",
    "salaire de base",
    "net a payer",           # accent-stripped version of "net à payer"
    "net imposable",
    "cotisations",
    "part salariale",
    "part patronale",
    "employeur",
    "salarie",               # accent-stripped version of "salarié"
    "securite sociale",      # accent-stripped
    "assurance maladie",
    "assurance veuvage",
    "assurance vieillesse",
    "allocation familiales",
    "virement bancaire",
    "total des cotisations",
    "accidents du travail",
    "aide au logement",
    "csg deductible",        # accent-stripped
    "crds",
    "av deplafonee",         # accent-stripped
    "av plafonee",
]

# ── Structural regex patterns for French payslips ──
# These catch keyword fragments even when OCR breaks words apart
_SALARY_REGEX_FR = [
    re.compile(r"bulletin\s+de\s+pai[es]", re.IGNORECASE),
    re.compile(r"salaire\s+brut", re.IGNORECASE),
    re.compile(r"salaire\s+de\s+base", re.IGNORECASE),
    re.compile(r"net\s+[àa]\s+payer", re.IGNORECASE),
    re.compile(r"net\s+imposable", re.IGNORECASE),
    re.compile(r"total\s+des?\s+cotisations?", re.IGNORECASE),
    re.compile(r"num[eé]ro\s+ape", re.IGNORECASE),
    re.compile(r"num[eé]ro\s+siret", re.IGNORECASE),
    re.compile(r"num[eé]ro\s+ss", re.IGNORECASE),
    re.compile(r"part\s+salarial", re.IGNORECASE),
    re.compile(r"part\s+patronal", re.IGNORECASE),
    re.compile(r"cp\s+et\s+ville", re.IGNORECASE),
    re.compile(r"hs\s+[àa]\s+25", re.IGNORECASE),  # "HS à 25%"
    re.compile(r"conserver\s+sans\s+limitation", re.IGNORECASE),  # Footer
]

_UTILITY_KEYWORDS = [
    "electricity bill",
    "water bill",
    "gas bill",
    "utility bill",
    "consumer number",
    "meter reading",
    "billing period",
    "units consumed",
    "amount due",
    "previous reading",
    "current reading",
]

_INVOICE_KEYWORDS = [
    "invoice",
    "receipt",
    "total amount",
    "subtotal",
    "sub total",
    "tax",
    "gst",
    "gstin",
    "bill to",
    "ship to",
    "invoice number",
    "invoice date",
    "due date",
    "payment terms",
    "quantity",
    "unit price",
    "amount payable",
    "tax invoice",
    "proforma invoice",
    "receipt no",
]


# ═══════════════════════════════════════════════════════════
#  Main classifier
# ═══════════════════════════════════════════════════════════

def _count_salary_hits(ocr_text: str) -> int:
    """
    Count French + English salary keyword hits using both
    exact matching and regex patterns, with accent stripping.
    """
    text_lower = ocr_text.lower()
    text_stripped = _strip_accents(text_lower)
    hits = 0

    # English keywords (exact match on lowercase)
    for kw in _SALARY_KEYWORDS_EN:
        if kw in text_lower:
            hits += 1

    # French keywords (match on accent-stripped text)
    for kw in _SALARY_KEYWORDS_FR:
        if kw in text_stripped:
            hits += 1

    # Regex patterns (match on original text — patterns handle accents)
    for pattern in _SALARY_REGEX_FR:
        if pattern.search(ocr_text):
            hits += 1

    return hits


def is_payslip_like(ocr_text: str) -> bool:
    """
    Check if OCR text looks like a payslip even if full classification failed.
    Used as a fallback to route 'other' docs to structured validation.
    """
    return _count_salary_hits(ocr_text) >= 1


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

    # ── Rule 4: Salary slip (French + English, OCR-resilient) ──
    salary_hits = _count_salary_hits(ocr_text)
    if salary_hits >= 2:
        conf = min(0.95, 0.60 + salary_hits * 0.05)
        logger.info(f"Classifier: Salary Slip detected (hits={salary_hits})")
        return {
            "document_type": "salary_slip",
            "confidence": round(conf, 2),
            "method": "rule:salary_keywords",
        }

    # ── Rule 5: Utility bill keywords ──
    utility_hits = sum(1 for kw in _UTILITY_KEYWORDS if kw in text_lower)
    if utility_hits >= 2:
        conf = min(0.95, 0.60 + utility_hits * 0.07)
        logger.info(f"Classifier: Utility Bill detected (hits={utility_hits})")
        return {
            "document_type": "utility_bill",
            "confidence": round(conf, 2),
            "method": "rule:utility_keywords",
        }

    # ── Rule 6: Aadhaar without QR (UID pattern alone) ──
    if _AADHAAR_UID_REGEX.search(ocr_text):
        if "aadhaar" in text_lower or "unique identification" in text_lower:
            logger.info("Classifier: Aadhaar detected (UID + keyword, no QR)")
            return {
                "document_type": "aadhaar",
                "confidence": 0.75,
                "method": "rule:uid_pattern+keyword",
            }

    # ── Rule 7: Invoice / Receipt keywords ──
    invoice_hits = sum(1 for kw in _INVOICE_KEYWORDS if kw in text_lower)
    if invoice_hits >= 2:
        conf = min(0.95, 0.60 + invoice_hits * 0.06)
        logger.info(f"Classifier: Invoice/Receipt detected (hits={invoice_hits})")
        return {
            "document_type": "invoice",
            "confidence": round(conf, 2),
            "method": "rule:invoice_keywords",
        }

    # ── Fallback: classify as 'other' instead of 'unknown' ──
    logger.warning("Classifier: Could not determine document type — classifying as 'other'")
    return {
        "document_type": "other",
        "confidence": 0.0,
        "method": "rule:none_matched",
    }
