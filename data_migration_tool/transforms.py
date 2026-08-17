"""Value level transforms shared by the cleaner, the mapper and the validator."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import phonenumbers
from dateutil import parser as date_parser

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
SCIENTIFIC_PATTERN = re.compile(r"^[+-]?\d+(\.\d+)?[eE][+-]?\d+$")
DEFAULT_MISSING_TOKENS = frozenset(
    {"", "-", "n/a", "na", "null", "none", "nan", "#n/a", "unknown"}
)


def is_missing(value: Any, tokens: frozenset[str] = DEFAULT_MISSING_TOKENS) -> bool:
    if value is None or value is pd.NaT:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str):
        return value.strip().lower() in tokens
    return False


def trim_whitespace(value: Any, collapse_internal: bool = True) -> Any:
    if not isinstance(value, str):
        return value
    trimmed = value.strip()
    if collapse_internal:
        trimmed = re.sub(r"\s+", " ", trimmed)
    return trimmed


def email_lowercase(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value.strip().lower()


def normalize_unicode(value: Any) -> Any:
    """Fold accented characters down to their closest ASCII equivalent."""
    if not isinstance(value, str):
        return value
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def phone_e164(value: Any, region: str = "US") -> Any:
    """Return the phone number in E.164 form, or the original value if unparseable."""
    if is_missing(value):
        return value
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    try:
        parsed = phonenumbers.parse(text, None if text.startswith("+") else region)
    except phonenumbers.NumberParseException:
        return text
    if not phonenumbers.is_possible_number(parsed):
        return text
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def is_valid_phone(value: Any, region: str = "US") -> bool:
    if is_missing(value):
        return False
    try:
        parsed = phonenumbers.parse(
            str(value).strip(), None if str(value).startswith("+") else region
        )
    except phonenumbers.NumberParseException:
        return False
    return phonenumbers.is_valid_number(parsed)


def is_valid_email(value: Any) -> bool:
    if is_missing(value):
        return False
    return bool(EMAIL_PATTERN.match(str(value).strip()))


def to_iso_date(value: Any, output_format: str = "%Y-%m-%d") -> Any:
    """Parse a heterogeneous date value into a single output format.

    Ambiguous numeric dates are read day-first only when the first component
    cannot be a month, which keeps ``12/31/24`` and ``31/12/24`` consistent.
    """
    if is_missing(value):
        return value
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.strftime(output_format)
    text = str(value).strip()
    leading = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", text)
    dayfirst = leading is not None and int(leading.group(1)) > 12
    try:
        parsed = date_parser.parse(text, dayfirst=dayfirst)
    except (ValueError, OverflowError):
        return text
    return parsed.strftime(output_format)


def expand_scientific_notation(value: Any) -> Any:
    """Undo Excel's ``4.05E+14`` mangling of long numeric identifiers."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not SCIENTIFIC_PATTERN.match(text):
        return value
    try:
        expanded = Decimal(text)
    except InvalidOperation:
        return value
    return format(expanded.normalize(), "f")


def title_case(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value.title()


def upper_case(value: Any) -> Any:
    return value.upper() if isinstance(value, str) else value


def lower_case(value: Any) -> Any:
    return value.lower() if isinstance(value, str) else value


def digits_only(value: Any) -> Any:
    if is_missing(value):
        return value
    return re.sub(r"\D", "", str(value))


TRANSFORMS: dict[str, Callable[[Any], Any]] = {
    "phone_e164": phone_e164,
    "email_lowercase": email_lowercase,
    "date_iso": to_iso_date,
    "trim": trim_whitespace,
    "title_case": title_case,
    "upper_case": upper_case,
    "lower_case": lower_case,
    "digits_only": digits_only,
    "ascii": normalize_unicode,
    "expand_scientific_notation": expand_scientific_notation,
}


def get_transform(name: str) -> Callable[[Any], Any]:
    try:
        return TRANSFORMS[name]
    except KeyError:
        raise ValueError(
            f"Unknown transform '{name}'. Available: {', '.join(sorted(TRANSFORMS))}"
        ) from None
