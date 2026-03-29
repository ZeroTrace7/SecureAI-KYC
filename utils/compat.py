"""
SecureAI-KYC — Compatibility Patches & Safe Import Helpers

Fixes known compatibility issues between library versions.
Import and call patch functions BEFORE importing the affected libraries.
"""


def patch_speechbrain():
    """
    Fix speechbrain 1.0.3 + torchaudio 2.11 compatibility.

    SpeechBrain 1.0.3 calls torchaudio.list_audio_backends() which was
    removed in torchaudio 2.11+. This patch adds the missing function.

    Usage:
        from utils.compat import patch_speechbrain
        patch_speechbrain()
        from speechbrain.inference.speaker import SpeakerRecognition
    """
    import torchaudio

    if not hasattr(torchaudio, "list_audio_backends"):
        torchaudio.list_audio_backends = lambda: ["default"]


def get_qr_decoder():
    """
    Returns a QR decoder function that works on the current system.
    Tries pyzbar first, falls back to OpenCV's built-in QR detector.

    Usage:
        from utils.compat import get_qr_decoder
        decode_qr = get_qr_decoder()
        results = decode_qr("path/to/image.jpg")
    """
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as pyzbar_decode

        def decode_with_pyzbar(image_path):
            img = Image.open(image_path)
            results = pyzbar_decode(img)
            return [obj.data.decode("utf-8") for obj in results]

        # Test that it actually works (DLL loads)
        decode_with_pyzbar.__name__ = "pyzbar"
        return decode_with_pyzbar

    except (ImportError, OSError):
        import cv2

        def decode_with_opencv(image_path):
            detector = cv2.QRCodeDetector()
            img = cv2.imread(image_path)
            data, bbox, _ = detector.detectAndDecode(img)
            return [data] if data else []

        decode_with_opencv.__name__ = "opencv"
        return decode_with_opencv


def get_tesseract_ocr():
    """
    Returns a configured pytesseract OCR function.
    Automatically finds Tesseract on common Windows install paths.

    Usage:
        from utils.compat import get_tesseract_ocr
        ocr = get_tesseract_ocr()
        text = ocr("path/to/image.jpg")
    """
    import os
    from pathlib import Path

    import pytesseract

    # Common Windows Tesseract paths
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
            os.getenv("USERNAME", "")
        ),
    ]

    # Try to find Tesseract
    for path in common_paths:
        if Path(path).exists():
            pytesseract.pytesseract.tesseract_cmd = path
            break

    def ocr_extract(image_path, lang="eng+hin"):
        """Extract text from image using Tesseract"""
        from PIL import Image

        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang=lang)

    return ocr_extract


def safe_import(module_name: str, package: str = None):
    """
    Safely import a module, returning None if not available.

    Usage:
        torch = safe_import("torch")
        if torch is not None:
            # use torch
    """
    try:
        import importlib

        return importlib.import_module(module_name, package)
    except ImportError:
        return None


def check_optional_deps() -> dict:
    """
    Check which optional dependencies are available.
    Useful for /api/health endpoint and startup diagnostics.

    Returns:
        dict mapping dependency name to availability status.
    """
    deps = {}

    # Core (should always be present)
    deps["opencv"] = safe_import("cv2") is not None
    deps["pillow"] = safe_import("PIL") is not None
    deps["numpy"] = safe_import("numpy") is not None
    deps["easyocr"] = safe_import("easyocr") is not None
    deps["fuzzywuzzy"] = safe_import("fuzzywuzzy") is not None
    deps["exifread"] = safe_import("exifread") is not None
    deps["fastapi"] = safe_import("fastapi") is not None

    # Optional
    deps["transformers"] = safe_import("transformers") is not None
    deps["torch"] = safe_import("torch") is not None
    deps["speechbrain"] = safe_import("speechbrain") is not None
    deps["pyzbar"] = safe_import("pyzbar") is not None
    deps["pytesseract"] = safe_import("pytesseract") is not None
    deps["google_genai"] = safe_import("google.genai") is not None

    return deps
