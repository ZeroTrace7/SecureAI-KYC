"""
SecureAI-KYC — FastAPI Application

Main entry point: orchestrates the full KYC verification pipeline.

Pipeline flow (target: 2-4 sec on CPU):
  Stage 0: Rule-based document classification
  Stage 1: Input quality gate
  Stage 2: Image preprocessing
  Stage 3: Parallel agents (ELA, OCR, QR, EXIF, Deepfake*, Voice*)
  Stage 4: Cross-validation (OCR vs QR)
  Stage 5-6: Weighted fraud scoring
  Stage 7: Explainable output (Gemini API / template)
  Stage 8: Audit logging
"""

import os
import time
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from loguru import logger

from config import HOST, PORT, DEBUG, CORS_ORIGINS, UPLOAD_DIR

# ── Pipeline imports ──
from pipeline.quality_gate import check_quality
from pipeline.preprocessor import preprocess
from pipeline.classifier import classify_document
from pipeline.cross_validator import cross_validate
from pipeline.scorer import compute_fraud_score
from pipeline.explainer import generate_explanation
from pipeline.audit_logger import log_verification, get_audit_record

# ── Agent imports ──
from agents.ela_agent import compute_ela
from agents.ocr_agent import extract_text, extract_fields
from agents.qr_agent import decode_document_qr
from agents.exif_agent import analyze_exif
from agents.deepfake_agent import analyze_deepfake
from agents.voice_agent import verify_voice


# ═══════════════════════════════════════════════════════════
#  FastAPI App
# ═══════════════════════════════════════════════════════════

