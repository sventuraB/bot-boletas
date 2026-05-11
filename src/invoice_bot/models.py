from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvoiceData:
    archivo_origen: str
    tipo_documento: str | None = None
    numero_documento: str | None = None
    fecha_emision: str | None = None
    rut_emisor: str | None = None
    razon_social: str | None = None
    monto_neto: int | None = None
    iva: int | None = None
    monto_total: int | None = None
    procesado_ok: bool = True
    errores: list[str] = field(default_factory=list)

    SHEET_HEADERS: list[str] = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "SHEET_HEADERS", [
            "Archivo",
            "Tipo Documento",
            "N° Documento",
            "Fecha Emisión",
            "RUT Emisor",
            "Razón Social",
            "Monto Neto",
            "IVA",
            "Monto Total",
            "Procesado OK",
            "Errores",
        ])

    def to_row(self) -> list[str]:
        return [
            self.archivo_origen,
            self.tipo_documento or "",
            self.numero_documento or "",
            self.fecha_emision or "",
            self.rut_emisor or "",
            self.razon_social or "",
            str(self.monto_neto) if self.monto_neto is not None else "",
            str(self.iva) if self.iva is not None else "",
            str(self.monto_total) if self.monto_total is not None else "",
            "Sí" if self.procesado_ok else "No",
            "; ".join(self.errores) if self.errores else "",
        ]

    @staticmethod
    def headers() -> list[str]:
        return [
            "Archivo",
            "Tipo Documento",
            "N° Documento",
            "Fecha Emisión",
            "RUT Emisor",
            "Razón Social",
            "Monto Neto",
            "IVA",
            "Monto Total",
            "Procesado OK",
            "Errores",
        ]
