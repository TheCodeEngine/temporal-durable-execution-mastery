# Research: mdBook Migration Best Practices

**Date**: 2025-11-19
**Feature**: 002-mdbook-migration
**Purpose**: Resolve technical unknowns for migrating Temporal book to mdBook

## 1. Directory Structure for Multi-Part Books

**Decision**: Use flat structure in `src/` with descriptive filenames (e.g., `part-01-chapter-01.md`), organized through SUMMARY.md rather than directory hierarchy.

**Rationale**:
- mdBook's core design prioritizes SUMMARY.md as the single source of truth for book structure
- Directory layout primarily affects URLs, not the logical organization visible to readers
- Flat structures are easier to maintain and all content is visible at a glance
- Nested directories don't add value in mdBook's paradigm since organization is already handled by SUMMARY.md

**Recommended Structure**:
```
src/
├── SUMMARY.md              # Table of contents (defines structure)
├── README.md               # Introduction/landing page
├── part-01-chapter-01.md   # Flat naming convention
├── part-01-chapter-02.md
├── part-01-chapter-03.md
├── part-02-chapter-04.md
├── ...
└── images/                 # All images centralized
    ├── part-01/
    ├── part-02/
    └── shared/
```

**SUMMARY.md Structure**:
```markdown
# Summary

[Introduction](README.md)

# Part I: Grundlagen der Durable Execution

- [Einführung in Temporal](part-01-chapter-01.md)
- [Kernbausteine: Workflows, Activities, Worker](part-01-chapter-02.md)
- [Architektur des Temporal Service](part-01-chapter-03.md)

# Part II: Entwicklung von Temporal-Anwendungen

- [Entwicklungs-Setup und SDK-Auswahl](part-02-chapter-04.md)
- [Workflows programmieren](part-02-chapter-05.md)
- [Kommunikation (Signale und Queries)](part-02-chapter-06.md)

# Part III: Resilienz, Evolution und Muster

- [Fehlerbehandlung und Retries](part-03-chapter-07.md)
- [SAGA Pattern](part-03-chapter-08.md)
- [Workflow-Evolution und Versionierung](part-03-chapter-09.md)

# Part IV: Betrieb, Skalierung und Best Practices

- [Produktions-Deployment](part-04-chapter-10.md)
- [Skalierung der Worker](part-04-chapter-11.md)
- [Observability und Monitoring](part-04-chapter-12.md)
- [Best Practices und Anti-Muster](part-04-chapter-13.md)

# Part V: Das Temporal Kochbuch

- [Muster-Rezepte](part-05-chapter-14.md)
- [Erweiterte Rezepte](part-05-chapter-15.md)
```

**Alternatives Considered**:
- Keep existing `part-*/chapter-*.md` structure: Rejected due to deep nesting that doesn't add value
- Mirror structure `src/part-i/chapter-01.md`: Rejected as unnecessary nesting complicates maintenance
- Fully flat without part prefix: Would work but harder to identify part grouping in file listing