app = FastAPI(
    title="SecureAI-KYC API",
    description="AI-Powered KYC Document Fraud Detection System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════════════════

@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint — verifies the API is running."""
    return {
        "status": "healthy",
        "service": "SecureAI-KYC",
        "version": "1.0.0",
    }


# ═══════════════════════════════════════════════════════════
#  Full KYC Verification Pipeline
# ═══════════════════════════════════════════════════════════

@app.post("/api/verify", tags=["Verification"])
async def verify_document(
    request: Request,
    document: UploadFile = File(...),
):
    """
    Upload a document for full KYC verification.

    Runs the complete 8-stage pipeline and returns:
    - Document type classification
    - Quality assessment
    - ELA tampering analysis (with heatmap)
    - OCR text extraction
    - QR code data
    - EXIF metadata analysis
    - Deepfake detection (if enabled)
    - Cross-validation (OCR vs QR)
    - Fraud score and decision
    - Human-readable explanation
    """
    start_time = time.time()

    # ── Save uploaded file ──
    file_id = str(uuid.uuid4())[:8]
    file_ext = os.path.splitext(document.filename)[1] or ".jpg"
    save_path = os.path.join(str(UPLOAD_DIR), f"{file_id}{file_ext}")

    try:
        contents = await document.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        logger.info(f"Pipeline: Saved upload as {save_path} ({len(contents)} bytes)")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File upload failed: {e}")

    try:
        # ═══ STAGE 1: Quality Gate ═══
        quality = check_quality(save_path)
        if not quality["quality_pass"]:
            logger.warning(f"Pipeline: Quality gate FAILED — {quality['details']}")
            # Continue anyway but flag it (don't block — let user see results)

        # ═══ STAGE 2: Preprocessing ═══
        clean_path = preprocess(save_path, output_dir=str(UPLOAD_DIR))

        # ═══ STAGE 3: Run Agents (sequentially for CPU, could be parallel with asyncio) ═══

        # Agent 1: ELA
        ela_result = _safe_run("ELA", compute_ela, clean_path, output_dir=str(UPLOAD_DIR))

        # Agent 2: OCR
        ocr_result = _safe_run("OCR", extract_text, clean_path)
        raw_text = ocr_result.get("raw_text", "") if ocr_result else ""

        # Agent 3: QR Decode
        qr_result = _safe_run("QR", decode_document_qr, save_path)  # use original (QR may be lost after preprocess)

        # Agent 4: EXIF
        exif_result = _safe_run("EXIF", analyze_exif, save_path)  # use original

        # Agent 5: Deepfake
        deepfake_result = _safe_run("Deepfake", analyze_deepfake, clean_path)

        # ═══ STAGE 0: Classification (needs OCR text + QR info) ═══
        has_qr = qr_result.get("has_qr", False) if qr_result else False
        classification = classify_document(raw_text, has_qr=has_qr)
        doc_type = classification.get("document_type", "unknown")

        # ═══ Extract structured fields from OCR ═══
        ocr_fields = extract_fields(raw_text, document_type=doc_type)

        # ═══ STAGE 4: Cross-Validation ═══
        cross_val = cross_validate(
            ocr_data=ocr_fields,
            qr_data=qr_result if qr_result else {},
        )

        # ═══ STAGE 5-6: Fraud Scoring ═══
        scoring_signals = {
            "ela_score": ela_result.get("ela_score") if ela_result else None,
            "exif_flag": exif_result.get("exif_flag") if exif_result else None,
            "deepfake_score": deepfake_result.get("deepfake_score") if deepfake_result else None,
            "qr_ocr_match": cross_val.get("qr_ocr_match"),
            "name_similarity": cross_val.get("name_similarity", 0),
            "voice_match": None,  # only set if voice endpoint is used
        }
        score_result = compute_fraud_score(scoring_signals)

        # ═══ STAGE 7: Explainability ═══
        explain_signals = {
            **scoring_signals,
            "document_type": doc_type,
            "fraud_score": score_result["fraud_score"],
            "decision": score_result["decision"],
            "ocr_name": ocr_fields.get("name"),
            "qr_name": qr_result.get("qr_name") if qr_result else None,
            "exif_software": exif_result.get("software") if exif_result else None,
        }
        explain_result = generate_explanation(explain_signals)

        # ═══ STAGE 8: Audit Log ═══
        elapsed = round(time.time() - start_time, 2)

        full_result = {
            "document_type": doc_type,
            "classification": classification,
            "quality": quality,
            "ela": ela_result or {},
            "ocr": {
                "raw_text": raw_text[:500],  # truncate for response
                "fields": ocr_fields,
                "method": ocr_result.get("method") if ocr_result else None,
            },
            "qr": qr_result or {},
            "exif": exif_result or {},
            "deepfake": deepfake_result or {},
            "cross_validation": cross_val,
            "fraud_score": score_result["fraud_score"],
            "decision": score_result["decision"],
            "score_breakdown": score_result["signal_breakdown"],
            "explanation": explain_result["explanation"],
            "explanation_method": explain_result["method"],
            "processing_time_seconds": elapsed,
        }

        # Get client IP
        client_ip = request.client.host if request.client else None
        audit_id = log_verification(full_result, filename=document.filename, ip_address=client_ip)
        full_result["audit_id"] = audit_id

        logger.info(
            f"Pipeline: COMPLETE in {elapsed}s — "
            f"type={doc_type} score={score_result['fraud_score']} "
            f"decision={score_result['decision']}"
        )

        return full_result

    except Exception as e:
        logger.exception(f"Pipeline: Unhandled error — {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    finally:
        # Clean up uploaded files (optional: keep for audit)
        pass


# ═══════════════════════════════════════════════════════════
#  Individual Endpoints
# ═══════════════════════════════════════════════════════════

@app.post("/api/classify", tags=["Individual"])
async def classify_only(document: UploadFile = File(...)):
    """Classify document type only (rule-based, instant)."""
    save_path = await _save_upload(document)
    ocr_result = extract_text(save_path)
    raw_text = ocr_result.get("raw_text", "")
    qr_result = decode_document_qr(save_path)
    has_qr = qr_result.get("has_qr", False)
    return classify_document(raw_text, has_qr=has_qr)


@app.post("/api/ocr", tags=["Individual"])
async def ocr_only(document: UploadFile = File(...)):
    """Extract text from document using EasyOCR."""
    save_path = await _save_upload(document)
    ocr_result = extract_text(save_path)
    raw_text = ocr_result.get("raw_text", "")
    fields = extract_fields(raw_text)
    return {"ocr": ocr_result, "fields": fields}


@app.post("/api/deepfake", tags=["Individual"])
async def deepfake_only(document: UploadFile = File(...)):
    """Run deepfake detection on a document face."""
    save_path = await _save_upload(document)
    return analyze_deepfake(save_path)


@app.post("/api/voice/verify", tags=["Individual"])
async def voice_verify(
    audio: UploadFile = File(...),
    reference: UploadFile = File(...),
):
    """Compare two voice recordings for speaker verification."""
    audio_path = await _save_upload(audio, prefix="voice_")
    ref_path = await _save_upload(reference, prefix="ref_")
    return verify_voice(audio_path, ref_path)


@app.get("/api/audit/{audit_id}", tags=["Audit"])
async def get_audit(audit_id: int):
    """Retrieve audit trail for a verification."""
    record = get_audit_record(audit_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return record


# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════

async def _save_upload(upload: UploadFile, prefix: str = "") -> str:
    """Save an uploaded file and return the path."""
    file_id = str(uuid.uuid4())[:8]
    file_ext = os.path.splitext(upload.filename)[1] or ".jpg"
    save_path = os.path.join(str(UPLOAD_DIR), f"{prefix}{file_id}{file_ext}")
    contents = await upload.read()
    with open(save_path, "wb") as f:
        f.write(contents)
    return save_path


def _safe_run(agent_name: str, func, *args, **kwargs) -> dict | None:
    """Run an agent function with full error trapping."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Agent '{agent_name}' crashed: {e}")
        return {"error": str(e), "agent": agent_name}


# ═══════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
