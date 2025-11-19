# Data Model: mdBook Migration

**Feature**: 002-mdbook-migration
**Date**: 2025-11-19
**Purpose**: Define the structural entities and their relationships in the mdBook project

## Overview

This document describes the key entities in the mdBook structure. Unlike traditional software data models, these entities represent the organizational structure of documentation content and configuration.

---

## Entity: Book Configuration

**Represents**: The mdBook project configuration defining metadata and build settings

**Location**: `book.toml` (repository root)

**Attributes**:
- `title` (string): Book title displayed in rendered output
- `authors` (array of strings): Book author names
- `language` (string): Content language code (e.g., "de" for German)
- `build-dir` (string): Output directory for generated HTML
- `description` (string, optional): Book description for metadata

**Relationships**:
- Configures the Book Structure entity
- Referenced by build tooling and GitHub Actions

**Validation Rules**:
- `language` must be valid ISO 639-1 code
- `build-dir` must not conflict with source directories

**Example**:
```toml
[book]
title = "Temporal.io – Durable Execution Mastery"
authors = ["Your Name"]
language = "de"
description = "Ein umfassender Deep Dive in die Orchestrierung verteilter Systeme mit Temporal"

[build]
build-dir = "book"

[output.html]
# HTML-specific configuration
```

---

## Entity: Book Structure (SUMMARY.md)

**Represents**: The hierarchical table of contents defining all parts and chapters

**Location**: `src/SUMMARY.md`

**Attributes**:
- Parts (array): Top-level sections grouping related chapters
- Chapters (array): Individual content pages
- Links (mapping): Chapter title → markdown file path

**Structure**:
```
Summary
├── Introduction (optional)
├── Part 1 (section header)
│   ├── Chapter 1.1 → file path
│   ├── Chapter 1.2 → file path
│   └── Chapter 1.3 → file path
├── Part 2 (section header)
│   └── ...
└── Part N
```

**Relationships**:
- References Chapter File entities via file paths
- Defines navigation hierarchy in rendered book
- Each Chapter File MUST be referenced to appear in book

**Validation Rules**:
- All referenced file paths must exist in `src/` directory
- Cannot have duplicate chapter titles at same level
- Proper markdown link syntax: `[Title](path.md)`
- Section headers use `#` prefix (no link)

**Example**:
```markdown
# Summary

[Introduction](README.md)

# Part I: Grundlagen der Durable Execution

- [Einführung in Temporal](part-01-chapter-01.md)
- [Kernbausteine](part-01-chapter-02.md)

# Part II: Entwicklung

- [Setup und SDK](part-02-chapter-04.md)
```

---

## Entity: Chapter File

**Represents**: A single markdown file containing book content

**Location**: `src/*.md`

**Attributes**:
- `filename` (string): File name (e.g., `part-01-chapter-01.md`)
- `title` (string): Chapter heading (first H1 in markdown)
- `content` (markdown): Chapter body with text, code blocks, images
- `references` (array): Links to other chapters or external resources

**Naming Convention**:
- Format: `part-NN-chapter-NN.md` or descriptive slugs
- Examples: `part-01-chapter-01.md`, `part-03-chapter-07.md`

**Relationships**:
- Referenced by Book Structure (SUMMARY.md)
- May reference Image Assets via relative paths
- May link to other Chapter Files or Example Projects

**Validation Rules**:
- Must be valid markdown syntax
- Must contain at least one H1 heading
- Image references must point to existing files in `src/images/`
- Internal links must use relative paths

**Content Structure**:
```markdown
# Chapter Title

## Section 1

Content with **formatting**, code blocks, and images.

![Diagram](images/part-01/diagram.png)

## Section 2

More content...
```

---

## Entity: Part

**Represents**: A logical grouping of related chapters (section header in SUMMARY.md)

**Attributes**:
- `number` (integer): Part number (1-5)
- `name` (string): Part title
- `chapters` (array): List of chapters in this part

**For This Book**:
- Part I: Grundlagen der Durable Execution (Chapters 1-3)
- Part II: Entwicklung von Temporal-Anwendungen (Chapters 4-6)
- Part III: Resilienz, Evolution und Muster (Chapters 7-9)
- Part IV: Betrieb, Skalierung und Best Practices (Chapters 10-13)
- Part V: Das Temporal Kochbuch (Chapters 14-15)

**Relationships**:
- Contains multiple Chapter Files
- Appears as section header in Book Structure
- Used to organize Image Assets in subdirectories

