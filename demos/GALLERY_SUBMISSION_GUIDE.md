# Marimo Gallery Submission Guide

**Notebook**: `wavesurfer_gallery.py`
**Category**: External (custom widget integrations)
**Repository**: https://github.com/marimo-team/gallery-examples
**Status**: Ready for submission ✅

---

## Overview

This guide outlines the steps to submit our WaveSurfer widget demo to the official marimo gallery. The notebook is already gallery-ready and meets all requirements.

---

## Pre-Submission Checklist

### ✅ Requirements Met

- [x] **PEP 723 metadata**: Lines 1-9 contain inline script dependencies
- [x] **Self-contained**: Uses synthetic audio, no external files required
- [x] **Dependencies pinned**: marimo>=0.10.0, anywidget>=0.9.0, traitlets>=5.0.0, numpy>=1.24.0
- [x] **Documentation**: Clear markdown cells explaining features
- [x] **Interactive features**: Playback speed, file upload, region annotation
- [x] **File size**: 18KB (well within limits)
- [x] **No empty cells**: All cells have content
- [x] **Runs without errors**: Verified with `python demos/wavesurfer_gallery.py`

### ⚠️ Pre-Submission Tasks

- [ ] Update `requires-python` to `>=3.12` (gallery standard)
- [ ] Run `uvx marimo check` validation
- [ ] Generate session metadata JSON file
- [ ] Fork marimo-team/gallery-examples repo
- [ ] Create feature branch
- [ ] Update gallery README.md

---

## Step-by-Step Submission Process

### Step 1: Update Python Version Requirement

The gallery uses Python 3.12+ as the standard.

**File**: `demos/wavesurfer_gallery.py`
**Change**: Line 3

```python
# Before:
# requires-python = ">=3.11"

# After:
# requires-python = ">=3.12"
```

### Step 2: Validate Notebook Locally

Run the marimo validation tool:

```bash
# Install marimo if needed
uvx marimo check demos/wavesurfer_gallery.py
```

Expected output:
```
✓ wavesurfer_gallery.py is valid
```

If there are any errors, fix them before proceeding.

### Step 3: Fork and Clone Gallery Repository

```bash
# Fork on GitHub
# https://github.com/marimo-team/gallery-examples -> Click "Fork"

# Clone your fork
cd ~/repos  # or your preferred location
git clone https://github.com/YOUR_USERNAME/gallery-examples.git
cd gallery-examples

# Add upstream remote
git remote add upstream https://github.com/marimo-team/gallery-examples.git

# Create feature branch
git checkout -b add-wavesurfer-widget
```

### Step 4: Copy Notebook to Gallery Repo

```bash
# Copy from your project to gallery repo
cp /Users/josephberry/.agor/worktrees/sephib/upload_youtube/add-text-to-video/demos/wavesurfer_gallery.py \
   ~/repos/gallery-examples/notebooks/external/wavesurfer_gallery.py
```

Or manually copy the file to:
```
gallery-examples/
└── notebooks/
    └── external/
        └── wavesurfer_gallery.py  # Your notebook here
```

### Step 5: Generate Session Metadata

The gallery uses pre-computed session files for faster loading.

```bash
cd ~/repos/gallery-examples

# Generate session metadata
uv run scripts/create-sessions.py notebooks/external/wavesurfer_gallery.py
```

This creates:
```
__marimo__/
└── session/
    └── wavesurfer_gallery.py.json  # Pre-computed cell outputs and hashes
```

**What this file contains**:
- Pre-computed cell outputs (for instant preview)
- MD5 hashes of cell code (for freshness validation)
- Cell execution order
- Widget state snapshots

**Important**: Both the `.py` notebook and `.json` session file must be committed together.

### Step 6: Update README.md

Add an entry to the gallery index.

**File**: `README.md`
**Section**: External → Add to the table

**Format**:
```markdown
| Wavesurfer Widget | Interactive audio waveform visualization with draggable regions, playback speed control, and file upload. Custom anywidget demo using wavesurfer.js. | [![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/marimo-team/gallery-examples/blob/main/notebooks/external/wavesurfer_gallery.py) |
```

**Location**: Insert alphabetically in the External table (between other entries).

### Step 7: Commit Changes

