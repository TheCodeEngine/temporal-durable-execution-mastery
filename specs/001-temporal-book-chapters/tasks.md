# Tasks: Temporal Book Chapter Structure with Python Examples

**Input**: Design documents from `/specs/001-temporal-book-chapters/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are NOT requested for this documentation/book project. Manual validation will be performed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Book project**: Root contains parts, each part contains chapters and examples
- Shared utilities at root: `shared/`
- Parts: `part-{roman}-{name}/`
- Examples: `part-{roman}-{name}/examples/chapter-{number}/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create root .gitignore file with Python/uv patterns (*.pyc, __pycache__/, .venv/, *.egg-info/, .uv/)
- [ ] T002 [P] Create root README.md with book overview, table of contents, and navigation to all parts
- [ ] T003 [P] Create shared/ directory with __init__.py for package initialization
- [ ] T004 [P] Implement shared/temporal_helpers.py with create_temporal_client() and get_default_namespace() functions
- [ ] T005 [P] Implement shared/examples_common.py with setup_logging() and parse_common_args() utilities

**Checkpoint**: Basic project structure and shared utilities ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core part/chapter directory structure that MUST be complete before content and examples can be added

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create part-i-grundlagen/ directory with assets/ subdirectory
- [ ] T007 Create part-ii-sdk-fokus/ directory with assets/ subdirectory
- [ ] T008 Create part-iii-resilienz/ directory with assets/ subdirectory
- [ ] T009 Create part-iv-betrieb/ directory with assets/ subdirectory
- [ ] T010 Create part-v-kochbuch/ directory with assets/ subdirectory
- [ ] T011 Create part-i-grundlagen/examples/ directory for chapter examples
- [ ] T012 Create part-ii-sdk-fokus/examples/ directory for chapter examples
- [ ] T013 Create part-iii-resilienz/examples/ directory for chapter examples
- [ ] T014 Create part-iv-betrieb/examples/ directory for chapter examples
- [ ] T015 Create part-v-kochbuch/examples/ directory for chapter examples

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Structured Chapter Organization with Example Code (Priority: P1) 🎯 MVP

**Goal**: Create a well-organized folder structure where each chapter has its own directory containing both markdown content and working Python examples

**Independent Test**: Navigate to any chapter directory, verify markdown file exists and examples directory is initialized with uv. Run `cd part-i-grundlagen/examples/chapter-01 && uv sync && uv run python simple_workflow.py` and verify it executes successfully.

### Part I: Grundlagen (3 chapters)

- [ ] T016 [P] [US1] Create part-i-grundlagen/chapter-01.md placeholder for "Einführung in Temporal"
- [ ] T017 [P] [US1] Create part-i-grundlagen/chapter-02.md placeholder for "Kernbausteine: Workflows, Activities, Worker"
- [ ] T018 [P] [US1] Create part-i-grundlagen/chapter-03.md placeholder for "Architektur des Temporal Service"

- [ ] T019 [US1] Create part-i-grundlagen/examples/chapter-01/ directory
- [ ] T020 [US1] Create part-i-grundlagen/examples/chapter-01/.python-version file with content "3.13"
- [ ] T021 [US1] Create part-i-grundlagen/examples/chapter-01/pyproject.toml using template from contracts/ with temporalio>=1.5.0
- [ ] T022 [US1] Create part-i-grundlagen/examples/chapter-01/README.md with setup instructions and prerequisites
- [ ] T023 [P] [US1] Create part-i-grundlagen/examples/chapter-01/simple_workflow.py with basic Temporal workflow example

- [ ] T024 [US1] Create part-i-grundlagen/examples/chapter-02/ directory
- [ ] T025 [US1] Create part-i-grundlagen/examples/chapter-02/.python-version file with content "3.13"
- [ ] T026 [US1] Create part-i-grundlagen/examples/chapter-02/pyproject.toml using template
- [ ] T027 [US1] Create part-i-grundlagen/examples/chapter-02/README.md with setup instructions
- [ ] T028 [P] [US1] Create part-i-grundlagen/examples/chapter-02/workflow.py demonstrating workflow definition
- [ ] T029 [P] [US1] Create part-i-grundlagen/examples/chapter-02/activities.py demonstrating activity implementation
- [ ] T030 [P] [US1] Create part-i-grundlagen/examples/chapter-02/worker.py demonstrating worker setup

