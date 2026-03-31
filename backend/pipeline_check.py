"""
Pipeline health check — verify every stage works correctly after OCR optimization.
Tests each agent and pipeline stage individually, reports PASS/FAIL.
"""
import os, sys, time, glob, json, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Find test images
clean_imgs = glob.glob("uploads/*_clean.jpg")
clean_imgs.sort(key=os.path.getmtime, reverse=True)
orig_imgs = [f for f in glob.glob("uploads/*.png") + glob.glob("uploads/*.jpg") + glob.glob("uploads/*.jpeg")
             if "_clean" not in f and "_ela" not in f]
orig_imgs.sort(key=os.path.getmtime, reverse=True)

test_clean = clean_imgs[0] if clean_imgs else None
test_orig = orig_imgs[0] if orig_imgs else None

print(f"Test clean image: {test_clean} ({os.path.getsize(test_clean)} bytes)" if test_clean else "NO CLEAN IMAGE")
print(f"Test orig image:  {test_orig} ({os.path.getsize(test_orig)} bytes)" if test_orig else "NO ORIG IMAGE")
print("=" * 70)

results = []

def check(label, func, *args, **kwargs):
    """Run a check, catch errors, report PASS/FAIL with details."""
    t0 = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        # Validate result is a dict (all agents return dicts)
        if not isinstance(result, dict):
            results.append({"stage": label, "status": "FAIL", "reason": f"Returned {type(result).__name__}, expected dict", "seconds": round(elapsed, 3)})
            return result
        # Check for explicit error
        if result.get("error"):
            results.append({"stage": label, "status": "WARN", "reason": f"Returned error: {result['error']}", "seconds": round(elapsed, 3), "result_keys": list(result.keys())})
            return result
        results.append({"stage": label, "status": "PASS", "seconds": round(elapsed, 3), "result_keys": list(result.keys())})
        return result
    except Exception as e:
        elapsed = time.perf_counter() - t0
        results.append({"stage": label, "status": "FAIL", "reason": str(e), "traceback": traceback.format_exc()[-300:], "seconds": round(elapsed, 3)})
        return None

# ════════════════════════════════════════════
# 1. Quality Gate
# ════════════════════════════════════════════
from pipeline.quality_gate import check_quality
qg = check("1. Quality Gate", check_quality, test_orig)
if qg:
    print(f"  Quality: pass={qg.get('quality_pass')}, blur={qg.get('blur_score')}, res={qg.get('resolution')}")

# ════════════════════════════════════════════
# 2. Preprocessing
# ════════════════════════════════════════════
from pipeline.preprocessor import preprocess
pp = check("2. Preprocessor", preprocess, test_orig, output_dir="uploads")
if isinstance(pp, str):
    # preprocess returns a string path, not dict — handle specially
    results[-1]["status"] = "PASS" if os.path.exists(pp) else "FAIL"
    results[-1]["result_keys"] = ["output_path"]
    print(f"  Preprocessed: {pp} (exists={os.path.exists(pp)})")

# ════════════════════════════════════════════
# 3. ELA Agent
# ════════════════════════════════════════════
from agents.ela_agent import compute_ela
ela = check("3. ELA Agent", compute_ela, test_clean, output_dir="uploads")
if ela:
    print(f"  ELA: score={ela.get('ela_score')}, heatmap={bool(ela.get('heatmap_path'))}")

# ════════════════════════════════════════════
# 4. EXIF Agent
# ════════════════════════════════════════════
from agents.exif_agent import analyze_exif
exif = check("4. EXIF Agent", analyze_exif, test_orig)
if exif:
    print(f"  EXIF: flag={exif.get('exif_flag')}, software={exif.get('software')}, has_exif={exif.get('has_exif')}")

# ════════════════════════════════════════════
# 5. QR Agent
# ════════════════════════════════════════════
from agents.qr_agent import decode_document_qr
qr = check("5. QR Agent", decode_document_qr, test_orig)
if qr:
    print(f"  QR: has_qr={qr.get('has_qr')}, method={qr.get('method')}")

# ════════════════════════════════════════════
# 6. OCR (EasyOCR) — THE CRITICAL TEST
# ════════════════════════════════════════════
from utils.ocr_loader import get_reader
t0 = time.perf_counter()
reader = get_reader()
load_time = round(time.perf_counter() - t0, 3)
if reader is None:
    results.append({"stage": "6a. EasyOCR Singleton", "status": "FAIL", "reason": "reader is None", "seconds": load_time})
else:
    results.append({"stage": "6a. EasyOCR Singleton", "status": "PASS", "seconds": load_time})
    print(f"  EasyOCR loaded in {load_time}s")

# Test readtext with 800px downscaling (same logic as main.py)
import cv2
_ocr_img = cv2.imread(test_clean)
_h, _w = _ocr_img.shape[:2]
_max_ocr = 800
if max(_h, _w) > _max_ocr:
    _scale = _max_ocr / max(_h, _w)
    _ocr_img = cv2.resize(_ocr_img, (int(_w * _scale), int(_h * _scale)), interpolation=cv2.INTER_AREA)
    print(f"  Downscaled: {_w}x{_h} -> {_ocr_img.shape[1]}x{_ocr_img.shape[0]}")
