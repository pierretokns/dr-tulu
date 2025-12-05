#!/usr/bin/env python3
"""
Download the DR-Tulu-8B model from HuggingFace.
"""

import os
from huggingface_hub import snapshot_download

def download_dr_tulu():
    """Download DR-Tulu-8B model from HuggingFace."""

    print("🔄 Downloading DR-Tulu-8B model...")
    print("=" * 50)

    # Create models directory
    models_dir = "./models/DR-Tulu-8B"
    os.makedirs(models_dir, exist_ok=True)

    try:
        print(f"📂 Downloading to: {os.path.abspath(models_dir)}")

        # Download the model
        snapshot_download(
            repo_id="rl-research/DR-Tulu-8B",
            local_dir=models_dir,
            repo_type="model"
        )

        print(f"✅ Successfully downloaded DR-Tulu-8B to {models_dir}")

        # List downloaded files
        print("\n📄 Downloaded files:")
        for file in os.listdir(models_dir):
            file_path = os.path.join(models_dir, file)
            if os.path.isfile(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  - {file} ({size_mb:.1f} MB)")

        return True

    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

if __name__ == "__main__":
    success = download_dr_tulu()
    if success:
        print("\n🎉 DR-Tulu-8B is ready to use!")
        print("Now you can update the configuration to use the real DR-Tulu model.")
    else:
        print("\n⚠️ Download failed. Please check your internet connection and try again.")