- [ ] T031 [US1] Create part-i-grundlagen/examples/chapter-03/ directory
- [ ] T032 [US1] Create part-i-grundlagen/examples/chapter-03/.python-version file with content "3.13"
- [ ] T033 [US1] Create part-i-grundlagen/examples/chapter-03/pyproject.toml using template
- [ ] T034 [US1] Create part-i-grundlagen/examples/chapter-03/README.md with setup instructions
- [ ] T035 [P] [US1] Create part-i-grundlagen/examples/chapter-03/service_interaction.py demonstrating Temporal service components

### Part II: SDK-Fokus (3 chapters)

- [ ] T036 [P] [US1] Create part-ii-sdk-fokus/chapter-04.md placeholder for "Entwicklungs-Setup und SDK-Auswahl"
- [ ] T037 [P] [US1] Create part-ii-sdk-fokus/chapter-05.md placeholder for "Workflows programmieren"
- [ ] T038 [P] [US1] Create part-ii-sdk-fokus/chapter-06.md placeholder for "Kommunikation (Signale und Queries)"

- [ ] T039 [US1] Create part-ii-sdk-fokus/examples/chapter-04/ directory with .python-version, pyproject.toml, and README.md
- [ ] T040 [P] [US1] Create part-ii-sdk-fokus/examples/chapter-04/sdk_setup.py demonstrating SDK initialization

- [ ] T041 [US1] Create part-ii-sdk-fokus/examples/chapter-05/ directory with .python-version, pyproject.toml, and README.md
- [ ] T042 [P] [US1] Create part-ii-sdk-fokus/examples/chapter-05/sequence_workflow.py demonstrating sequential workflow
- [ ] T043 [P] [US1] Create part-ii-sdk-fokus/examples/chapter-05/parallel_workflow.py demonstrating parallel task execution

- [ ] T044 [US1] Create part-ii-sdk-fokus/examples/chapter-06/ directory with .python-version, pyproject.toml, and README.md
- [ ] T045 [P] [US1] Create part-ii-sdk-fokus/examples/chapter-06/signals_example.py demonstrating workflow signals
- [ ] T046 [P] [US1] Create part-ii-sdk-fokus/examples/chapter-06/queries_example.py demonstrating workflow queries

### Part III: Resilienz (3 chapters)

- [ ] T047 [P] [US1] Create part-iii-resilienz/chapter-07.md placeholder for "Fehlerbehandlung und Retries"
- [ ] T048 [P] [US1] Create part-iii-resilienz/chapter-08.md placeholder for "SAGA Pattern"
- [ ] T049 [P] [US1] Create part-iii-resilienz/chapter-09.md placeholder for "Workflow-Evolution und Versionierung"

- [ ] T050 [US1] Create part-iii-resilienz/examples/chapter-07/ directory with .python-version, pyproject.toml, and README.md
- [ ] T051 [P] [US1] Create part-iii-resilienz/examples/chapter-07/retry_policy.py demonstrating retry strategies

- [ ] T052 [US1] Create part-iii-resilienz/examples/chapter-08/ directory with .python-version, pyproject.toml, and README.md
- [ ] T053 [P] [US1] Create part-iii-resilienz/examples/chapter-08/saga_workflow.py demonstrating SAGA pattern with compensation

- [ ] T054 [US1] Create part-iii-resilienz/examples/chapter-09/ directory with .python-version, pyproject.toml, and README.md
- [ ] T055 [P] [US1] Create part-iii-resilienz/examples/chapter-09/versioning_example.py demonstrating workflow versioning

### Part IV: Betrieb (4 chapters)

- [ ] T056 [P] [US1] Create part-iv-betrieb/chapter-10.md placeholder for "Produktions-Deployment"
- [ ] T057 [P] [US1] Create part-iv-betrieb/chapter-11.md placeholder for "Skalierung der Worker"
- [ ] T058 [P] [US1] Create part-iv-betrieb/chapter-12.md placeholder for "Observability und Monitoring"
- [ ] T059 [P] [US1] Create part-iv-betrieb/chapter-13.md placeholder for "Best Practices und Anti-Muster"

