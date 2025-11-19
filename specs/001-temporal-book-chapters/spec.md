# Feature Specification: Temporal Book Chapter Structure with Python Examples

**Feature Branch**: `001-temporal-book-chapters`
**Created**: 2025-11-19
**Status**: Draft
**Input**: User description: "ich will ein Buch schreiben über Temporal auch, damit ich es besser einsetzen kann und mehr lerne. Ich habe unter @reports/ schonmal ein paar Grundlegende Reports und auch eine Buchsturktur implementiert. Das sind nur erste ANhaltspunkte keine fertigen sachen. Was ich jetzt gerne generieren würde wäre für jedes Kapitel eine Order auch damit ich dort die Beispiele (in python) mit reinbringen kann (uv als package manager) damit das Buch nciht nur aus THeorie sondern am ende auch aus guten Beispielen besteht. Ich würde gerne das das Buch aus Markdown Dateien besteht so das ich am ende ein interaktives Buch generieren kann. Nehme auch mermaid für die visualisierungen."

## Clarifications

### Session 2025-11-19

- Q: The chapter structure needs to organize content and examples. Should chapters be nested under part directories, or should they use a flat structure with clear naming? → A: Hybrid - Parts as directories for organization, but all markdown files at part level with examples as subdirectories
- Q: The specification mentions shared utilities but doesn't clarify the dependency strategy. How should chapters handle shared code? → A: Central utilities - All shared code in a root-level shared/ or lib/ directory that all chapters can import
- Q: The specification mentions Python 3.11+ but doesn't specify which exact version should be standardized across all chapter examples. What Python version should be specified in `.python-version` files? → A: 3.13 als version

## User Scenarios & Testing

### User Story 1 - Structured Chapter Organization with Example Code (Priority: P1)

As an author writing a Temporal book, I need a well-organized folder structure where each chapter has its own directory containing both the markdown content and working Python examples, so that I can write theory alongside practical, runnable code examples that readers can execute and learn from.

**Why this priority**: This is the foundation of the entire book project. Without a proper chapter structure, neither content development nor example code can be organized effectively. This enables immediate value delivery - the author can start writing and coding right away.

**Independent Test**: Can be fully tested by creating the chapter folder structure, adding a sample markdown file to one chapter, and running a Python example using uv as the package manager. Success means the structure is navigable and examples are executable.

**Acceptance Scenarios**:

1. **Given** the project repository, **When** the chapter structure is created, **Then** each chapter from the book outline has a corresponding directory with subdirectories for content and examples
2. **Given** a chapter directory, **When** I navigate to the examples folder, **Then** I find a Python project initialized with uv that can run Temporal workflow examples
3. **Given** a chapter's example code, **When** I run `uv run python <example_file>.py`, **Then** the example executes successfully and demonstrates the chapter's concepts
4. **Given** the chapter structure, **When** I view the directory tree, **Then** I can easily locate any chapter's content or examples by its number and name

---

### User Story 2 - Interactive Markdown Content with Mermaid Diagrams (Priority: P2)

As an author, I need to write chapter content in Markdown format with support for Mermaid diagrams, so that I can create an interactive, visually rich book that can be rendered in various formats (web, PDF, etc.) and helps readers understand complex Temporal concepts through visual representations.

**Why this priority**: Quality content presentation is crucial for reader comprehension. Mermaid diagrams significantly enhance understanding of distributed systems concepts, workflow patterns, and architecture. This comes after P1 because you need the structure first before populating it with content.

**Independent Test**: Can be tested by creating a markdown file with Mermaid diagrams in one chapter and verifying it renders correctly in a markdown viewer or static site generator. Success means diagrams render properly and markdown is valid.

**Acceptance Scenarios**:

1. **Given** a chapter markdown file, **When** I include a Mermaid diagram definition, **Then** the diagram renders correctly when viewed in a markdown-compatible viewer
2. **Given** chapter content, **When** I write about Temporal workflows, **Then** I can embed sequence diagrams, state diagrams, and flowcharts using Mermaid syntax
3. **Given** the complete markdown files, **When** processed by a static site generator, **Then** all content and diagrams render as an interactive book

---

### User Story 3 - Python Example Integration with uv Package Manager (Priority: P1)

