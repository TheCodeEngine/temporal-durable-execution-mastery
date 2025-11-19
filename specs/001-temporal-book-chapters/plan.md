# Implementation Plan: Temporal Book Chapter Structure with Python Examples

**Branch**: `001-temporal-book-chapters` | **Date**: 2025-11-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-temporal-book-chapters/spec.md`

## Summary

This plan implements a comprehensive book project structure for a Temporal.io educational book in German. The project creates a hybrid directory organization where 5 major parts (Teil I-V) serve as top-level directories, each containing chapter markdown files and a centralized examples directory for Python code samples. All examples use Python 3.13 with uv package manager and the Temporal Python SDK. A central `shared/` directory at the root provides reusable utilities. The structure supports Mermaid diagrams for visualizations and is designed for eventual compilation into an interactive book using a static site generator.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**:
- temporalio (Temporal Python SDK)
- uv (package manager)
- Mermaid (diagram syntax, renderer-dependent)

**Storage**: File-based (Markdown files, Python scripts, version-controlled via Git)
**Testing**: Manual execution verification of Python examples (pytest for future automation out of scope)
**Target Platform**: Cross-platform development environment (macOS/Linux/Windows with Python 3.13)
**Project Type**: Documentation/book project with integrated code examples
**Performance Goals**:
- Chapter structure generation: <10 minutes total
- Individual example setup (uv sync): <2 minutes per chapter
- Static site build time: <5 minutes (renderer-dependent)

**Constraints**:
- All examples must run independently (no inter-chapter dependencies)
- Examples may import from central `shared/` directory
- Mermaid diagrams must render in at least 2 viewers (GitHub, VS Code, static site generators)
- Markdown compatibility with common static site generators (MkDocs, Docusaurus, mdBook)

**Scale/Scope**:
- 5 parts (Teil I-V)
- ~15 chapters total across all parts
- ~12+ working Python examples (80% of chapters minimum)
- ~20+ Mermaid diagrams for visualizations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ⚠️ No project-specific constitution defined

The `.specify/memory/constitution.md` file contains only template placeholders. This book/documentation project does not require the typical software development constitution (library-first, TDD, etc.) as it's primarily content creation with supporting code examples.

**Recommended Principles for This Project**:
1. **Content-First**: Markdown content is the primary deliverable; examples support understanding
2. **Progressive Complexity**: Examples build from simple to advanced following book structure
3. **Runnable Code**: All examples must execute successfully without errors
4. **Self-Contained Chapters**: Each chapter's examples run independently (with shared utilities allowed)
5. **Documentation Quality**: Code examples follow Python best practices (type hints, docstrings)

**Constitution Compliance**: ✅ PASS (project-appropriate principles applied)

## Project Structure

### Documentation (this feature)

```text
specs/001-temporal-book-chapters/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (content structure model)
├── quickstart.md        # Phase 1 output (getting started guide)
├── contracts/           # Phase 1 output (structure contracts/schemas)
└── checklists/          # Quality validation checklists
    └── requirements.md
```

### Book Content Structure (repository root)

Based on the hybrid organization clarified in the spec:

```text
temporal-book/
├── README.md                          # Book overview, navigation, setup
├── .gitignore                         # Python/uv ignores
├── shared/                            # Central utilities directory
│   ├── __init__.py
│   ├── temporal_helpers.py            # Common Temporal client setup
│   └── examples_common.py             # Shared example utilities
│
├── part-i-grundlagen/                 # Part I: Grundlagen
│   ├── chapter-01.md                  # Einführung in Temporal
│   ├── chapter-02.md                  # Kernbausteine
│   ├── chapter-03.md                  # Architektur des Temporal Service
│   ├── examples/
│   │   ├── chapter-01/
│   │   │   ├── pyproject.toml
│   │   │   ├── .python-version        # Contains "3.13"
│   │   │   ├── README.md
│   │   │   └── simple_workflow.py
│   │   ├── chapter-02/
│   │   │   ├── pyproject.toml
│   │   │   ├── .python-version
│   │   │   ├── README.md
│   │   │   ├── workflow.py
│   │   │   ├── activities.py
│   │   │   └── worker.py
│   │   └── chapter-03/
│   │       └── [similar structure]
│   └── assets/                        # Part-level shared images
│
├── part-ii-sdk-fokus/                 # Part II: SDK Development
│   ├── chapter-04.md                  # Entwicklungs-Setup
│   ├── chapter-05.md                  # Workflows programmieren
│   ├── chapter-06.md                  # Kommunikation (Signals/Queries)
│   ├── examples/
│   │   ├── chapter-04/
│   │   ├── chapter-05/
│   │   └── chapter-06/
│   └── assets/
│
├── part-iii-resilienz/                # Part III: Resilienz, Evolution, Muster
│   ├── chapter-07.md                  # Fehlerbehandlung und Retries
│   ├── chapter-08.md                  # SAGA Pattern
│   ├── chapter-09.md                  # Workflow-Evolution und Versionierung
│   ├── examples/
│   │   ├── chapter-07/
│   │   ├── chapter-08/
│   │   └── chapter-09/
│   └── assets/
│
├── part-iv-betrieb/                   # Part IV: Betrieb, Skalierung, Best Practices
│   ├── chapter-10.md                  # Produktions-Deployment
│   ├── chapter-11.md                  # Skalierung der Worker
│   ├── chapter-12.md                  # Observability und Monitoring
│   ├── chapter-13.md                  # Best Practices und Anti-Muster
│   ├── examples/
│   │   ├── chapter-10/
│   │   ├── chapter-11/
│   │   ├── chapter-12/
│   │   └── chapter-13/
│   └── assets/
│
└── part-v-kochbuch/                   # Part V: Das Temporal Kochbuch
    ├── chapter-14.md                  # Muster-Rezepte (Human-in-Loop, Cron, etc.)
    ├── chapter-15.md                  # Erweiterte Rezepte (AI Agents, Lambda, Polyglot)
    ├── examples/
    │   ├── chapter-14/
    │   │   ├── pyproject.toml
    │   │   ├── .python-version
    │   │   ├── README.md
    │   │   ├── human_in_loop.py
    │   │   ├── cron_workflow.py
    │   │   ├── order_fulfillment.py
    │   │   └── infrastructure_provisioning.py
    │   └── chapter-15/
    │       ├── pyproject.toml
    │       ├── .python-version
    │       ├── README.md
    │       ├── ai_agent.py
    │       ├── lambda_orchestration.py
    │       └── polyglot_workers.py
    └── assets/
