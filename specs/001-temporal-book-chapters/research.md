# Research & Technology Decisions

**Feature**: Temporal Book Chapter Structure with Python Examples
**Date**: 2025-11-19
**Status**: Complete

## Overview

This document consolidates research findings and technology decisions for the Temporal book project. All decisions support the goal of creating an educational, interactive book with working Python examples that readers can execute and learn from.

## Technology Decisions

### 1. Python Version: 3.13

**Decision**: Standardize all examples on Python 3.13

**Rationale**:
- **Latest Stable Release**: Python 3.13 (October 2024) provides cutting-edge features while being production-ready
- **Performance**: Significant improvements in JIT compilation and memory usage over 3.11/3.12
- **Modern Features**: Full support for enhanced type hints, pattern matching, improved error messages
- **Temporal SDK Compatibility**: Excellent support from temporalio SDK
- **Future-Proofing**: Book will remain relevant for 3-5 years; using latest version is strategic
- **uv Support**: Native support in uv package manager with `.python-version` files

**Alternatives Evaluated**:

| Version | Pros | Cons | Decision |
|---------|------|------|----------|
| Python 3.11 | Wide adoption, proven stability | Lacks newest features, slower than 3.13 | ❌ Rejected |
| Python 3.12 | Good middle ground, stable | Not latest, less performance gain | ❌ Rejected |
| Python 3.13 | Latest features, best performance | Newer, requires recent installation | ✅ **Selected** |
| Mixed versions | Flexibility per chapter | Inconsistent, confusing for readers | ❌ Rejected |

**Implementation Notes**:
- All chapter examples include `.python-version` file containing `3.13`
- Shared utilities target Python 3.13 features
- Quickstart guide documents Python 3.13 installation

---

### 2. Package Manager: uv

**Decision**: Use uv for all Python dependency management

**Rationale**:
- **Speed**: 10-100x faster than pip/poetry for dependency resolution and installation
- **Modern Tooling**: Built-in virtual environment management, lockfiles, version pinning
- **Developer Experience**: Simple CLI, excellent error messages, minimal configuration
- **Standards Compliant**: Uses standard `pyproject.toml`, compatible with PEP standards
- **Version Management**: Native support for `.python-version` files and Python version switching
- **Future Direction**: Gaining rapid adoption in Python community as pip/poetry replacement

**Alternatives Evaluated**:

| Tool | Pros | Cons | Decision |
|------|------|------|----------|
| pip + venv | Standard, universally known | Slow, manual venv management, no lockfiles | ❌ Rejected |
| poetry | Feature-rich, popular | Slower than uv, complex for beginners | ❌ Rejected |
| pipenv | Lockfiles, decent UX | Slow, losing community support | ❌ Rejected |
| uv | Fast, modern, simple | Newer tool, smaller ecosystem | ✅ **Selected** |

**Implementation Notes**:
- Each chapter's examples directory initialized with `uv init`
- Standard `pyproject.toml` format: `[project]` section with `temporalio` dependency
- Readers use `uv sync` to install dependencies (creates venv automatically)
- Readers use `uv run python <script>.py` to execute examples

---

### 3. Content Format: Markdown + Mermaid

**Decision**: Pure Markdown with embedded Mermaid diagrams

**Rationale**:
- **Universal Support**: Markdown supported by all static site generators, GitHub, VS Code
- **Version Control Friendly**: Text-based format diffs cleanly in Git
- **Mermaid Integration**: Diagrams-as-code rendered natively by GitHub, VS Code, MkDocs, Docusaurus
- **No External Tools**: No need for separate diagramming software or binary formats
- **Educational Value**: Readers can see and modify diagram source code
- **Interactive Rendering**: Mermaid diagrams are interactive in web formats (zoom, pan)

**Alternatives Evaluated**:

| Format | Pros | Cons | Decision |
|--------|------|------|----------|
| AsciiDoc | Powerful, semantic | Less tooling support, steeper learning curve | ❌ Rejected |
| reStructuredText | Python ecosystem standard | More complex syntax than Markdown | ❌ Rejected |
| Markdown + draw.io | Visual editor for diagrams | Binary files, harder to version control | ❌ Rejected |
| Markdown + Mermaid | Text-based, universal support | Limited diagram complexity | ✅ **Selected** |