else:
    print(f"  No downscale needed: {_w}x{_h} <= {_max_ocr}")

t0 = time.perf_counter()
ocr_raw = reader.readtext(_ocr_img)
ocr_time = round(time.perf_counter() - t0, 3)
if ocr_raw is not None and len(ocr_raw) > 0:
    results.append({"stage": "6b. EasyOCR readtext (800px)", "status": "PASS", "seconds": ocr_time, "regions": len(ocr_raw)})
    print(f"  OCR: {len(ocr_raw)} regions in {ocr_time}s")
else:
    results.append({"stage": "6b. EasyOCR readtext (800px)", "status": "FAIL", "reason": "No text detected", "seconds": ocr_time})

# Build OCR data for downstream stages
ocr_details = [{"bbox": bbox, "text": text, "confidence": conf} for bbox, text, conf in ocr_raw]
raw_text = " ".join(item["text"] for item in ocr_details)
print(f"  OCR text (first 100 chars): {raw_text[:100]}...")

# ════════════════════════════════════════════
# 7. Text Integrity Agent
# ════════════════════════════════════════════
from agents.text_integrity_agent import analyze_text_integrity
ti = check("7. Text Integrity Agent", analyze_text_integrity, test_clean, ocr_details=ocr_details)
if ti:
    print(f"  Text Integrity: score={ti.get('text_integrity_score')}, skipped={ti.get('skipped')}")
    print(f"    font_ok={ti.get('font_analysis',{}).get('font_consistent')}")
    print(f"    conf_ok={ti.get('confidence_analysis',{}).get('confidence_consistent')}")
    print(f"    layout_ok={ti.get('spatial_analysis',{}).get('layout_consistent')}")
    print(f"    dct_ok={ti.get('dct_analysis',{}).get('dct_consistent')}")
    print(f"    copy_move={ti.get('copy_move_analysis',{}).get('copy_move_detected')}")

# ════════════════════════════════════════════
# 8. Deepfake Agent
# ════════════════════════════════════════════
from agents.deepfake_agent import analyze_deepfake
df = check("8. Deepfake Agent", analyze_deepfake, test_clean)
if df:
    print(f"  Deepfake: score={df.get('deepfake_score')}, face={df.get('face_found')}, skipped={df.get('skipped')}")

# ════════════════════════════════════════════
# 9. ML Forgery Agent (expected: skipped)
# ════════════════════════════════════════════
from agents.ml_forgery_agent import analyze_forgery
ml = check("9. ML Forgery Agent", analyze_forgery, test_clean)
if ml:
    print(f"  ML Forgery: score={ml.get('ml_forgery_score')}, skipped={ml.get('skipped')}")

# ════════════════════════════════════════════
# 10. Signature/Seal Agent
# ════════════════════════════════════════════
from agents.signature_seal_agent import analyze_signature_seal
ss = check("10. Signature/Seal Agent", analyze_signature_seal, test_clean)
if ss:
    print(f"  Sig/Seal: score={ss.get('signature_seal_score')}, seal={ss.get('seal',{}).get('seal_found')}, sig={ss.get('signature',{}).get('signature_found')}")

# ════════════════════════════════════════════
# 11. Blockchain Verify
# ════════════════════════════════════════════
from pipeline.blockchain_ledger import verify_document
bc_v = check("11. Blockchain Verify", verify_document, test_orig)
if bc_v:
    print(f"  Blockchain: seen={bc_v.get('previously_seen')}, chain_ok={bc_v.get('chain_valid')}, blocks={bc_v.get('total_blocks')}")

# ════════════════════════════════════════════
# 12. Classifier
# ════════════════════════════════════════════
from pipeline.classifier import classify_document, is_payslip_like
clf = check("12. Classifier", classify_document, raw_text)
if clf:
    doc_type = clf.get("document_type", "unknown")
    print(f"  Classifier: type={doc_type}, confidence={clf.get('confidence')}, method={clf.get('method')}")
    # Test payslip fallback
    payslip_like = is_payslip_like(raw_text)
    print(f"  is_payslip_like: {payslip_like}")

# ════════════════════════════════════════════
# 13. Structured Doc Agent
# ════════════════════════════════════════════
from agents.structured_doc_agent import analyze_structured_document
doc_type = clf.get("document_type", "other") if clf else "other"
if doc_type == "other" and is_payslip_like(raw_text):
    doc_type = "salary_slip"
sd = check("13. Structured Doc Agent", analyze_structured_document, raw_text, doc_type=doc_type)
if sd:
    print(f"  Structured: score={sd.get('structured_validation_score')}, skipped={sd.get('skipped')}, anomalies={sd.get('anomaly_count')}")
    if sd.get("fields_extracted"):
        print(f"    fields: {list(sd['fields_extracted'].keys())[:8]}")

