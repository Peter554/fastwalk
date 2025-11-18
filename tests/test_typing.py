"""Type checking tests to verify type overloads work correctly."""

from typing import TYPE_CHECKING

import powerwalk

if TYPE_CHECKING:
    from typing_extensions import assert_type


def test_on_error_ignore_returns_direntry() -> None:
    """Test that on_error='ignore' returns Iterator[DirEntry]."""
    # With on_error="ignore" (default), should only yield DirEntry
    result = powerwalk.walk(".", on_error="ignore")

    if TYPE_CHECKING:
        # Type checker should know this is an iterator of DirEntry only
        for entry in result:
            assert_type(entry, powerwalk.DirEntry)


def test_on_error_raise_returns_direntry() -> None:
    """Test that on_error='raise' returns Iterator[DirEntry]."""
    # With on_error="raise", should only yield DirEntry (or raise)
    result = powerwalk.walk(".", on_error="raise")

    if TYPE_CHECKING:
        # Type checker should know this is an iterator of DirEntry only
        for entry in result:
            assert_type(entry, powerwalk.DirEntry)


def test_on_error_yield_returns_union() -> None:
    """Test that on_error='yield' returns Iterator[DirEntry | Error]."""
    # With on_error="yield", should yield DirEntry | Error
    result = powerwalk.walk(".", on_error="yield")

    if TYPE_CHECKING:
        # Type checker should know this can be either DirEntry or Error
        for entry in result:
            assert_type(entry, powerwalk.DirEntry | powerwalk.Error)
