"""Benchmarks for powerwalk to prevent performance regressions."""

import os
import random

import powerwalk
import pytest

_LARGE_DIR_FILES_PER_DIR = 10
_LARGE_DIR_SUBDIRS_PER_DIR = 5
_LARGE_DIR_DEPTH = 5


@pytest.fixture(scope="session")
def large_directory(tmp_path_factory):
    """Create a wide directory tree for benchmarking."""

    extensions = [".py", ".txt", ".md", ".json", ".yaml", ".rs", ".ts", ".jsx"]

    root = tmp_path_factory.mktemp("large_dir")

    def create_tree(path, depth, max_depth=_LARGE_DIR_DEPTH):
        if depth > max_depth:
            return

        for i in range(_LARGE_DIR_FILES_PER_DIR):
            ext = random.choice(extensions)
            (path / f"file_{i}{ext}").write_text("")

        for i in range(_LARGE_DIR_SUBDIRS_PER_DIR):
            subdir = path / f"dir_{i}"
            subdir.mkdir()
            create_tree(subdir, depth + 1, max_depth)

    # Fixed seed for reproducible benchmarks
    random.seed(42)
    create_tree(root, 0)

    return root


def test_benchmark_walk_all(benchmark, large_directory):
    """Benchmark walking all files without any filter."""

    def walk_all():
        return list(powerwalk.walk(large_directory))

    result = benchmark(walk_all)
    assert len(result) == 58591


def test_benchmark_walk_with_filter(benchmark, large_directory):
    """Benchmark walking with a single filter."""

    def walk_filtered():
        return list(powerwalk.walk(large_directory, filter="**/*.py"))

    result = benchmark(walk_filtered)
    assert len(result) == 4854
    assert all(entry.path_str.endswith(".py") for entry in result if entry.is_file)


def test_benchmark_os_walk_baseline(benchmark, large_directory):
    """Baseline benchmark using os.walk for comparison."""

    def walk_with_os():
        results = []
        for root, dirs, files in os.walk(large_directory):
            for name in files:
                results.append(os.path.join(root, name))
            for name in dirs:
                results.append(os.path.join(root, name))
        return results

    result = benchmark(walk_with_os)
    assert len(result) == 58590


def test_benchmark_os_walk_with_filter(benchmark, large_directory):
    """Baseline benchmark using os.walk with manual filtering for comparison."""

    def walk_with_os_filtered():
        results = []
        for root, dirs, files in os.walk(large_directory):
            for name in files:
                if name.endswith(".py"):
                    results.append(os.path.join(root, name))
        return results

    result = benchmark(walk_with_os_filtered)
    assert len(result) == 4854
