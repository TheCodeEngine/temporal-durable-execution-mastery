# Quickstart: mdBook Migration

**Feature**: 002-mdbook-migration
**Date**: 2025-11-19
**Purpose**: Step-by-step guide to migrate the Temporal book to mdBook

## Prerequisites

Before starting the migration, ensure you have:

- **mdBook installed**: Install via Homebrew (`brew install mdbook`) or Cargo (`cargo install mdbook`)
- **Git repository**: Working in the temporal-book repository
- **Backup**: Create a backup branch before migration
- **Python environment**: Existing examples should remain runnable (already set up)

## Installation

### Install mdBook (macOS)

```bash
# Option 1: Homebrew (recommended)
brew install mdbook

# Option 2: Cargo (Rust package manager)
cargo install mdbook --version 0.4.36

# Verify installation
mdbook --version
```

### Install mdBook (Linux)

```bash
# Download pre-built binary
curl -L https://github.com/rust-lang/mdBook/releases/download/v0.4.36/mdbook-v0.4.36-x86_64-unknown-linux-gnu.tar.gz | tar xz
sudo mv mdbook /usr/local/bin/

# Or install via Cargo
cargo install mdbook

# Verify installation
mdbook --version
```

## Migration Steps

### Phase 1: Initialize mdBook Structure

```bash
# Ensure you're on the migration branch
git checkout 002-mdbook-migration

# Create basic mdBook structure (book.toml and src/ directory)
mdbook init --title "Temporal.io – Durable Execution Mastery"

# This creates:
# - book.toml (basic config)
# - src/SUMMARY.md (template)
# - src/chapter_1.md (example, can be deleted)
```

### Phase 2: Configure book.toml

Replace the generated `book.toml` with the configuration from `specs/002-mdbook-migration/contracts/book.toml`:

```bash
cp specs/002-mdbook-migration/contracts/book.toml ./book.toml
```

Or manually edit `book.toml` to include:
- Title, authors, description in German
- Language set to "de"
- Build directory as "book"
- HTML output configuration
- Search and repository settings

**Important**: Update the `git-repository-url` in book.toml with your actual GitHub repository URL.

### Phase 3: Create Directory Structure

```bash
# Create images directory with part subdirectories
mkdir -p src/images/{part-01,part-02,part-03,part-04,part-05,shared}

# Remove example files from mdbook init
rm -f src/chapter_1.md
```

### Phase 4: Migrate Chapter Files

Move all chapter markdown files to `src/` with standardized naming:

```bash
# Part I: Grundlagen
cp part-i-grundlagen/chapter-01.md src/part-01-chapter-01.md
cp part-i-grundlagen/chapter-02.md src/part-01-chapter-02.md
cp part-i-grundlagen/chapter-03.md src/part-01-chapter-03.md

# Part II: SDK-Fokus
cp part-ii-sdk-fokus/chapter-04.md src/part-02-chapter-04.md
cp part-ii-sdk-fokus/chapter-05.md src/part-02-chapter-05.md
cp part-ii-sdk-fokus/chapter-06.md src/part-02-chapter-06.md

# Part III: Resilienz
cp part-iii-resilienz/chapter-07.md src/part-03-chapter-07.md
cp part-iii-resilienz/chapter-08.md src/part-03-chapter-08.md
cp part-iii-resilienz/chapter-09.md src/part-03-chapter-09.md

# Part IV: Betrieb
cp part-iv-betrieb/chapter-10.md src/part-04-chapter-10.md
cp part-iv-betrieb/chapter-11.md src/part-04-chapter-11.md
cp part-iv-betrieb/chapter-12.md src/part-04-chapter-12.md
cp part-iv-betrieb/chapter-13.md src/part-04-chapter-13.md

# Part V: Kochbuch
cp part-v-kochbuch/chapter-14.md src/part-05-chapter-14.md
cp part-v-kochbuch/chapter-15.md src/part-05-chapter-15.md

# Copy README as introduction
cp README.md src/README.md
```

### Phase 5: Migrate Images/Assets

If you have existing images or assets in part directories:

```bash
# Example: migrate images from part-i-grundlagen
if [ -d "part-i-grundlagen/assets" ]; then
  cp -r part-i-grundlagen/assets/* src/images/part-01/
fi

# Repeat for other parts
if [ -d "part-ii-sdk-fokus/assets" ]; then
  cp -r part-ii-sdk-fokus/assets/* src/images/part-02/
fi

# Continue for part-iii, part-iv, part-v...
```

### Phase 6: Update Image References

Update image paths in all chapter files from `./assets/image.png` to `images/part-XX/image.png`:

```bash
# Example: Update part-01 chapters
sed -i '' 's|./assets/|images/part-01/|g' src/part-01-chapter-*.md

# Repeat for other parts
sed -i '' 's|./assets/|images/part-02/|g' src/part-02-chapter-*.md
sed -i '' 's|./assets/|images/part-03/|g' src/part-03-chapter-*.md
sed -i '' 's|./assets/|images/part-04/|g' src/part-04-chapter-*.md
sed -i '' 's|./assets/|images/part-05/|g' src/part-05-chapter-*.md
```

**Note**: On Linux, use `sed -i` (without empty string) instead of `sed -i ''`.

### Phase 7: Create SUMMARY.md