**Validation Rules**:
- Must have at least one chapter
- Part titles should be unique
- Parts appear in SUMMARY.md as `# Part Title` (markdown heading without link)

---

## Entity: Image Asset

**Represents**: Static image files (diagrams, screenshots, illustrations)

**Location**: `src/images/`

**Attributes**:
- `filename` (string): Image file name
- `format` (string): File extension (png, jpg, svg, etc.)
- `part` (integer, optional): Associated part number
- `path` (string): Full path from src/ root

**Directory Structure**:
```
src/images/
├── part-01/
│   ├── temporal-architecture.png
│   └── workflow-lifecycle.svg
├── part-02/
│   └── sdk-structure.png
├── shared/
│   └── temporal-logo.png
└── (other parts...)
```

**Relationships**:
- Referenced by Chapter Files via markdown image syntax
- Organized by Part for easy management
- Shared images stored in `images/shared/`

**Validation Rules**:
- Supported formats: png, jpg, jpeg, svg, gif
- File paths in markdown must match actual file locations
- Image alt text should be descriptive

**Reference Syntax** (from chapter files):
```markdown
![Alt text](images/part-01/diagram.png)
```

---

## Entity: Example Project

**Represents**: Executable Python code examples demonstrating Temporal concepts

**Location**: `part-*/examples/chapter-NN/` (outside `src/` directory)

**Attributes**:
- `directory` (string): Path to example project
- `chapter_number` (integer): Associated chapter
- `dependencies` (array): Python packages (in pyproject.toml)

**Structure**:
```
examples/
└── part-01/
    └── chapter-01/
        ├── pyproject.toml
        ├── .python-version
        └── *.py
```

**Relationships**:
- Associated with specific Chapter Files
- Referenced in chapters with instructions to run
- Independent of mdBook build (not included in site)

**Validation Rules**:
- Each example must have `pyproject.toml` with dependencies
- Must specify Python version in `.python-version`
- Should be runnable with `uv sync && uv run python <file>.py`

**Integration**:
- Examples remain in current location (outside `src/`)
- Chapters provide clear instructions on navigating to and running examples
- Not part of mdBook build output (documentation only)

---

## Entity: Generated Output

**Represents**: The built static website

**Location**: `book/` (gitignored)

**Attributes**:
- HTML files (one per chapter)
- CSS stylesheets
- JavaScript for navigation/search
- Copied assets (images)

**Generation**:
- Created by `mdbook build` command
- Structure mirrors source organization
- URL mapping: `src/part-01-chapter-01.md` → `book/part-01-chapter-01.html`

**Relationships**:
- Generated from Book Configuration, Book Structure, and Chapter Files
- Deployed to GitHub Pages
- Regenerated on each build (ephemeral)

**Validation Rules**:
- Directory must be gitignored
- Never manually edited
- All links should resolve correctly in generated output

---

## State Transitions

### Migration States

1. **Pre-Migration**: Current structure with `part-*/chapter-*.md`
2. **Initialized**: `mdbook init` creates `book.toml` and `src/` directory
3. **Content Moved**: Chapter files copied to `src/` with new naming
4. **Assets Consolidated**: Images moved to `src/images/`
5. **Structure Defined**: `SUMMARY.md` created linking all chapters
6. **Validated**: `mdbook build` succeeds, all links work
7. **Deployed**: GitHub Actions workflow publishes to Pages

### Build States

1. **Source Updated**: Chapter or config file modified
2. **Build Triggered**: Manual `mdbook build` or GitHub Actions
3. **Processing**: mdBook parses markdown, generates HTML
4. **Output Generated**: `book/` directory populated
5. **Deployed**: (CI/CD only) Uploaded to GitHub Pages

---

## Relationships Diagram

```
Book Configuration (book.toml)
    ↓ configures
Book Structure (SUMMARY.md)
    ↓ references
Chapter Files (src/*.md)
    ↓ reference
Image Assets (src/images/*)

Example Projects (part-*/examples/*)
    ↑ referenced by
Chapter Files

Generated Output (book/*)
    ↑ built from
All Source Entities
```

---

## Summary

The mdBook data model centers on:
1. **Configuration** defining book metadata
2. **Structure** (SUMMARY.md) organizing content hierarchically
3. **Chapter Files** containing markdown content
4. **Image Assets** providing visual elements
5. **Example Projects** offering hands-on code (external to book)
6. **Generated Output** as the final deliverable

All entities work together to produce a navigable static website while preserving existing executable examples in their current locations.
