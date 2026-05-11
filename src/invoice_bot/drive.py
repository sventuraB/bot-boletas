from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)


@dataclass
class DriveFile:
    file_id: str
    name: str
    mime_type: str


def list_pdfs(credentials: Credentials, folder_id: str) -> list[DriveFile]:
    service = build("drive", "v3", credentials=credentials)

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    files: list[DriveFile] = []
    page_token: str | None = None

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                pageSize=100,
            )
            .execute()
        )

        for f in response.get("files", []):
            files.append(DriveFile(file_id=f["id"], name=f["name"], mime_type=f["mimeType"]))

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    logger.info("Found %d PDF files in folder %s", len(files), folder_id)
    return files


def download_pdf(credentials: Credentials, file_id: str) -> bytes:
    service = build("drive", "v3", credentials=credentials)
    request = service.files().get_media(fileId=file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue()
