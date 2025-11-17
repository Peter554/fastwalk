import errno
from pathlib import Path

import powerwalk
import pytest


def create_file(path, content=""):
    """Helper to create a file, creating parent directories if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_walk_basic(tmp_path):
    """Test that walk returns an iterator of DirEntry objects."""
    # Create some test files and directories
    create_file(tmp_path / "file1.txt")
    create_file(tmp_path / "file2.txt")
    (tmp_path / "subdir").mkdir()
    create_file(tmp_path / "subdir" / "file3.txt")

    # Walk the directory - use ignore_errors() for backward compatibility
    entries = list(powerwalk.walk(tmp_path))
    paths = {entry.path_str for entry in entries}

    # Check that all expected paths are present
    assert str(tmp_path / "file1.txt") in paths
    assert str(tmp_path / "file2.txt") in paths
    assert str(tmp_path / "subdir") in paths
    assert str(tmp_path / "subdir" / "file3.txt") in paths

    # Check entry properties
    for entry in entries:
        if entry.path_str.endswith("file1.txt"):
            assert entry.is_file
            assert not entry.is_dir
            assert not entry.is_symlink
        elif entry.path_str.endswith("subdir"):
            assert not entry.is_file
            assert entry.is_dir
            assert not entry.is_symlink


def test_filter_single_string(tmp_path):
    """Test filter parameter with a single string (new feature)."""
    create_file(tmp_path / "file1.py")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "file3.py")
    create_file(tmp_path / "file4.md")

    entries = list(powerwalk.walk(tmp_path, filter="*.py"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "file1.py") in paths
    assert str(tmp_path / "file3.py") in paths
    assert str(tmp_path / "file2.txt") not in paths
    assert str(tmp_path / "file4.md") not in paths


def test_filter_collection(tmp_path):
    """Test filter parameter with a collection of strings."""
    create_file(tmp_path / "file1.py")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "file3.py")
    create_file(tmp_path / "file4.md")

    entries = list(powerwalk.walk(tmp_path, filter=["*.py", "*.md"]))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "file1.py") in paths
    assert str(tmp_path / "file3.py") in paths
    assert str(tmp_path / "file4.md") in paths
    assert str(tmp_path / "file2.txt") not in paths


def test_filter_nested_directories(tmp_path):
    """Test that filter work in nested directories with ** pattern."""
    create_file(tmp_path / "root.py")
    create_file(tmp_path / "root.txt")
    create_file(tmp_path / "level1/file1.py")
    create_file(tmp_path / "level1/file1.txt")
    create_file(tmp_path / "level1/level2/file2.py")
    create_file(tmp_path / "level1/level2/file2.txt")

    # Use **/*.py to match files at any depth
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "root.py") in paths
    assert str(tmp_path / "level1/file1.py") in paths
    assert str(tmp_path / "level1/level2/file2.py") in paths
    assert str(tmp_path / "root.txt") not in paths
    assert str(tmp_path / "level1/file1.txt") not in paths


def test_exclude_single_pattern(tmp_path):
    """Test exclude parameter with a single glob pattern."""
    create_file(tmp_path / "include/file1.txt")
    create_file(tmp_path / "exclude/file2.txt")

    entries = list(powerwalk.walk(tmp_path, exclude="**/exclude"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "include") in paths
    assert str(tmp_path / "include/file1.txt") in paths
    assert str(tmp_path / "exclude") not in paths
    assert str(tmp_path / "exclude/file2.txt") not in paths


def test_exclude_multiple_patterns(tmp_path):
    """Test exclude parameter with multiple glob patterns."""
    create_file(tmp_path / "keep/file.txt")
    create_file(tmp_path / "skip1/file.txt")
    create_file(tmp_path / "skip2/file.txt")

    entries = list(powerwalk.walk(tmp_path, exclude=["**/skip1", "**/skip2"]))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "keep") in paths
    assert str(tmp_path / "keep/file.txt") in paths
    assert str(tmp_path / "skip1") not in paths
    assert str(tmp_path / "skip2") not in paths


def test_max_depth(tmp_path):
    """Test max_depth parameter."""
    create_file(tmp_path / "level0.txt")
    create_file(tmp_path / "level1/level1.txt")
    create_file(tmp_path / "level1/level2/level2.txt")
    create_file(tmp_path / "level1/level2/level3/level3.txt")

    entries = list(powerwalk.walk(tmp_path, max_depth=2))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "level0.txt") in paths
    assert str(tmp_path / "level1") in paths
    assert str(tmp_path / "level1/level1.txt") in paths
    assert str(tmp_path / "level1/level2") in paths
    assert str(tmp_path / "level1/level2/level2.txt") not in paths
    assert str(tmp_path / "level1/level2/level3") not in paths


def test_min_depth(tmp_path):
    """Test min_depth parameter.

    Depth counting: root=0, items in root=1, one level down=2, etc.
    """
    create_file(tmp_path / "level0.txt")
    create_file(tmp_path / "level1/level1.txt")
    create_file(tmp_path / "level1/level2/level2.txt")

    entries = list(powerwalk.walk(tmp_path, min_depth=2))
    paths = {entry.path_str for entry in entries}

    # Depth 1: should not be included
    assert str(tmp_path / "level0.txt") not in paths
    assert str(tmp_path / "level1") not in paths
    # Depth 2: should be included
    assert str(tmp_path / "level1/level1.txt") in paths
    assert str(tmp_path / "level1/level2") in paths
    # Depth 3: should be included
    assert str(tmp_path / "level1/level2/level2.txt") in paths


def test_ignore_hidden(tmp_path):
    """Test ignore_hidden parameter."""
    create_file(tmp_path / "visible.txt")
    create_file(tmp_path / ".hidden.txt")
    create_file(tmp_path / "subdir/file.txt")
    create_file(tmp_path / ".hidden_dir/file.txt")

    # With ignore_hidden=True (default)
    entries = list(powerwalk.walk(tmp_path, ignore_hidden=True))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "visible.txt") in paths
    assert str(tmp_path / "subdir") in paths
    assert str(tmp_path / ".hidden.txt") not in paths
    assert str(tmp_path / ".hidden_dir") not in paths

    # With ignore_hidden=False
    entries = list(powerwalk.walk(tmp_path, ignore_hidden=False))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "visible.txt") in paths
    assert str(tmp_path / ".hidden.txt") in paths
    assert str(tmp_path / ".hidden_dir") in paths
    assert str(tmp_path / ".hidden_dir/file.txt") in paths


def test_gitignore_respected(tmp_path):
    """Test that .gitignore is respected by default."""
    create_file(tmp_path / ".gitignore", "ignored.txt\nignored_dir/\n")
    create_file(tmp_path / "kept.txt")
    create_file(tmp_path / "ignored.txt")
    create_file(tmp_path / "ignored_dir/file.txt")

    # With respect_git_ignore=True (default) - note: ignore_hidden=True so .gitignore won't appear
    entries = list(powerwalk.walk(tmp_path, respect_git_ignore=True))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "kept.txt") in paths
    assert str(tmp_path / "ignored.txt") not in paths
    assert str(tmp_path / "ignored_dir") not in paths

    # With respect_git_ignore=False - ignored files should now appear (but not .gitignore as it's hidden)
    entries = list(powerwalk.walk(tmp_path, respect_git_ignore=False))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "kept.txt") in paths
    assert str(tmp_path / "ignored.txt") in paths
    assert str(tmp_path / "ignored_dir") in paths


def test_max_filesize(tmp_path):
    """Test max_filesize parameter."""
    create_file(tmp_path / "small.txt", "x" * 10)
    create_file(tmp_path / "medium.txt", "x" * 100)
    create_file(tmp_path / "large.txt", "x" * 1000)

    entries = list(powerwalk.walk(tmp_path, max_filesize=150))
    file_paths = {entry.path_str for entry in entries if entry.is_file}

    assert str(tmp_path / "small.txt") in file_paths
    assert str(tmp_path / "medium.txt") in file_paths
    assert str(tmp_path / "large.txt") not in file_paths


def test_empty_filters(tmp_path):
    """Test that empty filter returns all files."""
    create_file(tmp_path / "file1.py")
    create_file(tmp_path / "file2.txt")
    create_file(tmp_path / "file3.md")

    entries = list(powerwalk.walk(tmp_path, filter=[]))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "file1.py") in paths
    assert str(tmp_path / "file2.txt") in paths
    assert str(tmp_path / "file3.md") in paths


def test_empty_ignore_dirs(tmp_path):
    """Test that empty ignore_dirs doesn't ignore anything."""
    create_file(tmp_path / "dir1/file.txt")
    create_file(tmp_path / "dir2/file.txt")

    entries = list(powerwalk.walk(tmp_path, exclude=[]))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "dir1") in paths
    assert str(tmp_path / "dir1/file.txt") in paths
    assert str(tmp_path / "dir2") in paths
    assert str(tmp_path / "dir2/file.txt") in paths


