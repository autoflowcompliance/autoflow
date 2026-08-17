"""White-label branding for the generated reports."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

BRANDING_FILE = Path(__file__).resolve().parent / "branding.yaml"


@dataclass
class Branding:
    brand_name: str = "AutoFlow"
    logo_url: str = ""
    footer_note: str = ""
    accent_colour: str = "#111827"

    @classmethod
    def load(cls, path: str | Path | None = None) -> Branding:
        """Load branding from a YAML file, then let environment variables win.

        Precedence: ``BRAND_NAME``/``LOGO_URL``/``BRAND_FOOTER_NOTE``/``BRAND_ACCENT_COLOUR``
        environment variables, then the YAML file, then the defaults.
        """
        source = Path(path) if path else BRANDING_FILE
        values: dict[str, str] = {}
        if source.exists():
            loaded = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
            values.update({k: str(v) for k, v in loaded.items() if k in cls.__dataclass_fields__})
        for field_name, variable in (
            ("brand_name", "BRAND_NAME"),
            ("logo_url", "LOGO_URL"),
            ("footer_note", "BRAND_FOOTER_NOTE"),
            ("accent_colour", "BRAND_ACCENT_COLOUR"),
        ):
            override = os.environ.get(variable)
            if override:
                values[field_name] = override
        return cls(**values)