```bash
cd ~/repos/gallery-examples

# Stage files
git add notebooks/external/wavesurfer_gallery.py
git add __marimo__/session/wavesurfer_gallery.py.json
git add README.md

# Commit with conventional commit format
git commit -m "feat(external): add WaveSurfer audio widget demo

- Interactive waveform visualization with wavesurfer.js
- Draggable/resizable regions for audio annotation
- Playback speed control (0.5x - 2.0x)
- Multi-pitch synthetic audio generation
- Optional file upload (MP3/WAV/OGG/M4A)
- Bidirectional Python ↔ JavaScript sync via traitlets
- Self-contained demo with PEP 723 dependencies

Demo showcases custom anywidget integration for audio
analysis, transcription, and annotation workflows."
```

### Step 8: Push and Create Pull Request

```bash
# Push to your fork
git push origin add-wavesurfer-widget
```

Then on GitHub:

1. Navigate to: https://github.com/YOUR_USERNAME/gallery-examples
2. Click "Compare & pull request"
3. Fill in PR details:

**Title**:
```
feat(external): add WaveSurfer audio widget demo
```

**Description**:
```markdown
## Summary

Adds an interactive audio waveform widget demo using wavesurfer.js and anywidget.

## Features

- 🎵 **Interactive Waveform**: Draggable/resizable regions for audio segment annotation
- ⏩ **Playback Speed**: 7 speed options (0.5x - 2.0x) for transcription/analysis
- 🎹 **Synthetic Audio**: Self-contained with multi-pitch A major chord sample
- 📁 **File Upload**: Optional upload support (MP3/WAV/OGG/M4A)
- 🔄 **Bidirectional Sync**: Python ↔ JavaScript state via traitlets
- 📊 **Table Integration**: Two-way sync between table and waveform
- 📥 **Export**: JSON export of annotated regions

## Use Cases

- Audio transcription and annotation
- Podcast chapter marking
- Music analysis (verse/chorus identification)
- Language learning with sentence-level audio alignment
- Torah reading verse boundary alignment

## Technical Details

- **Widget Framework**: anywidget (portable across Jupyter/marimo)
- **Audio Library**: wavesurfer.js v7 (loaded from CDN)
- **Dependencies**: PEP 723 compliant (marimo, anywidget, traitlets, numpy)
- **Self-Contained**: Generates 5-second synthetic audio (A4/C5/E5 chord)
- **Size**: 18KB, 17 cells, ~600 lines
- **Python**: 3.12+ compatible

## Screenshots

_Add screenshots if available_

## Testing

- [x] `uvx marimo check` passes
- [x] Session metadata generated successfully
- [x] Notebook runs without errors
- [x] All interactive features tested
- [x] README.md updated

## Related

- Custom widget implementation demonstrates anywidget best practices
- Shows bidirectional state sync patterns for marimo widgets
- Educational example of CDN-based JavaScript library integration
```

4. Click "Create pull request"

### Step 9: Address CI/CD Checks

The gallery has automated checks that will run on your PR:

**1. check-notebooks.yml**
- Runs `uvx marimo check` on your notebook
- Validates Python syntax and marimo structure
- Must pass ✅

**2. validate-session-files.yml**
- Verifies session JSON exists
- Checks for execution errors
- Validates cell code hashes match
- Must pass ✅

**If checks fail**:
- Review the error messages in the PR
- Fix issues locally
- Re-run session generation if needed
- Push fixes to your branch (PR updates automatically)

### Step 10: Respond to Review Feedback

Marimo maintainers will review your PR and may request:

- **Code changes**: Simplifications, best practices
- **Documentation**: Clearer explanations
- **Dependencies**: Version updates or removals
- **Cell structure**: Reorganization for clarity

**Response process**:
1. Make requested changes locally
2. Test thoroughly
3. Regenerate session metadata if cells changed
4. Commit and push updates
5. Comment on PR with summary of changes

---

## Gallery Standards Reference

### Notebook Structure Patterns

**Simple (3-5 cells)**:
- Documentation cell
- Configuration/inputs
- Widget creation
- Display/output

**Medium (5-10 cells)**:
- Documentation
- Imports
- Data generation/loading
- Widget creation
- Interactive controls
- Display with state
- Export/actions

**Complex (10+ cells)** - Your notebook fits here:
- Title/intro
- File upload option
- Widget implementation (inline)
- Data generation
- Widget creation
- Display with state
- Table interaction
- Sync logic
- Export functionality
- Documentation

