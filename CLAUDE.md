# temporal-book Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-19

## Active Technologies

- Python 3.13 (001-temporal-book-chapters)
- mdBook (002-mdbook-migration) - Static site generator for documentation

## Project Structure

```text
src/                    # mdBook source (markdown chapters)
book/                   # Generated output (gitignored)
examples/               # Python code examples
shared/                 # Python utilities
tests/
```

## Commands

**Python Development**:
```bash
cd examples/part-01/chapter-01
uv sync
uv run python <file>.py
pytest
ruff check .
```

**mdBook**:
```bash
mdbook build        # Build static site
mdbook serve        # Preview locally at localhost:3000
mdbook clean        # Clean build output
```

## Code Style

- Python 3.13: Follow standard conventions
- Markdown: Follow mdBook conventions, German language content

## Recent Changes

- 002-mdbook-migration: Added mdBook for static site generation
- 001-temporal-book-chapters: Added Python 3.13

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
