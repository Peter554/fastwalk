"""Basic functionality tests for powerwalk."""

from conftest import by_path, create_file

import powerwalk


def test_walk_basic(tmp_path):
    """Test that walk returns an iterator of DirEntry objects."""
    # Create some test files and directories
    create_file(tmp_path / "file1.txt")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "subdir/file3.txt")

    # Walk the directory
    entries = list(powerwalk.walk(tmp_path))

    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "file1.txt",
        tmp_path / "file2.txt",
        tmp_path / "subdir",
        tmp_path / "subdir/file3.txt",
    }

    entries_by_path = by_path(entries)

    assert entries_by_path[tmp_path / "file1.txt"].is_file
    assert not entries_by_path[tmp_path / "file1.txt"].is_dir
    assert not entries_by_path[tmp_path / "file1.txt"].is_symlink

    assert not entries_by_path[tmp_path / "subdir"].is_file
    assert entries_by_path[tmp_path / "subdir"].is_dir
    assert not entries_by_path[tmp_path / "subdir"].is_symlink


def test_empty_directory(tmp_path):
    """Test walking an empty directory."""
    entries = list(powerwalk.walk(tmp_path))
    assert {entry.path for entry in entries} == {tmp_path}