**References**:
- [mdBook Creating a Book Guide](https://rust-lang.github.io/mdBook/guide/creating.html)
- [mdBook SUMMARY.md Format](https://rust-lang.github.io/mdBook/format/summary.html)

---

## 2. Asset and Image Handling

**Decision**: Store all images in `src/images/` directory with subdirectories organized by part. Reference using relative paths from markdown files.

**Rationale**:
- mdBook includes all files in `src/` directory in the build output
- Directory structure is preserved in rendered output (src/images/x.png → book/images/x.png)
- `src/images/` is the most commonly used pattern in mdBook ecosystem
- Centralized location makes asset management easier than co-located images
- Subdirectories by part provide organization without complicating paths

**Recommended Structure**:
```
src/
├── SUMMARY.md
├── part-01-chapter-01.md
└── images/
    ├── part-01/
    │   ├── temporal-architecture.png
    │   └── workflow-lifecycle.svg
    ├── part-02/
    │   ├── sdk-structure.png
    │   └── activity-diagram.png
    └── shared/
        └── temporal-logo.png
```

**Image References** (from any markdown file):
```markdown
![Temporal Architecture](images/part-01/temporal-architecture.png)
![Logo](images/shared/temporal-logo.png)
```

**Alternatives Considered**:
- Co-located images next to markdown files: Rejected due to clutter in main `src/` directory
- Top-level `assets/` directory outside `src/`: Not supported by mdBook (only `src/` files included)
- Use `src/img/` instead of `src/images/`: Valid but less explicit
- Flat image directory: Would become unwieldy with 15+ chapters

**References**:
- [mdBook Creating a Book - Source Files](https://rust-lang.github.io/mdBook/guide/creating.html)
- [mdBook Issue #1606 - Images discussion](https://github.com/rust-lang/mdBook/issues/1606)

---

## 3. GitHub Actions Workflow for mdBook + GitHub Pages

**Decision**: Use official GitHub Actions workflow with `actions/deploy-pages@v4` and `peaceiris/actions-mdbook@v2` for fast installation.

**Rationale**:
- Modern artifact-based deployment pattern (vs. deprecated gh-pages branch)
- Official GitHub support with proper security (OIDC verification)
- No repository bloat from generated HTML
- `peaceiris/actions-mdbook` is significantly faster than installing from Rust source
- Cleaner history and better integration with Pages environments

**Recommended Workflow** (`.github/workflows/deploy-mdbook.yml`):
```yaml
name: Deploy mdBook to Pages

on:
  push:
    branches: [develop]  # Adjust to your default branch
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup mdBook
        uses: peaceiris/actions-mdbook@v2
        with:
          mdbook-version: 'latest'

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Build with mdBook
        run: mdbook build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./book

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**Configuration Required**:

1. Enable GitHub Pages in Settings > Pages, set Source to "GitHub Actions"
2. Create `book.toml` in repository root:
```toml
[book]
title = "Temporal.io – Durable Execution Mastery"
authors = ["Your Name"]
language = "de"

[build]
build-dir = "book"

[output.html]
# Optional: custom theme, additional CSS, etc.
```

**Alternatives Considered**:
- Install mdBook from Cargo: Rejected due to 5-10x slower build times
- `peaceiris/actions-gh-pages`: Valid alternative but official pattern now recommended
- Manual gh-pages branch management: Strongly rejected (deprecated, bloats repo)

**References**:
- [Official GitHub Actions Starter Workflow for mdBook](https://github.com/actions/starter-workflows/blob/main/pages/mdbook.yml)
- [peaceiris/actions-mdbook](https://github.com/peaceiris/actions-mdbook)
- [actions/deploy-pages@v4](https://github.com/actions/deploy-pages)

---

## Migration Path Summary

### From Current Structure:
```
temporal-book/
├── part-i-grundlagen/
│   ├── chapter-01.md
│   ├── chapter-02.md
│   ├── assets/
│   └── examples/
├── part-ii-sdk-fokus/
└── ...
```

### To mdBook Structure:
```
temporal-book/
├── .github/workflows/deploy-mdbook.yml  # NEW
├── book.toml                            # NEW
├── src/                                 # NEW
│   ├── SUMMARY.md
│   ├── README.md
│   ├── part-01-chapter-01.md           # Moved
│   ├── ...
│   └── images/                          # NEW (consolidated)
│       ├── part-01/
│       └── ...
├── examples/                            # KEEP (not in book)
├── shared/                              # KEEP (Python utilities)
└── book/                                # NEW (gitignored)
```

### Key Migration Steps:

1. Initialize mdBook structure with `mdbook init`
2. Move chapter files to `src/` with flat naming
3. Consolidate assets into `src/images/` organized by part
4. Update image references in markdown files
5. Create SUMMARY.md defining book structure
6. Add GitHub Actions workflow
7. Update .gitignore to exclude `/book`
8. Test locally with `mdbook build` and `mdbook serve`

---

## Resolved Clarifications

All NEEDS CLARIFICATION items from Technical Context have been resolved:

✅ **Optimal mdBook directory structure**: Flat structure in src/ with descriptive filenames
✅ **Asset/image handling strategy**: Centralized in src/images/ with part-based subdirectories
✅ **GitHub Actions workflow configuration**: Modern artifact-based deployment with official actions

Research complete and ready for Phase 1 design artifacts.