- [ ] T060 [US1] Create part-iv-betrieb/examples/chapter-10/ directory with .python-version, pyproject.toml, and README.md
- [ ] T061 [P] [US1] Create part-iv-betrieb/examples/chapter-10/deployment_config.py demonstrating production configuration

- [ ] T062 [US1] Create part-iv-betrieb/examples/chapter-11/ directory with .python-version, pyproject.toml, and README.md
- [ ] T063 [P] [US1] Create part-iv-betrieb/examples/chapter-11/worker_scaling.py demonstrating worker tuning

- [ ] T064 [US1] Create part-iv-betrieb/examples/chapter-12/ directory with .python-version, pyproject.toml, and README.md
- [ ] T065 [P] [US1] Create part-iv-betrieb/examples/chapter-12/observability.py demonstrating metrics and logging

- [ ] T066 [US1] Create part-iv-betrieb/examples/chapter-13/ directory with .python-version, pyproject.toml, and README.md
- [ ] T067 [P] [US1] Create part-iv-betrieb/examples/chapter-13/best_practices.py demonstrating patterns vs anti-patterns

### Part V: Kochbuch (2 chapters)

- [ ] T068 [P] [US1] Create part-v-kochbuch/chapter-14.md placeholder for "Muster-Rezepte"
- [ ] T069 [P] [US1] Create part-v-kochbuch/chapter-15.md placeholder for "Erweiterte Rezepte"

- [ ] T070 [US1] Create part-v-kochbuch/examples/chapter-14/ directory with .python-version, pyproject.toml, and README.md
- [ ] T071 [P] [US1] Create part-v-kochbuch/examples/chapter-14/human_in_loop.py demonstrating human-in-the-loop pattern
- [ ] T072 [P] [US1] Create part-v-kochbuch/examples/chapter-14/cron_workflow.py demonstrating scheduled workflows
- [ ] T073 [P] [US1] Create part-v-kochbuch/examples/chapter-14/order_fulfillment.py demonstrating e-commerce saga

- [ ] T074 [US1] Create part-v-kochbuch/examples/chapter-15/ directory with .python-version, pyproject.toml, and README.md
- [ ] T075 [P] [US1] Create part-v-kochbuch/examples/chapter-15/ai_agent.py demonstrating durable AI agent
- [ ] T076 [P] [US1] Create part-v-kochbuch/examples/chapter-15/lambda_orchestration.py demonstrating FaaS integration

**Checkpoint**: At this point, User Story 1 should be fully functional - all 15 chapters have directories with initialized Python projects and placeholder examples

---

## Phase 4: User Story 2 - Interactive Markdown Content with Mermaid Diagrams (Priority: P2)

**Goal**: Write chapter content in Markdown with Mermaid diagrams to create visually rich, interactive documentation

**Independent Test**: Open any chapter markdown file in GitHub or VS Code, verify Mermaid diagrams render correctly. Build with MkDocs and verify diagrams appear in the generated site.

### Sample Content for Part I

- [ ] T077 [US2] Write part-i-grundlagen/chapter-01.md introduction section with learning objectives
- [ ] T078 [US2] Add Mermaid sequence diagram to chapter-01.md showing client-server-worker interaction
- [ ] T079 [US2] Add theory sections to chapter-01.md covering distributed systems challenges
- [ ] T080 [US2] Link chapter-01.md to examples directory with instructions for running simple_workflow.py
- [ ] T081 [US2] Add summary section to chapter-01.md with key takeaways

- [ ] T082 [US2] Write part-i-grundlagen/chapter-02.md covering workflows, activities, and workers
- [ ] T083 [US2] Add Mermaid flowchart to chapter-02.md showing workflow execution flow
- [ ] T084 [US2] Add Mermaid state diagram to chapter-02.md showing activity lifecycle
- [ ] T085 [US2] Link chapter-02.md to examples for workflow.py, activities.py, and worker.py