Replace `src/SUMMARY.md` with the table of contents from `specs/002-mdbook-migration/contracts/SUMMARY.md`:

```bash
cp specs/002-mdbook-migration/contracts/SUMMARY.md src/SUMMARY.md
```

Or manually create it following the structure in the contract file, ensuring all chapters are listed.

### Phase 8: Update Internal Links

If chapters link to each other, update paths to reflect new structure:

```bash
# Example: Change links from ./chapter-02.md to part-01-chapter-02.md
# This may require manual review of each chapter
grep -r "\\[.*\\](\\./chapter-" src/
```

Manually update found links to use the new flat naming convention.

### Phase 9: Test Local Build

```bash
# Build the book
mdbook build

# Check for errors
# If successful, book/ directory will be created with HTML output

# Serve locally for preview
mdbook serve --open

# This opens http://localhost:3000 in your browser
# Test navigation, check all chapters load, verify images display
```

**Common Issues**:
- **Missing chapters**: Ensure all files listed in SUMMARY.md exist in src/
- **Broken links**: Update relative paths to match new structure
- **Images not showing**: Verify image paths and file existence

### Phase 10: Update .gitignore

Add mdBook output to .gitignore:

```bash
echo "" >> .gitignore
echo "# mdBook build output" >> .gitignore
echo "/book" >> .gitignore
```

### Phase 11: Set Up GitHub Actions

Create the GitHub Actions workflow:

```bash
# Create workflow directory
mkdir -p .github/workflows

# Copy workflow configuration
cp specs/002-mdbook-migration/contracts/deploy-mdbook.yml .github/workflows/deploy-mdbook.yml
```

**Important**: Edit `.github/workflows/deploy-mdbook.yml` and verify:
- Branch name matches your default branch (develop or main)
- No other changes needed (workflow is ready to use)

### Phase 12: Enable GitHub Pages

1. Push your changes to GitHub:
   ```bash
   git add book.toml src/ .github/ .gitignore
   git commit -m "Migrate to mdBook structure"
   git push origin 002-mdbook-migration
   ```

2. In GitHub repository settings:
   - Go to **Settings > Pages**
   - Under **Source**, select **GitHub Actions**
   - No need to select a branch (the workflow handles deployment)

3. Merge the migration branch to your default branch (develop or main)

4. GitHub Actions will automatically build and deploy the book

5. Access your book at: `https://your-username.github.io/temporal-book/`

## Verification Checklist

After migration, verify:

- [ ] `mdbook build` completes without errors
- [ ] All 15 chapters appear in the navigation
- [ ] All internal links work correctly
- [ ] Images display properly in all chapters
- [ ] Book structure matches 5-part organization
- [ ] Local preview works (`mdbook serve`)
- [ ] GitHub Actions workflow runs successfully
- [ ] Book deploys to GitHub Pages
- [ ] Example code projects remain runnable from original locations
- [ ] German umlauts/special characters display correctly

## Working with mdBook

### Common Commands

```bash
# Build the book (generates book/ directory)
mdbook build

# Serve locally with auto-reload (watches for file changes)
mdbook serve --port 3000

# Open in browser automatically
mdbook serve --open

# Check for broken links and errors
mdbook test

# Clean build directory
mdbook clean
```

### Development Workflow

1. **Edit chapters**: Modify markdown files in `src/`
2. **Preview changes**: Run `mdbook serve` and view at localhost:3000
3. **Auto-reload**: mdBook watches for file changes and rebuilds automatically
4. **Commit changes**: Git tracks source files, not generated output
5. **Deploy**: Push to GitHub, Actions workflow builds and deploys

### Adding New Chapters

1. Create markdown file in `src/`: e.g., `src/part-06-chapter-16.md`
2. Add entry to `src/SUMMARY.md` in appropriate section
3. Build and preview to verify

### Managing Images

- Store new images in `src/images/part-XX/` matching the chapter's part
- Reference as: `![Alt text](images/part-XX/image-name.png)`
- Shared images (logo, icons) go in `src/images/shared/`

## Rollback Plan

If issues arise during migration:

```bash
# Return to pre-migration state
git checkout develop  # or your default branch
git branch -D 002-mdbook-migration

# Original structure remains intact on main branch
```

## Next Steps

After successful migration:

1. **Delete old structure** (optional): Remove `part-*/` directories after confirming book works
2. **Update README.md**: Add mdBook build instructions
3. **Customize theme**: Edit book.toml for styling preferences
4. **Add search**: Already enabled in book.toml configuration
5. **Set up redirects**: If migrating from existing docs site
6. **Announce**: Share the new book URL with readers

## Support

For mdBook-specific issues:
- [mdBook Documentation](https://rust-lang.github.io/mdBook/)
- [mdBook GitHub Issues](https://github.com/rust-lang/mdBook/issues)
- [mdBook User Guide](https://rust-lang.github.io/mdBook/guide/creating.html)

For migration questions:
- See `specs/002-mdbook-migration/research.md` for detailed research
- Review `specs/002-mdbook-migration/data-model.md` for structure details

---

**Time Estimate**: 1-2 hours for manual migration, 30 minutes for automation script
**Risk Level**: Low (non-destructive, original files remain)
**Reversible**: Yes (via git branch)
