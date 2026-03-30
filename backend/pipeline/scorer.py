"""
Stages 5-6 — Fraud Scoring & Decision Engine

Aggregates all signals into a single weighted fraud score (0-100).
Higher score = more likely fraudulent.

Weight distribution (9 signals, sum = 1.0):
  - QR-OCR mismatch:   0.25 (strongest, most unique)
  - ELA tampering:     0.18 (visual, reliable)
  - Signature/Seal:    0.12 (document integrity)
  - EXIF flag:         0.10 (binary, reliable)
  - Text Integrity:    0.10 (font/spatial anomalies)
  - Blockchain:        0.08 (hash ledger cross-ref)
  - Deepfake:          0.07 (noisy on small faces)
  - ML forgery:        0.05 (redundant with ELA)
  - Voice mismatch:    0.05 (optional)
"""

from loguru import logger

from config import (DEEPFAKE_THRESHOLD, ELA_THRESHOLD, FRAUD_SCORE_THRESHOLD,
                    WEIGHT_BLOCKCHAIN, WEIGHT_DEEPFAKE, WEIGHT_ELA,
                    WEIGHT_EXIF, WEIGHT_ML_FORGERY, WEIGHT_QR_OCR_MISMATCH,
                    WEIGHT_SIGNATURE_SEAL, WEIGHT_TEXT_INTEGRITY, WEIGHT_VOICE)


