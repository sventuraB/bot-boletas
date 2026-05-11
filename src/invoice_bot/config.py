from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class GoogleConfig:
    credentials_path: str
    drive_folder_id: str
    spreadsheet_id: str
    sheet_name: str


@dataclass
class ProcessingConfig:
    skip_already_processed: bool
    log_level: str


@dataclass
class AppConfig:
    google: GoogleConfig
    processing: ProcessingConfig


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    google_cfg = GoogleConfig(**raw["google"])
    processing_cfg = ProcessingConfig(**raw["processing"])

    logging.basicConfig(
        level=getattr(logging, processing_cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    return AppConfig(google=google_cfg, processing=processing_cfg)
