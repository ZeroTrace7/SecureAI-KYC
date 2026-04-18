"""
Stages 5-6 — Fraud Scoring & Decision Engine

Aggregates all signals into a single weighted fraud score (0-100).
Higher score = more likely fraudulent.

Document-type-aware scoring: each document family has an expected
feature profile that modifies signal weights. This prevents:
  - Genuine PAN cards from being penalized for missing seals
  - Payslips from being penalized for missing QR codes
  - IDs from being penalized for font variance in mixed scripts

Base weights (7 active signals):
  - QR-OCR mismatch:   0.25 (strongest deterministic signal)
  - ELA tampering:     0.18 (visual forensic evidence)
  - Signature/Seal:    0.12 (document integrity)
  - EXIF flag:         0.10 (metadata analysis)
  - Text Integrity:    0.10 (font/spatial anomalies)
  - Deepfake:          0.07 (face forensics)
  - Blockchain:        0.05 (hash ledger cross-ref)
"""

from loguru import logger

from config import (ELA_THRESHOLD, FRAUD_SCORE_THRESHOLD,
                    WEIGHT_BLOCKCHAIN, WEIGHT_DEEPFAKE, WEIGHT_ELA,
                    WEIGHT_EXIF, WEIGHT_QR_OCR_MISMATCH,
                    WEIGHT_SIGNATURE_SEAL, WEIGHT_STRUCTURED_VALIDATION,
                    WEIGHT_TEXT_INTEGRITY)


# ═══════════════════════════════════════════════════════════
#  Document-Type Expected Feature Profiles
# ═══════════════════════════════════════════════════════════
# For each document type, defines:
#   - Which features are expected (for gating irrelevant signals)
#   - Weight multipliers per signal (to tune sensitivity)
#
# A weight_mod of 0.0 means "this signal should not contribute
# to scoring for this document type", preventing false positives.

DOC_TYPE_PROFILE = {
    "aadhaar": {
        "expects_qr": True,
        "expects_face": True,
        "expects_signature": True,     # Aadhaar has authorized signatory
        "expects_seal": True,          # UIDAI embossed seal / emblem
        "rigid_template": True,
        "weight_mods": {
            "qr_ocr_mismatch": 1.3,   # QR-OCR is the kill feature for Aadhaar
            "ela": 1.0,
            "text_integrity": 0.3,     # e-Aadhaar has 3 scripts + 5 font sizes by design — very low weight
            "signature_seal": 1.5,     # UIDAI embossed seal + authorized signatory — primary signal
            "deepfake": 0.15,          # Tiny compressed ID photos (~80x100px) produce extremely noisy results
            "exif": 1.0,
            "blockchain": 1.0,
            "structured_validation": 0.5,  # Secondary for IDs
        },
    },
    "pan": {
        "expects_qr": False,
        "expects_face": True,
        "expects_signature": True,     # PAN has a signature line
        "expects_seal": False,         # No official seal on PAN
        "rigid_template": True,
        "weight_mods": {
            "qr_ocr_mismatch": 0.0,   # PAN cards don't have QR
            "ela": 1.0,
            "text_integrity": 0.3,     # PAN has mixed Hindi/English scripts by design — very low weight
            "signature_seal": 1.2,     # PAN has a signature line + Income Tax Dept emblem
            "deepfake": 0.8,           # Face photo matters but model is noisy on IDs
            "exif": 1.0,
            "blockchain": 1.0,
            "structured_validation": 0.5,  # Secondary for IDs
        },
    },
    "passport": {
        "expects_qr": False,
        "expects_face": True,
        "expects_signature": True,
        "expects_seal": True,
        "rigid_template": True,
        "weight_mods": {
            "qr_ocr_mismatch": 0.0,   # No QR on Indian passports
            "ela": 1.0,
            "text_integrity": 0.7,
            "signature_seal": 1.0,     # Both expected
            "deepfake": 1.0,           # Face swap is primary attack vector for passports
            "exif": 1.0,
            "blockchain": 1.0,
            "structured_validation": 0.3,  # Less relevant for passports
        },
    },
    "salary_slip": {
        "expects_qr": False,
        "expects_face": False,
        "expects_signature": False,    # Most payslips are digital
        "expects_seal": False,         # No seal expected
        "expects_text_integrity": True, # Font/layout is critical — #1 payslip forgery technique
        "expects_structured_validation": True,  # PRIMARY: arithmetic, format, field checks
        "rigid_template": False,       # Variable layouts across employers
        "weight_mods": {
            "qr_ocr_mismatch": 0.0,   # No QR on payslips
            "ela": 1.5,               # ELA is important — edited JPEGs show artifacts
            "text_integrity": 1.5,    # Increased to catch subtle font/layout edits
            "signature_seal": 0.0,     # No sig/seal expected
            "deepfake": 0.0,           # No face on payslips
            "exif": 2.0,              # Increased: Editor metadata is strong evidence
            "blockchain": 1.0,
            "structured_validation": 1.5,  # PRIMARY detector for payslips
        },
    },
    "utility_bill": {
        "expects_qr": False,
        "expects_face": False,
        "expects_signature": False,
        "expects_seal": False,
        "expects_text_integrity": True,
        "expects_structured_validation": True,
        "rigid_template": False,
        "weight_mods": {
            "qr_ocr_mismatch": 0.0,
            "ela": 1.2,
            "text_integrity": 0.8,
            "signature_seal": 0.0,
            "deepfake": 0.0,
            "exif": 1.3,
            "blockchain": 1.0,
            "structured_validation": 1.0,
        },
    },
    "invoice": {
        "expects_qr": False,
        "expects_face": False,
        "expects_signature": False,
        "expects_seal": False,
        "expects_text_integrity": True,
        "expects_structured_validation": True,
        "rigid_template": False,
        "weight_mods": {
            "qr_ocr_mismatch": 0.0,
            "ela": 1.2,
            "text_integrity": 0.8,
            "signature_seal": 0.0,
            "deepfake": 0.0,
            "exif": 1.3,
            "blockchain": 1.0,
            "structured_validation": 1.2,  # Important for invoices
        },
    },
}

