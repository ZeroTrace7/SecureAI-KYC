"""
Agent 8 — ML-Based Image Forgery Detector

Uses kumaran-0188/image_forgery_detector (MobileNetV2, ~87% accuracy)
to classify the ENTIRE document image as real or manipulated.

Unlike the Deepfake agent (which only checks the face region), this
agent analyzes the full document for signs of:
  - AI-generated images
  - Digitally spliced content
  - Copy-paste manipulations
  - General image forgery artifacts

Lightweight (~15 MB), fast inference, complements ELA+Deepfake signals.
"""

from loguru import logger

from config import ENABLE_ML_FORGERY, FORGERY_MODEL_ID

_forgery_pipeline = None


def _get_forgery_pipeline():
    """Lazy-load the HuggingFace forgery detection pipeline."""
    global _forgery_pipeline
    if _forgery_pipeline is None:
        try:
            from transformers import pipeline

            _forgery_pipeline = pipeline(
                "image-classification",
                model=FORGERY_MODEL_ID,
            )
            logger.info(f"ML Forgery Agent: Model loaded ({FORGERY_MODEL_ID})")
        except Exception as e:
            logger.error(f"ML Forgery Agent: Model load failed — {e}")
            return None
    return _forgery_pipeline


def analyze_forgery(image_path: str) -> dict:
    """
    Run ML-based forgery detection on the full document image.

    Returns:
        dict with: ml_forgery_score (0-1), prediction, skipped, reason
    """
    result = {
        "ml_forgery_score": None,
        "prediction": None,
        "skipped": False,
        "reason": None,
    }

    # ── Feature flag check ──
    if not ENABLE_ML_FORGERY:
        result["skipped"] = True
        result["reason"] = "ML forgery detection disabled (ENABLE_ML_FORGERY=false)"
        logger.info("ML Forgery Agent: Disabled by feature flag")
        return result

    # ── Load model ──
    pipe = _get_forgery_pipeline()
    if pipe is None:
        result["skipped"] = True
        result["reason"] = "ML forgery model not available"
        return result

    try:
        from PIL import Image

        img = Image.open(image_path).convert("RGB")

        predictions = pipe(img)

        # Find the "fake" / "forged" label score
        for pred in predictions:
            label = pred["label"].lower()
            if "fake" in label or "forged" in label or "manipulated" in label:
                result["ml_forgery_score"] = round(pred["score"], 4)
                result["prediction"] = pred["label"]
                break

        # If no explicit "fake" label, use 1 - real_score
        if result["ml_forgery_score"] is None and predictions:
            for pred in predictions:
                label = pred["label"].lower()
                if "real" in label or "genuine" in label or "authentic" in label:
                    result["ml_forgery_score"] = round(1.0 - pred["score"], 4)
                    result["prediction"] = f"Inverted from '{pred['label']}'"
                    break

        # Fallback: take the second class score (binary classifier)
        if result["ml_forgery_score"] is None and len(predictions) >= 2:
            # Assume sorted by score desc; second class is "not dominant"
            result["ml_forgery_score"] = round(predictions[1]["score"], 4)
            result["prediction"] = predictions[1]["label"]

        logger.info(
            f"ML Forgery Agent: score={result['ml_forgery_score']} "
            f"prediction='{result['prediction']}'"
        )

    except Exception as e:
        result["skipped"] = True
        result["reason"] = f"Inference failed: {e}"
        logger.error(f"ML Forgery Agent: Inference error — {e}")

    return result