def compute_fraud_score(signals: dict) -> dict:
    """
    Compute weighted fraud score from all pipeline signals.

    Args:
        signals: dict containing:
            - ela_score (float, 0-1): ELA tampering score
            - exif_flag (str): "clean" or "suspicious"
            - deepfake_score (float, 0-1 or None): deepfake probability
            - ml_forgery_score (float, 0-1 or None): ML forgery score
            - qr_ocr_match (bool or None): cross-validation result
            - name_similarity (int, 0-100): name match percentage
            - voice_match (bool or None): voice verification result
            - signature_seal_score (float, 0-1 or None): sig/seal anomaly score
            - text_integrity_score (float, 0-1 or None): text integrity score
            - blockchain_score (float, 0-1 or None): blockchain suspicion score

    Returns:
        dict with: fraud_score (0-100), decision, signal_breakdown
    """
    breakdown = {}
    total_weight = 0.0
    weighted_sum = 0.0

    # ── Fast Fail: Quality or Classification ──
    if not signals.get("quality_pass", True):
        return {
            "fraud_score": 100.0,
            "decision": "REJECTED",
            "threshold": FRAUD_SCORE_THRESHOLD,
            "signal_breakdown": {"quality_failure": {"raw_signal": 1.0, "weight": 1.0, "contribution": 100.0}},
            "signals_used": 1,
        }

    if signals.get("document_type") == "unknown":
        return {
            "fraud_score": 100.0,
            "decision": "REJECTED",
            "threshold": FRAUD_SCORE_THRESHOLD,
            "signal_breakdown": {"unknown_format": {"raw_signal": 1.0, "weight": 1.0, "contribution": 100.0}},
            "signals_used": 1,
        }

    # ── 1. QR-OCR Mismatch (0.25) ──
    qr_ocr_match = signals.get("qr_ocr_match")
    if qr_ocr_match is not None:
        if qr_ocr_match is False:
            # Mismatch detected — strong fraud signal
            name_sim = signals.get("name_similarity", 0)
            # Scale: lower similarity = higher fraud signal
            qr_signal = max(0.0, (100 - name_sim) / 100.0)
            qr_signal = min(1.0, qr_signal * 1.2)  # boost mismatches
        else:
            qr_signal = 0.0  # match = no fraud signal

        weighted_sum += qr_signal * WEIGHT_QR_OCR_MISMATCH
        total_weight += WEIGHT_QR_OCR_MISMATCH
        breakdown["qr_ocr_mismatch"] = {
            "raw_signal": round(qr_signal, 3),
            "weight": WEIGHT_QR_OCR_MISMATCH,
            "contribution": round(qr_signal * WEIGHT_QR_OCR_MISMATCH * 100, 1),
        }

    # ── 2. ELA Score (0.18) ──
    ela_score = signals.get("ela_score")
    if ela_score is not None:
        # Normalize: scores above threshold are suspicious
        ela_signal = (
            min(1.0, max(0.0, ela_score / ELA_THRESHOLD)) if ELA_THRESHOLD > 0 else 0
        )
        weighted_sum += ela_signal * WEIGHT_ELA
        total_weight += WEIGHT_ELA
        breakdown["ela"] = {
            "raw_signal": round(ela_signal, 3),
            "weight": WEIGHT_ELA,
            "contribution": round(ela_signal * WEIGHT_ELA * 100, 1),
        }

    # ── 3. Signature/Seal Score (0.12) ──
    sig_seal_score = signals.get("signature_seal_score")
    if sig_seal_score is not None:
        ss_signal = min(1.0, max(0.0, sig_seal_score))
        weighted_sum += ss_signal * WEIGHT_SIGNATURE_SEAL
        total_weight += WEIGHT_SIGNATURE_SEAL
        breakdown["signature_seal"] = {
            "raw_signal": round(ss_signal, 3),
            "weight": WEIGHT_SIGNATURE_SEAL,
            "contribution": round(ss_signal * WEIGHT_SIGNATURE_SEAL * 100, 1),
        }

    # ── 4. EXIF Flag (0.10) ──
    exif_flag = signals.get("exif_flag")
    if exif_flag is not None:
        if exif_flag == "suspicious":
            exif_signal = 1.0
        elif exif_flag == "notable":
            exif_signal = 0.5  # Missing EXIF = moderate suspicion
        else:
            exif_signal = 0.0
        weighted_sum += exif_signal * WEIGHT_EXIF
        total_weight += WEIGHT_EXIF
        breakdown["exif"] = {
            "raw_signal": exif_signal,
            "weight": WEIGHT_EXIF,
            "contribution": round(exif_signal * WEIGHT_EXIF * 100, 1),
        }

    # ── 5. Text Integrity Score (0.10) ──
    text_integrity_score = signals.get("text_integrity_score")
    if text_integrity_score is not None:
        ti_signal = min(1.0, max(0.0, text_integrity_score))
        weighted_sum += ti_signal * WEIGHT_TEXT_INTEGRITY
        total_weight += WEIGHT_TEXT_INTEGRITY
        breakdown["text_integrity"] = {
            "raw_signal": round(ti_signal, 3),
            "weight": WEIGHT_TEXT_INTEGRITY,
            "contribution": round(ti_signal * WEIGHT_TEXT_INTEGRITY * 100, 1),
        }

    # ── 6. Blockchain Score (0.08) ──
    blockchain_score = signals.get("blockchain_score")
    if blockchain_score is not None:
        bc_signal = min(1.0, max(0.0, blockchain_score))
        weighted_sum += bc_signal * WEIGHT_BLOCKCHAIN
        total_weight += WEIGHT_BLOCKCHAIN
        breakdown["blockchain"] = {
            "raw_signal": round(bc_signal, 3),
            "weight": WEIGHT_BLOCKCHAIN,
            "contribution": round(bc_signal * WEIGHT_BLOCKCHAIN * 100, 1),
        }

    # ── 7. Deepfake Score (0.07) ──
    deepfake_score = signals.get("deepfake_score")
    if deepfake_score is not None:
        df_signal = min(1.0, max(0.0, deepfake_score))
        weighted_sum += df_signal * WEIGHT_DEEPFAKE
        total_weight += WEIGHT_DEEPFAKE
        breakdown["deepfake"] = {
            "raw_signal": round(df_signal, 3),
            "weight": WEIGHT_DEEPFAKE,
            "contribution": round(df_signal * WEIGHT_DEEPFAKE * 100, 1),
        }

    # ── 8. ML Forgery (0.05, optional) ──
    ml_forgery_score = signals.get("ml_forgery_score")
    if ml_forgery_score is not None:
        ml_signal = min(1.0, max(0.0, ml_forgery_score))
        weighted_sum += ml_signal * WEIGHT_ML_FORGERY
        total_weight += WEIGHT_ML_FORGERY
        breakdown["ml_forgery"] = {
            "raw_signal": round(ml_signal, 3),
            "weight": WEIGHT_ML_FORGERY,
            "contribution": round(ml_signal * WEIGHT_ML_FORGERY * 100, 1),
        }

    # ── 9. Voice Match (0.05, optional) ──
    voice_match = signals.get("voice_match")
    if voice_match is not None:
        voice_signal = 0.0 if voice_match else 1.0
        weighted_sum += voice_signal * WEIGHT_VOICE
        total_weight += WEIGHT_VOICE
        breakdown["voice"] = {
            "raw_signal": voice_signal,
            "weight": WEIGHT_VOICE,
            "contribution": round(voice_signal * WEIGHT_VOICE * 100, 1),
        }

    # ── Compute final score ──
    if total_weight > 0:
        # Normalize by actual weight used (handles optional missing signals)
        fraud_score = (weighted_sum / total_weight) * 100
    else:
        fraud_score = 0.0

    fraud_score = round(min(100.0, max(0.0, fraud_score)), 1)

    # ── Decision ──
    if fraud_score >= FRAUD_SCORE_THRESHOLD:
        decision = "FORGED"
    elif fraud_score >= FRAUD_SCORE_THRESHOLD * 0.6:
        decision = "SUSPICIOUS"
    else:
        decision = "GENUINE"

    logger.info(
        f"Scorer: fraud_score={fraud_score} decision={decision} "
        f"signals_used={len(breakdown)}/{9}"
    )

    return {
        "fraud_score": fraud_score,
        "decision": decision,
        "threshold": FRAUD_SCORE_THRESHOLD,
        "signal_breakdown": breakdown,
        "signals_used": len(breakdown),
    }
