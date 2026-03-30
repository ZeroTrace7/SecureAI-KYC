"""
Agent 7 — Text Integrity Analysis

ML-enhanced text verification that goes beyond simple OCR extraction:

  1. Font Consistency Analysis: Analyzes OCR bounding box dimensions across
     regions to detect font-size inconsistencies (hallmark of text replacement).
  2. Character Confidence Mapping: Maps per-character confidence from EasyOCR
     to detect low-confidence clusters (pasted/replaced text zones).
  3. Spatial Anomaly Detection: Detects irregular spacing and alignment between
     text lines that suggest manual editing or digital text insertion.

Uses EasyOCR detailed output — no additional model download.
"""

import numpy as np
from loguru import logger


def _analyze_font_consistency(ocr_details: list[dict]) -> dict:
    """
    Analyze font size consistency across OCR bounding boxes.

    Expects ocr_details: list of { bbox, text, confidence } from EasyOCR.

    If font sizes (estimated from bbox heights) vary significantly,
    it suggests text replacement or insertion.
    """
    if not ocr_details or len(ocr_details) < 3:
        return {
            "font_consistent": True,
            "height_std": 0.0,
            "height_cv": 0.0,
            "outlier_count": 0,
            "outlier_regions": [],
            "detail": "Insufficient text regions for font analysis",
        }

    heights = []
    regions_data = []

    for item in ocr_details:
        bbox = item.get("bbox")
        text = item.get("text", "")
        if not bbox or len(text.strip()) < 2:
            continue

        # EasyOCR bbox format: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            try:
                ys = [pt[1] for pt in bbox]
                height = max(ys) - min(ys)
                xs = [pt[0] for pt in bbox]
                x_min = min(xs)
                y_min = min(ys)

                if height > 5:  # filter tiny artifacts
                    heights.append(height)
                    regions_data.append({
                        "text": text[:30],
                        "height": round(float(height), 1),
                        "x": round(float(x_min)),
                        "y": round(float(y_min)),
                    })
            except (IndexError, TypeError):
                continue

    if len(heights) < 3:
        return {
            "font_consistent": True,
            "height_std": 0.0,
            "height_cv": 0.0,
            "outlier_count": 0,
            "outlier_regions": [],
            "detail": "Too few valid text regions for analysis",
        }

    heights_arr = np.array(heights, dtype=np.float64)
    mean_h = float(np.mean(heights_arr))
    std_h = float(np.std(heights_arr))
    cv = std_h / mean_h if mean_h > 0 else 0  # coefficient of variation

    # Flag outliers: regions where height deviates > 1.8 std from mean
    outlier_threshold = 1.8
    outliers = []
    for i, h in enumerate(heights):
        if abs(h - mean_h) > outlier_threshold * std_h and std_h > 0:
            outliers.append(regions_data[i])

    # High CV suggests inconsistent fonts
    font_consistent = cv < 0.35 and len(outliers) <= 1

    return {
        "font_consistent": font_consistent,
        "height_mean": round(mean_h, 1),
        "height_std": round(std_h, 2),
        "height_cv": round(cv, 3),
        "outlier_count": len(outliers),
        "outlier_regions": outliers[:5],  # cap at 5 for response size
        "detail": (
            f"Font sizes are {'consistent' if font_consistent else 'INCONSISTENT'} "
            f"(CV={cv:.3f}, {len(outliers)} outliers)"
        ),
    }