def test_path_and_path_str_properties(tmp_path):
    """Test that path and path_str properties work correctly."""
    test_file = tmp_path / "test.txt"
    create_file(test_file)

    entries = list(powerwalk.walk(tmp_path))
    for entry in entries:
        if entry.path_str.endswith("test.txt"):
            assert isinstance(entry.path, Path)
            assert entry.path == test_file
            assert isinstance(entry.path_str, str)
            assert entry.path_str == str(test_file)
            break
    else:
        assert False, "test.txt not found in walk results"


def test_combined_filter_and_exclude(tmp_path):
    """Test using filter and exclude together."""
    create_file(tmp_path / "include/file.py")
    create_file(tmp_path / "include/file.txt")
    create_file(tmp_path / "exclude/file.py")
    create_file(tmp_path / "exclude/file.txt")

    # Use **/*.py to match all .py files, exclude the exclude directory
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py", exclude="**/exclude"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "include/file.py") in paths
    assert str(tmp_path / "include/file.txt") not in paths
    assert str(tmp_path / "exclude/file.py") not in paths
    assert str(tmp_path / "exclude/file.txt") not in paths


def test_filter_literal_separator(tmp_path):
    """Test that filter patterns respect literal separators.

    Without **, patterns should only match in the immediate directory.
    """
    create_file(tmp_path / "root.py")
    create_file(tmp_path / "root.txt")
    create_file(tmp_path / "subdir/nested.py")
    create_file(tmp_path / "subdir/nested.txt")

    # *.py should only match root-level .py files
    entries = list(powerwalk.walk(tmp_path, filter="*.py"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "root.py") in paths
    assert str(tmp_path / "subdir/nested.py") not in paths
    assert str(tmp_path / "root.txt") not in paths

    # **/*.py should match .py files at any depth
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "root.py") in paths
    assert str(tmp_path / "subdir/nested.py") in paths
    assert str(tmp_path / "root.txt") not in paths