- [ ] T086 [US2] Write part-i-grundlagen/chapter-03.md covering Temporal service architecture
- [ ] T087 [US2] Add Mermaid component diagram to chapter-03.md showing service components (Frontend, History, Matching)
- [ ] T088 [US2] Add performance considerations section to chapter-03.md with payload limits

### Sample Content for Part II

- [ ] T089 [P] [US2] Write part-ii-sdk-fokus/chapter-04.md covering SDK setup and installation
- [ ] T090 [P] [US2] Add code blocks to chapter-04.md with Python setup instructions
- [ ] T091 [P] [US2] Write part-ii-sdk-fokus/chapter-05.md covering workflow programming patterns
- [ ] T092 [P] [US2] Add Mermaid sequence diagram to chapter-05.md showing parallel task execution
- [ ] T093 [P] [US2] Write part-ii-sdk-fokus/chapter-06.md covering signals and queries
- [ ] T094 [P] [US2] Add Mermaid diagram to chapter-06.md showing signal handling flow

### Sample Content for Part III

- [ ] T095 [P] [US2] Write part-iii-resilienz/chapter-07.md covering error handling and retry policies
- [ ] T096 [P] [US2] Add Mermaid flowchart to chapter-07.md showing exponential backoff strategy
- [ ] T097 [P] [US2] Write part-iii-resilienz/chapter-08.md explaining SAGA pattern in detail
- [ ] T098 [P] [US2] Add Mermaid sequence diagram to chapter-08.md showing saga compensation flow
- [ ] T099 [P] [US2] Write part-iii-resilienz/chapter-09.md covering workflow versioning strategies
- [ ] T100 [P] [US2] Add Mermaid diagram to chapter-09.md showing worker versioning and pinning

### Sample Content for Parts IV & V

- [ ] T101 [P] [US2] Write part-iv-betrieb/chapter-10.md through chapter-13.md with deployment and operations content
- [ ] T102 [P] [US2] Add Mermaid diagrams to Part IV chapters showing deployment architecture and scaling patterns
- [ ] T103 [P] [US2] Write part-v-kochbuch/chapter-14.md and chapter-15.md with practical recipes and advanced patterns
- [ ] T104 [P] [US2] Add Mermaid diagrams to Part V chapters showing workflow patterns (human-in-loop, saga, etc.)

### Documentation Verification

- [ ] T105 [US2] Test all chapter markdown files render correctly in GitHub preview
- [ ] T106 [US2] Test all Mermaid diagrams render in VS Code Markdown Preview extension
- [ ] T107 [US2] Update root README.md with complete table of contents linking to all 15 chapters

**Checkpoint**: At this point, User Story 2 should be complete - all chapters have rich markdown content with Mermaid diagrams

---

## Phase 5: User Story 3 - Python Example Integration with uv Package Manager (Priority: P1)

**Goal**: Ensure each chapter's Python examples are properly managed with uv and execute successfully

**Independent Test**: Navigate to any chapter's examples directory, run `uv sync` (completes in <2 min), then `uv run python <example>.py` (executes without errors)

### Validate and Enhance Example Projects

- [ ] T108 [P] [US3] Test uv sync in part-i-grundlagen/examples/chapter-01/ completes in <2 minutes
- [ ] T109 [P] [US3] Test uv run python simple_workflow.py executes successfully in chapter-01
- [ ] T110 [P] [US3] Verify pyproject.toml in chapter-01 has correct temporalio dependency version

- [ ] T111 [P] [US3] Test uv sync in part-i-grundlagen/examples/chapter-02/ and verify all 3 examples run
- [ ] T112 [P] [US3] Test workflow.py, activities.py, and worker.py in chapter-02 execute without errors

- [ ] T113 [P] [US3] Test all Part II example projects (chapters 04-06) with uv sync and verify examples run
- [ ] T114 [P] [US3] Test all Part III example projects (chapters 07-09) with uv sync and verify examples run
- [ ] T115 [P] [US3] Test all Part IV example projects (chapters 10-13) with uv sync and verify examples run
- [ ] T116 [P] [US3] Test all Part V example projects (chapters 14-15) with uv sync and verify examples run

