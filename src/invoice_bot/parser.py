from __future__ import annotations

import logging
import re
from datetime import datetime

from invoice_bot.models import InvoiceData

logger = logging.getLogger(__name__)

MONTH_MAP = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

TIPO_DOCUMENTO_PATTERNS = [
    (r"FACTURA\s+ELECTR[OÓ]NICA\s+EXENTA", "FACTURA ELECTRÓNICA EXENTA"),
    (r"FACTURA\s+ELECTR[OÓ]NICA", "FACTURA ELECTRÓNICA"),
    (r"FACTURA\s+EXENTA", "FACTURA EXENTA"),
    (r"FACTURA", "FACTURA"),
    (r"BOLETA\s+ELECTR[OÓ]NICA", "BOLETA ELECTRÓNICA"),
    (r"BOLETA\s+DE\s+HONORARIOS\s+ELECTR[OÓ]NICA", "BOLETA DE HONORARIOS ELECTRÓNICA"),
    (r"BOLETA\s+DE\s+HONORARIOS", "BOLETA DE HONORARIOS"),
    (r"BOLETA", "BOLETA"),
    (r"NOTA\s+DE\s+CR[EÉ]DITO\s+ELECTR[OÓ]NICA", "NOTA DE CRÉDITO ELECTRÓNICA"),
    (r"NOTA\s+DE\s+CR[EÉ]DITO", "NOTA DE CRÉDITO"),
    (r"NOTA\s+DE\s+D[EÉ]BITO", "NOTA DE DÉBITO"),
    (r"GU[IÍ]A\s+DE\s+DESPACHO", "GUÍA DE DESPACHO"),
]

NUMERO_DOCUMENTO_PATTERNS = [
    r"(?:N[°º˚]|Nro\.?|Folio)\s*:?\s*(\d[\d.]*\d|\d+)",
    r"(?:FACTURA|BOLETA|NOTA)[^\n]*?N[°º˚]?\s*:?\s*(\d[\d.]*\d|\d+)",
    r"Documento\s*(?:N[°º˚]?)?\s*:?\s*(\d+)",
]

FECHA_PATTERNS = [
    r"Fecha\s+(?:de\s+)?[Ee]misi[oó]n\s*:?\s*(\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4})",
    r"Fecha\s*:?\s*(\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4})",
    r"(\d{1,2})\s+de\s+(\w+)\s+(?:de\s+)?(\d{4})",
    r"Fecha\s+(?:de\s+)?[Ee]misi[oó]n\s*:?\s*(\d{1,2}\s+de\s+\w+\s+(?:de\s+)?\d{4})",
    r"(\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4})",
]

RUT_PATTERNS = [
    r"R\.?U\.?T\.?\s*:?\s*([\d]{1,2}\.[\d]{3}\.[\d]{3}\s*-\s*[\dkK])",
    r"R\.?U\.?T\.?\s*:?\s*(\d{7,8}\s*-\s*[\dkK])",
    r"([\d]{1,2}\.[\d]{3}\.[\d]{3}\s*-\s*[\dkK])",
]

RAZON_SOCIAL_PATTERNS = [
    r"Raz[oó]n\s+Social\s*:?\s*(.+?)(?:\n|R\.?U\.?T|$)",
    r"Se[ñn]or(?:es|a)?\s*:?\s*(.+?)(?:\n|R\.?U\.?T|$)",
    r"Nombre\s*:?\s*(.+?)(?:\n|R\.?U\.?T|$)",
    r"Emisor\s*:?\s*(.+?)(?:\n|R\.?U\.?T|$)",
]

MONTO_TOTAL_PATTERNS = [
    r"TOTAL\s*\$?\s*([\d.,]+)",
    r"MONTO\s+TOTAL\s*\$?\s*([\d.,]+)",
    r"Total\s+a\s+[Pp]agar\s*:?\s*\$?\s*([\d.,]+)",
    r"VALOR\s+TOTAL\s*\$?\s*([\d.,]+)",
    r"Total\s*:?\s*\$?\s*([\d.,]+)",
]

MONTO_NETO_PATTERNS = [
    r"(?:MONTO\s+)?NETO\s*\$?\s*([\d.,]+)",
    r"Sub\s*[Tt]otal\s*\$?\s*([\d.,]+)",
    r"AFECTO\s*\$?\s*([\d.,]+)",
]

IVA_PATTERNS = [
    r"I\.?V\.?A\.?\s*(?:\(?\s*19\s*%?\s*\)?)?\s*\$?\s*([\d.,]+)",
    r"IMPUESTO\s*\$?\s*([\d.,]+)",
]


def _first_match(text: str, patterns: list[str]) -> re.Match | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def _parse_amount(raw: str) -> int | None:
    cleaned = raw.replace(".", "").replace(",", "").replace("$", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return None


def _parse_date(text: str) -> str | None:
    # "15 de Marzo de 2025" format
    match = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+(?:de\s+)?(\d{4})", text, re.IGNORECASE)
    if match:
        day, month_name, year = match.group(1), match.group(2).lower(), match.group(3)
        month_num = MONTH_MAP.get(month_name)
        if month_num:
            return f"{year}-{month_num:02d}-{int(day):02d}"

    # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    match = re.search(r"(\d{1,2})[\-/\.](\d{1,2})[\-/\.](\d{2,4})", text)
    if match:
        day, month, year = match.group(1), match.group(2), match.group(3)
        if len(year) == 2:
            year = f"20{year}"
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            # Try swapping day/month
            try:
                dt = datetime(int(year), int(day), int(month))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def parse_invoice(text: str, filename: str) -> InvoiceData:
    data = InvoiceData(archivo_origen=filename)

    if not text.strip():
        data.procesado_ok = False
        data.errores.append("Sin texto extraíble")
        return data

    # Tipo de documento
    for pattern, label in TIPO_DOCUMENTO_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            data.tipo_documento = label
            break
    if not data.tipo_documento:
        data.errores.append("tipo_documento no encontrado")

    # Número de documento
    match = _first_match(text, NUMERO_DOCUMENTO_PATTERNS)
    if match:
        data.numero_documento = match.group(1).replace(".", "")
    else:
        data.errores.append("numero_documento no encontrado")

    # Fecha
    for pattern in FECHA_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(0)
            parsed = _parse_date(date_str)
            if parsed:
                data.fecha_emision = parsed
                break
    if not data.fecha_emision:
        data.errores.append("fecha_emision no encontrada")

    # RUT emisor
    match = _first_match(text, RUT_PATTERNS)
    if match:
        data.rut_emisor = match.group(1).replace(" ", "")
    else:
        data.errores.append("rut_emisor no encontrado")

    # Razón social
    match = _first_match(text, RAZON_SOCIAL_PATTERNS)
    if match:
        data.razon_social = match.group(1).strip()
    else:
        data.errores.append("razon_social no encontrada")

    # Monto total
    match = _first_match(text, MONTO_TOTAL_PATTERNS)
    if match:
        data.monto_total = _parse_amount(match.group(1))
    else:
        data.errores.append("monto_total no encontrado")

    # Monto neto
    match = _first_match(text, MONTO_NETO_PATTERNS)
    if match:
        data.monto_neto = _parse_amount(match.group(1))

    # IVA
    match = _first_match(text, IVA_PATTERNS)
    if match:
        data.iva = _parse_amount(match.group(1))

    if data.errores:
        logger.warning("'%s': missing fields: %s", filename, ", ".join(data.errores))

    return data
