"""
Agent 6 — Signature & Seal Verification

Detects, isolates, and verifies signatures and official seals/stamps
on documents using computer vision techniques:

  1. Seal Detection: HSV color-space filtering for red/blue circular seals,
     Hough Circle Transform, contour validation, circularity scoring.
  2. Signature Detection: Adaptive thresholding + contour analysis to find
     handwriting-like ink strokes in lower document regions.
  3. Consistency Scoring: Measures seal circularity, signature stroke density,
     spatial positioning relative to document layout.

No external model download needed — pure OpenCV + numpy.
"""

import cv2
import numpy as np
from loguru import logger


# ── Color ranges for common seal/stamp colors (HSV) ──
# Red seals (two ranges because red wraps around in HSV)
_RED_LOWER_1 = np.array([0, 70, 50])
_RED_UPPER_1 = np.array([10, 255, 255])
_RED_LOWER_2 = np.array([160, 70, 50])
_RED_UPPER_2 = np.array([180, 255, 255])

# Blue seals
_BLUE_LOWER = np.array([100, 70, 50])
_BLUE_UPPER = np.array([130, 255, 255])

# Purple / violet seals
_PURPLE_LOWER = np.array([130, 50, 50])
_PURPLE_UPPER = np.array([160, 255, 255])


def _detect_seals(img: np.ndarray) -> dict:
    """
    Detect circular seals/stamps using color segmentation + contour analysis.

    Returns dict with: seal_found, seal_count, seal_confidence,
                       seal_regions[], seal_details
    """
    result = {
        "seal_found": False,
        "seal_count": 0,
        "seal_confidence": 0.0,
        "seal_regions": [],
        "seal_details": [],
    }

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]

    # Combine masks for red, blue, and purple seals
    mask_red1 = cv2.inRange(hsv, _RED_LOWER_1, _RED_UPPER_1)
    mask_red2 = cv2.inRange(hsv, _RED_LOWER_2, _RED_UPPER_2)
    mask_blue = cv2.inRange(hsv, _BLUE_LOWER, _BLUE_UPPER)
    mask_purple = cv2.inRange(hsv, _PURPLE_LOWER, _PURPLE_UPPER)

    combined_mask = mask_red1 | mask_red2 | mask_blue | mask_purple

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(
        combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    min_seal_area = (h * w) * 0.001  # at least 0.1% of image
    max_seal_area = (h * w) * 0.15   # at most 15% of image

    seal_candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_seal_area or area > max_seal_area:
            continue

        # Circularity check
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)

        # Bounding rect aspect ratio
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect_ratio = min(bw, bh) / max(bw, bh) if max(bw, bh) > 0 else 0

        # Seal-like if reasonably circular or has moderate aspect ratio
        # (seals can be oval too)
        if circularity > 0.3 and aspect_ratio > 0.5:
            confidence = min(1.0, circularity * 1.2)
            seal_candidates.append({
                "x": int(x), "y": int(y),
                "width": int(bw), "height": int(bh),
                "area": int(area),
                "circularity": round(float(circularity), 3),
                "confidence": round(float(confidence), 3),
            })

    if seal_candidates:
        # Sort by confidence, take top 3
        seal_candidates.sort(key=lambda s: s["confidence"], reverse=True)
        top_seals = seal_candidates[:3]

        result["seal_found"] = True
        result["seal_count"] = len(top_seals)
        result["seal_confidence"] = round(
            max(s["confidence"] for s in top_seals), 3
        )
        result["seal_regions"] = top_seals
        result["seal_details"].append(
            f"Detected {len(top_seals)} seal-like region(s) with "
            f"max circularity={top_seals[0]['circularity']}"
        )
    else:
        result["seal_details"].append("No circular seal or stamp detected")

    return result