**Mermaid Diagram Types Used**:
- **Sequence Diagrams**: Workflow execution flows, client-worker-server interactions
- **State Diagrams**: Workflow state transitions, lifecycle management
- **Flowcharts**: Decision trees, algorithm flows
- **Class Diagrams**: Entity relationships (if needed for advanced chapters)

**Implementation Notes**:
- Mermaid code blocks: ` ```mermaid ... ``` `
- Test rendering in: GitHub preview, VS Code Markdown Preview, target static site generator
- Conservative syntax (avoid cutting-edge Mermaid features for maximum compatibility)

---

### 4. Directory Structure: Hybrid Organization

**Decision**: Parts as top-level directories, chapters and examples within

**Rationale**:
- **Logical Grouping**: 5 parts (Teil I-V) provide pedagogical structure from book outline
- **Flat Access**: Chapter markdown files at part level (not nested further) for easy editing
- **Centralized Examples**: Single `examples/` directory per part contains all chapter examples
- **Reduced Duplication**: Assets shared at part level (diagrams, images used by multiple chapters)
- **Clear Navigation**: Path `part-i-grundlagen/chapter-01.md` is self-documenting
- **Tool-Friendly**: Predictable structure for scripts, static site generators

**Alternatives Evaluated**:

| Structure | Pros | Cons | Decision |
|-----------|------|------|----------|
| Flat (all chapters at root) | Simple, one level | Loses part organization, 15+ files at root | ❌ Rejected |
| Fully nested (chapters as subdirs) | Maximum organization | Markdown files buried deep, harder to browse | ❌ Rejected |
| No parts (just numbered chapters) | Simplest | Loses pedagogical grouping from outline | ❌ Rejected |
| Hybrid (parts→chapters→examples) | Balanced organization and access | Requires understanding of structure | ✅ **Selected** |

**Structure Schema**:
```
part-{roman-numeral}-{name}/
├── chapter-{number}.md          # Chapter content
├── chapter-{number}.md          # Additional chapters
├── examples/                    # All examples for this part
│   ├── chapter-{number}/        # Example for specific chapter
│   │   ├── pyproject.toml
│   │   ├── .python-version
│   │   ├── README.md
│   │   └── *.py                 # Python example files
│   └── chapter-{number}/        # More examples
└── assets/                      # Shared images/diagrams for part
```

**Implementation Notes**:
- Part names use Roman numerals (i, ii, iii, iv, v) in kebab-case
- Chapter numbers are zero-padded (01, 02, ... 15)
- Examples directory mirrors chapter structure

---

### 5. Code Sharing Strategy: Central Utilities

**Decision**: Root-level `shared/` directory for reusable code

**Rationale**:
- **DRY Principle**: Temporal client setup code written once, imported by all examples
- **Consistency**: All examples use identical connection/configuration patterns
- **Maintainability**: Bug fixes and improvements in one location
- **Educational**: Demonstrates proper Python project organization and imports
- **Explicit Dependencies**: Examples clearly show `from shared import ...`

**Alternatives Evaluated**:

| Strategy | Pros | Cons | Decision |
|----------|------|------|----------|
| Code duplication per chapter | Each chapter fully self-contained | Unmaintainable, inconsistent patterns | ❌ Rejected |
| Progressive (chapters import earlier ones) | Shows build-up of knowledge | Breaks independence, confusing paths | ❌ Rejected |
| No shared code (inline everything) | Maximum clarity per file | Verbose, repetitive, hides patterns | ❌ Rejected |
| Central shared/ directory | Maintainable, consistent, DRY | Adds import complexity | ✅ **Selected** |

**Shared Utilities Content**:
```python
shared/
├── __init__.py                  # Package marker
├── temporal_helpers.py          # Temporal client setup, connection utilities
└── examples_common.py           # Common example utilities (logging, CLI args)
```

**Example Utilities**:
- `create_temporal_client()`: Standard Temporal client connection
- `setup_logging()`: Consistent logging configuration
- `parse_example_args()`: CLI argument parsing for examples
- `run_worker()`: Worker setup boilerplate

**Implementation Notes**:
- Shared directory is a proper Python package (has `__init__.py`)
- Examples add `shared/` to PYTHONPATH or use relative imports
- Shared utilities include type hints and comprehensive docstrings

