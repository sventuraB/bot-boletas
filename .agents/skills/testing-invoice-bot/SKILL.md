---
name: testing-invoice-bot
description: Test the Google Drive invoice bot end-to-end. Use when verifying PDF extraction, parsing, or Sheets writing changes.
---

# Testing the Invoice Bot

## Prerequisites

- `credentials.json` (Google Service Account key) in the repo root — this file is gitignored and must be placed manually
- The Drive folder and Google Sheet must be shared with the Service Account email (check `client_email` in credentials.json)
- PDFs must exist in the configured Drive folder

## Devin Secrets Needed

No Devin-managed secrets required. The Service Account credentials are provided as a JSON file (`credentials.json`) placed in the repo root.

## Environment Setup

```bash
cd /home/ubuntu/repos/google-drive-invoice-bot
uv sync
# Copy credentials.json to repo root if not present
```

## Running the Bot

```bash
uv run python -m invoice_bot
```

## Testing Procedure

### 1. Verify connectivity

Before running the full bot, verify auth and API access independently:

```python
# Check auth
from invoice_bot.auth import get_credentials
from invoice_bot.config import load_config
config = load_config()
creds = get_credentials(config.google.credentials_path)
# Should print: Authenticated as <email>

# Check Drive access
from invoice_bot.drive import list_pdfs
files = list_pdfs(creds, config.google.drive_folder_id)
# Should list PDF files

# Check Sheets access
import gspread
gc = gspread.authorize(creds)
ss = gc.open_by_key(config.google.spreadsheet_id)
print(ss.title, [ws.title for ws in ss.worksheets()])
```

### 2. Full E2E test

Run `uv run python -m invoice_bot` and verify:
- Auth succeeds
- PDFs are found and downloaded
- Text is extracted from each PDF
- Fields are parsed (check log lines for tipo, numero, fecha, total)
- Rows are written to the Google Sheet

### 3. Idempotency test

Run the bot again immediately. It should:
- Log "Already processed: N files"
- Log "Nothing new to process"
- NOT add duplicate rows

### 4. Verify Sheet data

Read the Sheet data directly to verify correctness:

```python
ws = ss.worksheet('Datos')
all_values = ws.get_all_values()
for row in all_values:
    print(row)
```

Check that:
- Headers match the 11 expected columns
- Data rows match the number of PDFs processed
- Montos are integers (no dots/commas)
- Dates are in YYYY-MM-DD format

## Known Parser Limitations

- `razon_social` might not be extracted if the business name doesn't follow standard label patterns (e.g., "Razón Social:", "Señor:"). Some PDFs just list the name without a label.
- `razon_social` regex might capture prefix artifacts like `(es):` from some PDF formats.
- RUT format is not normalized — preserved as-is from the PDF (some with dots, some without).
- IVA might not be extracted from all formats — e.g., "El IVA de esta boleta es $X" is not matched by current patterns. Standard "IVA 19% $X" format works.
- Chilean boleta/factura formats vary significantly by provider. New patterns may need to be added to `parser.py` as new providers are encountered.

## Configuration

- `config.yaml` contains Drive folder ID, Spreadsheet ID, sheet name, and processing options
- `skip_already_processed: true` enables idempotency by checking the Sheet for already-processed filenames
- `log_level: INFO` can be changed to `DEBUG` for more verbose text extraction output