### Enhance Examples to Import Shared Utilities

- [ ] T117 [US3] Update part-i-grundlagen/examples/chapter-01/simple_workflow.py to import from shared/temporal_helpers.py
- [ ] T118 [P] [US3] Update chapter-02 examples to use shared utilities for client creation
- [ ] T119 [P] [US3] Update chapter-06 examples to use shared/examples_common.py for logging
- [ ] T120 [P] [US3] Update Part III examples to use shared utilities where appropriate
- [ ] T121 [P] [US3] Update Part IV and V examples to use shared utilities consistently

### Example Documentation

- [ ] T122 [P] [US3] Update all chapter README.md files with clear uv sync and uv run instructions
- [ ] T123 [P] [US3] Add prerequisites section to each example README (Python 3.13, uv, Temporal server)
- [ ] T124 [US3] Verify all .python-version files contain "3.13" across all 15 chapter example directories
- [ ] T125 [US3] Verify all pyproject.toml files use temporalio>=1.5.0,<2.0.0 dependency

### Dependency Isolation Verification

- [ ] T126 [US3] Test that multiple chapter examples can have uv sync run simultaneously without conflicts
- [ ] T127 [US3] Verify each chapter's .venv directory is isolated and doesn't interfere with others
- [ ] T128 [US3] Document in quickstart.md that each chapter maintains its own isolated environment

**Checkpoint**: At this point, User Story 3 should be complete - all examples use uv, run successfully, and import shared utilities

---

## Phase 6: User Story 4 - Complete Book Structure Based on Outline (Priority: P2)

**Goal**: Verify the folder structure matches the complete book outline (Teil I-V with all 15 chapters) and provides comprehensive navigation

**Independent Test**: Compare directory structure against reports/book outline, verify all 5 parts exist with correct chapter counts, navigate from README to any chapter in ≤3 clicks

### Structure Validation

- [ ] T129 [US4] Verify part-i-grundlagen/ contains exactly 3 chapter markdown files (01-03)
- [ ] T130 [US4] Verify part-ii-sdk-fokus/ contains exactly 3 chapter markdown files (04-06)
- [ ] T131 [US4] Verify part-iii-resilienz/ contains exactly 3 chapter markdown files (07-09)
- [ ] T132 [US4] Verify part-iv-betrieb/ contains exactly 4 chapter markdown files (10-13)
- [ ] T133 [US4] Verify part-v-kochbuch/ contains exactly 2 chapter markdown files (14-15)
- [ ] T134 [US4] Verify total of 15 chapter markdown files exist across all parts

### Examples Directory Validation

- [ ] T135 [US4] Verify part-i-grundlagen/examples/ contains chapter-01/, chapter-02/, chapter-03/ subdirectories
- [ ] T136 [US4] Verify part-ii-sdk-fokus/examples/ contains chapter-04/, chapter-05/, chapter-06/ subdirectories
- [ ] T137 [US4] Verify part-iii-resilienz/examples/ contains chapter-07/, chapter-08/, chapter-09/ subdirectories
- [ ] T138 [US4] Verify part-iv-betrieb/examples/ contains chapter-10/, chapter-11/, chapter-12/, chapter-13/ subdirectories
- [ ] T139 [US4] Verify part-v-kochbuch/examples/ contains chapter-14/, chapter-15/ subdirectories
- [ ] T140 [US4] Verify total of 15 example project directories exist

### Navigation and Documentation

- [ ] T141 [US4] Update root README.md with hierarchical navigation to all 5 parts
- [ ] T142 [US4] Add direct links from README.md to each of the 15 chapters
- [ ] T143 [US4] Test navigation: README → Part → Chapter takes ≤3 clicks
- [ ] T144 [US4] Create visual directory tree diagram in README.md showing complete structure
- [ ] T145 [US4] Add chapter summaries to README.md describing content of each chapter

### Cross-References

- [ ] T146 [P] [US4] Add "Next Chapter" and "Previous Chapter" links in each chapter markdown file
- [ ] T147 [P] [US4] Add "Back to Table of Contents" link at top of each chapter
- [ ] T148 [US4] Verify all internal links in markdown files are correct (no broken links)

