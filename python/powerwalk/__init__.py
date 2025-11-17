"""
.. include:: ../../README.md
"""

from __future__ import annotations

import dataclasses
import enum
import errno
import functools
from collections.abc import Collection, Iterator
from pathlib import Path
from typing import Literal, overload

from powerwalk import _core  # ty: ignore[unresolved-import]

_PathLike = Path | str


@overload
def walk(
    root: _PathLike,
    *,
    filter: str | Collection[str] = ...,
    exclude: str | Collection[str] = ...,
    ignore_hidden: bool = ...,
    respect_git_ignore: bool = ...,
    respect_global_git_ignore: bool = ...,
    respect_git_exclude: bool = ...,
    respect_ignore: bool = ...,
    follow_symlinks: bool = ...,
    max_depth: int | None = ...,
    min_depth: int | None = ...,
    max_filesize: int | None = ...,
    threads: int = ...,
    on_error: Literal["continue"] = ...,
) -> Iterator[DirEntry]: ...


@overload
def walk(
    root: _PathLike,
    *,
    filter: str | Collection[str] = ...,
    exclude: str | Collection[str] = ...,
    ignore_hidden: bool = ...,
    respect_git_ignore: bool = ...,
    respect_global_git_ignore: bool = ...,
    respect_git_exclude: bool = ...,
    respect_ignore: bool = ...,
    follow_symlinks: bool = ...,
    max_depth: int | None = ...,
    min_depth: int | None = ...,
    max_filesize: int | None = ...,
    threads: int = ...,
    on_error: Literal["yield"],
) -> "Iterator[DirEntry | Error]": ...


def walk(
    root: _PathLike,
    *,
    filter: str | Collection[str] = (),
    exclude: str | Collection[str] = (),
    ignore_hidden: bool = True,
    respect_git_ignore: bool = True,
    respect_global_git_ignore: bool = True,
    respect_git_exclude: bool = True,
    respect_ignore: bool = True,
    follow_symlinks: bool = False,
    max_depth: int | None = None,
    min_depth: int | None = None,
    max_filesize: int | None = None,
    threads: int = 0,
    on_error: Literal["continue", "yield"] = "continue",
):
    """Walk a directory tree in parallel, yielding DirEntry objects.

    This function uses Rust's `ignore` crate for fast parallel directory traversal
    with built-in support for gitignore rules and other common ignore patterns.

    ## Arguments

    - `root`: The root directory to start walking from.
    - `filter`: Glob pattern(s) to filter files (any matching pattern includes the file).
      Example: `"*.py"` or `["*.py", "*.txt"]`
    - `exclude`: Glob pattern(s) to exclude files and directories.
      Example: `"**/node_modules"` or `["**/__pycache__", "**/node_modules"]`
    - `ignore_hidden`: If True, ignore hidden files and directories.
    - `respect_git_ignore`: If True, respect .gitignore files.
    - `respect_global_git_ignore`: If True, respect global gitignore.
    - `respect_git_exclude`: If True, respect .git/info/exclude.
    - `respect_ignore`: If True, respect .ignore files.
    - `follow_symlinks`: If True, follow symbolic links.
    - `max_depth`: Maximum depth to descend.
    - `min_depth`: Minimum depth before yielding entries.
    - `max_filesize`: Maximum file size in bytes to consider.
    - `threads`: Number of threads to use (0 for automatic, based on CPU count).
    - `on_error`: How to handle errors during traversal:
      - `"continue"` (default): Silently ignore errors and only yield DirEntry objects.
      - `"yield"`: Yield both DirEntry and Error objects.

    ## Returns

    An iterator that yields `DirEntry` objects (if `on_error="continue"`) or
    `DirEntry | Error` objects (if `on_error="yield"`).

    ## Example

    ```python
    # Default: continue on errors, only yield successful entries
    for entry in walk(".", filter="**/*.py"):
        print(entry.path)

    # Handle errors during directory traversal
    for result in walk(".", filter="**/*.py", on_error="yield"):
        match result:
            case DirEntry():
                print(result.path)
            case Error():
                print(f"Error at {result.path}: {result.message}")

    # Exclude patterns
    for entry in walk(".", filter="**/*.py", exclude=["**/test_*", "**/__pycache__"]):
        print(entry.path)
    ```
    """
    # Convert root to string
    root_str = str(root)

    # Convert filter to list
    filter_list = [filter] if isinstance(filter, str) else list(filter)

    # Convert exclude to list
    exclude_list = [exclude] if isinstance(exclude, str) else list(exclude)

    # Call the Rust implementation which returns an iterator
    walk_iterator = _core.walk(
        root_str,
        filter_list,
        exclude_list,
        ignore_hidden,
        respect_git_ignore,
        respect_global_git_ignore,
        respect_git_exclude,
        respect_ignore,
        follow_symlinks,
        max_depth,
        min_depth,
        max_filesize,
        threads,
    )

    dir_walker = _DirWalker(walk_iterator)

    if on_error == "continue":
        return _ErrorIgnoringDirWalker(dir_walker)
    else:
        return dir_walker