---

## Static Site Generator Recommendation

**For German-language technical book with Python examples and Mermaid diagrams:**

### Recommended: MkDocs with Material Theme

**Rationale**:
- **Python Ecosystem**: Built with Python, aligns with book topic (Temporal Python SDK)
- **Material Theme**: Beautiful, responsive design with excellent UX
- **Mermaid Support**: Via `mkdocs-mermaid2-plugin` - native, high-quality rendering
- **Search**: Built-in client-side search (no backend required)
- **Navigation**: Auto-generates navigation from directory structure
- **Code Highlighting**: Excellent Python syntax highlighting
- **Multilingual**: Strong i18n support (though book is German-only)
- **Active Development**: Large community, frequent updates

**Configuration**:
```yaml
# mkdocs.yml
site_name: Temporal.io - Durable Execution Mastery
theme:
  name: material
  language: de
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
plugins:
  - search:
      lang: de
  - mermaid2
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:mermaid2.fence_mermaid
```

**Alternatives**:

| Generator | Pros | Cons | Decision |
|-----------|------|------|----------|
| Docusaurus | Very polished, React-based | JavaScript/Node ecosystem, less Python-aligned | ⭐ Alternative |
| mdBook | Fast (Rust), simple | Less feature-rich, smaller plugin ecosystem | ⭐ Alternative |
| MkDocs + Material | Python ecosystem, excellent features | Requires plugin for Mermaid | ✅ **Recommended** |

---

## Temporal Python SDK Integration

**SDK**: `temporalio` (official Temporal Python SDK)

**Version Strategy**: Pin to a stable recent version in shared dependencies

**Example**:
```toml
# shared/pyproject.toml or in each chapter's pyproject.toml
[project]
dependencies = [
    "temporalio>=1.5.0,<2.0.0",  # Pin major version, allow minor updates
]
```

**Key SDK Features Used**:
- **Workflows**: `@workflow.defn`, `workflow.run()`, `workflow.execute_activity()`
- **Activities**: `@activity.defn`, activity options (timeouts, retries)
- **Workers**: `Worker()` with workflow and activity registration
- **Clients**: `Client.connect()`, `client.start_workflow()`, `client.get_workflow_handle()`
- **Signals/Queries**: `@workflow.signal`, `@workflow.query`, `workflow.wait_condition()`
- **Advanced**: Child workflows, continue-as-new, versioning

**Temporal Server Requirements**:
- **Local Development**: Temporal CLI (`temporal server start-dev`) or Docker Compose
- **Cloud**: Temporal Cloud connection (documented in quickstart)
- Examples include connection strings for both local and cloud

---

## Research Findings Summary

| Decision Area | Selected Technology | Key Benefit |
|---------------|-------------------|-------------|
| Python Version | 3.13 | Latest features, best performance |
| Package Manager | uv | 10-100x faster, modern tooling |
| Content Format | Markdown + Mermaid | Universal support, version-control friendly |
| Directory Structure | Hybrid (parts/chapters/examples) | Balanced organization and accessibility |
| Code Sharing | Central `shared/` directory | DRY, consistency, maintainability |
| Static Site Generator | MkDocs + Material (recommended) | Python-aligned, beautiful, feature-rich |

---

## Implementation Impact

### Developer Experience
- **Fast Setup**: `uv sync` installs dependencies in seconds
- **Clear Structure**: Intuitive navigation, predictable file locations
- **Reusable Code**: Shared utilities reduce boilerplate
- **Quality Tooling**: Modern Python ecosystem practices

### Reader Experience
- **Runnable Examples**: All examples execute successfully on first try
- **Visual Learning**: Mermaid diagrams enhance comprehension
- **Progressive Complexity**: Examples build on concepts chapter by chapter
- **Interactive Book**: Web-based format with search, navigation, code highlighting

### Maintenance
- **Version Control**: Text-based formats diff cleanly
- **Consistency**: Central utilities ensure uniform patterns
- **Scalability**: Structure supports adding more chapters/parts easily
- **Updates**: Pin SDK version, update once in shared dependencies

---

**Status**: All research complete, ready for Phase 1 design artifacts
**Next**: Generate data-model.md, contracts/, and quickstart.md