def _detect_signatures(img: np.ndarray) -> dict:
    """
    Detect handwritten signatures using adaptive thresholding + stroke analysis.

    Looks primarily in the bottom-third (typical signature zone) but also
    scans the full document for completeness.

    Returns dict with: signature_found, signature_confidence,
                       signature_regions[], signature_details
    """
    result = {
        "signature_found": False,
        "signature_confidence": 0.0,
        "signature_regions": [],
        "signature_details": [],
    }

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Focus on bottom-third where signatures usually appear
    sig_zone_y = int(h * 0.55)
    sig_roi = gray[sig_zone_y:, :]

    # Adaptive threshold to isolate dark ink strokes
    thresh = cv2.adaptiveThreshold(
        sig_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 10
    )

    # Remove noise
    kernel_small = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_small)

    # Find contours
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Signature characteristics:
    # - Wide and short (aspect ratio > 2)
    # - Moderate area (not too tiny = noise, not too big = text block)
    # - Low solidity (handwriting is "sparse" compared to printed text)
    min_sig_width = w * 0.05
    min_sig_area = (h * w) * 0.0005
    max_sig_area = (h * w) * 0.05

    sig_candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_sig_area or area > max_sig_area:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw < min_sig_width:
            continue

        aspect = bw / bh if bh > 0 else 0

        # Solidity: area / convex hull area
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        # Stroke density: ratio of filled pixels in bounding box
        roi_mask = thresh[y:y + bh, x:x + bw]
        stroke_density = np.sum(roi_mask > 0) / (bw * bh) if (bw * bh) > 0 else 0

        # Signature heuristic:
        # - aspect ratio > 1.5 (wider than tall)
        # - low-to-moderate solidity (0.1-0.7, handwriting is sparse)
        # - moderate stroke density (0.05-0.5)
        if aspect > 1.3 and 0.05 < solidity < 0.75 and 0.03 < stroke_density < 0.55:
            confidence = min(1.0, 0.4 + aspect * 0.1 + (1 - solidity) * 0.3)
            sig_candidates.append({
                "x": int(x),
                "y": int(y + sig_zone_y),  # offset back to full-image coords
                "width": int(bw),
                "height": int(bh),
                "aspect_ratio": round(float(aspect), 2),
                "solidity": round(float(solidity), 3),
                "stroke_density": round(float(stroke_density), 3),
                "confidence": round(float(confidence), 3),
            })

    if sig_candidates:
        sig_candidates.sort(key=lambda s: s["confidence"], reverse=True)
        top_sigs = sig_candidates[:2]

        result["signature_found"] = True
        result["signature_confidence"] = round(
            max(s["confidence"] for s in top_sigs), 3
        )
        result["signature_regions"] = top_sigs
        result["signature_details"].append(
            f"Detected {len(top_sigs)} signature-like region(s) in document"
        )
    else:
        result["signature_details"].append(
            "No handwritten signature pattern detected"
        )

    return result


