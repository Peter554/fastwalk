```
██████╗  ██████╗ ██╗    ██╗███████╗██████╗ ██╗    ██╗ █████╗ ██╗     ██╗  ██╗
██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔══██╗██║    ██║██╔══██╗██║     ██║ ██╔╝
██████╔╝██║   ██║██║ █╗ ██║█████╗  ██████╔╝██║ █╗ ██║███████║██║     █████╔╝
██╔═══╝ ██║   ██║██║███╗██║██╔══╝  ██╔══██╗██║███╗██║██╔══██║██║     ██╔═██╗
██║     ╚██████╔╝╚███╔███╔╝███████╗██║  ██║╚███╔███╔╝██║  ██║███████╗██║  ██╗
╚═╝      ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
```

[![PyPI](https://img.shields.io/pypi/v/powerwalk.svg)](https://pypi.org/project/powerwalk/)
[![CI](https://github.com/Peter554/powerwalk/actions/workflows/check.yml/badge.svg)](https://github.com/Peter554/powerwalk/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://peter554.github.io/powerwalk/)

Fast parallel directory walking for Python, powered by Rust.

- Find the repo [here](https://github.com/Peter554/powerwalk).
- Read the docs [here](https://peter554.github.io/powerwalk/).

## Features

- 🚀 **Fast**: Uses the rust [ignore](https://crates.io/crates/ignore) crate for fast directory traversal.
- ⚡ **Parallel**: Multi-threaded directory traversal.
- 🎯 **Smart filtering**: Built-in support for `.gitignore`, hidden files and glob patterns.
- 🔒 **Type-safe**: Full type hints.
- 🛡️ **Error handling**: Flexible error handling with `ignore`, `raise` and `yield` modes.

## Installation

```bash
pip install powerwalk
```

## Quick Start

```python
import powerwalk

# Find all Python files (errors ignored by default)
for entry in powerwalk.walk(".", filter="**/*.py"):
    if entry.is_file:
        print(entry.path)
```

## Feature Details

### 🚀 Fast

`powerwalk` leverages Rust's [`ignore`](https://crates.io/crates/ignore) crate, which is the same library used by [ripgrep](https://github.com/BurntSushi/ripgrep) for blazing-fast file traversal. This means you get production-grade performance for scanning large directory trees.

### ⚡ Parallel

Directory traversal is performed in parallel across multiple threads, significantly speeding up operations on large codebases. The number of threads can be configured via the `threads` parameter, or set to `0` (default) to automatically use a number based on your CPU count.

```python
# Use 8 threads for traversal
for entry in powerwalk.walk(".", threads=8):
    print(entry.path)
```

### 🎯 Smart Filtering

`powerwalk` respects common ignore patterns out of the box:

- **`.gitignore`** files (via `respect_git_ignore=True`, default)
- **Global gitignore** (via `respect_global_git_ignore=True`, default)
- **`.git/info/exclude`** (via `respect_git_exclude=True`, default)
- **`.ignore`** files (via `respect_ignore=True`, default)
- **Hidden files** (via `ignore_hidden=True`, default)

You can also use glob patterns to filter or exclude specific files:

```python
# Find all Python and JavaScript files, excluding tests
for entry in powerwalk.walk(
    ".",
    filter=["**/*.py", "**/*.js"],
    exclude=["**/test_*", "**/*_test.py"],
):
    print(entry.path)

# Control ignore behavior
for entry in powerwalk.walk(
    ".",
    ignore_hidden=False,  # Include hidden files
    respect_git_ignore=False,  # Don't respect .gitignore
):
    print(entry.path)
```

### 🔒 Type-Safe

`powerwalk` provides full type hints and uses `typing.overload` to ensure precise type inference based on the `on_error` parameter:

```python
# Type checkers know this yields only DirEntry
for entry in powerwalk.walk(".", on_error="ignore"):
    reveal_type(entry)  # DirEntry

# Type checkers know this yields DirEntry | Error
for result in powerwalk.walk(".", on_error="yield"):
    reveal_type(result)  # DirEntry | Error
```

### 🛡️ Error Handling

`powerwalk` offers three modes for handling errors during traversal:

**`on_error="ignore"` (default)** - Silently skip errors and only yield successful entries:

```python
for entry in powerwalk.walk(".", on_error="ignore"):
    print(entry.path)  # Only successful entries
```

**`on_error="raise"` - Raise an exception on the first error:**

```python
try:
    for entry in powerwalk.walk(".", on_error="raise"):
        print(entry.path)
except (FileNotFoundError, PermissionError, OSError) as e:
    print(f"Traversal failed: {e}")
```

**`on_error="yield"` - Yield both successful entries and errors:**

```python
for result in powerwalk.walk(".", on_error="yield"):
    match result:
        case powerwalk.DirEntry():
            print(f"File: {result.path}")
        case powerwalk.Error():
            match result.kind:
                case powerwalk.ErrorKind.PermissionDenied:
                    print(f"Permission denied: {result.message}")
                case powerwalk.ErrorKind.NotFound:
                    print(f"Not found: {result.message}")
                case powerwalk.ErrorKind.FilesystemLoop:
                    print(f"Filesystem loop: {result.message}")
                case _:
                    print(f"Error: {result.message}")
```
