import os
import sys
import urllib.request


def download_file(url, target_path):
    print(f"Downloading {os.path.basename(target_path)}...")
    print(f"URL: {url}")
    try:
        urllib.request.urlretrieve(url, target_path)
        print(f"✅ Successfully downloaded to {target_path}")
    except Exception as e:
        print(f"❌ Failed to download: {e}")


def main():
    tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools"))
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)

    print(f"Saving tools to: {tools_dir}\n")

    # 1. Tesseract OCR Installer (Windows 64-bit)
    tesseract_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
    tesseract_dest = os.path.join(tools_dir, "tesseract-ocr-w64-setup.exe")
    if not os.path.exists(tesseract_dest):
        download_file(tesseract_url, tesseract_dest)
    else:
        print("✅ Tesseract installer already present.")

    # 2. Visual C++ 2013 Redistributable (needed for pyzbar)
    vcredist_url = "https://aka.ms/highdpimfc2013x64enu"
    vcredist_dest = os.path.join(tools_dir, "vcredist_x64_2013.exe")
    if not os.path.exists(vcredist_dest):
        download_file(vcredist_url, vcredist_dest)
    else:
        print("✅ VC++ 2013 Redistributable installer already present.")

    print("\n🎉 Tool downloads complete. You can find them in the 'tools/' folder.")


if __name__ == "__main__":
    main()
