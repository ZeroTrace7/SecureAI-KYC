"""
Singleton EasyOCR Reader — shared across all agents.

Prevents multiple 400 MB model loads. Every module that needs OCR
should import `get_reader()` from here instead of creating its own.
"""

from loguru import logger

_reader = None


def get_reader():
    """Return the global EasyOCR reader, creating it on first call."""
    global _reader
    if _reader is None:
        try:
            import easyocr

            _reader = easyocr.Reader(["en", "hi"], gpu=False, verbose=False)
            logger.info("OCR Loader: EasyOCR reader initialized (en+hi, singleton)")
        except ImportError:
            logger.error("OCR Loader: easyocr package not installed")
            return None
        except Exception as e:
            logger.error(f"OCR Loader: EasyOCR init failed — {e}")
            return None
    return _reader
