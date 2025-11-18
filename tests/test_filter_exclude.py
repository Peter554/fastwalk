"""Tests for filter parameter behavior."""

from conftest import create_file

import powerwalk


def test_filter_single_pattern(tmp_path):
    """Test filter parameter with a single string."""
    create_file(tmp_path / "file1.py")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "file3.py")
    create_file(tmp_path / "file4.md")

    entries = list(powerwalk.walk(tmp_path, filter="*.py"))
    assert {entry.path for entry in entries} == {
        tmp_path / "file1.py",
        tmp_path / "file3.py",
    }


def test_filter_multiple_patterns(tmp_path):
    """Test filter parameter with a collection of strings."""
    create_file(tmp_path / "file1.py")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "file3.py")
    create_file(tmp_path / "file4.md")

    entries = list(powerwalk.walk(tmp_path, filter=["*.py", "*.md"]))
    assert {entry.path for entry in entries} == {
        tmp_path / "file1.py",
        tmp_path / "file3.py",
        tmp_path / "file4.md",
    }


def test_filter_globstar(tmp_path):
    """Test that filter patterns respect literal separators.

    Without **, patterns should only match in the immediate directory.
    """
    create_file(tmp_path / "root.py")
    create_file(tmp_path / "root.txt")
    create_file(tmp_path / "subdir/nested.py")
    create_file(tmp_path / "subdir/nested.txt")

    # *.py should only match root-level .py files
    entries = list(powerwalk.walk(tmp_path, filter="*.py"))
    assert {entry.path for entry in entries} == {
        tmp_path / "root.py",
    }

    # **/*.py should match .py files at any depth
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py"))
    assert {entry.path for entry in entries} == {
        tmp_path / "root.py",
        tmp_path / "subdir/nested.py",
    }


def test_empty_filter(tmp_path):
    """Test that empty filter returns all files."""
    create_file(tmp_path / "file1.py")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "file3.md")

    entries = list(powerwalk.walk(tmp_path, filter=[]))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "file1.py",
        tmp_path / "file2.txt",
        tmp_path / "file3.md",
    }


def test_exclude_single_pattern(tmp_path):
    """Test exclude parameter with a single glob pattern."""
    create_file(tmp_path / "include/file1.txt")
    create_file(tmp_path / "exclude/file2.txt")

    entries = list(powerwalk.walk(tmp_path, exclude="**/exclude"))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "include",
        tmp_path / "include/file1.txt",
    }


def test_exclude_multiple_patterns(tmp_path):
    """Test exclude parameter with multiple glob patterns."""
    create_file(tmp_path / "keep/file.txt")
    create_file(tmp_path / "skip1/file.txt")
    create_file(tmp_path / "skip2/file.txt")

    entries = list(powerwalk.walk(tmp_path, exclude=["**/skip1", "**/skip2"]))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "keep",
        tmp_path / "keep/file.txt",
    }


def test_exclude_globstar(tmp_path):
    """Test that exclude patterns respect literal separators.

    Without **, patterns should only exclude in the immediate directory.
    """
    create_file(tmp_path / "keep.txt")
    create_file(tmp_path / "skip.txt")
    create_file(tmp_path / "subdir/keep.txt")
    create_file(tmp_path / "subdir/skip.txt")

    # skip.txt should only exclude root-level skip.txt
    entries = list(powerwalk.walk(tmp_path, exclude="skip.txt"))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "keep.txt",
        tmp_path / "subdir",
        tmp_path / "subdir/keep.txt",
        tmp_path / "subdir/skip.txt",
    }

    # **/skip.txt should exclude skip.txt at any depth
    entries = list(powerwalk.walk(tmp_path, exclude="**/skip.txt"))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "keep.txt",
        tmp_path / "subdir",
        tmp_path / "subdir/keep.txt",
    }


def test_empty_exclude(tmp_path):
    """Test that empty exclude doesn't exclude anything."""
    create_file(tmp_path / "file1.txt")
    create_file(tmp_path / "file2.txt")

    entries = list(powerwalk.walk(tmp_path, exclude=[]))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "file1.txt",
        tmp_path / "file2.txt",
    }


def test_combined_filter_and_exclude(tmp_path):
    """Test using filter and exclude together."""
    create_file(tmp_path / "include/file.py")
    create_file(tmp_path / "include/file.txt")
    create_file(tmp_path / "exclude/file.py")
    create_file(tmp_path / "exclude/file.txt")

    # Use **/*.py to match all .py files, exclude the exclude directory
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py", exclude="**/exclude"))
    assert {entry.path for entry in entries} == {tmp_path / "include/file.py"}
