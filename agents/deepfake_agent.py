"""
Agent 5 — Deepfake / Face Detection

Single model: dima806/deepfake_vs_real_image_detection (350 MB)
Weight capped at 0.10 in fraud score.

IMPORTANT: Aadhaar photos are small (~100x120px) and low quality.
The model was trained on high-res selfies/videos, so results on
document photos are NOISY. This is a secondary signal only.

Safety features:
  - Skips if face is smaller than MIN_FACE_SIZE
  - Skips if model fails to load
  - Returns neutral result on any error
"""

import cv2
import numpy as np
from loguru import logger
from config import ENABLE_DEEPFAKE, DEEPFAKE_MODEL_ID, MIN_FACE_SIZE

# ── Lazy-loaded model ──
_deepfake_pipeline = None
_face_cascade = None


def _get_face_cascade():
    """Get OpenCV's Haar cascade for face detection (lighter than DeepFace)."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade


def _get_deepfake_pipeline():
    """Lazy-load the HF deepfake detection pipeline."""
    global _deepfake_pipeline
    if _deepfake_pipeline is None:
        try:
            from transformers import pipeline
            _deepfake_pipeline = pipeline(
                "image-classification",
                model=DEEPFAKE_MODEL_ID,
            )
            logger.info(f"Deepfake Agent: Model loaded ({DEEPFAKE_MODEL_ID})")
        except Exception as e:
            logger.error(f"Deepfake Agent: Model load failed — {e}")
            return None
    return _deepfake_pipeline


def _extract_face(image_path: str) -> np.ndarray | None:
    """Extract the largest face from the document using Haar cascades."""
    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = _get_face_cascade()
    faces = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    if len(faces) == 0:
        return None

    # Take the largest face
    areas = [w * h for (x, y, w, h) in faces]
    best_idx = np.argmax(areas)
    x, y, w, h = faces[best_idx]

    return img[y : y + h, x : x + w]


def analyze_deepfake(image_path: str) -> dict:
    """
    Run deepfake detection on a document image.

    Returns:
        dict with: deepfake_score (0-1 or None), face_found, face_size, skipped, reason
    """
    result = {
        "deepfake_score": None,
        "face_found": False,
        "face_size": None,
        "skipped": False,
        "reason": None,
    }

    # ── Feature flag check ──
    if not ENABLE_DEEPFAKE:
        result["skipped"] = True
        result["reason"] = "Deepfake detection disabled (ENABLE_DEEPFAKE=false)"
        logger.info("Deepfake Agent: Disabled by feature flag")
        return result

    # ── Extract face ──
    try:
        face = _extract_face(image_path)
    except Exception as e:
        result["skipped"] = True
        result["reason"] = f"Face extraction failed: {e}"
        logger.warning(f"Deepfake Agent: Face extraction error — {e}")
        return result

    if face is None:
        result["reason"] = "No face detected in document"
        logger.info("Deepfake Agent: No face found, skipping")
        return result

    result["face_found"] = True
    h, w = face.shape[:2]
    result["face_size"] = f"{w}x{h}"

    # ── Size check (skip tiny faces) ──
    if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
        result["skipped"] = True
        result["reason"] = (
            f"Face too small ({w}x{h}px, min={MIN_FACE_SIZE}px). "
            f"Results would be unreliable on low-res document photos."
        )
        logger.info(f"Deepfake Agent: Face too small ({w}x{h}), skipping")
        return result

    # ── Load model & predict ──
    pipe = _get_deepfake_pipeline()
    if pipe is None:
        result["skipped"] = True
        result["reason"] = "Deepfake model not available"
        return result

    try:
        # Convert BGR→RGB for the model
        from PIL import Image as PILImage

        face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        face_pil = PILImage.fromarray(face_rgb)

        predictions = pipe(face_pil)

        # Find the "fake" label score
        for pred in predictions:
            label = pred["label"].lower()
            if "fake" in label or "forged" in label or "deepfake" in label:
                result["deepfake_score"] = round(pred["score"], 4)
                break

        # If no explicit "fake" label, use 1 - real_score
        if result["deepfake_score"] is None and predictions:
            for pred in predictions:
                label = pred["label"].lower()
                if "real" in label or "genuine" in label:
                    result["deepfake_score"] = round(1.0 - pred["score"], 4)
                    break

        logger.info(
            f"Deepfake Agent: score={result['deepfake_score']} "
            f"face_size={w}x{h}"
        )

    except Exception as e:
        result["skipped"] = True
        result["reason"] = f"Model inference failed: {e}"
        logger.error(f"Deepfake Agent: Inference error — {e}")

    return result
