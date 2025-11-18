[default]
_default:
    @just --list

# Run all checks
check: test lint

# Compile the Rust extension in debug mode
compile-dev:
    @uv run maturin develop

# Compile the Rust extension in release mode
compile-release:
    @uv run maturin develop --release

# Format the rust code
[group('fmt')]
[working-directory: 'rust']
fmt-rs:
    @cargo fmt

# Format the python code
[group('fmt')]
fmt-py:
    @uv run ruff format

# Format the code
[group('fmt')]
fmt: fmt-rs fmt-py

# Run all tests
[group('test')]
test: compile-dev test-rs test-py

# Run Rust tests
[group('test')]
[working-directory: 'rust']
test-rs:
    @cargo test --all-features

# Run Python tests
[group('test')]
test-py:
    @uv run pytest --benchmark-skip

# Run benchmarks
[group('test')]
benchmark: compile-release
    @uv run pytest --benchmark-only --benchmark-autosave --benchmark-compare --benchmark-group-by=func --benchmark-columns mean,stddev,rounds,iterations

# Run all linters
[group('lint')]
lint: lint-rs lint-py

# Run Rust linters
[group('lint')]
[working-directory: 'rust']
lint-rs:
    @cargo clippy --all-targets --all-features -- -D warnings
    @cargo fmt -- --check

# Run Python linters
[group('lint')]
lint-py:
    @uv run ty check
    @uv run ruff check
    @uv run ruff format --check

# Auto-fix all issues
[group('fix')]
fix: fix-rs fix-py

# Auto-fix Rust issues
[group('fix')]
[working-directory: 'rust']
fix-rs:
    @cargo clippy --all-targets --all-features --fix --allow-staged
    @just fmt

# Auto-fix Python issues
[group('fix')]
fix-py:
    @uv run ruff check --fix
    @just fmt

# Build documentation
[group('docs')]
docs-build: compile-dev
    @uv run pdoc powerwalk -o docs/

# Serve documentation locally
[group('docs')]
docs-serve: compile-dev
    @uv run pdoc powerwalk

# Publish a new version. Usage: just publish patch|minor|major
[group('publish')]
publish MODE:
    just _publish-check-mode "{{MODE}}"
    just check
    just _check-uncommitted-changes
    cargo bump {{MODE}}
    just compile-dev
    git add --all
    git commit -m "Bump version v`just _get-version`"
    git tag "v`just _get-version`"
    git push
    git push --tags

_publish-check-mode MODE:
    @[[ "{{MODE}}" =~ ^(patch|minor|major)$ ]] || (echo "Error: MODE must be patch, minor, or major" && exit 1)

_check-uncommitted-changes:
    @test -z "$(git status -s)" || (echo "Error: There are uncommitted changes" && exit 1)

_get-version:
    @cargo metadata --format-version=1 --no-deps | jq -r '.packages[0].version'
