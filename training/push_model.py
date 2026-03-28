"""
training/push_model.py
-----------------------
Push the trained model.pkl and version.txt to Hugging Face Hub.

Usage:
    HF_TOKEN=your_token HF_REPO_ID=username/ipl-score-predictor python training/push_model.py

Run this after train.py to make the model available to the API.
"""

import os
import sys
import logging
from huggingface_hub import HfApi, create_repo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_TOKEN  = os.environ.get("HF_TOKEN")
HF_REPO_ID = os.environ.get("HF_REPO_ID", "your-username/ipl-score-predictor")


def push():
    if not HF_TOKEN:
        logger.error("HF_TOKEN environment variable not set.")
        sys.exit(1)

    if not os.path.exists("model.pkl"):
        logger.error("model.pkl not found. Run training/train.py first.")
        sys.exit(1)

    api = HfApi()

    # Create repo if it doesn't exist
    try:
        create_repo(repo_id=HF_REPO_ID, repo_type="model", token=HF_TOKEN, exist_ok=True)
        logger.info(f"Repo {HF_REPO_ID} ready.")
    except Exception as e:
        logger.warning(f"Could not create repo (may already exist): {e}")

    # Upload model
    api.upload_file(
        path_or_fileobj="model.pkl",
        path_in_repo="model.pkl",
        repo_id=HF_REPO_ID,
        repo_type="model",
        token=HF_TOKEN,
    )
    logger.info("✅ model.pkl uploaded")

    # Upload version
    if os.path.exists("version.txt"):
        api.upload_file(
            path_or_fileobj="version.txt",
            path_in_repo="version.txt",
            repo_id=HF_REPO_ID,
            repo_type="model",
            token=HF_TOKEN,
        )
        logger.info("✅ version.txt uploaded")

    logger.info(f"🚀 Model live at: https://huggingface.co/{HF_REPO_ID}")


if __name__ == "__main__":
    push()
