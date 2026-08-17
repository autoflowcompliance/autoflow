from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data_migration_tool.branding import Branding
from data_migration_tool.pipeline import run_pipeline


def test_defaults_to_autoflow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRAND_NAME", raising=False)
    assert Branding.load().brand_name == "AutoFlow"


def test_environment_overrides_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAND_NAME", "Northwind Agency")
    monkeypatch.setenv("LOGO_URL", "https://example.com/logo.png")
    branding = Branding.load()
    assert branding.brand_name == "Northwind Agency"
    assert branding.logo_url == "https://example.com/logo.png"


def test_yaml_file_is_read(tmp_path: Path) -> None:
    path = tmp_path / "branding.yaml"
    path.write_text("brand_name: Acme Data\nfooter_note: hello@acme.test\n", encoding="utf-8")
    branding = Branding.load(path)
    assert branding.brand_name == "Acme Data"
    assert branding.footer_note == "hello@acme.test"


def test_report_uses_branding() -> None:
    source = pd.DataFrame({"First Name": ["Ada"], "Email Address": ["ada@example.com"]})
    result = run_pipeline(
        source=source,
        crm="hubspot",
        branding=Branding(brand_name="Northwind", logo_url="https://x.test/l.png"),
        run_structural_check=False,
    )
    assert "Northwind" in result.qa_report_html
    assert "https://x.test/l.png" in result.qa_report_html
    assert "AutoFlow" not in result.qa_report_html
