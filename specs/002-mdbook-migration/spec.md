# Feature Specification: mdBook Migration

**Feature Branch**: `002-mdbook-migration`
**Created**: 2025-11-19
**Status**: Draft
**Input**: User description: "ich habe jetz mal einfahc angefangen mein Grundbuch zu bauen um es auch lesbar zu machen, allerdings fällt mir jetzt auch das es eher doof war, weil ich will schon sowas wie mdBook nutzen, damit ich es auch später auf github pages und so veröffentlichen kann. Baue alles so um das ich es mit mdBook nutzen kann, baue lieber die bestehende Struktur um und zwar alles als irgendwie ..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure mdBook Structure (Priority: P1)

As a book author, I need to restructure my existing Temporal book content to work with mdBook so that I can generate a professional static website that can be hosted on GitHub Pages.

**Why this priority**: This is the foundation for all other work. Without proper mdBook configuration and structure, the book cannot be built or published.

**Independent Test**: Can be fully tested by running `mdbook build` and verifying that it generates a `book/` directory with a navigable HTML site that correctly displays all chapters in the proper hierarchy.

**Acceptance Scenarios**:

1. **Given** the existing book structure with part-*/chapter-*.md files, **When** I initialize mdBook and configure SUMMARY.md, **Then** all chapters are organized hierarchically by parts with correct navigation
2. **Given** a configured mdBook project, **When** I run `mdbook build`, **Then** a static website is generated in the book/ directory without errors
3. **Given** the generated book output, **When** I open book/index.html in a browser, **Then** I see a table of contents sidebar with all parts and chapters properly nested

---

### User Story 2 - Migrate Content Files (Priority: P2)

As a book author, I need all existing markdown chapter files and their examples to be correctly referenced in the mdBook structure so that no content is lost during migration.

**Why this priority**: Content integrity is critical, but depends on having the basic structure (P1) in place first.

**Independent Test**: Can be tested by opening each chapter in the generated book and verifying that all content, code examples, and links render correctly.

**Acceptance Scenarios**:

1. **Given** existing chapter markdown files in part-* directories, **When** mdBook builds the site, **Then** all chapter content appears correctly formatted with no broken links
2. **Given** chapters with code examples in examples/ subdirectories, **When** viewing chapters in the book, **Then** code examples are properly linked and accessible
3. **Given** relative links between chapters in original markdown, **When** mdBook processes the files, **Then** all internal links work correctly in the generated site

---

### User Story 3 - Preserve Example Code Structure (Priority: P3)

As a reader, I need the executable Python examples to remain accessible and runnable from their current locations so that I can follow along with the book's practical exercises.

**Why this priority**: While important for learning, the examples can remain in their current location and be referenced from the book rather than requiring restructuring.

**Independent Test**: Can be tested by following the quickstart instructions in a chapter to run an example and verifying it executes successfully.

**Acceptance Scenarios**:

1. **Given** example code in part-i-grundlagen/examples/chapter-01/, **When** a reader follows the instructions in Chapter 1, **Then** they can execute the example using `uv run python simple_workflow.py`
2. **Given** the mdBook site, **When** viewing a chapter with examples, **Then** clear instructions are provided on how to navigate to and run the example code
3. **Given** shared utilities in the shared/ directory, **When** examples are executed, **Then** they correctly import and use the shared modules

---

### User Story 4 - GitHub Pages Deployment Setup (Priority: P4)

As a book author, I need GitHub Actions configuration to automatically build and deploy the mdBook site to GitHub Pages so that readers can access the published book online.

**Why this priority**: Publishing is the end goal, but it depends on all previous infrastructure being in place.

**Independent Test**: Can be tested by pushing to the repository and verifying that GitHub Actions successfully builds the book and deploys it to GitHub Pages with an accessible URL.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions workflow file, **When** code is pushed to the main branch, **Then** the workflow automatically builds the mdBook and deploys to GitHub Pages
2. **Given** a deployed GitHub Pages site, **When** accessing the site URL, **Then** the full book is accessible with working navigation and all content
3. **Given** updates to chapter content, **When** changes are pushed, **Then** the site is automatically rebuilt and updated within minutes

