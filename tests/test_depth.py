"""Tests for min_depth and max_depth parameters."""

from conftest import create_file

import powerwalk


def test_max_depth(tmp_path):
    """Test max_depth parameter."""
    create_file(tmp_path / "a.txt")
    create_file(tmp_path / "a/b.txt")
    create_file(tmp_path / "a/b/c.txt")
    create_file(tmp_path / "a/b/c/d.txt")

    entries = list(powerwalk.walk(tmp_path, max_depth=2))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "a.txt",
        tmp_path / "a",
        tmp_path / "a/b.txt",
        tmp_path / "a/b",
    }


def test_min_depth(tmp_path):
    """Test min_depth parameter."""
    create_file(tmp_path / "a.txt")
    create_file(tmp_path / "a/b.txt")
    create_file(tmp_path / "a/b/c.txt")
    create_file(tmp_path / "a/b/c/d.txt")

    entries = list(powerwalk.walk(tmp_path, min_depth=2))
    assert {entry.path for entry in entries} == {
        tmp_path / "a/b.txt",
        tmp_path / "a/b",
        tmp_path / "a/b/c.txt",
        tmp_path / "a/b/c",
        tmp_path / "a/b/c/d.txt",
    }


def test_min_and_max_depth_combined(tmp_path):
    """Test using min_depth and max_depth together."""
    create_file(tmp_path / "a.txt")
    create_file(tmp_path / "a/b.txt")
    create_file(tmp_path / "a/b/c.txt")
    create_file(tmp_path / "a/b/c/d.txt")

    entries = list(powerwalk.walk(tmp_path, min_depth=2, max_depth=3))
    assert {entry.path for entry in entries} == {
        tmp_path / "a/b.txt",
        tmp_path / "a/b",
        tmp_path / "a/b/c.txt",
        tmp_path / "a/b/c",
    }