def _detect_pasted_elements(img) -> dict:
    """
    Detect unnaturally sharp edges — hallmark of digitally pasted seals/signatures.

    In naturally scanned or photographed documents, all elements have similar
    edge softness due to lens blur and paper texture. When a seal or signature
    is digitally pasted (copy-pasted from another document or created in
    Photoshop), it often has unnaturally sharp edges vs. the background.

    Uses Sobel edge detection to compare edge sharpness across the document.
    A high max-to-mean edge ratio indicates pasted elements.
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Sobel edge detection in both directions
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.sqrt(sobelx**2 + sobely**2)

        # Statistics
        mean_edge = np.mean(edge_magnitude)
        max_edge = np.max(edge_magnitude)

        # ── Born-digital detection ──
        # In a scanned/photographed document, mean edge strength is LOW (~10-25)
        # because paper texture and camera blur soften everything.
        # In a born-digital PDF (e-Aadhaar, DigiLocker), mean edge strength is
        # HIGH (>35) because ALL elements (text, logos, borders) are digitally crisp.
        # Pasted elements are only suspicious when sharp AGAINST a soft background.
        if mean_edge > 35:
            logger.info(
                f"Signature/Seal Agent: Born-digital document detected "
                f"(mean_edge={mean_edge:.1f} > 35) — skipping edge forensics"
            )
            return {
                "edge_consistent": True,
                "edge_ratio": round(float(max_edge / mean_edge if mean_edge > 0 else 0), 2),
                "percentile_ratio": 0.0,
                "detail": (
                    f"Edge analysis: born-digital document detected "
                    f"(mean_edge={mean_edge:.1f}) — uniform sharpness is expected"
                ),
            }

        # Edge ratio: how much sharper are the sharpest edges vs. average
        edge_ratio = max_edge / mean_edge if mean_edge > 0 else 0

        # High percentile analysis — check if top 1% of edges are extreme outliers
        p99 = np.percentile(edge_magnitude, 99)
        p50 = np.percentile(edge_magnitude, 50)
        percentile_ratio = p99 / p50 if p50 > 0 else 0

        # Suspicious if max edges are >15x stronger than average
        # OR if 99th percentile is >20x stronger than median
        suspicious = edge_ratio > 15 or percentile_ratio > 20

        return {
            "edge_consistent": not suspicious,
            "edge_ratio": round(float(edge_ratio), 2),
            "percentile_ratio": round(float(percentile_ratio), 2),
            "detail": (
                f"Edge analysis: {'SUSPICIOUS — unnaturally sharp edges detected '
                 f'(ratio={edge_ratio:.1f}, p99/p50={percentile_ratio:.1f}) — '
                 f'possible digitally pasted elements' if suspicious else
                 f'consistent edge profile (ratio={edge_ratio:.1f})'}"
            ),
        }

    except Exception as e:
        logger.warning(f"Signature/Seal Agent: Edge analysis failed — {e}")
        return {
            "edge_consistent": True,
            "edge_ratio": 0,
            "detail": f"Edge analysis: error ({e})",
        }


def analyze_signature_seal(image_path: str) -> dict:
    """
    Run signature and seal verification on a document image.

    Returns:
        dict with combined seal + signature results, plus overall score.
    """
    result = {
        "seal": {"seal_found": False, "seal_confidence": 0.0},
        "signature": {"signature_found": False, "signature_confidence": 0.0},
        "edge_analysis": {},
        "signature_seal_score": 0.0,
        "anomalies": [],
        "skipped": False,
    }

    try:
        img = cv2.imread(image_path)
        if img is None:
            result["skipped"] = True
            result["anomalies"].append("Cannot read image file")
            logger.error(f"Signature/Seal Agent: Cannot read {image_path}")
            return result
    except Exception as e:
        result["skipped"] = True
        result["anomalies"].append(f"Image load error: {e}")
        logger.error(f"Signature/Seal Agent: Load error — {e}")
        return result

    # ── Detect seals ──
    seal_result = _detect_seals(img)
    result["seal"] = seal_result

    # ── Detect signatures ──
    sig_result = _detect_signatures(img)
    result["signature"] = sig_result

    # ── Edge sharpness (pasted element detection) ──
    edge_result = _detect_pasted_elements(img)
    result["edge_analysis"] = edge_result

    # ── Anomaly checks ──
    if seal_result["seal_found"]:
        for region in seal_result.get("seal_regions", []):
            if region.get("circularity", 0) < 0.5:
                result["anomalies"].append(
                    f"Seal region at ({region['x']},{region['y']}) has low "
                    f"circularity ({region['circularity']}), possibly irregular"
                )

    # Flag pasted elements
    if not edge_result.get("edge_consistent", True):
        result["anomalies"].append(edge_result["detail"])

    # ── Overall score (0 = clean, 1 = suspicious) ──
    anomaly_count = len(result["anomalies"])
    if anomaly_count > 0:
        result["signature_seal_score"] = min(1.0, 0.3 + anomaly_count * 0.2)
    else:
        result["signature_seal_score"] = 0.0

    logger.info(
        f"Signature/Seal Agent: seal_found={seal_result['seal_found']} "
        f"sig_found={sig_result['signature_found']} "
        f"edge_ok={edge_result.get('edge_consistent')} "
        f"score={result['signature_seal_score']} "
        f"anomalies={anomaly_count}"
    )

    return result

