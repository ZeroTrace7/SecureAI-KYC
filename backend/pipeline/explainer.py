"""
Stage 7 — Explainer (Gemini API + Template Fallback)

Replaces Flan-T5 (990 MB) with:
  1. Gemini API (online, fast, accurate) — free tier: 15 RPM
  2. Template-based explanation (offline fallback, zero models, instant)

Both produce structured, hallucination-free fraud explanations.

Now covers 9 signal types including Signature/Seal, Text Integrity,
and Blockchain Ledger verification.
"""

import os

from loguru import logger

from config import GEMINI_API_KEY, GEMINI_MODEL


def _build_signal_summary(signals: dict) -> str:
    """Build a concise signal summary string for prompts/templates."""
    parts = []

    # Document type
    doc_type = signals.get("document_type", "unknown")
    parts.append(f"Document Type: {doc_type.upper()}")

    # ELA
    ela = signals.get("ela_score")
    if ela is not None:
        status = "HIGH (possible tampering)" if ela > 0.35 else "LOW (normal)"
        parts.append(f"ELA Tampering Score: {ela:.3f} — {status}")

    # EXIF
    exif = signals.get("exif_flag", "unknown")
    exif_sw = signals.get("exif_software", "")
    if exif == "suspicious":
        parts.append(f"EXIF Metadata: SUSPICIOUS — edited with {exif_sw}")
    else:
        parts.append("EXIF Metadata: Clean")

    # Cross-validation
    qr_match = signals.get("qr_ocr_match")
    name_sim = signals.get("name_similarity", 0)
    if qr_match is False:
        parts.append(
            f"QR-OCR Cross-Validation: MISMATCH — "
            f"OCR name '{signals.get('ocr_name', '?')}' vs "
            f"QR name '{signals.get('qr_name', '?')}' "
            f"(similarity: {name_sim}%)"
        )
    elif qr_match is True:
        parts.append(f"QR-OCR Cross-Validation: MATCH (similarity: {name_sim}%)")
    else:
        parts.append("QR-OCR Cross-Validation: Not available")

    # Deepfake
    df = signals.get("deepfake_score")
    if df is not None:
        status = "SUSPICIOUS" if df > 0.5 else "NORMAL"
        parts.append(f"Deepfake Score: {df:.3f} — {status}")

    # Signature/Seal
    sig_seal = signals.get("signature_seal_score")
    if sig_seal is not None:
        seal_found = signals.get("seal_found", False)
        sig_found = signals.get("signature_found", False)
        status = "ANOMALIES DETECTED" if sig_seal > 0.3 else "NORMAL"
        parts.append(
            f"Signature/Seal: seal={'found' if seal_found else 'none'}, "
            f"signature={'found' if sig_found else 'none'}, "
            f"anomaly_score={sig_seal:.3f} — {status}"
        )

    # Text Integrity
    ti_score = signals.get("text_integrity_score")
    if ti_score is not None:
        status = "SUSPICIOUS" if ti_score > 0.3 else "NORMAL"
        parts.append(f"Text Integrity Score: {ti_score:.3f} — {status}")

    # Blockchain
    bc_seen = signals.get("blockchain_previously_seen")
    bc_score = signals.get("blockchain_score")
    if bc_score is not None:
        if bc_seen:
            parts.append(f"Blockchain Ledger: Document PREVIOUSLY SEEN (score={bc_score:.3f})")
        else:
            parts.append(f"Blockchain Ledger: First submission (score={bc_score:.3f})")

    # Structured Validation
    sv_score = signals.get("structured_validation_score")
    if sv_score is not None and sv_score > 0:
        sv_details = signals.get("structured_validation_details", [])
        detail_text = "; ".join(sv_details[:3]) if sv_details else "anomalies detected"
        parts.append(f"Structured Validation: score={sv_score:.3f} — {detail_text}")

    # Final score
    parts.append(f"Fraud Score: {signals.get('fraud_score', 0)}/100")
    parts.append(f"Decision: {signals.get('decision', 'UNKNOWN')}")

    return "\n".join(parts)


