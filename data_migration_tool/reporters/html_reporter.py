"""Render QA and audit reports as standalone HTML."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..branding import Branding
from ..validators.quality_validator import ValidationReport

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def _table(frame: pd.DataFrame, limit: int = 200) -> str:
    if frame.empty:
        return "<p class='empty'>Nothing to report.</p>"
    html = frame.head(limit).to_html(index=False, border=0, classes="data", escape=True)
    if len(frame) > limit:
        html += f"<p class='empty'>Showing first {limit} of {len(frame)} rows.</p>"
    return html


def render_qa_report(
    report: ValidationReport,
    mapping_log: pd.DataFrame,
    cleaning_log: pd.DataFrame,
    mapped: pd.DataFrame,
    project_name: str,
    source_filename: str,
    crm: str,
    structural: dict[str, Any] | None = None,
    branding: Branding | None = None,
) -> str:
    summary = report.summary()
    flagged = set(report.flagged_rows)
    passing = mapped[[i + 2 not in flagged for i in range(len(mapped))]]
    template = _environment.get_template("report_template.html")
    return template.render(
        project_name=project_name,
        source_filename=source_filename,
        crm=crm,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        branding=branding or Branding.load(),
        summary=summary,
        checks=report.checks,
        issues_table=_table(report.issues_frame()),
        mapping_table=_table(mapping_log),
        cleaning_table=_table(cleaning_log),
        sample_table=_table(passing.head(10)),
        structural=structural or {},
    )


def render_audit_report(
    stats: dict[str, Any],
    mismatches: pd.DataFrame,
    project_name: str,
    branding: Branding | None = None,
) -> str:
    template = _environment.get_template("audit_template.html")
    return template.render(
        project_name=project_name,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        branding=branding or Branding.load(),
        stats=stats,
        mismatch_table=_table(mismatches),
    )
