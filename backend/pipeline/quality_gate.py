"""
Stage 1 — Input Quality Gate

Pure OpenCV checks — no AI model needed.
Validates: blur, resolution, brightness/contrast.
"""

import cv2
import numpy as np
from loguru import logger

from config import (BLUR_THRESHOLD, BRIGHTNESS_MAX, BRIGHTNESS_MIN,
                    MIN_RESOLUTION)


def check_quality(image_path: str) -> dict:
    """
    Run quality checks on an uploaded document image.

    Returns:
        dict with: quality_pass (bool), blur_score, resolution_ok,
        brightness, contrast, details (list of failure reasons)
    """
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Quality gate: Cannot read image at {image_path}")
        return {
            "quality_pass": False,
            "details": ["Cannot read image file"],
            "blur_score": 0,
            "resolution_ok": False,
            "brightness": 0,
            "contrast": 0,
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    details = []

    # ── 1. Blur detection (Laplacian variance) ──
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_ok = blur_score > BLUR_THRESHOLD
    if not blur_ok:
        details.append(
            f"Image is too blurry (score={blur_score:.1f}, min={BLUR_THRESHOLD})"
        )

    # ── 2. Resolution check ──
    h, w = img.shape[:2]
    resolution_ok = h >= MIN_RESOLUTION and w >= MIN_RESOLUTION
    if not resolution_ok:
        details.append(
            f"Resolution too low ({w}x{h}, min={MIN_RESOLUTION}x{MIN_RESOLUTION})"
        )

    # ── 3. Brightness check ──
    brightness = float(np.mean(gray))
    brightness_ok = BRIGHTNESS_MIN < brightness < BRIGHTNESS_MAX
    if not brightness_ok:
        if brightness <= BRIGHTNESS_MIN:
            details.append(f"Image is too dark (brightness={brightness:.1f})")
        else:
            details.append(
                f"Image is too bright/washed out (brightness={brightness:.1f})"
            )

    # ── 4. Contrast check (std deviation of grayscale) ──
    contrast = float(np.std(gray))
    contrast_ok = contrast > 20
    if not contrast_ok:
        details.append(f"Image has very low contrast (std={contrast:.1f})")

    quality_pass = blur_ok and resolution_ok and brightness_ok and contrast_ok

    result = {
        "quality_pass": quality_pass,
        "blur_score": round(blur_score, 2),
        "resolution": f"{w}x{h}",
        "resolution_ok": resolution_ok,
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "details": details if details else ["All quality checks passed"],
    }

    logger.info(f"Quality gate: pass={quality_pass} blur={blur_score:.1f} res={w}x{h}")
    return result