---

### Edge Cases

- What happens when chapter numbering changes (e.g., inserting a new chapter between existing ones)?
- How are assets (images, diagrams) referenced from both the source markdown and the generated book?
- What happens if SUMMARY.md structure conflicts with actual file structure?
- How are code blocks with syntax highlighting handled during the build?
- What happens when running `mdbook serve` locally for preview vs. building for production?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a `book.toml` configuration file in the project root with appropriate metadata (title, authors, language)
- **FR-002**: System MUST create a `src/` directory containing a `SUMMARY.md` file that defines the book structure with all parts and chapters
- **FR-003**: System MUST reorganize existing chapter files from `part-*/chapter-*.md` structure into a format compatible with mdBook's expectations
- **FR-004**: System MUST preserve all existing markdown content without data loss during migration
- **FR-005**: System MUST maintain the existing example code structure in `part-*/examples/` directories
- **FR-006**: System MUST ensure all relative links between chapters continue to work in the mdBook output
- **FR-007**: System MUST generate a navigable HTML site when running `mdbook build`
- **FR-008**: The generated book MUST support serving locally via `mdbook serve` for development preview
- **FR-009**: System MUST configure the book to be deployable to GitHub Pages
- **FR-010**: System MUST preserve existing assets (images, diagrams) in an accessible location with working references
- **FR-011**: The mdBook structure MUST support the five-part organization: Grundlagen, SDK-Fokus, Resilienz, Betrieb, and Kochbuch
- **FR-012**: README.md MUST be updated to include mdBook build and serve instructions
- **FR-013**: System MUST handle German language content correctly in the generated book

### Key Entities *(include if feature involves data)*

- **Book Structure**: Represents the hierarchical organization of parts and chapters, defined in SUMMARY.md with links to actual content files
- **Chapter File**: A markdown file containing book content, must be referenced in SUMMARY.md to appear in the book
- **Part**: A top-level section grouping related chapters (e.g., "Teil I: Grundlagen der Durable Execution")
- **Example Project**: An executable Python project in examples/ directories with pyproject.toml, demonstrating Temporal concepts
- **Configuration**: The book.toml file defining book metadata, output settings, and build options

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `mdbook build` completes without errors and generates a book/ directory with HTML output
- **SC-002**: The generated book contains all 15 chapters organized into 5 parts with correct hierarchical navigation
- **SC-003**: All internal links between chapters work correctly in the generated book (0% broken links)
- **SC-004**: Running `mdbook serve` allows local preview of the book at http://localhost:3000
- **SC-005**: The book can be built and deployed to GitHub Pages with a publicly accessible URL
- **SC-006**: All existing code examples remain executable from their original locations
- **SC-007**: The migration preserves 100% of existing markdown content without data loss

## Assumptions *(include if relevant)*

1. **mdBook is the chosen tool**: We assume mdBook is the appropriate static site generator for this Rust/systems programming adjacent book
2. **German language support**: We assume mdBook handles German umlauts and special characters correctly in output
3. **File organization flexibility**: We assume mdBook allows keeping example code in separate directories outside of src/
4. **GitHub Pages compatibility**: We assume the project will be hosted on GitHub and Pages is the deployment target
5. **Existing structure is mostly compatible**: The current part-*/chapter-*.md structure can be adapted to mdBook with SUMMARY.md without requiring complete file reorganization
6. **No content rewrites needed**: The existing markdown content is already in a format compatible with mdBook's parser

## Scope *(include if relevant)*

### In Scope

- Creating mdBook configuration (book.toml, SUMMARY.md)
- Organizing existing chapter files to work with mdBook
- Setting up build and serve workflows
- Configuring GitHub Pages deployment
- Updating README with mdBook instructions
- Preserving all existing content and examples

### Out of Scope

- Rewriting or editing chapter content
- Creating new chapters or sections
- Redesigning the book structure or reorganizing parts
- Adding mdBook themes or custom styling
- Setting up custom domains for GitHub Pages
- Creating CI/CD for automated testing of code examples
- Adding search functionality or other advanced mdBook plugins
