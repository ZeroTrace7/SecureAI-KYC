"""
Stage 2 — Image Preprocessor

Normalizes the input image for all downstream agents.
Pure OpenCV + Pillow — no AI model needed.
"""

import os

import cv2
from loguru import logger
from PIL import Image


def preprocess(image_path: str, output_dir: str = None) -> str:
    """
    Preprocess document image for analysis:
      - Resize to max 1024px on longest side (preserve aspect ratio)
      - Bilateral filter (denoise while keeping edges)
      - Re-encode as JPEG (strips adversarial noise, normalizes encoding)

    Args:
        image_path: Path to the original uploaded image.
        output_dir:  Directory to save preprocessed image.
                     Defaults to same directory as input.

    Returns:
        Path to the preprocessed image.
    """
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Preprocessor: Cannot read image at {image_path}")
        return image_path  # return original if we can't process

    # ── 1. Resize (preserve aspect ratio, max 1024px) ──
    h, w = img.shape[:2]
    max_side = 1024
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug(f"Preprocessor: Resized {w}x{h} → {new_w}x{new_h}")

    # ── 2. Bilateral filter (reduce noise, preserve edges) ──
    img = cv2.bilateralFilter(img, 9, 75, 75)

    # ── 3. Convert BGR → RGB and re-encode as high-quality JPEG ──
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)

    if output_dir is None:
        output_dir = os.path.dirname(image_path)

    basename = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{basename}_clean.jpg")
    pil_img.save(output_path, "JPEG", quality=95)

    logger.info(f"Preprocessor: Saved clean image to {output_path}")
    return output_path
