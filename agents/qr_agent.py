"""
Agent 3 — QR Code Decoder

Decodes QR codes from Aadhaar cards and extracts embedded XML data.
  Primary:  pyzbar (fast, reliable)
  Fallback: OpenCV QRCodeDetector (no extra DLL needed)

Aadhaar QR contains XML with name, DOB, gender, UID (last 4 digits).
"""

import xml.etree.ElementTree as ET
from loguru import logger
from utils.compat import get_qr_decoder


# Get the best available QR decoder
_decode_qr = get_qr_decoder()


def decode_document_qr(image_path: str) -> dict:
    """
    Decode QR code from a document image.

    For Aadhaar cards, parses the embedded XML data.
    For other documents, returns raw QR data.

    Returns:
        dict with: has_qr, qr_name, qr_dob, qr_gender, qr_uid, qr_raw, method
    """
    result = {
        "has_qr": False,
        "qr_name": None,
        "qr_dob": None,
        "qr_gender": None,
        "qr_uid": None,
        "qr_raw": None,
        "method": _decode_qr.__name__,
    }

    try:
        decoded_data = _decode_qr(image_path)
    except Exception as e:
        logger.error(f"QR Agent: Decoding failed — {e}")
        result["error"] = str(e)
        return result

    if not decoded_data:
        logger.info("QR Agent: No QR code found in image")
        return result

    result["has_qr"] = True
    raw_data = decoded_data[0]  # Take first QR code
    result["qr_raw"] = raw_data

    # ── Try to parse as Aadhaar XML ──
    try:
        root = ET.fromstring(raw_data)

        # Aadhaar QR XML format: <PrintLetterBil498 ... name="..." dob="..." gender="..." uid="..." .../>
        # Attributes may vary, try common ones
        attrs = root.attrib

        result["qr_name"] = (
            attrs.get("name")
            or attrs.get("Name")
            or attrs.get("nm")
            or None
        )
        result["qr_dob"] = (
            attrs.get("dob")
            or attrs.get("DOB")
            or attrs.get("db")
            or None
        )
        result["qr_gender"] = (
            attrs.get("gender")
            or attrs.get("Gender")
            or attrs.get("g")
            or None
        )

        uid_raw = (
            attrs.get("uid")
            or attrs.get("UID")
            or attrs.get("Uid")
            or ""
        )
        # Only keep last 4 digits of UID (privacy)
        result["qr_uid"] = uid_raw[-4:] if len(uid_raw) >= 4 else uid_raw

        logger.info(
            f"QR Agent: Aadhaar XML parsed — name='{result['qr_name']}' "
            f"dob='{result['qr_dob']}' uid_last4='{result['qr_uid']}'"
        )

    except ET.ParseError:
        # Not XML — might be a URL or plain text QR
        logger.info(f"QR Agent: QR data is not XML (raw={raw_data[:100]}...)")

    except Exception as e:
        logger.warning(f"QR Agent: XML parsing error — {e}")

    return result
