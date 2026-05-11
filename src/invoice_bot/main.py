from __future__ import annotations

import logging
import sys

from invoice_bot.auth import get_credentials
from invoice_bot.config import load_config
from invoice_bot.drive import download_pdf, list_pdfs
from invoice_bot.extractor import extract_text
from invoice_bot.models import InvoiceData
from invoice_bot.parser import parse_invoice
from invoice_bot.sheets import get_processed_files, write_results

logger = logging.getLogger(__name__)


def main(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    credentials = get_credentials(config.google.credentials_path)

    # List PDFs in Drive folder
    pdf_files = list_pdfs(credentials, config.google.drive_folder_id)

    if not pdf_files:
        logger.info("No PDF files found in folder")
        return

    # Check already processed files
    already_processed: set[str] = set()
    if config.processing.skip_already_processed:
        already_processed = get_processed_files(
            credentials,
            config.google.spreadsheet_id,
            config.google.sheet_name,
        )
        logger.info("Already processed: %d files", len(already_processed))

    # Filter out already processed
    pending = [f for f in pdf_files if f.name not in already_processed]
    logger.info("Files to process: %d (of %d total)", len(pending), len(pdf_files))

    if not pending:
        logger.info("Nothing new to process")
        return

    # Process each PDF
    results: list[InvoiceData] = []
    for i, pdf_file in enumerate(pending, 1):
        logger.info("[%d/%d] Processing: %s", i, len(pending), pdf_file.name)

        try:
            pdf_bytes = download_pdf(credentials, pdf_file.file_id)
        except Exception:
            logger.exception("Failed to download '%s'", pdf_file.name)
            results.append(InvoiceData(
                archivo_origen=pdf_file.name,
                procesado_ok=False,
                errores=["Error al descargar"],
            ))
            continue

        text = extract_text(pdf_bytes, pdf_file.name)
        invoice = parse_invoice(text, pdf_file.name)
        results.append(invoice)

        logger.info(
            "  -> %s | %s | %s | Total: %s",
            invoice.tipo_documento or "?",
            invoice.numero_documento or "?",
            invoice.fecha_emision or "?",
            invoice.monto_total or "?",
        )

    # Write to Google Sheets
    written = write_results(
        credentials,
        config.google.spreadsheet_id,
        config.google.sheet_name,
        results,
    )

    # Summary
    ok = sum(1 for r in results if r.procesado_ok)
    with_errors = sum(1 for r in results if r.errores)
    logger.info(
        "Done. Processed: %d | Written: %d | OK: %d | With warnings: %d",
        len(results), written, ok, with_errors,
    )


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    main(config_file)