### Outline Comparison

- [ ] T149 [US4] Compare generated structure against reports/Temporal Buchstruktur und Deep Dive.md
- [ ] T150 [US4] Verify all part names match the book outline (Grundlagen, SDK-Fokus, Resilienz, Betrieb, Kochbuch)
- [ ] T151 [US4] Verify chapter titles match the outline (Einführung, Kernbausteine, etc.)
- [ ] T152 [US4] Document any structural differences in specs/001-temporal-book-chapters/structure-validation.md

**Checkpoint**: At this point, User Story 4 should be complete - structure matches outline 1:1 and navigation is clear

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, documentation, and validation across all user stories

### Documentation

- [ ] T153 [P] Update specs/001-temporal-book-chapters/quickstart.md with final setup instructions
- [ ] T154 [P] Create CONTRIBUTING.md at root with guidelines for adding new chapters
- [ ] T155 [P] Add LICENSE file at root (confirm with user which license)
- [ ] T156 [P] Update CLAUDE.md agent context with final project structure

### Code Quality

- [ ] T157 [P] Run Python linter (ruff) on all example code in shared/ directory
- [ ] T158 [P] Verify all shared utilities have comprehensive docstrings and type hints
- [ ] T159 [P] Ensure all example Python files follow PEP 8 style guidelines
- [ ] T160 [P] Add inline comments to complex examples explaining Temporal concepts

### Testing and Validation

- [ ] T161 Manually test at least 3 examples from different parts to verify they execute
- [ ] T162 Verify all pyproject.toml files are consistent across chapters
- [ ] T163 Test that shared utilities can be imported from any example directory
- [ ] T164 Run structure validation script (if created) to verify all required files exist

### Static Site Generator Setup (Optional)

- [ ] T165 [P] Create mkdocs.yml configuration file for MkDocs + Material theme
- [ ] T166 [P] Configure Mermaid plugin in mkdocs.yml
- [ ] T167 [P] Set up navigation structure in mkdocs.yml mapping to all 15 chapters
- [ ] T168 Test mkdocs serve locally and verify all content renders correctly
- [ ] T169 Test mkdocs build generates static site in <5 minutes

### Final Validation

- [ ] T170 Run comprehensive check: verify 5 parts, 15 chapters, 15 example projects
- [ ] T171 Test end-to-end workflow: clone repo → cd chapter-01 examples → uv sync → run example
- [ ] T172 Verify success criteria SC-001 through SC-007 from spec.md are all met
- [ ] T173 Update root README.md with "Getting Started" quick links
- [ ] T174 Create repository tags/releases marking completion of structure generation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Structure & Examples - Foundation for all
  - User Story 3 (P1): uv Integration - Can proceed in parallel with US1
  - User Story 2 (P2): Markdown Content - Can start after US1 creates structure
  - User Story 4 (P2): Validation - Should wait for US1, US2, US3 to complete
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Structure & Examples
  - Depends on: Foundational (Phase 2)
  - Blocks: US2, US4
  - Parallel with: US3 (different concerns)