@dataclasses.dataclass(frozen=True)
class DirEntry:
    """A directory entry returned by walk().

    This class wraps the Rust DirEntry and provides convenient access to
    path information and file type checks.
    """

    _core_entry: _core.DirEntry

    @functools.cached_property
    def path(self) -> Path:
        """The full path as a Path object."""
        return Path(self._core_entry.path)

    @functools.cached_property
    def path_str(self) -> str:
        """The full path as a string."""
        return self._core_entry.path

    @functools.cached_property
    def is_file(self) -> bool:
        """True if this entry is a regular file."""
        return self._core_entry.is_file

    @functools.cached_property
    def is_dir(self) -> bool:
        """True if this entry is a directory."""
        return self._core_entry.is_dir

    @functools.cached_property
    def is_symlink(self) -> bool:
        """True if this entry is a symbolic link."""
        return self._core_entry.is_symlink


@dataclasses.dataclass(frozen=True)
class Error:
    """An error returned by walk().

    Represents an error encountered during directory traversal.
    """

    _core_error: _core.Error

    @functools.cached_property
    def message(self) -> str:
        """The error message."""
        return self._core_error.message

    @functools.cached_property
    def path(self) -> Path | None:
        """The path where the error occurred, if available."""
        return Path(self._core_error.path) if self._core_error.path else None

    @functools.cached_property
    def path_str(self) -> str | None:
        """The path where the error occurred as a string, if available."""
        return self._core_error.path

    @functools.cached_property
    def kind(self) -> ErrorKind | None:
        """The error kind, if known.

        Returns the kind of error that occurred:
        - NotFound: File or directory not found
        - PermissionDenied: Permission denied to access the path
        - FilesystemLoop: Encountered a filesystem loop (circular symlinks)
        """
        if self._core_error.kind is None:
            return None
        return ErrorKind(self._core_error.kind)

    def raise_(self):
        match self.kind:
            case ErrorKind.NotFound:
                raise FileNotFoundError(errno.ENOENT, self.message, self.path_str)
            case ErrorKind.PermissionDenied:
                raise PermissionError(errno.EACCES, self.message, self.path_str)
            case ErrorKind.FilesystemLoop:
                raise OSError(errno.ELOOP, self.message, self.path_str)
            case None:
                raise OSError(self.message)


class ErrorKind(enum.StrEnum):
    """The kind of error that occurred during directory traversal."""

    NotFound = "NotFound"
    PermissionDenied = "PermissionDenied"
    FilesystemLoop = "FilesystemLoop"


class _DirWalker(Iterator[DirEntry | Error]):
    """Iterator that yields both DirEntry objects and Error objects.

    Use this when you want to handle errors during directory traversal.
    """

    def __init__(self, walk_iterator: _core.WalkIterator):
        self._walk_iterator = walk_iterator

    def __iter__(self) -> _DirWalker:
        return self

    def __next__(self) -> DirEntry | Error:
        result = next(self._walk_iterator)
        if isinstance(result, _core.DirEntry):
            return DirEntry(_core_entry=result)
        else:
            return Error(_core_error=result)


class _ErrorIgnoringDirWalker(Iterator[DirEntry]):
    """Iterator that only yields DirEntry objects, silently ignoring errors."""

    def __init__(self, dir_walker: _DirWalker):
        self._dir_walker = dir_walker

    def __iter__(self) -> _ErrorIgnoringDirWalker:
        return self

    def __next__(self) -> DirEntry:
        while True:
            result = next(self._dir_walker)
            if isinstance(result, DirEntry):
                return result
