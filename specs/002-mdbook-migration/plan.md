# Implementation Plan: mdBook Migration

**Branch**: `002-mdbook-migration` | **Date**: 2025-11-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-mdbook-migration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Restructure the existing Temporal book content to use mdBook as the static site generator, enabling professional website generation and GitHub Pages deployment. The migration will preserve all existing markdown chapters, maintain the five-part structure (Grundlagen, SDK-Fokus, Resilienz, Betrieb, Kochbuch), keep example code executable in current locations, and set up automated deployment workflows.

## Technical Context

**Tool**: mdBook (Rust-based static site generator)
**Content Format**: Markdown (existing .md files)
**Build Tool**: mdBook CLI (`mdbook build`, `mdbook serve`)
**Deployment Target**: GitHub Pages (static HTML hosting)
**Source Language**: N/A (documentation project, not software)
**Content Language**: German (with proper UTF-8/umlaut support)
**Project Type**: Documentation/Book (static site generation)
**Existing Structure**: 5 parts, 15 chapters in `part-*/chapter-*.md` format
**Example Code**: Python 3.13 projects in `part-*/examples/` (preserved as-is)
**Performance Goals**: Build time <30 seconds, static site generation
**Constraints**: Must preserve all content, maintain navigability, support offline reading
**Scale/Scope**: 15 chapters, 5 parts, multiple code examples, assets/diagrams

**Key Decisions** (resolved in Phase 0):
- ✅ Directory structure: Flat layout in `src/` with `part-NN-chapter-NN.md` naming
- ✅ Asset handling: Centralized `src/images/` with part-based subdirectories
- ✅ Deployment: GitHub Actions with artifact-based Pages deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: N/A - Constitution template is unpopulated

The project constitution file (`.specify/memory/constitution.md`) contains only template placeholders and has not been ratified. This feature is a documentation tooling migration, not a software development feature, so traditional architectural principles (Library-First, CLI Interface, TDD) do not apply.

**Recommendation**: If the project adopts a constitution in the future, this migration should be reviewed to ensure documentation practices align with project standards.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**Current Structure** (before migration):
```text
temporal-book/
├── part-i-grundlagen/
│   ├── chapter-01.md
│   ├── chapter-02.md
│   ├── chapter-03.md
│   └── examples/
│       ├── chapter-01/
│       ├── chapter-02/
│       └── chapter-03/
├── part-ii-sdk-fokus/
│   ├── chapter-04.md
│   ├── chapter-05.md
│   ├── chapter-06.md
│   └── examples/
├── part-iii-resilienz/
│   ├── chapter-07.md
│   ├── chapter-08.md
│   ├── chapter-09.md
│   └── examples/
├── part-iv-betrieb/
│   ├── chapter-10.md
│   ├── chapter-11.md
│   ├── chapter-12.md
│   └── chapter-13.md
├── part-v-kochbuch/
│   ├── chapter-14.md (placeholder)
│   └── chapter-15.md (placeholder)
├── shared/                    # Common Python utilities
├── reports/                   # Research documents
└── README.md
```

**Target Structure** (after migration - determined by research):
```text
temporal-book/
├── book.toml                  # mdBook configuration
├── src/                       # mdBook source directory
│   ├── SUMMARY.md             # Book structure/TOC
│   └── [chapter organization - TBD in Phase 0]
├── book/                      # Generated output (gitignored)
├── part-*/                    # [Strategy TBD: keep or move into src/]
├── shared/                    # Preserved (Python utilities)
└── .github/
    └── workflows/
        └── deploy.yml         # GitHub Pages automation
```

**Structure Decision**: Flat organization in `src/` with descriptive filenames (e.g., `part-01-chapter-01.md`). Book hierarchy defined in SUMMARY.md. Images centralized in `src/images/` organized by part. See Phase 1 for complete structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution in place, no violations to track.
## Phase 0: Research & Decisions ✅

**Status**: Complete
**Output**: [research.md](./research.md)

### Research Completed

All technical unknowns have been resolved through comprehensive research:

1. **Directory Structure**: Flat structure in `src/` with descriptive filenames (e.g., `part-01-chapter-01.md`)
2. **Asset Handling**: Centralized `src/images/` directory with part-based subdirectories
3. **GitHub Actions**: Modern artifact-based deployment with `actions/deploy-pages@v4` and `peaceiris/actions-mdbook@v2`

### Key Decisions

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| Flat src/ structure | mdBook organizes via SUMMARY.md, not directories | Deep nesting adds no value |
| src/images/ for assets | mdBook standard, easy management | Co-located images create clutter |
| Artifact deployment | Official GitHub pattern, no branch bloat | gh-pages branch deprecated |

### Documentation

Complete research findings with references and examples available in [research.md](./research.md).

---

