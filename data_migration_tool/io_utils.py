"""Reading client CSVs that are not necessarily UTF-8, comma separated or clean."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import IO

import pandas as pd
from charset_normalizer import from_bytes

MAX_UPLOAD_MB = 200
DETECTION_SAMPLE_BYTES = 256 * 1024
FALLBACK_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")


class SourceFileError(ValueError):
    """The uploaded file cannot be read as a table; the message is client-safe."""


def detect_encoding(raw: bytes) -> str:
    """Best guess at the encoding of ``raw``; falls back to cp1252, never raises.

    Legacy CRM exports are commonly Windows-1252 rather than UTF-8, and cp1252
    decodes any byte sequence, so a wrong guess degrades rather than crashes.
    """
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    best = from_bytes(raw[:DETECTION_SAMPLE_BYTES]).best()
    return best.encoding if best is not None else "cp1252"


def _decode(raw: bytes) -> str:
    for encoding in (detect_encoding(raw), *FALLBACK_ENCODINGS):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("latin-1", errors="replace")


def detect_delimiter(text: str) -> str:
    sample = text[:64 * 1024]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def read_bytes(raw: bytes, filename: str = "upload.csv") -> pd.DataFrame:
    """Parse CSV bytes of unknown encoding and delimiter into an all-string frame."""
    if not raw.strip():
        raise SourceFileError(f"{filename} is empty.")
    text = _decode(raw)
    try:
        frame = pd.read_csv(
            io.StringIO(text),
            dtype=str,
            keep_default_na=False,
            sep=detect_delimiter(text),
            engine="python",
        )
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise SourceFileError(
            f"{filename} could not be read as a CSV table ({error}). "
            "Please export it again as a comma separated CSV."
        ) from error
    if frame.columns.empty:
        raise SourceFileError(f"{filename} has no columns.")
    return frame


def read_source(source: str | Path | IO[bytes], filename: str | None = None) -> pd.DataFrame:
    """Read a CSV from a path or an uploaded file object."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        return read_bytes(path.read_bytes(), path.name)
    raw = source.read()
    name = filename or str(getattr(source, "name", "") or "upload.csv")
    return read_bytes(raw, name)


def exceeds_size_limit(size_bytes: int, limit_mb: int = MAX_UPLOAD_MB) -> bool:
    return size_bytes > limit_mb * 1024 * 1024