# ════════════════════════════════════════════
# 14. Cross-Validator
# ════════════════════════════════════════════
from pipeline.cross_validator import cross_validate
from agents.ocr_agent import extract_fields
fields = extract_fields(raw_text, document_type=doc_type)
cv = check("14. Cross-Validator", cross_validate, ocr_data=fields, qr_data=qr if qr else {})
if cv:
    print(f"  Cross-val: match={cv.get('qr_ocr_match')}, similarity={cv.get('name_similarity')}")

# ════════════════════════════════════════════
# 15. Scorer
# ════════════════════════════════════════════
from pipeline.scorer import compute_fraud_score
signals = {
    "quality_pass": qg.get("quality_pass", True) if qg else True,
    "quality_details": qg.get("details", "") if qg else "",
    "document_type": doc_type,
    "ela_score": ela.get("ela_score") if ela else None,
    "exif_flag": exif.get("exif_flag") if exif else None,
    "deepfake_score": df.get("deepfake_score") if df else None,
    "qr_ocr_match": cv.get("qr_ocr_match") if cv else None,
    "name_similarity": cv.get("name_similarity", 0) if cv else 0,
    "voice_match": None,
    "ml_forgery_score": ml.get("ml_forgery_score") if ml else None,
    "signature_seal_score": ss.get("signature_seal_score") if ss else None,
    "text_integrity_score": ti.get("text_integrity_score") if ti else None,
    "blockchain_score": bc_v.get("blockchain_score") if bc_v else None,
    "structured_validation_score": sd.get("structured_validation_score") if sd else None,
}
scorer = check("15. Scorer", compute_fraud_score, signals)
if scorer:
    print(f"  Scorer: fraud_score={scorer.get('fraud_score'):.1f}, decision={scorer.get('decision')}, signals_used={scorer.get('signals_used')}")
    print(f"    breakdown: {list(scorer.get('signal_breakdown', {}).keys())}")

# ════════════════════════════════════════════
# 16. Explainer
# ════════════════════════════════════════════
from pipeline.explainer import generate_explanation
exp_signals = {**signals, "fraud_score": scorer.get("fraud_score", 0) if scorer else 0,
               "decision": scorer.get("decision", "UNKNOWN") if scorer else "UNKNOWN",
               "ocr_name": fields.get("name"), "qr_name": qr.get("qr_name") if qr else None,
               "exif_software": exif.get("software") if exif else None}
exp = check("16. Explainer", generate_explanation, exp_signals)
if exp:
    print(f"  Explainer: method={exp.get('method')}, len={len(exp.get('explanation',''))}")

# ════════════════════════════════════════════
# 17. Blockchain Register
# ════════════════════════════════════════════
from pipeline.blockchain_ledger import register_document
bc_r = check("17. Blockchain Register", register_document, test_orig, filename="pipeline_test", document_type=doc_type, fraud_decision=scorer.get("decision","UNKNOWN") if scorer else "UNKNOWN")
if bc_r:
    print(f"  Blockchain Reg: registered={bc_r.get('registered')}, block_id={bc_r.get('block_id')}")

# ════════════════════════════════════════════
# 18. Audit Logger
# ════════════════════════════════════════════
from pipeline.audit_logger import log_verification
full_result = {"document_type": doc_type, "fraud_score": scorer.get("fraud_score",0) if scorer else 0,
               "decision": scorer.get("decision","UNKNOWN") if scorer else "UNKNOWN",
               "explanation": exp.get("explanation","") if exp else ""}
audit_id = log_verification(full_result, filename="pipeline_test")
if audit_id and audit_id > 0:
    results.append({"stage": "18. Audit Logger", "status": "PASS", "seconds": 0.0, "audit_id": audit_id})
    print(f"  Audit: logged as #{audit_id}")
else:
    results.append({"stage": "18. Audit Logger", "status": "FAIL", "reason": f"audit_id={audit_id}"})

# ════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════
print("\n" + "=" * 70)
print("PIPELINE HEALTH CHECK SUMMARY")
print("=" * 70)

passed = sum(1 for r in results if r["status"] == "PASS")
warned = sum(1 for r in results if r["status"] == "WARN")
failed = sum(1 for r in results if r["status"] == "FAIL")
total_time = sum(r.get("seconds", 0) for r in results)

for r in results:
    icon = "✓" if r["status"] == "PASS" else ("⚠" if r["status"] == "WARN" else "✗")
    line = f"  {icon} {r['stage']:45s} {r['status']:6s} {r.get('seconds',0):7.3f}s"
    if r.get("reason"):
        line += f"  | {r['reason'][:60]}"
    print(line)

print(f"\n  TOTAL: {passed} PASS, {warned} WARN, {failed} FAIL (serial time: {total_time:.1f}s)")

# Write JSON
with open("pipeline_health.json", "w") as f:
    json.dump({"summary": {"passed": passed, "warned": warned, "failed": failed, "total_seconds": round(total_time,1)}, "stages": results}, f, indent=2, default=str)

print("\nFull results written to pipeline_health.json")
