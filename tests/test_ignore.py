"""Tests for ignore-related parameters (hidden files, gitignore, etc.)."""

from conftest import create_file

import powerwalk


def test_ignore_hidden_default(tmp_path):
    """Test that hidden files are ignored by default."""
    create_file(tmp_path / "visible.txt")
    create_file(tmp_path / ".hidden.txt")
    create_file(tmp_path / "subdir/file.txt")
    create_file(tmp_path / ".hidden_dir/file.txt")

    # With ignore_hidden=True (default)
    entries = list(powerwalk.walk(tmp_path))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "visible.txt",
        tmp_path / "subdir",
        tmp_path / "subdir/file.txt",
    }


def test_ignore_hidden_false(tmp_path):
    """Test that hidden files are included when ignore_hidden=False."""
    create_file(tmp_path / "visible.txt")
    create_file(tmp_path / ".hidden.txt")
    create_file(tmp_path / "subdir/file.txt")
    create_file(tmp_path / ".hidden_dir/file.txt")

    # With ignore_hidden=False
    entries = list(powerwalk.walk(tmp_path, ignore_hidden=False))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "visible.txt",
        tmp_path / ".hidden.txt",
        tmp_path / "subdir",
        tmp_path / "subdir/file.txt",
        tmp_path / ".hidden_dir",
        tmp_path / ".hidden_dir/file.txt",
    }


def test_respect_git_ignore_default(tmp_path):
    """Test that .gitignore is respected by default."""
    create_file(tmp_path / ".gitignore", "ignored.txt\nignored_dir/\n")
    create_file(tmp_path / "kept.txt")
    create_file(tmp_path / "ignored.txt")
    create_file(tmp_path / "ignored_dir/file.txt")

    # With respect_git_ignore=True (default) - note: ignore_hidden=True so .gitignore won't appear
    entries = list(powerwalk.walk(tmp_path))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "kept.txt",
    }


def test_respect_git_ignore_false(tmp_path):
    """Test that .gitignore can be disabled."""
    create_file(tmp_path / ".gitignore", "ignored.txt\nignored_dir/\n")
    create_file(tmp_path / "kept.txt")
    create_file(tmp_path / "ignored.txt")
    create_file(tmp_path / "ignored_dir/file.txt")

    # With respect_git_ignore=False - ignored files should now appear (but not .gitignore as it's hidden)
    entries = list(powerwalk.walk(tmp_path, respect_git_ignore=False))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "kept.txt",
        tmp_path / "ignored.txt",
        tmp_path / "ignored_dir",
        tmp_path / "ignored_dir/file.txt",
    }


def test_respect_ignore_file(tmp_path):
    """Test that .ignore files are respected by default."""
    create_file(tmp_path / ".ignore", "*.log\ntemp/\n")
    create_file(tmp_path / "file.txt")
    create_file(tmp_path / "debug.log")
    create_file(tmp_path / "temp/data.txt")

    # With respect_ignore=True (default)
    entries = list(powerwalk.walk(tmp_path))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "file.txt",
    }


def test_respect_ignore_false(tmp_path):
    """Test that .ignore files can be disabled."""
    create_file(tmp_path / ".ignore", "*.log\ntemp/\n")
    create_file(tmp_path / "file.txt")
    create_file(tmp_path / "debug.log")
    create_file(tmp_path / "temp/data.txt")

    # With respect_ignore=False
    entries = list(powerwalk.walk(tmp_path, respect_ignore=False))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "file.txt",
        tmp_path / "debug.log",
        tmp_path / "temp",
        tmp_path / "temp/data.txt",
    }