As an author, I need each chapter's Python examples to be managed with uv package manager, so that readers can easily set up dependencies, run examples in isolated environments, and have a consistent, modern Python development experience across all chapters.

**Why this priority**: This is equally critical as P1 because examples that don't run frustrate readers and undermine the book's value. Modern tooling (uv) ensures fast setup and reproducibility, which is essential for a technical book.

**Independent Test**: Can be tested by navigating to any chapter's examples directory, running `uv sync` to install dependencies, and executing example scripts. Success means examples run without errors and demonstrate Temporal concepts clearly.

**Acceptance Scenarios**:

1. **Given** a chapter's examples directory, **When** I run `uv init` or find an existing `pyproject.toml`, **Then** the Python project is properly configured with Temporal SDK dependencies
2. **Given** a configured Python project, **When** I run `uv sync`, **Then** all dependencies including the Temporal Python SDK are installed in an isolated environment
3. **Given** installed dependencies, **When** I execute `uv run python examples/<workflow_example>.py`, **Then** the Temporal workflow executes and demonstrates the chapter's concepts
4. **Given** multiple chapters with examples, **When** each uses uv, **Then** dependencies are isolated per chapter and there are no version conflicts

---

### User Story 4 - Complete Book Structure Based on Outline (Priority: P2)

As an author, I need the folder structure to reflect the complete book outline from the reports (Teil I-V with all chapters), so that I have a comprehensive skeleton to guide my writing and ensure I cover all planned topics systematically.

**Why this priority**: While important for completeness, this is P2 because you can start writing and creating examples with a subset of chapters. The full structure can be generated upfront, but work can proceed incrementally.

**Independent Test**: Can be tested by comparing the generated folder structure against the book outline from the reports and verifying all parts and chapters are represented. Success means the structure matches the outline 1:1.

**Acceptance Scenarios**:

1. **Given** the book outline with 5 parts (Teil I-V), **When** the structure is generated, **Then** each part is represented with all its chapters
2. **Given** the chapter structure, **When** I review the hierarchy, **Then** chapters are organized by part and numbered sequentially
3. **Given** all chapters, **When** I navigate the structure, **Then** I can find chapters ranging from "Einführung in Temporal" through "Erweiterte und sprachspezifische Rezepte"

---

### Edge Cases

- What happens when a chapter needs multiple example files (e.g., workflow, activity, worker)?
  - Solution: Each chapter's examples directory can contain multiple Python files, organized by concept

- How does the system handle chapters that are purely theoretical with no code examples?
  - Solution: Include an examples directory anyway for consistency, but it may contain only minimal or skeleton code

- What happens when example code requires external services (like Temporal Server running locally)?
  - Solution: Include README files in each chapter's examples directory with setup instructions and prerequisites

- How does the system handle shared code or utilities needed across multiple chapters?
  - Solution: Create a `shared/` or `lib/` directory at the root level containing reusable utilities (e.g., common Temporal client setup, helper functions) that all chapter examples can import

- What happens when Mermaid diagrams become too complex for a single diagram?
  - Solution: Break complex diagrams into multiple smaller diagrams, each focusing on a specific aspect

## Requirements

### Functional Requirements

- **FR-001**: System MUST create a chapter folder structure that mirrors the book outline from the existing reports (5 parts, approximately 15 chapters)

- **FR-002**: Each part directory MUST contain:
  - Chapter markdown files at the part level (e.g., `part-i-grundlagen/chapter-01.md`)
  - An `examples/` subdirectory containing numbered example directories per chapter (e.g., `part-i-grundlagen/examples/chapter-01/`)
  - Optionally, an `assets/` subdirectory for shared part-level images or resources

- **FR-003**: Each chapter's examples directory MUST be initialized as a uv-managed Python project with:
  - A `pyproject.toml` file configured for the Temporal Python SDK
  - Appropriate dependencies including `temporalio` SDK
  - A `.python-version` file specifying Python 3.13

- **FR-004**: Chapter markdown files MUST support:
  - Standard markdown syntax for text formatting
  - Mermaid diagram syntax for visualizations (sequence diagrams, state diagrams, flowcharts)
  - Code blocks with syntax highlighting for Python