def _analyze_confidence_map(ocr_details: list[dict]) -> dict:
    """
    Map per-region OCR confidence to detect low-confidence clusters.

    Low-confidence text regions may indicate:
    - Overlaid / pasted text (different compression level)
    - Digitally inserted text (font rendering artifacts)
    - Edited regions where original text was removed
    """
    if not ocr_details:
        return {
            "confidence_consistent": True,
            "low_confidence_regions": [],
            "avg_confidence": 0.0,
            "min_confidence": 0.0,
            "detail": "No OCR data available",
        }

    confidences = []
    low_conf_regions = []

    for item in ocr_details:
        conf = item.get("confidence", 0.0)
        text = item.get("text", "")
        bbox = item.get("bbox")

        if len(text.strip()) < 2:
            continue

        confidences.append(conf)

        # Flag regions with notably low confidence
        if conf < 0.5:
            region_info = {"text": text[:30], "confidence": round(conf, 3)}
            if bbox and len(bbox) == 4:
                try:
                    region_info["x"] = round(float(min(pt[0] for pt in bbox)))
                    region_info["y"] = round(float(min(pt[1] for pt in bbox)))
                except (IndexError, TypeError):
                    pass
            low_conf_regions.append(region_info)

    if not confidences:
        return {
            "confidence_consistent": True,
            "low_confidence_regions": [],
            "avg_confidence": 0.0,
            "min_confidence": 0.0,
            "detail": "No confidence data available",
        }

    avg_conf = float(np.mean(confidences))
    min_conf = float(np.min(confidences))
    std_conf = float(np.std(confidences))

    # Suspicious if many low-confidence regions or high variance
    confidence_consistent = len(low_conf_regions) <= 2 and std_conf < 0.3

    return {
        "confidence_consistent": confidence_consistent,
        "avg_confidence": round(avg_conf, 3),
        "min_confidence": round(min_conf, 3),
        "confidence_std": round(std_conf, 3),
        "low_confidence_count": len(low_conf_regions),
        "low_confidence_regions": low_conf_regions[:5],
        "detail": (
            f"OCR confidence is {'uniform' if confidence_consistent else 'VARIABLE'} "
            f"(avg={avg_conf:.3f}, {len(low_conf_regions)} low-confidence regions)"
        ),
    }


def _analyze_spatial_layout(ocr_details: list[dict]) -> dict:
    """
    Detect spatial anomalies in text layout: irregular line spacing,
    misaligned baselines, or orphaned text fragments.
    """
    if not ocr_details or len(ocr_details) < 3:
        return {
            "layout_consistent": True,
            "spacing_anomalies": [],
            "detail": "Insufficient text regions for spatial analysis",
        }

    # Extract y-centers and sort by vertical position
    entries = []
    for item in ocr_details:
        bbox = item.get("bbox")
        text = item.get("text", "")
        if not bbox or len(bbox) != 4 or len(text.strip()) < 2:
            continue
        try:
            ys = [pt[1] for pt in bbox]
            xs = [pt[0] for pt in bbox]
            y_center = (min(ys) + max(ys)) / 2
            height = max(ys) - min(ys)
            entries.append({
                "y_center": y_center,
                "height": height,
                "x_min": min(xs),
                "text": text[:30],
            })
        except (IndexError, TypeError):
            continue

    if len(entries) < 3:
        return {
            "layout_consistent": True,
            "spacing_anomalies": [],
            "detail": "Too few valid entries for spatial analysis",
        }

    # Sort by y_center
    entries.sort(key=lambda e: e["y_center"])

    # Compute line gaps
    gaps = []
    for i in range(1, len(entries)):
        gap = entries[i]["y_center"] - entries[i - 1]["y_center"]
        if gap > 2:  # ignore overlapping lines
            gaps.append({
                "gap": gap,
                "between": f"'{entries[i-1]['text']}' → '{entries[i]['text']}'",
                "y_position": entries[i]["y_center"],
            })

    if not gaps:
        return {
            "layout_consistent": True,
            "spacing_anomalies": [],
            "detail": "Could not compute line spacing",
        }

    gap_values = np.array([g["gap"] for g in gaps], dtype=np.float64)
    mean_gap = float(np.mean(gap_values))
    std_gap = float(np.std(gap_values))

    # Flag anomalies: gaps that deviate > 2 std from mean
    anomalies = []
    if std_gap > 0:
        for g in gaps:
            deviation = abs(g["gap"] - mean_gap) / std_gap
            if deviation > 2.0:
                anomalies.append({
                    "gap": round(g["gap"], 1),
                    "expected": round(mean_gap, 1),
                    "deviation_sigma": round(deviation, 1),
                    "between": g["between"],
                })

    layout_consistent = len(anomalies) <= 1

    return {
        "layout_consistent": layout_consistent,
        "mean_line_gap": round(mean_gap, 1),
        "gap_std": round(std_gap, 2),
        "spacing_anomaly_count": len(anomalies),
        "spacing_anomalies": anomalies[:5],
        "detail": (
            f"Line spacing is {'regular' if layout_consistent else 'IRREGULAR'} "
            f"(mean_gap={mean_gap:.1f}px, {len(anomalies)} anomalies)"
        ),
    }


