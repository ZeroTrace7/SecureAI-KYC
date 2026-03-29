import os
import sys

def cache_huggingface_models():
    """Download only the essential HF models (optimized: ~350 MB total)."""
    try:
        from huggingface_hub import snapshot_download
        models = [
            # ── Required (350 MB) ──
            "dima806/deepfake_vs_real_image_detection",

            # ── Optional (uncomment if needed) ──
            # "kumaran-0188/image_forgery_detector",     # +90 MB — ML forgery (redundant with ELA)
            # "speechbrain/spkrec-ecapa-voxceleb",       # +80 MB — Voice verification
        ]
        print("\n=== Caching Hugging Face Models (Optimized) ===")
        print(f"Models to download: {len(models)}")
        for model_id in models:
            print(f"Downloading/Verifying {model_id}...")
            snapshot_download(
                repo_id=model_id, 
                resume_download=True, 
                allow_patterns=["*.bin", "*.safetensors", "*.json", "*.txt", "*.model", "*.h5", "*.md"]
            )
            print(f"✅ {model_id} is cached locally.")
    except ImportError:
        print("❌ huggingface_hub not installed. Run 'pip install transformers huggingface_hub'.")
    except Exception as e:
        print(f"❌ HF model caching encountered an error: {e}")

def cache_easyocr_models():
    """Download EasyOCR language models (English + Hindi, ~40 MB)."""
    try:
        import easyocr
        print("\n=== Caching EasyOCR Text Models ===")
        print("Initializing EasyOCR reader (this forces EN/HI model download)...")
        _ = easyocr.Reader(['en', 'hi'], gpu=False)
        print("✅ EasyOCR models for English and Hindi are cached.")
    except ImportError:
        print("❌ easyocr not installed. Run 'pip install easyocr'.")
    except Exception as e:
        print(f"❌ EasyOCR model caching encountered an error: {e}")

def main():
    print("🚀 SECUREAI-KYC 🚀 — Optimized AI Model Caching\n")
    print("This script precaches required AI weight files.")
    print("Estimated download: ~400 MB (down from ~4 GB)\n")
    print("Removed models (no longer needed):")
    print("  ❌ microsoft/dit-base-finetuned-rvlcdip (340 MB) → rule-based classifier")
    print("  ❌ microsoft/trocr-base-printed (650 MB) → EasyOCR")
    print("  ❌ microsoft/trocr-base-handwritten (650 MB) → EasyOCR")
    print("  ❌ microsoft/layoutlmv3-base (500 MB) → not needed")
    print("  ❌ prithivMLmods/Deep-Fake-Detector-v2-Model (350 MB) → 1 model only")
    print("  ❌ google/flan-t5-base (990 MB) → Gemini API + template\n")

    cache_easyocr_models()
    cache_huggingface_models()

    print("\n🎉 Model caching complete!")
    print("📊 Total estimated: ~400 MB (91% reduction from original ~4 GB)")

if __name__ == "__main__":
    main()
