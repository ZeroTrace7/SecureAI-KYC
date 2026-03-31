"""
Stage 4 — Cross-Validation (OCR vs QR Data)

This is the KILLER FEATURE — matches OCR-extracted text against
QR-decoded data using fuzzy string matching.

A mismatch here is the strongest signal of document tampering.
"""

from fuzzywuzzy import fuzz
from loguru import logger

from config import NAME_MATCH_THRESHOLD


def cross_validate(ocr_data: dict, qr_data: dict) -> dict:
    """
    Cross-validate OCR-extracted fields against QR-embedded data.

    Args:
        ocr_data: {'name': str, 'dob': str, 'uid': str, ...}
        qr_data:  {'qr_name': str, 'qr_dob': str, 'qr_uid': str, ...}

    Returns:
        dict with match scores and mismatch flags.
    """
    result = {
        "qr_ocr_match": True,
        "name_similarity": 0,
        "dob_match": False,
        "uid_match": False,
        "mismatches": [],
        "confidence": 0.0,
    }

    # ── If no QR data available, skip cross-validation ──
    has_qr = qr_data.get("has_qr", False) if qr_data else False
    if not qr_data or qr_data.get("error") or not has_qr:
        logger.warning("Cross-validation: No QR data available, skipping")
        return {
            **result,
            "qr_ocr_match": None,  # indeterminate — scorer will skip this signal
            "confidence": 0.0,
            "mismatches": ["QR data not available for cross-validation"],
        }

    # ── Name matching (fuzzy) ──
    ocr_name = (ocr_data.get("name") or "").strip().lower()
    qr_name = (qr_data.get("qr_name") or "").strip().lower()

    if ocr_name and qr_name:
        # Use token_sort_ratio for name order variations
        # e.g. "Rajesh Kumar" vs "Kumar Rajesh"
        name_score = max(
            fuzz.ratio(ocr_name, qr_name),
            fuzz.token_sort_ratio(ocr_name, qr_name),
        )
        result["name_similarity"] = name_score

        if name_score < NAME_MATCH_THRESHOLD:
            result["mismatches"].append(
                f"Name mismatch: OCR='{ocr_data.get('name')}' vs QR='{qr_data.get('qr_name')}' "
                f"(similarity={name_score}%, threshold={NAME_MATCH_THRESHOLD}%)"
            )
            result["qr_ocr_match"] = False
    else:
        result["mismatches"].append("Name field missing from OCR or QR data")
        result["qr_ocr_match"] = False

    # ── DOB matching (exact) ──
    ocr_dob = (ocr_data.get("dob") or "").strip()
    qr_dob = (qr_data.get("qr_dob") or "").strip()

    if ocr_dob and qr_dob:
        # Normalize date separators: 01/01/1990 vs 01-01-1990
        ocr_dob_norm = ocr_dob.replace("/", "-").replace(".", "-")
        qr_dob_norm = qr_dob.replace("/", "-").replace(".", "-")
        result["dob_match"] = ocr_dob_norm == qr_dob_norm

        if not result["dob_match"]:
            result["mismatches"].append(
                f"DOB mismatch: OCR='{ocr_dob}' vs QR='{qr_dob}'"
            )
            result["qr_ocr_match"] = False
    else:
        result["mismatches"].append("DOB field missing from OCR or QR data")
        result["qr_ocr_match"] = False

    # ── UID matching (last 4 digits) ──
    ocr_uid = (ocr_data.get("uid") or "").replace(" ", "")[-4:]
    qr_uid = (qr_data.get("qr_uid") or "").replace(" ", "")[-4:]

    if ocr_uid and qr_uid:
        result["uid_match"] = ocr_uid == qr_uid
        if not result["uid_match"]:
            result["mismatches"].append(
                f"UID mismatch: OCR last4='{ocr_uid}' vs QR last4='{qr_uid}'"
            )
            result["qr_ocr_match"] = False
    else:
        result["mismatches"].append("UID field missing from OCR or QR data")
        result["qr_ocr_match"] = False

    # ── Overall confidence ──
    if result["qr_ocr_match"] is True and not result["mismatches"]:
        result["confidence"] = round(result["name_similarity"] / 100, 2)
    elif result["qr_ocr_match"] is False:
        result["confidence"] = 0.0

    logger.info(
        f"Cross-validation: match={result['qr_ocr_match']} "
        f"name_sim={result['name_similarity']}% "
        f"dob={result['dob_match']} uid={result['uid_match']}"
    )

    return result
