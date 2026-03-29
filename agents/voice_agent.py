"""
Agent 6 — Voice Verification (100% OPTIONAL)

Compares a user's voice recording against a reference voice embedding.
Uses SpeechBrain ECAPA-TDNN for speaker recognition.

This agent is:
  - DISABLED by default (ENABLE_VOICE=false)
  - Lazy-loaded (models only download when endpoint is called)
  - Fully wrapped in try/except at every level
  - Returns a neutral "skipped" result on ANY failure

If this crashes during a demo, NOTHING else is affected.
"""

from loguru import logger
from config import ENABLE_VOICE


_speaker_model = None


def _get_speaker_model():
    """Lazy-load SpeechBrain speaker recognition model."""
    global _speaker_model
    if _speaker_model is None:
        try:
            # Apply compatibility patch BEFORE importing speechbrain
            from utils.compat import patch_speechbrain
            patch_speechbrain()

            from speechbrain.inference.speaker import SpeakerRecognition
            _speaker_model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
            )
            logger.info("Voice Agent: SpeechBrain model loaded")
        except ImportError as e:
            logger.warning(f"Voice Agent: SpeechBrain not available — {e}")
            return None
        except Exception as e:
            logger.warning(f"Voice Agent: Model load failed — {e}")
            return None
    return _speaker_model


def verify_voice(audio_path: str, reference_path: str) -> dict:
    """
    Compare two voice recordings for speaker verification.

    Args:
        audio_path:     Path to the user's voice recording.
        reference_path: Path to the reference voice recording.

    Returns:
        dict with: voice_match (bool or None), similarity_score, skipped, reason
    """
    result = {
        "voice_match": None,
        "similarity_score": None,
        "skipped": False,
        "reason": None,
    }

    # ── Feature flag ──
    if not ENABLE_VOICE:
        result["skipped"] = True
        result["reason"] = "Voice verification disabled (ENABLE_VOICE=false)"
        logger.info("Voice Agent: Disabled by feature flag")
        return result

    # ── File validation ──
    import os
    if not os.path.exists(audio_path):
        result["skipped"] = True
        result["reason"] = f"Audio file not found: {audio_path}"
        return result

    if not os.path.exists(reference_path):
        result["skipped"] = True
        result["reason"] = f"Reference file not found: {reference_path}"
        return result

    # ── Load model ──
    model = _get_speaker_model()
    if model is None:
        result["skipped"] = True
        result["reason"] = "Voice model not available"
        return result

    # ── Run verification ──
    try:
        score, prediction = model.verify_files(audio_path, reference_path)
        result["voice_match"] = bool(prediction.item())
        result["similarity_score"] = round(float(score.item()), 4)

        logger.info(
            f"Voice Agent: match={result['voice_match']} "
            f"score={result['similarity_score']}"
        )

    except Exception as e:
        result["skipped"] = True
        result["reason"] = f"Voice verification failed: {e}"
        logger.error(f"Voice Agent: Inference error — {e}")

    return result