## Phase 1: Design Artifacts ✅

**Status**: Complete
**Outputs**: 
- [data-model.md](./data-model.md)
- [contracts/](./contracts/)
- [quickstart.md](./quickstart.md)

### Design Artifacts Created

1. **Data Model** ([data-model.md](./data-model.md)):
   - Book Configuration entity (book.toml)
   - Book Structure entity (SUMMARY.md)
   - Chapter File entity
   - Part entity (logical grouping)
   - Image Asset entity
   - Example Project entity
   - Generated Output entity
   - Entity relationships and state transitions

2. **Contracts** ([contracts/](./contracts/)):
   - `book.toml`: Complete mdBook configuration with German language support
   - `SUMMARY.md`: Table of contents structure for all 15 chapters
   - `deploy-mdbook.yml`: GitHub Actions workflow for automated deployment
   - `.gitignore-additions`: Build output exclusions

3. **Quickstart Guide** ([quickstart.md](./quickstart.md)):
   - Installation instructions (macOS/Linux)
   - 12-phase migration steps
   - Command reference
   - Verification checklist
   - Development workflow
   - Rollback plan

### Updated Target Structure

Based on research, final structure will be:

```text
temporal-book/
├── book.toml                       # NEW: mdBook config
├── src/                            # NEW: Book source
│   ├── SUMMARY.md                  # NEW: TOC
│   ├── README.md                   # Moved from root
│   ├── part-01-chapter-01.md       # Flat naming
│   ├── part-01-chapter-02.md
│   ├── ... (all 15 chapters)
│   └── images/                     # NEW: Assets
│       ├── part-01/
│       ├── part-02/
│       ├── part-03/
│       ├── part-04/
│       ├── part-05/
│       └── shared/
├── book/                           # NEW: Build output (gitignored)
├── examples/                       # PRESERVED: Python code
│   ├── part-01/
│   ├── part-02/
│   └── ...
├── shared/                         # PRESERVED: Python utilities
└── .github/
    └── workflows/
        └── deploy-mdbook.yml       # NEW: CI/CD
```

**Old structure** (`part-*/chapter-*.md`) can be archived or removed after successful migration verification.

---

## Phase 2: Implementation Tasks

**Status**: Ready for `/speckit.tasks`
**Output**: Will generate [tasks.md](./tasks.md)

### Task Categories

When `/speckit.tasks` is run, it will generate actionable tasks in these categories:

1. **Setup & Initialization**
   - Install mdBook
   - Initialize project structure
   - Configure book.toml

2. **Content Migration**
   - Move chapter files to src/
   - Consolidate images to src/images/
   - Update image references
   - Fix internal links

3. **Structure Configuration**
   - Create SUMMARY.md
   - Update .gitignore
   - Create resources.md (if needed)

4. **Validation**
   - Test local build
   - Verify chapter navigation
   - Check image display
   - Test all internal links

5. **Deployment Setup**
   - Create GitHub Actions workflow
   - Configure GitHub Pages
   - Test automated deployment

6. **Documentation Updates**
   - Update README.md
   - Add mdBook usage guide
   - Document migration changes

7. **Cleanup** (Optional)
   - Archive old part-* directories
   - Remove obsolete files
   - Update project documentation

### Prerequisites for Implementation

- [ ] Plan approved and reviewed
- [ ] mdBook installed locally for testing
- [ ] Backup created (via git branch)
- [ ] No uncommitted changes in working directory

### Estimated Effort

- **Manual Migration**: 1-2 hours
- **Automated Script**: 30 minutes (if scripted)
- **Testing & Validation**: 30 minutes
- **Total**: 2-3 hours

---

## Post-Design Constitution Check

**Status**: N/A - No constitution to validate against

If a constitution is established, review:
- Documentation structure standards
- Build/deploy practices
- Version control conventions
- Asset management policies

---

## Next Steps

1. **Review this plan**: Ensure all decisions align with project goals
2. **Run `/speckit.tasks`**: Generate actionable task breakdown
3. **Begin implementation**: Follow quickstart.md for migration steps
4. **Validate**: Use verification checklist in quickstart.md
5. **Deploy**: Merge to default branch and verify GitHub Pages deployment

---

## References

- **Feature Spec**: [spec.md](./spec.md) - User requirements and success criteria
- **Research**: [research.md](./research.md) - Technical decisions and alternatives
- **Data Model**: [data-model.md](./data-model.md) - Structure entities and relationships
- **Quickstart**: [quickstart.md](./quickstart.md) - Step-by-step migration guide
- **Contracts**: [contracts/](./contracts/) - Configuration files and templates

---

**Plan Status**: Complete ✅  
**Ready for**: `/speckit.tasks` (task generation)  
**Implementation**: Can begin immediately with quickstart.md