def _analyze_dct_consistency(image_path: str) -> dict:
    """
    Detect double JPEG compression — a hallmark of edited documents.

    When a JPEG is opened in an editor, modified, and re-saved, the
    8×8 DCT block boundaries from the original compression create
    periodic artifacts in the DC coefficient histogram (multiple peaks).
    Single-compressed images have a smooth, unimodal distribution.
    """
    try:
        import cv2

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {"dct_consistent": True, "peak_count": 0,
                    "detail": "DCT analysis: cannot read image"}

        h, w = img.shape
        if h < 64 or w < 64:
            return {"dct_consistent": True, "peak_count": 0,
                    "detail": "DCT analysis: image too small for analysis"}

        # Compute DCT on 8x8 blocks (standard JPEG block size)
        dc_coefficients = []
        for i in range(0, h - 8, 8):
            for j in range(0, w - 8, 8):
                block = np.float32(img[i:i+8, j:j+8])
                dct_block = cv2.dct(block)
                dc_coefficients.append(dct_block[0][0])  # DC component

        if len(dc_coefficients) < 50:
            return {"dct_consistent": True, "peak_count": 0,
                    "detail": "DCT analysis: insufficient blocks"}

        coeffs = np.array(dc_coefficients)

        # Analyze distribution: double-compressed images have
        # a bimodal or multi-modal DC coefficient histogram
        hist, bin_edges = np.histogram(coeffs, bins=64)

        # Smooth histogram to reduce noise
        from scipy.ndimage import uniform_filter1d
        smoothed = uniform_filter1d(hist.astype(float), size=3)

        # Count significant peaks (above mean + 1.5*std)
        threshold = np.mean(smoothed) + 1.5 * np.std(smoothed)
        peaks = 0
        for i in range(1, len(smoothed) - 1):
            if smoothed[i] > threshold and smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
                peaks += 1

        # Multiple prominent peaks = double compression = edited
        suspicious = peaks >= 3

        return {
            "dct_consistent": not suspicious,
            "peak_count": int(peaks),
            "detail": (
                f"DCT analysis: {'SUSPICIOUS — double JPEG compression detected '
                 f'({peaks} spectral peaks, expected ≤2)' if suspicious else
                 f'normal compression pattern ({peaks} peaks)'}"
            ),
        }

    except ImportError:
        return {"dct_consistent": True, "peak_count": 0,
                "detail": "DCT analysis: scipy not available (skipped)"}
    except Exception as e:
        logger.warning(f"Text Integrity Agent: DCT analysis failed — {e}")
        return {"dct_consistent": True, "peak_count": 0,
                "detail": f"DCT analysis: error ({e})"}


def _detect_copy_move(image_path: str) -> dict:
    """
    Detect copy-move forgery using ORB feature matching.

    If large clusters of keypoint matches are found between
    different regions of the same image, it indicates that
    a region was duplicated (copy-moved).
    """
    try:
        import cv2

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {"copy_move_detected": False, "match_clusters": 0,
                    "detail": "Copy-move: cannot read image"}

        # ORB feature detection
        orb = cv2.ORB_create(nfeatures=1000)
        keypoints, descriptors = orb.detectAndCompute(img, None)

        if descriptors is None or len(keypoints) < 20:
            return {"copy_move_detected": False, "match_clusters": 0,
                    "detail": "Copy-move: insufficient features for analysis"}

        # Brute-force match descriptors against themselves
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descriptors, descriptors, k=5)

        # Filter: keep matches that are spatially distant
        # (same feature in different locations = copy-move)
        suspicious_matches = 0
        min_distance = 50  # pixels — matches closer than this are just neighbors

        for m_list in matches:
            for m in m_list:
                if m.queryIdx == m.trainIdx:
                    continue  # skip self-match
                if m.distance > 30:
                    continue  # too different

                # Check spatial distance
                pt1 = keypoints[m.queryIdx].pt
                pt2 = keypoints[m.trainIdx].pt
                spatial_dist = np.sqrt(
                    (pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2
                )

                if spatial_dist > min_distance:
                    suspicious_matches += 1

        # Normalize by total keypoints
        match_ratio = suspicious_matches / max(len(keypoints), 1)
        copy_detected = match_ratio > 0.15  # >15% suspicious matches

        return {
            "copy_move_detected": copy_detected,
            "match_clusters": suspicious_matches,
            "match_ratio": round(match_ratio, 3),
            "detail": (
                f"Copy-move: {'SUSPICIOUS — {suspicious_matches} duplicated feature '
                 f'clusters detected (ratio={match_ratio:.1%})' if copy_detected else
                 f'no significant duplication found ({suspicious_matches} matches)'}"
            ),
        }

    except Exception as e:
        logger.warning(f"Text Integrity Agent: Copy-move detection failed — {e}")
        return {"copy_move_detected": False, "match_clusters": 0,
                "detail": f"Copy-move: error ({e})"}


