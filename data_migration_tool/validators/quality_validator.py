"""Quality checks over the mapped, import-ready frame."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field

import pandas as pd

from ..mappers.schema import MappingConfig
from ..transforms import is_missing, is_valid_email, is_valid_phone, to_iso_date

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


@dataclass
class Issue:
    check: str
    severity: str
    field: str
    row: int | None
    message: str
    recommendation: str


@dataclass
class ValidationReport:
    total_records: int
    issues: list[Issue] = field(default_factory=list)
    checks: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def flagged_rows(self) -> list[int]:
        return sorted({i.row for i in self.issues if i.row is not None})

    @property
    def quality_score(self) -> float:
        """Share of records with no error and no warning, as a percentage."""
        if not self.total_records:
            return 0.0
        clean = self.total_records - len(self.flagged_rows)
        return round(100 * clean / self.total_records, 1)

    def record(self, check: str, failures: int) -> None:
        bucket = self.checks.setdefault(check, {"passed": 0, "failed": 0})
        bucket["failed"] += failures
        bucket["passed"] += max(self.total_records - failures, 0)

    def issues_frame(self) -> pd.DataFrame:
        columns = ["check", "severity", "field", "row", "message", "recommendation"]
        if not self.issues:
            return pd.DataFrame(columns=columns)
        frame = pd.DataFrame([issue.__dict__ for issue in self.issues], columns=columns)
        ordered = frame.assign(_rank=frame["severity"].map(SEVERITY_ORDER))
        return (
            ordered.sort_values(by=["_rank", "row"])
            .drop(columns="_rank")
            .reset_index(drop=True)
        )

    def summary(self) -> dict[str, object]:
        return {
            "total_records": self.total_records,
            "quality_score": self.quality_score,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "records_to_review": len(self.flagged_rows),
            "valid": self.valid,
        }


def _row_numbers(frame: pd.DataFrame) -> dict[Hashable, int]:
    """Map index labels to spreadsheet row numbers (header row plus 1-based)."""
    return {label: position + 2 for position, label in enumerate(frame.index)}


def validate_data(
    frame: pd.DataFrame,
    config: MappingConfig | None = None,
    date_format: str = "%Y-%m-%d",
) -> ValidationReport:
    report = ValidationReport(total_records=len(frame))
    required = set(config.required_fields()) if config else set()
    unique = set(config.unique_fields()) if config else set()
    field_types = {f.name: f for f in config.fields} if config else {}
    row_numbers = _row_numbers(frame)

    for column in frame.columns:
        series = frame[column]
        blanks = series.map(is_missing)
        if column in required:
            for index in series.index[blanks]:
                report.issues.append(
                    Issue(
                        "completeness",
                        "error",
                        column,
                        row_numbers[index],
                        f"Required field '{column}' is empty",
                        "Populate the value in the source system or exclude the record",
                    )
                )
            report.record(f"completeness:{column}", int(blanks.sum()))
        elif blanks.any():
            report.record(f"completeness:{column}", 0)

        target = field_types.get(column)
        transform = target.transform if target else None

        if transform == "email_lowercase" or column.lower().endswith("email"):
            invalid = series.index[~blanks & ~series.map(is_valid_email)]
            for index in invalid:
                report.issues.append(
                    Issue(
                        "validity",
                        "error",
                        column,
                        row_numbers[index],
                        f"'{series[index]}' is not a valid email address",
                        "Correct the address or clear the field before import",
                    )
                )
            report.record(f"validity:{column}", len(invalid))

        if transform == "phone_e164":
            invalid = series.index[~blanks & ~series.map(is_valid_phone)]
            for index in invalid:
                report.issues.append(
                    Issue(
                        "validity",
                        "warning",
                        column,
                        row_numbers[index],
                        f"'{series[index]}' is not a valid phone number",
                        "Check the country code; the CRM may reject the value",
                    )
                )
            report.record(f"validity:{column}", len(invalid))

        if transform == "date_iso":
            normalized = series.map(lambda v: to_iso_date(v, date_format)).astype("string")
            mismatched = series.index[~blanks & (series.astype("string") != normalized)]
            for index in mismatched:
                report.issues.append(
                    Issue(
                        "consistency",
                        "warning",
                        column,
                        row_numbers[index],
                        f"'{series[index]}' is not in {date_format} format",
                        "Re-run the cleaner or fix the source value",
                    )
                )
            report.record(f"consistency:{column}", len(mismatched))

        if column in unique:
            populated = series[~blanks]
            duplicated = populated[populated.duplicated(keep=False)]
            for index, value in duplicated.items():
                report.issues.append(
                    Issue(
                        "uniqueness",
                        "error",
                        column,
                        row_numbers[index],
                        f"Duplicate value '{value}' in unique field '{column}'",
                        "Merge the duplicate records before importing",
                    )
                )
            report.record(f"uniqueness:{column}", len(duplicated))

    return report