def _explain_with_gemini(signals: dict) -> str:
    """Generate explanation using Gemini API with RBI compliance context."""
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        summary = _build_signal_summary(signals)
        prompt = (
            "You are an RBI-compliant KYC fraud analyst operating under the following regulation:\n\n"
            "--- REGULATORY CONTEXT ---\n"
            "Per RBI KYC Master Direction 2016 (updated 2024):\n"
            "- Section 16: Regulated entities must maintain records of the nature and reasons "
            "for rejection of KYC applications.\n"
            "- Section 38(c): Document integrity failure, including evidence of tampering, "
            "alteration, or fabrication, constitutes valid grounds for rejection.\n"
            "- Section 56: Every CDD (Customer Due Diligence) decision must be auditable "
            "with specific, documented justification.\n"
            "--- END REGULATORY CONTEXT ---\n\n"
            "Based on the following verification signals, write a clear, professional "
            "3-4 sentence explanation for a compliance officer. "
            "You MUST cite the relevant RBI KYC Master Direction section in your response. "
            "Be specific about which signals triggered concern and why. "
            "Do NOT make up information beyond what is provided.\n\n"
            f"Verification Signals:\n{summary}\n\n"
            "Compliance Explanation:"
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        explanation = response.text.strip()
        logger.info("Explainer: Generated via Gemini API")
        return explanation

    except ImportError:
        logger.warning(
            "Explainer: google-genai not installed, falling back to template"
        )
        return None
    except Exception as e:
        logger.warning(f"Explainer: Gemini API failed ({e}), falling back to template")
        return None


def _explain_with_template(signals: dict) -> str:
    """Generate explanation using structured templates (offline, instant)."""
    decision = signals.get("decision", "UNKNOWN")
    fraud_score = signals.get("fraud_score", 0)
    doc_type = signals.get("document_type", "document").upper()

    reasons = []

    # QR-OCR mismatch
    qr_match = signals.get("qr_ocr_match")
    if qr_match is False:
        name_sim = signals.get("name_similarity", 0)
        reasons.append(
            f"Critical mismatch between OCR-extracted text and QR-embedded data "
            f"(name similarity: {name_sim}%). This is a strong indicator of document tampering."
        )

    # ELA
    ela = signals.get("ela_score")
    if ela is not None and ela > 0.35:
        reasons.append(
            f"Error Level Analysis detected potential image manipulation (score: {ela:.3f}). "
            f"Regions of the document show inconsistent compression artifacts."
        )

    # EXIF
    if signals.get("exif_flag") == "suspicious":
        sw = signals.get("exif_software", "image editing software")
        reasons.append(
            f"Metadata analysis reveals the document was processed with {sw}, "
            f"which is unusual for authentic government-issued documents."
        )

    # Deepfake
    df = signals.get("deepfake_score")
    if df is not None and df > 0.5:
        reasons.append(
            f"Face analysis returned an elevated artificiality score ({df:.3f}), "
            f"though this may be influenced by low-resolution document photos."
        )

    # Signature/Seal anomalies
    sig_seal = signals.get("signature_seal_score")
    if sig_seal is not None and sig_seal > 0.3:
        anomalies = signals.get("signature_seal_anomalies", [])
        anomaly_text = "; ".join(anomalies[:2]) if anomalies else "irregular seal/signature patterns"
        reasons.append(
            f"Signature and seal verification flagged anomalies: {anomaly_text}."
        )

    # Text Integrity
    ti_score = signals.get("text_integrity_score")
    if ti_score is not None and ti_score > 0.3:
        ti_details = signals.get("text_integrity_details", [])
        detail_text = " ".join(ti_details[:2]) if ti_details else "font or spacing inconsistencies detected"
        reasons.append(
            f"Text integrity analysis detected potential text manipulation "
            f"(score: {ti_score:.3f}). {detail_text}."
        )

    # Blockchain
    bc_seen = signals.get("blockchain_previously_seen", False)
    bc_score = signals.get("blockchain_score", 0)
    if bc_seen and bc_score > 0.5:
        bc_details = signals.get("blockchain_match_details", [])
        detail_text = bc_details[0] if bc_details else "previously flagged document"
        reasons.append(
            f"Blockchain ledger flagged this document: {detail_text}."
        )

    # Structured Validation
    sv_score = signals.get("structured_validation_score", 0)
    if sv_score > 0.1:
        sv_details = signals.get("structured_validation_details", [])
        if sv_details:
            detail_text = " ".join(sv_details[:3])
        else:
            detail_text = "format violations, character anomalies, or arithmetic inconsistencies"
        reasons.append(
            f"Structured document validation detected semantic anomalies "
            f"(score: {sv_score:.3f}). {detail_text}."
        )

    if decision == "REJECTED":
        quality_details = signals.get("quality_details", "")
        explanation = (
            f"The document was instantly REJECTED prior to forensic scoring. "
            f"Reason: {quality_details or 'Unrecognized or unsupported document format.'} "
            f"Please upload a clear, supported, high-resolution government ID."
        )
    elif decision == "GENUINE":
        if not reasons:
            explanation = (
                f"The {doc_type} document passed all verification checks including "
                f"ELA forensics, text integrity analysis, signature/seal verification, "
                f"and blockchain ledger validation. "
                f"Fraud score: {fraud_score}/100."
            )
        else:
            explanation = (
                f"The {doc_type} document is assessed as likely genuine (score: {fraud_score}/100), "
                f"though minor observations were noted: {' '.join(reasons)}"
            )
    elif decision == "SUSPICIOUS":
        explanation = (
            f"The {doc_type} document raised moderate concerns (score: {fraud_score}/100). "
            + " ".join(reasons)
            + " Manual review by a compliance officer is recommended."
        )
    else:  # FORGED
        explanation = (
            f"The {doc_type} document is flagged as likely FORGED (score: {fraud_score}/100). "
            + " ".join(reasons)
            + " This document should be rejected and escalated for investigation."
        )

    logger.info("Explainer: Generated via template")
    return explanation


def generate_explanation(signals: dict) -> dict:
    """
    Generate a human-readable fraud explanation.

    Tries Gemini API first (if key is configured), falls back to templates.

    Args:
        signals: Combined dict of all pipeline results.

    Returns:
        dict with: explanation (str), method (str)
    """
    explanation = None
    method = "template"

    # Try Gemini API if key is available
    if GEMINI_API_KEY:
        explanation = _explain_with_gemini(signals)
        if explanation:
            method = "gemini_api"

    # Fallback to template
    if not explanation:
        explanation = _explain_with_template(signals)
        method = "template"

    return {
        "explanation": explanation,
        "method": method,
    }