### PEP 723 Format

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.19.7",
#     "anywidget>=0.9",
#     "traitlets>=5.0",
#     "numpy>=1.24",
# ]
# ///
```

**Best Practices**:
- Pin major/minor versions for stability
- Use `>=` for minimum versions
- Keep dependencies minimal
- Only include what's actually used

### Cell Naming Conventions

The gallery prefers descriptive function names:

```python
@app.cell
def imports():
    import marimo as mo
    return (mo,)

@app.cell(hide_code=True)
def documentation(mo):
    mo.md("# Title...")
    return

@app.cell
def create_widget(WavesurferWidget, data):
    widget = WavesurferWidget(...)
    return (widget,)
```

### Documentation Style

- Use `mo.md()` for narrative sections
- Keep code comments minimal
- Focus on "what" and "why", not "how"
- Use `mo.callout()` for important tips
- Include use cases and examples

---

## Common Issues & Solutions

### Issue: ModuleNotFoundError

**Problem**: Session file has import errors

**Solution**:
```bash
# Ensure all dependencies in PEP 723 block
# Regenerate session
uv run scripts/create-sessions.py notebooks/external/wavesurfer_gallery.py
```

### Issue: Cell hash mismatch

**Problem**: Cell code changed after session generation

**Solution**:
```bash
# Regenerate session after any code changes
uv run scripts/create-sessions.py notebooks/external/wavesurfer_gallery.py
git add __marimo__/session/wavesurfer_gallery.py.json
```

### Issue: Empty cells error

**Problem**: Session validation fails on empty cells

**Solution**:
- Remove all empty `@app.cell` definitions
- Ensure every cell has content or returns something

### Issue: marimo version mismatch

**Problem**: Notebook requires newer marimo features

**Solution**:
```python
# Update dependency version in PEP 723
# dependencies = [
#     "marimo>=0.21.0",  # Use version with required features
# ]
```

---

## Post-Submission

### After PR Merge

1. **Clean up local branches**:
   ```bash
   git checkout main
   git pull upstream main
   git branch -d add-wavesurfer-widget
   ```

2. **Update your fork**:
   ```bash
   git push origin main
   ```

3. **Share the news**:
   - Tweet about it (tag @marimo_io)
   - Share in marimo Discord
   - Update project documentation

### Gallery URL

Your notebook will be available at:
```
https://marimo.io/gallery#wavesurfer-widget
```

With direct run link:
```
https://molab.marimo.io/github/marimo-team/gallery-examples/blob/main/notebooks/external/wavesurfer_gallery.py
```

---

## Timeline Expectations

**Typical PR lifecycle**:
- **CI checks**: 5-10 minutes
- **Initial review**: 1-3 days
- **Feedback iteration**: Variable (depends on changes needed)
- **Merge**: After approval and passing checks

**Be patient**: Maintainers review in their spare time.

---

## Resources

### Documentation
- **Gallery Repo**: https://github.com/marimo-team/gallery-examples
- **Marimo Docs**: https://docs.marimo.io/
- **anywidget Guide**: https://anywidget.dev/
- **PEP 723 Spec**: https://peps.python.org/pep-0723/

### Examples to Study
- **notebooks/external/neo4jwidget.py** - Custom widget pattern
- **notebooks/external/mandelbrot.py** - Complex computation (~600 lines)
- **notebooks/dashboard/movies.py** - Interactive controls
- **notebooks/external/wandbchart.py** - External service integration

### Getting Help
- **Marimo Discord**: https://discord.gg/JE7nhX6mD8
- **GitHub Discussions**: https://github.com/marimo-team/marimo/discussions
- **Issues**: Open an issue if you encounter bugs

---

## Quick Reference Commands

```bash
# Validation
uvx marimo check notebooks/external/wavesurfer_gallery.py

# Session generation
uv run scripts/create-sessions.py notebooks/external/wavesurfer_gallery.py

# Run locally
marimo run notebooks/external/wavesurfer_gallery.py

# Git workflow
git checkout -b add-wavesurfer-widget
git add notebooks/external/wavesurfer_gallery.py
git add __marimo__/session/wavesurfer_gallery.py.json
git add README.md
git commit -m "feat(external): add WaveSurfer audio widget demo"
git push origin add-wavesurfer-widget
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-16
**Status**: Ready for submission ✅
**Next Step**: Fork repository and begin Step 1
