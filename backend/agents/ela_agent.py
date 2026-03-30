"""
Agent 1 — ELA (Error Level Analysis) Forensics

Custom ELA implementation (no ML model needed):
  1. Re-compress image at lower quality
  2. Compute pixel-level difference
  3. Amplify and score the difference
  4. Generate heatmap for visual demo

Tampered regions show HIGHER error levels because they were
saved at a different compression level than the rest of the image.
"""

import os

import numpy as np
from loguru import logger
from PIL import Image, ImageChops


def compute_ela(image_path: str, quality: int = 90, output_dir: str = None) -> dict:
    """
    Perform Error Level Analysis on a document image.

    Args:
        image_path: Path to the preprocessed document image.
        quality:    JPEG re-compression quality (lower = more sensitive).
        output_dir: Directory to save the heatmap. Defaults to same dir.

    Returns:
        dict with: ela_score (0-1), heatmap_path, max_diff, mean_diff
    """
    try:
        original = Image.open(image_path).convert("RGB")
    except Exception as e:
        logger.error(f"ELA Agent: Cannot open image — {e}")
        return {"ela_score": 0.0, "heatmap_path": None, "error": str(e)}

    if output_dir is None:
        output_dir = os.path.dirname(image_path)

    # ── Step 1: Re-save at lower quality ──
    temp_path = os.path.join(output_dir, "_ela_temp.jpg")
    original.save(temp_path, "JPEG", quality=quality)
    resaved = Image.open(temp_path)

    # ── Step 2: Compute pixel-level difference ──
    ela_image = ImageChops.difference(original, resaved)

    # ── Step 3: Amplify differences for visualization ──
    extrema = ela_image.getextrema()
    max_diff = max(ex[1] for ex in extrema)

    if max_diff == 0:
        # Perfectly identical — no ELA signal
        _cleanup(temp_path)
        logger.info("ELA Agent: No difference detected (score=0.0)")
        return {
            "ela_score": 0.0,
            "heatmap_path": None,
            "max_diff": 0,
            "mean_diff": 0.0,
        }

    scale = 255.0 / max_diff
    ela_enhanced = ela_image.point(lambda x: min(255, int(x * scale)))

    # ── Step 4: Save heatmap ──
    basename = os.path.splitext(os.path.basename(image_path))[0]
    heatmap_path = os.path.join(output_dir, f"{basename}_ela_heatmap.png")
    ela_enhanced.save(heatmap_path)

    # ── Step 5: Compute score ──
    ela_array = np.array(ela_enhanced, dtype=np.float64)
    mean_diff = float(np.mean(ela_array))
    ela_score = mean_diff / 255.0  # normalize to 0-1

    # Clean up temp file
    _cleanup(temp_path)

    logger.info(
        f"ELA Agent: score={ela_score:.4f} max_diff={max_diff} "
        f"mean_diff={mean_diff:.2f} heatmap={heatmap_path}"
    )

    return {
        "ela_score": round(ela_score, 4),
        "heatmap_path": heatmap_path,
        "max_diff": max_diff,
        "mean_diff": round(mean_diff, 2),
    }


def _cleanup(path: str):
    """Silently remove a temp file."""
    try:
        os.remove(path)
    except OSError:
        pass