def analyze_text_integrity(image_path: str) -> dict:
    """
    Run comprehensive text integrity analysis on a document image.

    Uses EasyOCR detailed output (with bounding boxes) to perform:
    - Font consistency analysis
    - Character confidence mapping
    - Spatial layout anomaly detection

    Returns:
        dict with: text_integrity_score, font_analysis, confidence_analysis,
                   spatial_analysis, integrity_details
    """
    result = {
        "text_integrity_score": 0.0,
        "font_analysis": {},
        "confidence_analysis": {},
        "spatial_analysis": {},
        "integrity_details": [],
        "skipped": False,
    }

    # ── Get detailed OCR output with bounding boxes ──
    try:
        from utils.ocr_loader import get_reader

        reader = get_reader()
        if reader is None:
            result["skipped"] = True
            result["integrity_details"].append("EasyOCR not available")
            logger.error("Text Integrity Agent: EasyOCR singleton unavailable")
            return result

        raw_results = reader.readtext(image_path)

        ocr_details = []
        for bbox, text, conf in raw_results:
            ocr_details.append({
                "bbox": bbox,
                "text": text,
                "confidence": conf,
            })

        logger.info(
            f"Text Integrity Agent: Got {len(ocr_details)} OCR regions"
        )

    except ImportError:
        result["skipped"] = True
        result["integrity_details"].append("EasyOCR not available")
        logger.error("Text Integrity Agent: easyocr not installed")
        return result
    except Exception as e:
        result["skipped"] = True
        result["integrity_details"].append(f"OCR extraction failed: {e}")
        logger.error(f"Text Integrity Agent: OCR error — {e}")
        return result

    if len(ocr_details) < 3:
        result["integrity_details"].append(
            "Too few text regions detected for integrity analysis"
        )
        logger.info("Text Integrity Agent: Insufficient text regions")
        return result

    # ── Run analyses ──
    font_result = _analyze_font_consistency(ocr_details)
    conf_result = _analyze_confidence_map(ocr_details)
    spatial_result = _analyze_spatial_layout(ocr_details)

    # ── Frequency-domain and feature-based analyses ──
    dct_result = _analyze_dct_consistency(image_path)
    copy_move_result = _detect_copy_move(image_path)

    result["font_analysis"] = font_result
    result["confidence_analysis"] = conf_result
    result["spatial_analysis"] = spatial_result
    result["dct_analysis"] = dct_result
    result["copy_move_analysis"] = copy_move_result

    # ── Compute overall integrity score (0 = clean, 1 = suspicious) ──
    score_components = []

    # Font inconsistency contributes to suspicion
    if not font_result.get("font_consistent", True):
        cv = font_result.get("height_cv", 0)
        score_components.append(min(1.0, cv * 2))
        result["integrity_details"].append(font_result["detail"])

    # Low-confidence clusters
    if not conf_result.get("confidence_consistent", True):
        low_count = conf_result.get("low_confidence_count", 0)
        score_components.append(min(1.0, low_count * 0.15))
        result["integrity_details"].append(conf_result["detail"])

    # Spatial anomalies
    if not spatial_result.get("layout_consistent", True):
        anomaly_count = spatial_result.get("spacing_anomaly_count", 0)
        score_components.append(min(1.0, anomaly_count * 0.2))
        result["integrity_details"].append(spatial_result["detail"])

    # DCT double-compression
    if not dct_result.get("dct_consistent", True):
        peak_count = dct_result.get("peak_count", 0)
        score_components.append(min(1.0, peak_count * 0.25))
        result["integrity_details"].append(dct_result["detail"])

    # Copy-move detection
    if copy_move_result.get("copy_move_detected", False):
        match_ratio = copy_move_result.get("match_ratio", 0)
        score_components.append(min(1.0, match_ratio * 3))
        result["integrity_details"].append(copy_move_result["detail"])

    if score_components:
        result["text_integrity_score"] = round(
            float(np.mean(score_components)), 3
        )
    else:
        result["text_integrity_score"] = 0.0
        result["integrity_details"].append(
            "Text integrity checks passed — no anomalies detected"
        )

    logger.info(
        f"Text Integrity Agent: score={result['text_integrity_score']} "
        f"font_ok={font_result.get('font_consistent')} "
        f"conf_ok={conf_result.get('confidence_consistent')} "
        f"layout_ok={spatial_result.get('layout_consistent')} "
        f"dct_ok={dct_result.get('dct_consistent')} "
        f"copy_move={copy_move_result.get('copy_move_detected')}"
    )

    return result

