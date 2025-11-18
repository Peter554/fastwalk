"""Tests for error handling behavior."""

import errno
import os
import platform
import stat

import pytest
from conftest import create_file

import powerwalk


def test_on_error_ignore(tmp_path):
    """Test that errors are ignored when on_error='ignore'."""
    entries = list(powerwalk.walk("oops", on_error="ignore"))
    assert len(entries) == 0


def test_on_error_yield(tmp_path):
    """Test that errors are yielded when on_error='yield'."""
    entries = list(powerwalk.walk("oops", on_error="yield"))
    assert len([e for e in entries if isinstance(e, powerwalk.Error)]) > 0


def test_on_error_raise():
    """Test that on_error='raise' raises exceptions on errors."""
    with pytest.raises(FileNotFoundError):
        list(powerwalk.walk("oops", on_error="raise"))


def test_error_kind_not_found(tmp_path):
    """Test that NotFound error kind is detected."""
    results = list(powerwalk.walk("oops", on_error="yield"))
    errors = [r for r in results if isinstance(r, powerwalk.Error)]

    not_found_errors = [e for e in errors if e.kind == powerwalk.ErrorKind.NotFound]
    assert len(not_found_errors) > 0

    with pytest.raises(FileNotFoundError):
        raise not_found_errors[0].as_exception()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Windows handles file permissions differently than Unix-like systems",
)
def test_error_kind_permission_denied(tmp_path):
    """Test that PermissionDenied error kind is detected."""
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
    assert e.value.errno == errno.ELOOP