# Default profile for unknown/other document types — conservative, all signals active
_DEFAULT_PROFILE = {
    "expects_qr": False,
    "expects_face": False,
    "expects_signature": False,
    "expects_seal": False,
    "rigid_template": False,
    "weight_mods": {
        "qr_ocr_mismatch": 1.0,
        "ela": 1.0,
        "text_integrity": 1.0,
        "signature_seal": 0.5,  # Reduced — don't know if seal is expected
        "deepfake": 0.5,        # Reduced — don't know if face is expected
        "exif": 1.0,
        "blockchain": 1.0,
        "structured_validation": 0.8,
    },
}


def _get_profile(doc_type: str) -> dict:
    """Get the expected feature profile for a document type."""
    return DOC_TYPE_PROFILE.get(doc_type, _DEFAULT_PROFILE)


def compute_fraud_score(signals: dict) -> dict:
    """
    Compute weighted fraud score from all pipeline signals.

    Uses document-type-aware weight modifiers to prevent false
    positives from signals irrelevant to the document type.

    Args:
        signals: dict containing:
            - document_type (str): classified doc type
            - ela_score (float, 0-1): ELA tampering score
            - exif_flag (str): "clean" or "suspicious"
            - deepfake_score (float, 0-1 or None): deepfake probability
            - qr_ocr_match (bool or None): cross-validation result
            - name_similarity (int, 0-100): name match percentage
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

    # ── Load document-type profile ──
    doc_type = signals.get("document_type", "other")
    profile = _get_profile(doc_type)
    mods = profile["weight_mods"]

    logger.info(
        f"Scorer: Using profile for '{doc_type}' — "
        f"expects_qr={profile['expects_qr']} "
        f"expects_face={profile['expects_face']} "
        f"expects_sig={profile['expects_signature']} "
        f"expects_seal={profile['expects_seal']}"
    )

    # ── 1. QR-OCR Mismatch ──
    qr_ocr_match = signals.get("qr_ocr_match")
    effective_qr_weight = WEIGHT_QR_OCR_MISMATCH * mods.get("qr_ocr_mismatch", 1.0)

    if qr_ocr_match is not None and effective_qr_weight > 0:
        if qr_ocr_match is False:
            name_sim = signals.get("name_similarity", 0)
            qr_signal = max(0.0, (100 - name_sim) / 100.0)
            qr_signal = min(1.0, qr_signal * 1.2)
        else:
            qr_signal = 0.0

        weighted_sum += qr_signal * effective_qr_weight
        total_weight += effective_qr_weight
        breakdown["qr_ocr_mismatch"] = {
            "raw_signal": round(qr_signal, 3),
            "weight": round(effective_qr_weight, 3),
            "contribution": round(qr_signal * effective_qr_weight * 100, 1),
        }

    # ── 2. ELA Score ──
    ela_score = signals.get("ela_score")
    effective_ela_weight = WEIGHT_ELA * mods.get("ela", 1.0)

    if ela_score is not None and effective_ela_weight > 0:
        # Deadband: scores well below threshold are clearly clean — no signal
        if ela_score < ELA_THRESHOLD * 0.5:
            ela_signal = 0.0
        else:
            ela_signal = (
                min(1.0, max(0.0, ela_score / ELA_THRESHOLD)) if ELA_THRESHOLD > 0 else 0
            )
        weighted_sum += ela_signal * effective_ela_weight
        total_weight += effective_ela_weight
        breakdown["ela"] = {
            "raw_signal": round(ela_signal, 3),
            "weight": round(effective_ela_weight, 3),
            "contribution": round(ela_signal * effective_ela_weight * 100, 1),
        }

    # ── 3. Signature/Seal Score ──
    sig_seal_score = signals.get("signature_seal_score")
    effective_ss_weight = WEIGHT_SIGNATURE_SEAL * mods.get("signature_seal", 1.0)

    if sig_seal_score is not None and effective_ss_weight > 0:
        ss_signal = min(1.0, max(0.0, sig_seal_score))
        weighted_sum += ss_signal * effective_ss_weight
        total_weight += effective_ss_weight
        breakdown["signature_seal"] = {
            "raw_signal": round(ss_signal, 3),
            "weight": round(effective_ss_weight, 3),
            "contribution": round(ss_signal * effective_ss_weight * 100, 1),
        }

    # ── 4. EXIF Flag ──
    exif_flag = signals.get("exif_flag")
    effective_exif_weight = WEIGHT_EXIF * mods.get("exif", 1.0)

    if exif_flag is not None and effective_exif_weight > 0:
        if exif_flag == "suspicious":
            exif_signal = 1.0
        elif exif_flag == "notable":
            exif_signal = 0.05  # Informational only — e-Aadhaar/DigiLocker/scans naturally lack EXIF
        else:
            exif_signal = 0.0
        weighted_sum += exif_signal * effective_exif_weight
        total_weight += effective_exif_weight
        breakdown["exif"] = {
            "raw_signal": exif_signal,
            "weight": round(effective_exif_weight, 3),
            "contribution": round(exif_signal * effective_exif_weight * 100, 1),
        }

    # ── 5. Text Integrity Score ──
    text_integrity_score = signals.get("text_integrity_score")
    effective_ti_weight = WEIGHT_TEXT_INTEGRITY * mods.get("text_integrity", 1.0)

    if text_integrity_score is not None and effective_ti_weight > 0:
        ti_signal = min(1.0, max(0.0, text_integrity_score))
        weighted_sum += ti_signal * effective_ti_weight
        total_weight += effective_ti_weight
        breakdown["text_integrity"] = {
            "raw_signal": round(ti_signal, 3),
            "weight": round(effective_ti_weight, 3),
            "contribution": round(ti_signal * effective_ti_weight * 100, 1),
        }

    # ── 6. Blockchain Score ──
    blockchain_score = signals.get("blockchain_score")
    effective_bc_weight = WEIGHT_BLOCKCHAIN * mods.get("blockchain", 1.0)

    if blockchain_score is not None and effective_bc_weight > 0:
        bc_signal = min(1.0, max(0.0, blockchain_score))
        weighted_sum += bc_signal * effective_bc_weight
        total_weight += effective_bc_weight
        breakdown["blockchain"] = {
            "raw_signal": round(bc_signal, 3),
            "weight": round(effective_bc_weight, 3),
            "contribution": round(bc_signal * effective_bc_weight * 100, 1),
        }

    # ── 7. Deepfake Score ──
    deepfake_score = signals.get("deepfake_score")
    effective_df_weight = WEIGHT_DEEPFAKE * mods.get("deepfake", 1.0)

    if deepfake_score is not None and effective_df_weight > 0:
        df_signal = min(1.0, max(0.0, deepfake_score))
        weighted_sum += df_signal * effective_df_weight
        total_weight += effective_df_weight
        breakdown["deepfake"] = {
            "raw_signal": round(df_signal, 3),
            "weight": round(effective_df_weight, 3),
            "contribution": round(df_signal * effective_df_weight * 100, 1),
        }

    # ── 8. Structured Validation Score ──
    structured_score = signals.get("structured_validation_score")
    effective_sv_weight = WEIGHT_STRUCTURED_VALIDATION * mods.get("structured_validation", 1.0)

    if structured_score is not None and effective_sv_weight > 0:
        sv_signal = min(1.0, max(0.0, structured_score))
        weighted_sum += sv_signal * effective_sv_weight
        total_weight += effective_sv_weight
        breakdown["structured_validation"] = {
            "raw_signal": round(sv_signal, 3),
            "weight": round(effective_sv_weight, 3),
            "contribution": round(sv_signal * effective_sv_weight * 100, 1),
        }

    # ── Compute base fraud score ──
    if total_weight > 0:
        fraud_score = (weighted_sum / total_weight) * 100
    else:
        fraud_score = 0.0

    # ── Critical expected-feature failure ──
    # If a document type EXPECTS seal/signature and the agent detects anomalies,
    # add a direct penalty that bypasses weighted-average dilution.
    # Without this, clean agents (ELA=0, blockchain=0) average DOWN the fraud
    # score of a document with a clearly forged seal.
    critical_penalty_applied = False

    if profile.get("expects_seal") or profile.get("expects_signature"):
        ss_data = breakdown.get("signature_seal", {})
        ss_raw = ss_data.get("raw_signal", 0)
        if ss_raw > 0.4:
            # Direct penalty: 15 points for moderate anomalies, up to 25 for severe
            penalty = min(25.0, ss_raw * 30.0)
            fraud_score += penalty
            critical_penalty_applied = True
            logger.warning(
                f"Scorer: Seal/Signature critical failure on '{doc_type}' "
                f"(raw_signal={ss_raw:.3f}, penalty=+{penalty:.1f}) — "
                f"document type expects seal={profile.get('expects_seal')} "
                f"sig={profile.get('expects_signature')}"
            )

    # ── Critical: Structured validation failure on financial documents ──
    # Payslips, utility bills, and invoices rely on structured validation as
    # their PRIMARY forensic signal (arithmetic totals, format checksums, etc.).
    # A failure here is equivalent to a sig/seal failure on an identity document.
    if profile.get("expects_structured_validation"):
        sv_data = breakdown.get("structured_validation", {})
        sv_raw = sv_data.get("raw_signal", 0)
        if sv_raw > 0.25:
            # Direct penalty: 15 points for moderate, up to 30 for severe
            sv_penalty = min(30.0, sv_raw * 40.0)
            fraud_score += sv_penalty
            critical_penalty_applied = True
            logger.warning(
                f"Scorer: Structured validation critical failure on '{doc_type}' "
                f"(raw_signal={sv_raw:.3f}, penalty=+{sv_penalty:.1f}) — "
                f"arithmetic/format inconsistencies detected"
            )

    # ── Critical: Text integrity failure on financial documents ──
    # Font substitution is the #1 payslip forgery technique. Forgers match the
    # arithmetic perfectly but use a different font (Calibri vs CourierNew, etc.).
    # Text integrity is often the ONLY signal that catches these forgeries.
    if profile.get("expects_text_integrity"):
        ti_data = breakdown.get("text_integrity", {})
        ti_raw = ti_data.get("raw_signal", 0)
        if ti_raw > 0.2:  # Lower threshold — even mild font inconsistency is suspicious
            # Direct penalty: 11 points for mild (0.2), up to 30 for severe (0.55+)
            ti_penalty = min(30.0, ti_raw * 55.0)
            fraud_score += ti_penalty
            critical_penalty_applied = True
            logger.warning(
                f"Scorer: Text integrity critical failure on '{doc_type}' "
                f"(raw_signal={ti_raw:.3f}, penalty=+{ti_penalty:.1f}) — "
                f"font/layout inconsistency on financial document"
            )

    # ── Missing expected feature penalties ──
    # If the document type EXPECTS a feature (QR code, face photo) but the
    # agent couldn't find it, this is itself suspicious. Real government IDs
    # always have readable QR codes and passport-quality photos.
    # Unlike anomaly penalties above, these fire when signals are MISSING.

    if profile.get("expects_qr") and signals.get("qr_ocr_match") is None:
        # Aadhaar expects a readable QR. If we can't decode it:
        # - Photo taken at bad angle/quality, or
        # - QR was deliberately removed/obscured, or
        # - Document is fabricated without a valid UIDAI QR
        qr_missing_penalty = 15.0
        fraud_score += qr_missing_penalty
        critical_penalty_applied = True
        breakdown["missing_qr_penalty"] = {
            "raw_signal": 1.0,
            "weight": 0.0,
            "contribution": qr_missing_penalty,
            "detail": "Document type expects QR code but none could be decoded",
        }
        logger.warning(
            f"Scorer: Missing QR penalty on '{doc_type}' — "
            f"expects_qr=True but qr_ocr_match=None (+{qr_missing_penalty})"
        )

    if profile.get("expects_face") and signals.get("deepfake_score") is None:
        # Aadhaar/PAN/Passport expect a face photo. If Haar cascade can't
        # find ANY face, the photo is either missing, obscured, or non-photographic
        # (e.g., a cartoon/illustration instead of a real photo).
        face_missing_penalty = 10.0
        fraud_score += face_missing_penalty
        critical_penalty_applied = True
        breakdown["missing_face_penalty"] = {
            "raw_signal": 1.0,
            "weight": 0.0,
            "contribution": face_missing_penalty,
            "detail": "Document type expects face photo but none detected",
        }
        logger.warning(
            f"Scorer: Missing face penalty on '{doc_type}' — "
            f"expects_face=True but deepfake_score=None (+{face_missing_penalty})"
        )

    # ── If any critical expected-feature penalty fired, ensure minimum SUSPICIOUS ──
    # A document that failed an expected forensic check (sig/seal on ID, structured
    # validation or text integrity on payslip) should NEVER be marked GENUINE.
    if critical_penalty_applied:
        suspicious_threshold = FRAUD_SCORE_THRESHOLD * 0.6
        if fraud_score < suspicious_threshold:
            logger.info(
                f"Scorer: Critical penalty floor — bumping score from "
                f"{fraud_score:.1f} to {suspicious_threshold:.1f} (SUSPICIOUS minimum)"
            )
            fraud_score = suspicious_threshold

        # ── Tiered escalation for financial documents ──
        # For salary_slips/utility_bills/invoices: text_integrity > 0.28 is
        # definitive font forgery (genuine payslips score 0.10-0.18, forged
        # score 0.29-0.39 — gap of 0.10+ points). Escalate to FORGED.
        if profile.get("expects_text_integrity"):
            ti_data = breakdown.get("text_integrity", {})
            ti_raw_score = ti_data.get("raw_signal", 0)
            if ti_raw_score > 0.28 and fraud_score < FRAUD_SCORE_THRESHOLD:
                logger.warning(
                    f"Scorer: Text integrity FORGED escalation on '{doc_type}' "
                    f"(ti_raw={ti_raw_score:.3f} > 0.28) — font substitution confirmed. "
                    f"Bumping {fraud_score:.1f} → {FRAUD_SCORE_THRESHOLD}"
                )
                fraud_score = FRAUD_SCORE_THRESHOLD

    # ── Corroboration check ──
    # A single noisy agent should NOT push a document to FORGED by itself.
    # Require at least 2 independent signals firing > 0.3 for FORGED verdict.
    # Exception: if a critical expected-feature penalty was applied, the document
    # type profile already validated relevance — don't cap those.
    firing_signals = [
        name for name, data in breakdown.items()
        if data.get("raw_signal", 0) > 0.3
    ]
    signal_count = len(firing_signals)

    if signal_count < 2 and fraud_score >= FRAUD_SCORE_THRESHOLD and not critical_penalty_applied:
        fraud_score = min(fraud_score, FRAUD_SCORE_THRESHOLD - 1)
        logger.info(
            f"Scorer: Corroboration cap applied — only 1 signal firing "
            f"({firing_signals}), capping score at {fraud_score}"
        )

    fraud_score = round(min(100.0, max(0.0, fraud_score)), 1)

    # ── Decision (4-tier) ──
    # MANUAL_REVIEW: not enough signals to be confident either way.
    # This prevents poisoning accuracy on unsupported document types.
    if fraud_score >= FRAUD_SCORE_THRESHOLD:
        decision = "FORGED"
    elif fraud_score >= FRAUD_SCORE_THRESHOLD * 0.6:
        decision = "SUSPICIOUS"
    elif len(breakdown) < 3:
        # Too few signals contributed — can't be confident
        decision = "MANUAL_REVIEW"
    else:
        decision = "GENUINE"

    # ── Safety net for ALL documents ──
    # If a document is about to be marked GENUINE, but has suspicious anomalies,
    # we escalate it to prevent obvious forgeries from slipping through the weighted average.
    # Uses contribution-weighted check so signals that the profile de-weighted
    # (e.g. deepfake at 0.3x for Aadhaar) don't trigger false escalations.
    if decision == "GENUINE":
        suspicious_signals = [
            name for name, data in breakdown.items()
            if data.get("raw_signal", 0) > 0.3
            and data.get("contribution", 0) > 2.0  # must contribute >2% to score
        ]
        if len(suspicious_signals) >= 2:
            decision = "SUSPICIOUS"
            # Artificially bump the score to hit the SUSPICIOUS threshold + 1
            fraud_score = max(fraud_score, (FRAUD_SCORE_THRESHOLD * 0.6) + 1.0)
            logger.warning(
                f"Scorer: Escalating doc from GENUINE → SUSPICIOUS — "
                f"multiple signals {suspicious_signals} are elevated. Score bumped to {fraud_score}."
            )
        elif len(suspicious_signals) == 1 and doc_type == "other":
            # Only escalate "other" (unrecognized) document types on a single signal.
            # Known document types have calibrated profiles — noisy signals
            # are already de-weighted appropriately.
            decision = "MANUAL_REVIEW"
            fraud_score = max(fraud_score, (FRAUD_SCORE_THRESHOLD * 0.45))
            logger.warning(
                f"Scorer: Escalating doc from GENUINE → MANUAL_REVIEW — "
                f"signal {suspicious_signals} is elevated. Score bumped to {fraud_score}."
            )

    logger.info(
        f"Scorer: fraud_score={fraud_score} decision={decision} "
        f"doc_type={doc_type} profile_used=True "
        f"signals_used={len(breakdown)}/8 "
        f"corroborating_signals={signal_count} ({firing_signals})"
    )

    return {
        "fraud_score": fraud_score,
        "decision": decision,
        "threshold": FRAUD_SCORE_THRESHOLD,
        "signal_breakdown": breakdown,
        "signals_used": len(breakdown),
        "corroborating_signals": signal_count,
        "doc_type_profile": doc_type,
    }
