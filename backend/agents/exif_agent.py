"""
Agent 4 — EXIF Metadata Analyzer

Extracts EXIF metadata and flags documents edited with
Photoshop, GIMP, Canva, Paint, or other image editors.
Also detects timestamp impossibilities and missing metadata.

No AI model needed — pure library-based analysis.
"""

import exifread
from loguru import logger

_SUSPICIOUS_SOFTWARE = [
    "photoshop",
    "gimp",
    "paint",
    "editor",
    "canva",
    "lightroom",
    "affinity",
    "pixlr",
    "fotor",
    "snapseed",
    "picsart",
    "corel",
    "inkscape",
    "illustrator",
    # AI generators and screenshot tools
    "dall-e",
    "midjourney",
    "stable diffusion",
    "comfyui",
    "automatic1111",
    "screenshot",
    "snipping",
    "greenshot",
    "sharex",
]


def _parse_exif_datetime(dt_str: str):
    """Parse EXIF datetime string (YYYY:MM:DD HH:MM:SS) to comparable tuple."""
    if not dt_str or dt_str.strip() == "":
        return None
    try:
        # EXIF format: "2024:03:15 14:30:00"
        parts = dt_str.strip().replace("-", ":").split(" ")
        if len(parts) >= 1:
            date_parts = parts[0].split(":")
            if len(date_parts) == 3:
                return tuple(int(p) for p in date_parts)
    except (ValueError, IndexError):
        pass
    return None


def analyze_exif(image_path: str) -> dict:
    """
    Extract and analyze EXIF metadata from a document image.

    Flags:
      - Documents processed with image editing software
      - Missing EXIF data (could indicate a scan or screenshot)
      - Suspicious modification timestamps
      - Timestamp impossibilities (modified before created)

    Returns:
        dict with: exif_flag, software, camera_make, date_taken, has_exif, details
    """
    result = {
        "exif_flag": "clean",
        "software": None,
        "camera_make": None,
        "camera_model": None,
        "date_taken": None,
        "date_modified": None,
        "has_exif": False,
        "details": [],
    }

    try:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)
    except Exception as e:
        logger.warning(f"EXIF Agent: Cannot read EXIF — {e}")
        result["details"].append(f"Cannot read EXIF data: {e}")
        return result

    if not tags:
        result["exif_flag"] = "notable"
        result["details"].append(
            "No EXIF metadata found — authentic smartphone photos always contain "
            "EXIF data. Missing metadata is a hallmark of images exported from "
            "Photoshop, Canva, AI generators, or screenshots."
        )
        logger.info("EXIF Agent: No EXIF data — flagged as notable")
        return result

    result["has_exif"] = True

    # ── Extract key fields ──
    software = str(tags.get("Image Software", "")).strip()
    if software:
        result["software"] = software

    make = str(tags.get("Image Make", "")).strip()
    if make:
        result["camera_make"] = make

    model = str(tags.get("Image Model", "")).strip()
    if model:
        result["camera_model"] = model

    date_original = str(tags.get("EXIF DateTimeOriginal", "")).strip()
    if date_original:
        result["date_taken"] = date_original

    date_modified = str(tags.get("Image DateTime", "")).strip()
    if date_modified:
        result["date_modified"] = date_modified

    # ── Check 1: Suspicious software ──
    if software:
        sw_lower = software.lower()
        for keyword in _SUSPICIOUS_SOFTWARE:
            if keyword in sw_lower:
                result["exif_flag"] = "suspicious"
                result["details"].append(
                    f"Document was edited with '{software}' — "
                    f"this is unusual for authentic government documents"
                )
                break

    # ── Check 2: Timestamp impossibility ──
    if date_original and date_modified:
        dt_orig = _parse_exif_datetime(date_original)
        dt_mod = _parse_exif_datetime(date_modified)
        if dt_orig and dt_mod and dt_mod < dt_orig:
            result["exif_flag"] = "suspicious"
            result["details"].append(
                f"TIMESTAMP ANOMALY: File was modified ({date_modified}) "
                f"BEFORE it was originally created ({date_original}) — "
                f"this is physically impossible and indicates metadata tampering"
            )

    # ── Check 3: Camera make vs Software mismatch ──
    if make and software:
        # If there's a camera make but also editing software, it was captured then edited
        sw_lower = software.lower()
        has_editor = any(kw in sw_lower for kw in _SUSPICIOUS_SOFTWARE)
        if has_editor and make:
            result["details"].append(
                f"Photo was captured by '{make}' camera but then processed "
                f"with '{software}' — possible post-capture editing"
            )

    if result["exif_flag"] == "clean":
        result["details"].append("EXIF metadata appears normal")

    logger.info(
        f"EXIF Agent: flag={result['exif_flag']} software='{software}' "
        f"make='{make}' has_exif={result['has_exif']}"
    )

    return result