```

**Structure Decision**: Hybrid organization selected based on clarification session. This structure:
- Groups related chapters under part directories for logical organization
- Keeps chapter markdown files at the part level for easy access and editing
- Centralizes examples in a single `examples/` directory per part, with subdirectories per chapter
- Provides a `shared/` directory at root for common utilities that all examples can import
- Maintains clear separation between content (markdown) and code (examples)
- Supports both human navigation (clear hierarchy) and automated processing (predictable paths)

## Complexity Tracking

No constitution violations to justify. This is a documentation/educational project rather than a traditional software application, so standard software development constitution principles (library-first, strict TDD, etc.) do not apply. The project follows content-first principles with supporting executable examples.

## Phase 0: Research & Technology Decisions

### Technology Selection Rationale

#### 1. Python 3.13 as Standard Version

**Decision**: Standardize all examples on Python 3.13

**Rationale**:
- Latest stable Python release (October 2024) with performance improvements
- Full support for modern Python features (type hints, pattern matching, async/await)
- Excellent Temporal Python SDK compatibility
- Future-proof choice for a book that will be used for years
- uv package manager has excellent Python 3.13 support

**Alternatives Considered**:
- Python 3.11: More widely adopted but lacks latest features and performance improvements
- Python 3.12: Good middle ground but 3.13 is already stable and available
- Mixed versions: Rejected due to complexity and inconsistency

#### 2. uv Package Manager

**Decision**: Use uv for all Python dependency management

**Rationale**:
- Significantly faster than pip/poetry (10-100x speed improvements)
- Built-in virtual environment management
- Excellent reproducibility with lockfiles
- Simple, modern CLI interface ideal for beginners
- Works seamlessly with `pyproject.toml` standard
- Supports `.python-version` files for version specification

**Alternatives Considered**:
- pip + venv: Standard but slower, requires manual venv management
- poetry: Feature-rich but slower and more complex than needed
- pipenv: Falling out of favor, slower than uv

#### 3. Markdown + Mermaid for Content

**Decision**: Pure Markdown with Mermaid diagram syntax

**Rationale**:
- Universal format supported by all static site generators
- Mermaid renders in GitHub, VS Code, and major SSG tools
- Text-based version control friendly
- No proprietary formats or external diagram tools needed
- Diagrams-as-code keeps everything in one place

**Alternatives Considered**:
- AsciiDoc: More powerful but less widely supported
- reStructuredText: Python ecosystem standard but more complex syntax
- External diagram tools (draw.io, Lucidchart): Harder to version control, not code-based

#### 4. Hybrid Directory Structure

**Decision**: Parts as directories, chapters and examples within

**Rationale**:
- Balances logical grouping (parts) with flat access to chapters
- Examples consolidated per part reduces duplication
- Clear navigation: `part-i-grundlagen/chapter-01.md` is self-documenting
- Supports both human browsing and programmatic processing
- Assets can be shared at part level reducing redundancy

**Alternatives Considered**:
- Flat structure: All chapters at root → loses part organization, harder to navigate
- Fully nested: chapters as subdirectories → extra navigation depth, markdown files buried
- No parts: Just chapters → loses pedagogical structure from book outline

#### 5. Central Shared Utilities

**Decision**: Root-level `shared/` directory for common code

**Rationale**:
- DRY principle: Temporal client setup code written once
- Easier maintenance: Fix bugs in one place
- Consistent patterns: All examples use same connection logic
- Clear dependency: Examples explicitly import from `shared/`
- Educational value: Shows proper code organization

**Alternatives Considered**:
- Code duplication per chapter: Educational but unmaintainable, inconsistent
- Progressive dependencies (chapters import from earlier chapters): Confusing navigation, breaks independence
- No shared code: Forces complex examples to be self-contained → too verbose

### Static Site Generator Recommendations

**For German-language technical book with code examples:**

1. **MkDocs with Material theme** (RECOMMENDED)
   - Excellent Mermaid support via plugin
   - Beautiful responsive design
   - Built-in search and navigation
   - Python-based (aligns with book topic)
   - Great multilingual support

2. **Docusaurus** (Alternative)
   - React-based, very polished
   - Native Mermaid support
   - Versioning built-in
   - Interactive components possible

3. **mdBook** (Alternative)
   - Rust-based, very fast
   - Simple, book-focused design
   - Good Mermaid support
   - Less feature-rich but lightweight

**Configuration Notes**: All three support the hybrid structure and can generate navigation from directory hierarchy.

## Phase 1: Design & Contracts

### Content Model (data-model.md)

See [data-model.md](./data-model.md) for detailed entity definitions.

**Core Entities**:
- Book (root container)
- Part (5 total, organizing chapters)
- Chapter (15+ total, containing content and examples)
- Example (Python code demonstrating concepts)
- Diagram (Mermaid visualizations)
- SharedUtility (reusable code in `shared/`)

### Directory Structure Contract (contracts/)

See [contracts/](./contracts/) for formal structure schemas.

**Contracts Define**:
- Required files per chapter (`chapter-XX.md`, `examples/chapter-XX/pyproject.toml`, `.python-version`)
- Naming conventions (part-{roman}-{name}, chapter-{number}.md)
- Python project structure (pyproject.toml contents, dependencies)
- Shared utilities interface (exported functions/classes)

### Getting Started Guide (quickstart.md)

See [quickstart.md](./quickstart.md) for complete setup instructions.

**Covers**:
- Prerequisites (Python 3.13, uv, Git, Temporal CLI/Docker)
- Initial project setup
- Running first example
- Adding new chapters/examples
- Using shared utilities
- Building the interactive book

## Implementation Phases

### Phase 2: Task Breakdown (executed by /speckit.tasks)

The `/speckit.tasks` command will generate `tasks.md` with dependency-ordered implementation tasks:

**Expected Task Categories**:
1. Repository setup (README, .gitignore, shared/)
2. Part directory creation (5 parts)
3. Chapter markdown file scaffolding (~15 chapters)
4. Example directory structure with uv initialization (~12+ example projects)
5. Shared utilities implementation (temporal_helpers.py, examples_common.py)
6. Documentation (quickstart guide, contribution guide)
7. Sample content and examples (at least 1 complete chapter)
8. Validation (structure verification, example execution tests)

### Phase 3: Implementation (executed by /speckit.implement)

The `/speckit.implement` command will execute tasks from `tasks.md`:
- Create all directories and scaffold files
- Initialize Python projects with uv
- Generate template markdown files
- Implement shared utilities
- Create sample examples for early chapters

## Success Metrics

From the specification success criteria:

- ✅ **SC-001**: All 15+ chapters have folder structures with markdown and examples directories
- ✅ **SC-002**: Each chapter's examples initialize via `uv sync` in <2 minutes
- ✅ **SC-003**: Mermaid diagrams render in GitHub + VS Code + static site generator
- ✅ **SC-004**: Navigation from README to any chapter in ≤3 clicks
- ✅ **SC-005**: 80%+ of chapters have working Python examples
- ✅ **SC-006**: Complete structure generation in <10 minutes
- ✅ **SC-007**: Example code follows Python best practices (type hints, docstrings)

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Python 3.13 not widely adopted yet | Medium | Document fallback to 3.12; uv handles version switching easily |
| Temporal SDK breaking changes | Medium | Pin SDK version in shared dependencies; document in quickstart |
| Static site generator incompatibility | Low | Structure is SSG-agnostic; test with multiple generators |
| Example complexity creep | Medium | Strict scope per chapter; progressive complexity enforced in review |
| Mermaid rendering differences | Low | Use conservative Mermaid syntax; test in target platforms |
| Shared utilities coupling | Low | Keep shared/ minimal; document clear interfaces |

## Next Steps

1. ✅ **Review this plan** - Validate technical decisions and structure
2. ⏭️ **Generate tasks** - Run `/speckit.tasks` to create dependency-ordered implementation tasks
3. ⏭️ **Implement structure** - Run `/speckit.implement` to execute tasks and create the book skeleton
4. ⏭️ **Begin content creation** - Start writing chapter content and examples using the scaffolded structure

---

**Phase 0 Complete**: Research and technology decisions documented
**Phase 1 Status**: Proceeding to detailed design artifacts generation

