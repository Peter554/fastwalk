#![feature(io_error_more)]

use std::path::PathBuf;
use std::sync::Arc;
use std::thread;

use crossbeam::channel;
use globset::GlobSetBuilder;
use ignore::WalkBuilder;
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct DirEntry {
    #[pyo3(get)]
    path: String,
    #[pyo3(get)]
    is_file: bool,
    #[pyo3(get)]
    is_dir: bool,
    #[pyo3(get)]
    is_symlink: bool,
}

#[pyclass]
#[derive(Clone)]
pub struct Error {
    #[pyo3(get)]
    message: String,
    #[pyo3(get)]
    path: Option<String>,
    #[pyo3(get)]
    kind: Option<String>,
}

enum WalkResult {
    DirEntry(DirEntry),
    Error(Error),
}

#[pyclass]
pub struct WalkIterator {
    receiver: channel::Receiver<WalkResult>,
}

#[pymethods]
impl WalkIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<PyObject>> {
        match self.receiver.recv().ok() {
            Some(WalkResult::DirEntry(entry)) => Ok(Some(Py::new(py, entry)?.into_any())),
            Some(WalkResult::Error(error)) => Ok(Some(Py::new(py, error)?.into_any())),
            None => Ok(None),
        }
    }
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn walk(
    root: String,
    filter: Vec<String>,
    exclude: Vec<String>,
    ignore_hidden: bool,
    respect_git_ignore: bool,
    respect_global_git_ignore: bool,
    respect_git_exclude: bool,
    respect_ignore: bool,
    follow_symlinks: bool,
    max_depth: Option<usize>,
    min_depth: Option<usize>,
    max_filesize: Option<u64>,
    threads: usize,
) -> PyResult<WalkIterator> {
    let root_path = PathBuf::from(root);

    let mut builder = WalkBuilder::new(&root_path);

    builder
        .hidden(ignore_hidden)
        .git_ignore(respect_git_ignore)
        .git_global(respect_global_git_ignore)
        .git_exclude(respect_git_exclude)
        .ignore(respect_ignore)
        .require_git(false)
        .follow_links(follow_symlinks)
        .threads(threads);

    if let Some(depth) = max_depth {
        builder.max_depth(Some(depth));
    }

    if let Some(depth) = min_depth {
        builder.min_depth(Some(depth));
    }

    if let Some(size) = max_filesize {
        builder.max_filesize(Some(size));
    }

    // Build glob matcher for filter
    let filter_glob_matcher = if !filter.is_empty() {
        let mut glob_builder = GlobSetBuilder::new();
        for pattern in &filter {
            let glob = globset::GlobBuilder::new(pattern)
                .literal_separator(true)
                .build()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
            glob_builder.add(glob);
        }
        Some(Arc::new(glob_builder.build().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })?))
    } else {
        None
    };

    // Build glob matcher for exclude patterns
    let exclude_glob_matcher = if !exclude.is_empty() {
        let mut glob_builder = GlobSetBuilder::new();
        for pattern in &exclude {
            let glob = globset::GlobBuilder::new(pattern)
                .literal_separator(true)
                .build()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
            glob_builder.add(glob);
        }
        Some(Arc::new(glob_builder.build().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })?))
    } else {
        None
    };

    // Apply exclude filter if patterns are provided
    if let Some(ref glob) = exclude_glob_matcher {
        let glob = glob.clone();
        let root_path = root_path.clone();
        builder.filter_entry(move |entry| {
            // Exclude entries that match any exclude pattern
            let relative_path = entry.path().strip_prefix(&root_path).unwrap();
            !glob.is_match(relative_path)
        });
    }

    // Create a bounded channel for parallel walking
    // Buffer size of 10000 provides good throughput while limiting memory usage
    let (sender, receiver) = channel::bounded(10000);

    // Spawn a thread to do the walking
    thread::spawn(move || {
        builder.build_parallel().run(|| {
            let sender = sender.clone();
            let filter_glob_matcher = filter_glob_matcher.clone();
            let root_path = root_path.clone();
            Box::new(move |result| {
                match result {
                    Ok(entry) => {
                        let path = entry.path();

                        // Apply glob filters if present
                        if let Some(ref glob) = filter_glob_matcher {
                            let relative_path = path.strip_prefix(&root_path).unwrap();
                            if !glob.is_match(relative_path) {
                                return ignore::WalkState::Continue;
                            }
                        }

                        let file_type = entry.file_type();
                        let dir_entry = DirEntry {
                            path: path.to_string_lossy().to_string(),
                            is_file: file_type.as_ref().is_some_and(|ft| ft.is_file()),
                            is_dir: file_type.as_ref().is_some_and(|ft| ft.is_dir()),
                            is_symlink: file_type.as_ref().is_some_and(|ft| ft.is_symlink()),
                        };
                        let _ = sender.send(WalkResult::DirEntry(dir_entry));
                    }
                    Err(err) => {
                        let error = Error {
                            message: err.to_string(),
                            path: extract_error_path(&err),
                            kind: extract_error_kind(&err),
                        };
                        let _ = sender.send(WalkResult::Error(error));
                    }
                }
                ignore::WalkState::Continue
            })
        });
    });

    Ok(WalkIterator { receiver })
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<DirEntry>()?;
    m.add_class::<Error>()?;
    m.add_class::<WalkIterator>()?;
    m.add_function(wrap_pyfunction!(walk, m)?)?;
    Ok(())
}

// Recursively extract the path from the ignore::Error
// Similar to how is_io() recursively checks variants
fn extract_error_path(err: &ignore::Error) -> Option<String> {
    match err {
        ignore::Error::WithPath { path, .. } => Some(path.to_string_lossy().to_string()),
        ignore::Error::WithLineNumber { err, .. } => extract_error_path(err),
        ignore::Error::WithDepth { err, .. } => extract_error_path(err),
        ignore::Error::Partial(errs) => {
            if errs.len() == 1 {
                extract_error_path(&errs[0])
            } else {
                None
            }
        }
        _ => None,
    }
}

fn extract_error_kind(err: &ignore::Error) -> Option<String> {
    match err {
        // Loop error from ignore crate
        ignore::Error::Loop { .. } => Some("FilesystemLoop".to_string()),

        // Recurse into wrapper errors
        ignore::Error::WithPath { err, .. } => extract_error_kind(err),
        ignore::Error::WithLineNumber { err, .. } => extract_error_kind(err),
        ignore::Error::WithDepth { err, .. } => extract_error_kind(err),

        // Partial errors - check first error
        ignore::Error::Partial(errs) => {
            if !errs.is_empty() {
                extract_error_kind(&errs[0])
            } else {
                None
            }
        }

        // IO errors - inspect the std::io::ErrorKind
        ignore::Error::Io(io_err) => {
            use std::io::ErrorKind;
            match io_err.kind() {
                ErrorKind::NotFound => Some("NotFound".to_string()),
                ErrorKind::PermissionDenied => Some("PermissionDenied".to_string()),
                ErrorKind::FilesystemLoop => Some("FilesystemLoop".to_string()),
                _ => None,
            }
        }

        _ => None,
    }
}
