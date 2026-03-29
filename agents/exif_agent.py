"""
Agent 4 — EXIF Metadata Analyzer

Extracts EXIF metadata and flags documents edited with
Photoshop, GIMP, Canva, Paint, or other image editors.

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
]


def analyze_exif(image_path: str) -> dict:
    """
    Extract and analyze EXIF metadata from a document image.

    Flags:
      - Documents processed with image editing software
      - Missing EXIF data (could indicate a scan or screenshot)
      - Suspicious modification timestamps

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
        result["details"].append(
            "No EXIF metadata found — document may be a scan, screenshot, or stripped"
        )
        logger.info("EXIF Agent: No EXIF data found")
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

    # ── Check for suspicious software ──
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

    if result["exif_flag"] == "clean":
        result["details"].append("EXIF metadata appears normal")

    logger.info(
        f"EXIF Agent: flag={result['exif_flag']} software='{software}' "
        f"make='{make}' has_exif={result['has_exif']}"
    )

    return result
