from __future__ import annotations

import logging
from pathlib import Path

from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials(credentials_path: str) -> Credentials:
    path = Path(credentials_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_path}. "
            "Download the Service Account JSON key from Google Cloud Console."
        )

    creds = Credentials.from_service_account_file(str(path), scopes=SCOPES)
    logger.info("Authenticated as %s", creds.service_account_email)
    return creds
