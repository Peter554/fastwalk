"""Tests for follow_symlinks parameter."""

from conftest import by_path, create_file

import powerwalk


def test_symlink_not_followed_by_default(tmp_path):
    """Test that symlinks are detected but not followed by default."""
    create_file(tmp_path / "foo/file.txt")
    create_file(tmp_path / "bar/file.txt")
    (tmp_path / "foo/link.txt").symlink_to(tmp_path / "bar/file.txt")

    entries = list(powerwalk.walk(tmp_path / "foo"))
    assert {entry.path for entry in entries} == {
        tmp_path / "foo",
        tmp_path / "foo/file.txt",
        tmp_path / "foo/link.txt",
    }

    entries_by_path = by_path(entries)
    assert not entries_by_path[tmp_path / "foo/link.txt"].is_file
    assert not entries_by_path[tmp_path / "foo/link.txt"].is_dir
    assert entries_by_path[tmp_path / "foo/link.txt"].is_symlink


def test_symlink_behaviour(tmp_path):
    """Test directory symlinks are traversed when follow_symlinks=True."""
    # Create a real directory with contents
    create_file(tmp_path / "real_dir/file1.txt")

    # Create a symlink to that directory
    (tmp_path / "link_to_dir").symlink_to(tmp_path / "real_dir")

    # Without follow_symlinks, the symlink appears but its contents are not traversed
    entries = list(powerwalk.walk(tmp_path, follow_symlinks=False))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "real_dir",
        tmp_path / "real_dir/file1.txt",
        tmp_path / "link_to_dir",
    }

    entries_by_path = by_path(entries)
    assert not entries_by_path[tmp_path / "link_to_dir"].is_file
    assert not entries_by_path[tmp_path / "link_to_dir"].is_dir
    assert entries_by_path[tmp_path / "link_to_dir"].is_symlink

    # With follow_symlinks=True, traverse into the symlinked directory
    entries = list(powerwalk.walk(tmp_path, follow_symlinks=True))
    assert {entry.path for entry in entries} == {
        tmp_path,
        tmp_path / "real_dir",
        tmp_path / "real_dir/file1.txt",
        tmp_path / "link_to_dir",
        tmp_path / "link_to_dir/file1.txt",
    }
