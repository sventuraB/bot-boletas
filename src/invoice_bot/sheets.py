from __future__ import annotations

import logging

import gspread
from google.oauth2.service_account import Credentials

from invoice_bot.models import InvoiceData

logger = logging.getLogger(__name__)


def _get_worksheet(
    credentials: Credentials,
    spreadsheet_id: str,
    sheet_name: str,
) -> gspread.Worksheet:
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        logger.info("Created new worksheet '%s'", sheet_name)

    return worksheet


def _ensure_headers(worksheet: gspread.Worksheet) -> None:
    existing = worksheet.row_values(1)
    headers = InvoiceData.headers()
    if existing != headers:
        worksheet.update([headers], "A1")
        logger.info("Headers written to sheet")


def get_processed_files(
    credentials: Credentials,
    spreadsheet_id: str,
    sheet_name: str,
) -> set[str]:
    worksheet = _get_worksheet(credentials, spreadsheet_id, sheet_name)
    _ensure_headers(worksheet)

    all_values = worksheet.col_values(1)
    # Skip header row
    return set(all_values[1:]) if len(all_values) > 1 else set()


def write_results(
    credentials: Credentials,
    spreadsheet_id: str,
    sheet_name: str,
    invoices: list[InvoiceData],
) -> int:
    if not invoices:
        logger.info("No invoices to write")
        return 0

    worksheet = _get_worksheet(credentials, spreadsheet_id, sheet_name)
    _ensure_headers(worksheet)

    rows = [invoice.to_row() for invoice in invoices]
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    logger.info("Wrote %d rows to sheet '%s'", len(rows), sheet_name)
    return len(rows)
