# Tasks: mdBook Migration

**Input**: Design documents from `/specs/002-mdbook-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not applicable for this documentation migration project

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

This is a documentation project with the following structure:
- **mdBook source**: `src/` (markdown chapters, SUMMARY.md, images)
- **Generated output**: `book/` (gitignored)
- **Example code**: `examples/` (preserved, outside mdBook)
- **Configuration**: `book.toml`, `.github/workflows/deploy-mdbook.yml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize mdBook and create basic project structure

- [x] T001 Install mdBook using homebrew or cargo (verify with `mdbook --version`)
- [x] T002 Run `mdbook init --title "Temporal.io – Durable Execution Mastery"` to create initial structure
- [x] T003 [P] Copy book.toml configuration from specs/002-mdbook-migration/contracts/book.toml to project root
- [x] T004 [P] Create src/images directory structure with subdirectories: part-01/, part-02/, part-03/, part-04/, part-05/, shared/
- [x] T005 Remove default example file src/chapter_1.md created by mdbook init
- [x] T006 Add /book to .gitignore file

---

## Phase 2: User Story 1 - Configure mdBook Structure (Priority: P1) 🎯 MVP

**Goal**: Set up mdBook configuration and structure so `mdbook build` generates a navigable website with all chapters organized by parts

**Independent Test**: Run `mdbook build` without errors and verify book/index.html displays table of contents with all 5 parts and 15 chapters in correct hierarchy

### Configuration for User Story 1

- [x] T007 [US1] Verify book.toml contains correct German language setting (language = "de")
- [x] T008 [US1] Create src/SUMMARY.md using structure from specs/002-mdbook-migration/contracts/SUMMARY.md
- [x] T009 [US1] Copy README.md to src/README.md as introduction page

### Validation for User Story 1

- [x] T010 [US1] Run `mdbook build` and verify it completes without errors
- [x] T011 [US1] Open book/index.html in browser and verify navigation sidebar displays correctly
- [x] T012 [US1] Run `mdbook serve` and verify book is accessible at http://localhost:3000

