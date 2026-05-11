from __future__ import annotations

import io
import logging

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text(pdf_bytes: bytes, filename: str) -> str:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text)
                else:
                    logger.warning("Page %d of '%s' has no extractable text", i + 1, filename)
            full_text = "\n".join(pages_text)
    except Exception:
        logger.exception("Failed to extract text from '%s'", filename)
        return ""

    if not full_text.strip():
        logger.warning("No text extracted from '%s'", filename)
        return ""

    logger.debug("Extracted %d characters from '%s'", len(full_text), filename)
    return full_text