- **User Story 3 (P1)**: uv Package Management
  - Depends on: Foundational (Phase 2)
  - Parallel with: US1 (can enhance examples as they're created)
  - Blocks: None (but enhances US1 examples)

- **User Story 2 (P2)**: Markdown Content
  - Depends on: US1 (needs structure to exist)
  - Parallel with: US3 (different files)
  - Blocks: US4 (validation needs content)

- **User Story 4 (P2)**: Structure Validation
  - Depends on: US1, US2, US3 (validates their outputs)
  - Blocks: None
  - Should be last user story before Polish

### Within Each User Story

**User Story 1 (Structure)**:
1. Create part directories (T006-T010) - parallel
2. Create examples directories (T011-T015) - parallel
3. For each part, create chapters + examples sequentially:
   - Part I: T016-T035 (chapters can be parallel, examples sequential per chapter)
   - Part II: T036-T046
   - Part III: T047-T055
   - Part IV: T056-T067
   - Part V: T068-T076

**User Story 2 (Content)**:
- All content tasks can run in parallel (different markdown files)
- Mermaid diagrams can be added independently
- Verification tasks (T105-T107) run after content is written

**User Story 3 (uv)**:
- Testing tasks can run in parallel per chapter
- Enhancement tasks modify existing examples (sequential per file, parallel across chapters)
- Documentation updates can run in parallel

**User Story 4 (Validation)**:
- Validation tasks can run in parallel (read-only checks)
- Navigation updates should be sequential
- Cross-reference tasks can run in parallel

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T002, T003, T004, T005 can all run in parallel (different files)

**Within Foundational (Phase 2)**:
- All part directory creation (T006-T015) can run in parallel

**Within User Story 1**:
- All chapter markdown placeholders can be created in parallel
- Example projects for different chapters can be initialized in parallel
- Within a chapter: workflow.py, activities.py, worker.py can be written in parallel

**Within User Story 2**:
- All chapter content writing can proceed in parallel
- All Mermaid diagram additions can proceed in parallel

**Within User Story 3**:
- Testing different chapter examples can run in parallel
- Updating different example files to use shared utilities can run in parallel

**Across User Stories**:
- US1 and US3 can proceed largely in parallel (US3 enhances US1 outputs)
- Once US1 creates a chapter structure, US2 can immediately add content to that chapter

---

## Parallel Example: User Story 1 (Part I)

```bash
# Launch all chapter markdown creation together:
Task: "Create part-i-grundlagen/chapter-01.md placeholder"
Task: "Create part-i-grundlagen/chapter-02.md placeholder"
Task: "Create part-i-grundlagen/chapter-03.md placeholder"

# Launch all example Python files for chapter-02 together:
Task: "Create part-i-grundlagen/examples/chapter-02/workflow.py"
Task: "Create part-i-grundlagen/examples/chapter-02/activities.py"
Task: "Create part-i-grundlagen/examples/chapter-02/worker.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 3 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T015) - CRITICAL
3. Complete Phase 3: User Story 1 - Part I only (T016-T035)
4. Complete Phase 5: User Story 3 - Part I validation (T108-T112, T117-T118)
5. **STOP and VALIDATE**: Test Part I examples independently
6. Deploy/demo if ready

This gives you a working MVP with 3 chapters and runnable examples.

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add Part I (US1 + US3) → Test independently → **MVP!**
3. Add Part II (US1 + US3) → Test independently → Delivery 2
4. Add Parts III, IV, V (US1 + US3) → Test independently → Delivery 3
5. Add Content (US2) → All chapters have rich markdown → Delivery 4
6. Validate Structure (US4) → Confirm completeness → Delivery 5
7. Polish (Phase 7) → Production ready → Final Release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T015)
2. Once Foundational is done:
   - Developer A: User Story 1 - Parts I & II
   - Developer B: User Story 1 - Parts III & IV
   - Developer C: User Story 1 - Part V + User Story 3
   - Developer D: User Story 2 (after US1 parts complete)
3. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 174
**Setup Tasks**: 5 (T001-T005)
**Foundational Tasks**: 10 (T006-T015)
**User Story 1 Tasks**: 61 (T016-T076) - Structure & Examples
**User Story 2 Tasks**: 31 (T077-T107) - Markdown Content
**User Story 3 Tasks**: 21 (T108-T128) - uv Integration
**User Story 4 Tasks**: 24 (T129-T152) - Validation
**Polish Tasks**: 22 (T153-T174)

**Parallel Task Count**: ~130 tasks can run in parallel (marked with [P])
**Sequential Dependencies**: Minimal - mostly phase boundaries and within-chapter sequencing

**MVP Scope** (Recommended): Phase 1 + Phase 2 + User Story 1 (Part I only) + User Story 3 (Part I validation) = ~30 tasks
This delivers 3 working chapters with runnable examples as proof of concept.

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [US1], [US2], [US3], [US4] labels map tasks to specific user stories for traceability
- Each user story is independently completable and testable
- Stop at any checkpoint to validate story independently
- Commit after each task or logical group
- Manual testing preferred over automated tests for this documentation project
- Focus on runnable code examples that readers can execute and learn from