**Checkpoint**: mdBook structure is configured and builds successfully. SUMMARY.md references all chapters (even though content files don't exist yet - will be added in US2).

---

## Phase 3: User Story 2 - Migrate Content Files (Priority: P2)

**Goal**: Move all existing chapter markdown files to src/ with mdBook-compatible naming so all content appears in the generated book without data loss

**Independent Test**: Open each chapter in the generated book and verify all content, code blocks, and formatting render correctly with no broken links

### Chapter Migration for User Story 2

**Part I: Grundlagen (Chapters 1-3)**
- [ ] T013 [P] [US2] Copy part-i-grundlagen/chapter-01.md to src/part-01-chapter-01.md
- [ ] T014 [P] [US2] Copy part-i-grundlagen/chapter-02.md to src/part-01-chapter-02.md
- [ ] T015 [P] [US2] Copy part-i-grundlagen/chapter-03.md to src/part-01-chapter-03.md

**Part II: SDK-Fokus (Chapters 4-6)**
- [ ] T016 [P] [US2] Copy part-ii-sdk-fokus/chapter-04.md to src/part-02-chapter-04.md
- [ ] T017 [P] [US2] Copy part-ii-sdk-fokus/chapter-05.md to src/part-02-chapter-05.md
- [ ] T018 [P] [US2] Copy part-ii-sdk-fokus/chapter-06.md to src/part-02-chapter-06.md

**Part III: Resilienz (Chapters 7-9)**
- [ ] T019 [P] [US2] Copy part-iii-resilienz/chapter-07.md to src/part-03-chapter-07.md
- [ ] T020 [P] [US2] Copy part-iii-resilienz/chapter-08.md to src/part-03-chapter-08.md
- [ ] T021 [P] [US2] Copy part-iii-resilienz/chapter-09.md to src/part-03-chapter-09.md

**Part IV: Betrieb (Chapters 10-13)**
- [ ] T022 [P] [US2] Copy part-iv-betrieb/chapter-10.md to src/part-04-chapter-10.md
- [ ] T023 [P] [US2] Copy part-iv-betrieb/chapter-11.md to src/part-04-chapter-11.md
- [ ] T024 [P] [US2] Copy part-iv-betrieb/chapter-12.md to src/part-04-chapter-12.md
- [ ] T025 [P] [US2] Copy part-iv-betrieb/chapter-13.md to src/part-04-chapter-13.md

**Part V: Kochbuch (Chapters 14-15)**
- [ ] T026 [P] [US2] Copy part-v-kochbuch/chapter-14.md to src/part-05-chapter-14.md (if exists)
- [ ] T027 [P] [US2] Copy part-v-kochbuch/chapter-15.md to src/part-05-chapter-15.md (if exists)

### Image Migration for User Story 2

- [ ] T028 [P] [US2] If part-i-grundlagen/assets/ exists, copy contents to src/images/part-01/
- [ ] T029 [P] [US2] If part-ii-sdk-fokus/assets/ exists, copy contents to src/images/part-02/
- [ ] T030 [P] [US2] If part-iii-resilienz/assets/ exists, copy contents to src/images/part-03/
- [ ] T031 [P] [US2] If part-iv-betrieb/assets/ exists, copy contents to src/images/part-04/
- [ ] T032 [P] [US2] If part-v-kochbuch/assets/ exists, copy contents to src/images/part-05/

### Link Updates for User Story 2

- [ ] T033 [US2] Update image references in all part-01-chapter-*.md files from ./assets/ to images/part-01/
- [ ] T034 [US2] Update image references in all part-02-chapter-*.md files from ./assets/ to images/part-02/
- [ ] T035 [US2] Update image references in all part-03-chapter-*.md files from ./assets/ to images/part-03/
- [ ] T036 [US2] Update image references in all part-04-chapter-*.md files from ./assets/ to images/part-04/
- [ ] T037 [US2] Update image references in all part-05-chapter-*.md files from ./assets/ to images/part-05/
- [ ] T038 [US2] Update internal chapter links from ./chapter-NN.md to part-0X-chapter-NN.md format in all chapters

### Validation for User Story 2

- [ ] T039 [US2] Run `mdbook build` and verify no errors about missing files
- [ ] T040 [US2] Open book/index.html and click through all 15 chapters to verify content displays correctly
- [ ] T041 [US2] Check that all images display correctly in rendered book (no broken image links)
- [ ] T042 [US2] Verify all internal chapter links work correctly in the generated book
- [ ] T043 [US2] Verify German umlauts and special characters render correctly

**Checkpoint**: All chapter content is migrated and renders correctly in mdBook. Navigation works, images display, links function.

---

## Phase 4: User Story 3 - Preserve Example Code Structure (Priority: P3)

**Goal**: Ensure Python example projects remain executable from original locations and are properly referenced in book chapters

**Independent Test**: Navigate to examples/part-01/chapter-01/, run `uv sync && uv run python <file>.py`, and verify example executes successfully

### Documentation Updates for User Story 3

- [ ] T044 [P] [US3] Review chapter-01 (src/part-01-chapter-01.md) and ensure example instructions reference ../examples/part-01/chapter-01/
- [ ] T045 [P] [US3] Review chapter-02 (src/part-01-chapter-02.md) and ensure example instructions reference ../examples/part-01/chapter-02/
- [ ] T046 [P] [US3] Review chapter-03 (src/part-01-chapter-03.md) and ensure example instructions reference ../examples/part-01/chapter-03/
- [ ] T047 [P] [US3] Review chapter-06 (src/part-02-chapter-06.md) and ensure example instructions reference ../examples/part-02/chapter-06/
- [ ] T048 [P] [US3] Review chapters in part-03 and part-04 to ensure example paths are correct

### Validation for User Story 3

- [ ] T049 [US3] Test running example from examples/part-01/chapter-01/ directory using `uv sync && uv run python <file>.py`
- [ ] T050 [US3] Verify shared utilities in shared/ directory are accessible from examples
- [ ] T051 [US3] Confirm examples directory structure remains unchanged (not moved into src/)
- [ ] T052 [US3] Verify book chapters provide clear instructions for navigating to and running examples

**Checkpoint**: Example code structure is preserved, examples are runnable, and chapters document how to use them.

---

## Phase 5: User Story 4 - GitHub Pages Deployment Setup (Priority: P4)

**Goal**: Configure automated deployment so pushing to the main branch automatically builds and publishes the book to GitHub Pages

**Independent Test**: Push to repository, wait for GitHub Actions workflow to complete, and verify book is accessible at the GitHub Pages URL

### GitHub Actions Setup for User Story 4

- [x] T053 [US4] Create .github/workflows/ directory if it doesn't exist
- [x] T054 [US4] Copy specs/002-mdbook-migration/contracts/deploy-mdbook.yml to .github/workflows/deploy-mdbook.yml
- [x] T055 [US4] Update branch name in deploy-mdbook.yml from 'develop' to match your default branch if needed
- [x] T056 [US4] Update git-repository-url in book.toml with actual GitHub repository URL
- [x] T057 [US4] Update edit-url-template in book.toml with actual GitHub repository URL

### GitHub Configuration for User Story 4

- [x] T058 [US4] Commit all changes to git: book.toml, src/, .github/workflows/, .gitignore
- [ ] T059 [US4] Push changes to GitHub repository on the migration branch
- [x] T060 [US4] Navigate to repository Settings > Pages in GitHub
- [x] T061 [US4] Set Source to "GitHub Actions" (not branch-based deployment)
- [x] T062 [US4] Merge migration branch to default branch (develop or main)

### Validation for User Story 4

- [x] T063 [US4] Verify GitHub Actions workflow triggers on push to default branch
- [x] T064 [US4] Check GitHub Actions workflow runs successfully without errors
- [x] T065 [US4] Verify book is deployed to GitHub Pages at https://<username>.github.io/<repo-name>/
- [x] T066 [US4] Open deployed GitHub Pages URL and verify full book is accessible
- [x] T067 [US4] Make a small change to a chapter, push, and verify automatic redeployment works

**Checkpoint**: CI/CD is configured, book automatically deploys to GitHub Pages on push, and is publicly accessible.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final polish

- [x] T068 [P] Update root README.md to include mdBook build instructions (mdbook build, mdbook serve)
- [x] T069 [P] Update root README.md to replace old structure references with new mdBook structure
- [x] T070 [P] Add section in README.md about GitHub Pages deployment
- [x] T071 [P] Create resources.md in src/ with links to Temporal documentation and community (optional)
- [x] T072 Review all chapters one final time for formatting consistency
- [x] T073 Run complete verification checklist from specs/002-mdbook-migration/quickstart.md
- [x] T074 Document migration changes in CHANGELOG.md or commit messages

### Optional Cleanup

- [x] T075 Archive or remove old part-i-grundlagen/ directory after verifying migration success
- [x] T076 Archive or remove old part-ii-sdk-fokus/ directory after verifying migration success
- [x] T077 Archive or remove old part-iii-resilienz/ directory after verifying migration success
- [x] T078 Archive or remove old part-iv-betrieb/ directory after verifying migration success
- [x] T079 Archive or remove old part-v-kochbuch/ directory after verifying migration success
- [ ] T080 Remove reports/ directory if no longer needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup completion
- **User Story 2 (Phase 3)**: Depends on User Story 1 completion (needs SUMMARY.md and structure)
- **User Story 3 (Phase 4)**: Can start after User Story 2 (needs chapter files to update documentation)
- **User Story 4 (Phase 5)**: Depends on User Story 1 and 2 completion (needs working mdBook build)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation - MUST complete first
- **User Story 2 (P2)**: Depends on US1 (needs structure in place) - MUST complete before US4
- **User Story 3 (P3)**: Can be done in parallel with or after US2 - Independent concern
- **User Story 4 (P4)**: Depends on US1 and US2 (needs working book to deploy) - Final integration

### Within Each User Story

- **US1**: Configuration tasks (T007-T009) → Validation (T010-T012)
- **US2**: All chapter copies (T013-T027) can run in parallel → Image migration (T028-T032) in parallel → Link updates (T033-T038) sequentially → Validation (T039-T043)
- **US3**: All documentation reviews (T044-T048) in parallel → Validation (T049-T052)
- **US4**: GitHub Actions setup (T053-T057) → GitHub config (T058-T062) → Validation (T063-T067)

### Parallel Opportunities

- **Setup Phase**: T003 and T004 can run in parallel
- **US2 Chapter Migration**: All T013-T027 (chapter copies) can run in parallel
- **US2 Image Migration**: All T028-T032 (image copies) can run in parallel
- **US3 Documentation**: All T044-T048 (chapter reviews) can run in parallel
- **Polish Phase**: T068, T069, T070, T071 (documentation updates) can run in parallel

---

## Parallel Example: User Story 2 (Chapter Migration)

```bash
# Launch all chapter copy tasks together (15 chapters):
Task: "Copy part-i-grundlagen/chapter-01.md to src/part-01-chapter-01.md"
Task: "Copy part-i-grundlagen/chapter-02.md to src/part-01-chapter-02.md"
Task: "Copy part-i-grundlagen/chapter-03.md to src/part-01-chapter-03.md"
Task: "Copy part-ii-sdk-fokus/chapter-04.md to src/part-02-chapter-04.md"
# ... and so on for all 15 chapters

# Then launch all image migration tasks together (5 parts):
Task: "Copy part-i-grundlagen/assets/ to src/images/part-01/"
Task: "Copy part-ii-sdk-fokus/assets/ to src/images/part-02/"
Task: "Copy part-iii-resilienz/assets/ to src/images/part-03/"
Task: "Copy part-iv-betrieb/assets/ to src/images/part-04/"
Task: "Copy part-v-kochbuch/assets/ to src/images/part-05/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: User Story 1 (T007-T012)
3. **STOP and VALIDATE**: Run `mdbook build` and `mdbook serve`
4. Verify basic structure works before proceeding

### Incremental Delivery

1. Complete Setup + US1 → Basic mdBook structure working
2. Add US2 → All content migrated and rendered → Test independently
3. Add US3 → Examples verified working → Test independently
4. Add US4 → Automated deployment configured → Test independently
5. Polish → Final documentation and cleanup

### Sequential Implementation (Recommended for Solo Developer)

1. **Day 1 Morning**: Setup + US1 (T001-T012) - 30 minutes
2. **Day 1 Afternoon**: US2 Chapter Migration (T013-T043) - 1 hour
3. **Day 2 Morning**: US3 Example Verification (T044-T052) - 30 minutes
4. **Day 2 Afternoon**: US4 GitHub Pages Setup (T053-T067) - 45 minutes
5. **Day 3**: Polish and Cleanup (T068-T080) - 30 minutes

**Total Estimated Time**: 3-4 hours

---

## Notes

- [P] tasks = different files, no dependencies, can be parallelized
- [Story] label (US1, US2, US3, US4) maps task to specific user story
- Each user story is independently testable via checkpoint validations
- Checkpoint after each phase to validate before proceeding
- No tests required - this is a documentation migration, not software development
- All file paths are from repository root
- Original example code structure remains untouched (outside src/)
- Commit after completing each user story phase

---

## Task Summary

- **Total Tasks**: 80
- **Setup Phase**: 6 tasks (T001-T006)
- **User Story 1 (P1)**: 6 tasks (T007-T012) - MVP foundation
- **User Story 2 (P2)**: 31 tasks (T013-T043) - Content migration
- **User Story 3 (P3)**: 9 tasks (T044-T052) - Example preservation
- **User Story 4 (P4)**: 15 tasks (T053-T067) - Deployment setup
- **Polish Phase**: 13 tasks (T068-T080)

**Parallel Opportunities**:
- 28 tasks marked [P] can be executed in parallel
- Chapter copies (15 tasks) can all run simultaneously
- Image migrations (5 tasks) can all run simultaneously
- Documentation reviews (5 tasks) can all run simultaneously

**MVP Scope**: Complete Setup + User Story 1 (12 tasks total) for basic working mdBook

**Format Validation**: ✅ All tasks follow required checklist format with ID, optional [P], required [Story] for US phases, and exact file paths