def test_exclude_literal_separator(tmp_path):
    """Test that exclude patterns respect literal separators.

    Without **, patterns should only exclude in the immediate directory.
    """
    create_file(tmp_path / "keep.txt")
    create_file(tmp_path / "skip.txt")
    create_file(tmp_path / "subdir/keep.txt")
    create_file(tmp_path / "subdir/skip.txt")

    # skip.txt should only exclude root-level skip.txt
    entries = list(powerwalk.walk(tmp_path, exclude="skip.txt"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "keep.txt") in paths
    assert str(tmp_path / "skip.txt") not in paths
    assert str(tmp_path / "subdir/keep.txt") in paths
    assert str(tmp_path / "subdir/skip.txt") in paths  # Not excluded (in subdir)

    # **/skip.txt should exclude skip.txt at any depth
    entries = list(powerwalk.walk(tmp_path, exclude="**/skip.txt"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "keep.txt") in paths
    assert str(tmp_path / "skip.txt") not in paths
    assert str(tmp_path / "subdir/keep.txt") in paths
    assert str(tmp_path / "subdir/skip.txt") not in paths  # Excluded


def test_filter_and_exclude_with_literal_separator(tmp_path):
    """Test that both filter and exclude respect literal separators together."""
    create_file(tmp_path / "root.py")
    create_file(tmp_path / "test.py")
    create_file(tmp_path / "subdir/nested.py")
    create_file(tmp_path / "subdir/test.py")
    create_file(tmp_path / "subdir/deep/test.py")

    # Use **/*.py to match all .py files, but exclude test.py at root only
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py", exclude="test.py"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "root.py") in paths
    assert str(tmp_path / "test.py") not in paths  # Excluded at root
    assert str(tmp_path / "subdir/nested.py") in paths
    assert str(tmp_path / "subdir/test.py") in paths  # Not excluded (in subdir)
    assert str(tmp_path / "subdir/deep/test.py") in paths  # Not excluded (in subdir)

    # Use **/test.py to exclude test.py at any depth
    entries = list(powerwalk.walk(tmp_path, filter="**/*.py", exclude="**/test.py"))
    paths = {entry.path_str for entry in entries}

    assert str(tmp_path / "root.py") in paths
    assert str(tmp_path / "test.py") not in paths
    assert str(tmp_path / "subdir/nested.py") in paths
    assert str(tmp_path / "subdir/test.py") not in paths  # Excluded
    assert str(tmp_path / "subdir/deep/test.py") not in paths  # Excluded


def test_error_handling(tmp_path):
    """Test that errors are returned as Error objects."""
    create_file(tmp_path / "accessible.txt")
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    create_file(restricted_dir / "file.txt")

    # Make the directory inaccessible (this may not work on all systems)
    import os
    import stat

    try:
        os.chmod(restricted_dir, 0o000)

        # Walk and collect all results with on_error="yield" to get Error objects
        results = list(powerwalk.walk(tmp_path, on_error="yield"))

        # Check that we get DirEntry objects
        entries = [r for r in results if isinstance(r, powerwalk.DirEntry)]
        assert len(entries) >= 1  # At least accessible.txt

        # Check if we got any errors (depends on permissions)
        errors = [r for r in results if isinstance(r, powerwalk.Error)]
        # Note: Error behavior depends on OS and permissions
        for error in errors:
            assert isinstance(error.message, str)
            assert error.path == restricted_dir
            assert error.path_str == str(restricted_dir)
    finally:
        # Restore permissions for cleanup
        os.chmod(restricted_dir, stat.S_IRWXU)


def test_error_kind_permission_denied(tmp_path):
    """Test that PermissionDenied error kind is detected."""
    import os
    import stat

    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    create_file(restricted_dir / "file.txt")

    try:
        os.chmod(restricted_dir, 0o000)

        results = list(powerwalk.walk(tmp_path, on_error="yield"))
        errors = [r for r in results if isinstance(r, powerwalk.Error)]

        permission_errors = [
            e for e in errors if e.kind == powerwalk.ErrorKind.PermissionDenied
        ]
        assert len(permission_errors) > 0

        with pytest.raises(PermissionError):
            raise permission_errors[0].as_exception()
    finally:
        os.chmod(restricted_dir, stat.S_IRWXU)


def test_error_kind_not_found(tmp_path):
    """Test that NotFound error kind is detected."""
    results = list(powerwalk.walk("oops", on_error="yield"))
    errors = [r for r in results if isinstance(r, powerwalk.Error)]

    not_found_errors = [e for e in errors if e.kind == powerwalk.ErrorKind.NotFound]
    assert len(not_found_errors) > 0

    with pytest.raises(FileNotFoundError):
        raise not_found_errors[0].as_exception()


def test_error_kind_filesystem_loop(tmp_path):
    """Test that FilesystemLoop error kind is detected."""
    # Create a circular symlink
    link1 = tmp_path / "link1"
    link2 = tmp_path / "link2"

    link1.symlink_to(link2)
    link2.symlink_to(link1)

    # Walk with follow_symlinks=True to trigger loop detection
    results = list(powerwalk.walk(tmp_path, follow_symlinks=True, on_error="yield"))
    errors = [r for r in results if isinstance(r, powerwalk.Error)]

    loop_errors = [e for e in errors if e.kind == powerwalk.ErrorKind.FilesystemLoop]
    assert len(loop_errors) > 0

    with pytest.raises(OSError) as e:
        raise loop_errors[0].as_exception()
    assert e.value.errno == errno.ELOOP  #  # ty: ignore[unresolved-attribute]


def test_on_error_raise(tmp_path):
    """Test that on_error='raise' raises exceptions on errors."""
    import os
    import stat

    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    create_file(restricted_dir / "file.txt")
    create_file(tmp_path / "accessible.txt")

    try:
        os.chmod(restricted_dir, 0o000)

        # Should raise an exception when encountering the restricted directory
        with pytest.raises(PermissionError):
            list(powerwalk.walk(tmp_path, on_error="raise"))
    finally:
        os.chmod(restricted_dir, stat.S_IRWXU)
