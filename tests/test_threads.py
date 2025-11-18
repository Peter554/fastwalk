"""Tests for threads parameter."""

import pytest
from conftest import create_file

import powerwalk


@pytest.mark.parametrize("threads", [0, 1, 4])
def test_threads(tmp_path, threads):
    create_file(tmp_path / "file1.txt")
    create_file(tmp_path / "file2.txt")

    entries = list(powerwalk.walk(tmp_path, threads=threads))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "file1.txt",
        tmp_path / "file2.txt",
    }
