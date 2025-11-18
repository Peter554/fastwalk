"""Tests for max_filesize parameter."""

from conftest import create_file

import powerwalk


def test_max_filesize_basic(tmp_path):
    """Test max_filesize parameter."""
    create_file(tmp_path / "small.txt", "x" * 10)
    create_file(tmp_path / "medium.txt", "x" * 100)
    create_file(tmp_path / "large.txt", "x" * 1000)

    entries = list(powerwalk.walk(tmp_path, max_filesize=150))
    assert {entry.path for entry in entries if entry.is_file} == {
        tmp_path / "small.txt",
        tmp_path / "medium.txt",
    }
