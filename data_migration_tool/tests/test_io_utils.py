from __future__ import annotations

import io

import pytest

from data_migration_tool.io_utils import (
    SourceFileError,
    detect_delimiter,
    detect_encoding,
    exceeds_size_limit,
    read_bytes,
    read_source,
)

LATIN1 = "name,city\nMüller,Café\n".encode("cp1252")


def test_reads_windows_1252_without_crashing() -> None:
    frame = read_bytes(LATIN1)
    assert frame.loc[0, "name"] == "Müller"
    assert frame.loc[0, "city"] == "Café"


def test_reads_utf8_with_bom() -> None:
    frame = read_bytes("name\nMüller\n".encode("utf-8-sig"))
    assert list(frame.columns) == ["name"]
    assert frame.loc[0, "name"] == "Müller"


def test_detects_bom_encoding() -> None:
    assert detect_encoding("a\n".encode("utf-8-sig")) == "utf-8-sig"


def test_detects_semicolon_delimiter() -> None:
    text = "name;city\nA;B\nC;D\n"
    assert detect_delimiter(text) == ";"
    assert list(read_bytes(text.encode()).columns) == ["name", "city"]


def test_empty_file_raises_client_safe_error() -> None:
    with pytest.raises(SourceFileError):
        read_bytes(b"   \n")


def test_read_source_from_file_object() -> None:
    frame = read_source(io.BytesIO(LATIN1), "contacts.csv")
    assert len(frame) == 1


def test_size_limit() -> None:
    assert exceeds_size_limit(201 * 1024 * 1024)
    assert not exceeds_size_limit(5 * 1024 * 1024)