- **FR-005**: The folder structure MUST follow a clear naming convention:
  - Parts: `part-{roman-numeral}-{name}` (e.g., `part-i-grundlagen`) as top-level directories
  - Chapter markdown files: `chapter-{number}.md` or `chapter-{number}-{short-name}.md` within part directories
  - Example directories: `examples/chapter-{number}/` within each part directory

- **FR-006**: Each chapter's Python examples MUST be independently runnable without requiring code from other chapter-specific examples, but MAY import from the central `shared/` utilities directory

- **FR-007**: The project root MUST include:
  - A main `README.md` with book overview and navigation
  - A `.gitignore` file appropriate for Python/uv projects
  - A `shared/` directory for reusable utilities and common code that all chapters can import
  - Optionally, a global `pyproject.toml` for shared dependencies or tooling

- **FR-008**: Examples MUST demonstrate Temporal concepts progressively:
  - Early chapters: Simple workflows and activities
  - Middle chapters: Signals, queries, timers, child workflows
  - Later chapters: Advanced patterns (SAGA, versioning, testing)

### Key Entities

- **Book**: The top-level container representing the entire Temporal book, organized into parts and chapters

- **Part**: A major section of the book (5 total: Grundlagen, SDK-Fokus, Resilienz/Evolution/Muster, Betrieb/Skalierung, Kochbuch), containing multiple related chapters

- **Chapter**: An individual chapter within a part, containing:
  - Theoretical content in Markdown
  - Practical Python examples
  - Mermaid visualizations
  - Key concepts and learning objectives

- **Example**: A runnable Python code sample demonstrating Temporal concepts, including:
  - Workflow definitions
  - Activity implementations
  - Worker setup
  - Client code to start/interact with workflows

- **Diagram**: A Mermaid visualization embedded in markdown, representing:
  - Workflow sequences
  - Architecture diagrams
  - State transitions
  - Component interactions

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 15+ chapters from the book outline have corresponding folder structures created with markdown files and examples directories

- **SC-002**: Each chapter's Python examples can be initialized and run successfully with `uv sync` and `uv run` commands, completing in under 2 minutes for setup

- **SC-003**: Markdown files with Mermaid diagrams render correctly in at least 2 different viewers (e.g., GitHub, VS Code markdown preview, or a static site generator)

- **SC-004**: The author can navigate from the root README to any chapter's content or examples in 3 clicks or less (clear hierarchical structure)

- **SC-005**: At least 80% of chapters include working Python examples that successfully demonstrate core Temporal concepts without errors

- **SC-006**: The complete book structure can be generated and examples initialized in under 10 minutes on a standard development machine

- **SC-007**: Example code follows Python best practices (type hints, docstrings, clear variable names) making it educational and production-quality

## Assumptions

- **A-001**: The book will be primarily consumed in digital format (web/interactive) rather than print, allowing for interactive diagrams and runnable code links

- **A-002**: Readers will have Python 3.13 installed and are comfortable with command-line tools for running examples

- **A-003**: Readers will run examples against a local Temporal server (using Docker or Temporal CLI) or Temporal Cloud

- **A-004**: The uv package manager is the preferred tooling as it provides faster dependency resolution and better developer experience than pip/poetry

- **A-005**: Mermaid is sufficient for all diagram needs; no custom diagram tools or image generation is required

- **A-006**: Chapter examples can share the same Temporal Python SDK version across all chapters (version specified in a common dependency or documented requirement)

- **A-007**: The interactive book will be generated using a static site generator that supports Markdown and Mermaid (e.g., MkDocs, Docusaurus, mdBook)

## Dependencies

- **D-001**: Python 3.13 must be available in the development environment (examples standardized on this version)

- **D-002**: uv package manager must be installed for dependency management

- **D-003**: Temporal Python SDK must be available via PyPI for installation in examples

- **D-004**: A markdown renderer that supports Mermaid diagrams (for preview and final book generation)

- **D-005**: Git must be available for version control of the book content

## Out of Scope

- **OS-001**: Automatic translation of content to other languages - the book is written in German

- **OS-002**: Hosting or deployment of the interactive book website - only structure and content generation

- **OS-003**: Examples in programming languages other than Python (the book focuses on Python SDK)

- **OS-004**: Video content or interactive code playgrounds embedded in the book

- **OS-005**: Automated testing infrastructure for all example code (though examples should be tested manually)

- **OS-006**: Integration with specific Learning Management Systems (LMS) or course platforms
