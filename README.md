# Google Drive Invoice Bot

Bot en Python que extrae datos de boletas y facturas (PDF) desde Google Drive y los escribe en Google Sheets.

## Funcionalidades

- Autenticación con Google APIs via Service Account
- Lectura de PDFs desde una carpeta de Google Drive
- Extracción de texto con `pdfplumber`
- Parsing de campos: tipo documento, número, fecha, RUT emisor, razón social, montos
- Escritura automática en Google Sheets (una fila por documento)
- Detección de archivos ya procesados para evitar duplicados

## Pre-requisitos

1. **Python 3.11+** y [`uv`](https://docs.astral.sh/uv/)
2. **Google Cloud Project** con las APIs habilitadas:
   - Google Drive API
   - Google Sheets API
3. **Service Account** con JSON key descargado como `credentials.json`
4. **Carpeta de Drive** y **Google Sheet** compartidos con el email de la Service Account

## Instalación

```bash
uv sync
```

## Configuración

Editar `config.yaml` con los IDs correspondientes:

```yaml
google:
  credentials_path: "credentials.json"
  drive_folder_id: "TU_FOLDER_ID"
  spreadsheet_id: "TU_SPREADSHEET_ID"
  sheet_name: "Datos"

processing:
  skip_already_processed: true
  log_level: "INFO"
```

## Uso

```bash
uv run python -m invoice_bot
```

O con un archivo de configuración específico:

```bash
uv run python -m invoice_bot config.yaml
```

## Campos Extraídos

| Campo | Descripción |
|---|---|
| Tipo Documento | Factura, Boleta, Nota de Crédito, etc. |
| N° Documento | Número de folio |
| Fecha Emisión | Fecha en formato YYYY-MM-DD |
| RUT Emisor | RUT del proveedor |
| Razón Social | Nombre del proveedor |
| Monto Neto | Monto sin IVA |
| IVA | Impuesto |
| Monto Total | Total con IVA |
