# WaveSurfer Demo: Gallery Refactoring Plan

**Date**: 2026-03-16
**Status**: Planning Phase
**Goal**: Refactor `demos/wavesurfer_demo.py` to match marimo gallery standards for potential submission

---

## Executive Summary

This document provides a comprehensive refactoring plan to transform our WaveSurfer demo notebook from a functional prototype into a gallery-worthy example that adheres to marimo gallery standards.

**Current State**:
- 434 lines, ~17 cells
- Functional custom anywidget demonstration
- Good documentation but non-standard structure
- External file dependency (sample.mp3)
- Missing PEP 723 metadata block

**Target State**:
- Self-contained, runs immediately
- PEP 723 compliant dependency declaration
- Streamlined documentation (< 300 lines)
- Gallery-standard cell organization
- Embedded sample audio or generated waveform
- Clean widget integration without sys.path manipulation

**Effort Estimate**: 4-6 hours of focused refactoring

---

## Gallery Standards Analysis

### Examined Examples

Five representative notebooks from the marimo gallery were analyzed:

1. **scatter-demo.py** (drawdata) - Custom widget integration, 60 lines, 6 cells
2. **movies.py** (dashboard) - Interactive filtering, ~15 cells, state management
3. **neo4jwidget.py** (external) - External widget, minimal setup, PEP 723
4. **altair-demo.py** (library) - Library showcase, 6 cells, progressive complexity
5. **simpsons-paradox.py** (analysis) - Educational, ~30 cells, hide_code usage

### Key Patterns Identified

#### 1. **Dependency Declaration** (CRITICAL)
- **Pattern**: PEP 723 script metadata block at top
- **Format**:
  ```python
  # /// script
  # requires-python = ">=3.11"
  # dependencies = [
  #   "marimo",
  #   "anywidget>=0.9",
  #   "traitlets>=5.0",
  # ]
  # ///
  ```
- **Purpose**: Enables reproducibility, automatic environment setup
- **Our Gap**: ❌ Missing entirely

#### 2. **Import Organization**
- **Pattern**: Clean runtime imports in `app.setup` or individual cells
- **Anti-pattern**: Sys.path manipulation, complex import logic
- **Our Gap**: ⚠️ Sys.path manipulation in widget_setup cell (lines 60-66)

#### 3. **Cell Structure & Size**
- **Pattern**:
  - Small cells: 2-5 lines (display, simple operations)
  - Medium cells: 10-20 lines (data processing, widget creation)
  - Large cells: 30+ lines (only for complex visualizations)
- **Guideline**: One focused responsibility per cell
- **Our Gap**: ⚠️ load_audio cell is 44 lines (too complex)

#### 4. **Documentation Style**
- **Pattern**: Heavy use of `mo.md()` for narrative
- **Guideline**:
  - Inline code comments are minimal/absent
  - Documentation precedes code cells
  - Focus on "what" and "why", not "how"
  - Concise explanations (not encyclopedic)
- **Our Gap**: ⚠️ Final documentation cell is 114 lines (too long)

#### 5. **Cell Naming Conventions**
- **Pattern A**: All anonymous `_()` (most common)
- **Pattern B**: All descriptive names
- **Anti-pattern**: Mixed approach
- **Our Gap**: ⚠️ Inconsistent naming

#### 6. **Widget Presentation**
- **Pattern**:
  - Dedicated cell for widget creation
  - Separate cell for display
  - State inspection in follow-up cells
  - Two-way sync demonstrated explicitly
- **Our Strength**: ✅ This is well-structured in our demo

#### 7. **Data/Asset Handling**
- **Pattern**:
  - Small embedded datasets (CSV strings, JSON)
  - Generated synthetic data
  - CDN-loaded resources (like wavesurfer.js)
  - Public APIs for data
- **Anti-pattern**: External file dependencies
- **Our Gap**: ❌ Requires external sample.mp3 file

#### 8. **Layout Components**
- **Pattern**: Strategic use of `mo.vstack()`, `mo.hstack()`, `mo.callout()`
- **Our Gap**: ⚠️ Could use more layout composition (state + widget)

#### 9. **Self-Containment**
- **Critical Requirement**: Notebook must run immediately without user setup
- **Our Gap**: ❌ Requires audio file or user upload

#### 10. **Overall Length**
- **Guideline**: Most notebooks 150-300 lines
- **Educational notebooks**: Can be 400+ lines
- **Our Current**: 434 lines (acceptable but could be optimized)

---

## Detailed Gap Analysis

### CRITICAL Issues (Must Fix)

#### C1. Missing PEP 723 Metadata Block
- **Impact**: Cannot be submitted to gallery without this
- **Fix**: Add script metadata block declaring all dependencies
- **Priority**: P0 (Blocker)

#### C2. External File Dependency (sample.mp3)
- **Impact**: Notebook cannot run immediately, violates self-containment
- **Current Behavior**: Complex fallback logic (lines 113-146) can fail
- **Priority**: P0 (Blocker)
- **Solutions**:
  - Option A: Embed base64-encoded minimal MP3 (3-second clip, ~4KB)
  - Option B: Generate synthetic audio waveform (sine wave)
  - Option C: Use a CDN-hosted public domain audio file
  - **Recommendation**: Option A (most self-contained)

#### C3. Sys.path Manipulation
- **Impact**: Not gallery-standard, assumes specific file structure
- **Current**: Lines 60-66 in widget_setup cell
- **Priority**: P0 (Blocker)
- **Solution**: Package widget properly or include inline in notebook

### MAJOR Issues (Should Fix)

#### M1. Overly Complex load_audio Cell
- **Impact**: Reduces readability, violates single-responsibility
- **Current**: 44 lines with multiple fallback paths
- **Priority**: P1
- **Solution**: Simplify to single embedded audio source

#### M2. Inconsistent Cell Naming
- **Impact**: Reduces clarity, not gallery-standard
- **Current**: Mix of named and anonymous cells
- **Priority**: P1
- **Solution**: Choose one pattern (recommend all descriptive names for educational clarity)

#### M3. Overly Long Documentation Cell
- **Impact**: Intimidating wall of text at end
- **Current**: 114 lines (lines 371-432)
- **Priority**: P1
- **Solution**:
  - Move architecture details to widget docstring
  - Condense "How It Works" to 2-3 key points
  - Remove redundant information already in widget docs

### MINOR Issues (Nice to Have)

#### N1. State Display Separated from Widget
- **Impact**: User must scroll to see state updates
- **Current**: widget_state_display is separate cell
- **Priority**: P2
- **Solution**: Use `mo.hstack()` or `mo.vstack()` to combine widget + state

#### N2. Regions Table Could Be More Integrated
- **Impact**: Feels disconnected from widget
- **Priority**: P2
- **Solution**: Layout widget, state, and table together

#### N3. Export Functionality Is Multi-Cell
- **Impact**: Slightly fragmented UX
- **Current**: export_button_create + export_button_handler
- **Priority**: P2
- **Solution**: Combine into single cell

---

## Refactoring Recommendations

### Category 1: Structure (Critical)

#### R1.1: Add PEP 723 Metadata Block
**Action**: Add at top of file (before imports)
```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "marimo>=0.10.0",
#   "anywidget>=0.9.0",
#   "traitlets>=5.0.0",
# ]
# ///
```
**Rationale**: Required for gallery submission, enables reproducibility
**Effort**: 5 minutes
**Priority**: P0

#### R1.2: Embed Sample Audio
**Action**: Replace external file dependency with embedded base64 audio
```python
# Minimal 5-second MP3 (base64 encoded)
SAMPLE_AUDIO_BASE64 = "SUQzBAAAAAAAI1RTU0UAAAAP..."
sample_audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
```
**Rationale**: Ensures self-containment, notebook runs immediately
**Effort**: 30 minutes (find/create minimal audio, encode, test)
**Priority**: P0
**Alternative**: Use synthetic sine wave audio (10 minutes effort)

#### R1.3: Remove Sys.path Manipulation
**Action**: Either:
- Option A: Include widget code inline in notebook (educational value)
- Option B: Assume widget is installed (not recommended for demo)
- Option C: Reference widget as external dependency

**Recommendation**: Option A for gallery submission
**Rationale**: Shows complete implementation, maximally educational
**Effort**: 1 hour (inline widget code, test)
**Priority**: P0

### Category 2: Documentation (Major)

#### R2.1: Condense Final Documentation Cell
**Current**: 114 lines
**Target**: 30-40 lines
**Action**:
- Remove architecture diagram (or make it visual with mo.mermaid if available)
- Condense "Key Features" to 3 bullet points
- Remove "Use Cases" (implied by demo itself)
- Keep "Resources" section but shorten
- Move technical details to widget docstring

**Rationale**: Gallery notebooks favor concise docs with learning-by-doing
**Effort**: 20 minutes
**Priority**: P1

#### R2.2: Streamline Step Documentation
**Current**: Separate mo.md() cells for each step intro
**Action**: Keep step headers but make them more concise
**Example**:
```python
# Before (lines 76-86):
mo.md("""
## Step 1: Load Sample Audio

For this demo, you'll need to provide an audio file. You can:
...
""")

# After:
mo.md("## Step 1: Audio Waveform\n\nThe widget visualizes a 3-second audio sample with interactive regions.")
```
**Rationale**: Reduce reading time, let demo speak for itself
**Effort**: 15 minutes
**Priority**: P1

### Category 3: Code Quality (Major)

#### R3.1: Simplify load_audio Cell
**Action**: Replace 44-line cell with simple embedded audio loading
```python
@app.cell
def load_audio():
    """Load embedded sample audio."""
    import base64
    audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
    return (audio_bytes,)
```
**Rationale**: Single responsibility, clear intent
**Effort**: 5 minutes (after R1.2 complete)
**Priority**: P1

#### R3.2: Standardize Cell Naming
**Action**: Use descriptive function names for all cells
**Pattern**:
- `setup()` → `imports()`
- `title()` ✅ Keep
- `widget_setup()` → `widget_code()` or remove if inlined
- `sample_audio_note()` → Merge with next cell
- `load_audio()` ✅ Keep
- etc.

**Rationale**: Consistency improves readability
**Effort**: 10 minutes
**Priority**: P1

### Category 4: Presentation (Minor)

#### R4.1: Combine Widget + State Display
**Action**: Use layout to show widget and state side-by-side
```python
@app.cell
def display_widget_with_state(widget_ui):
    """Display widget and state together."""
    # Widget on left, state on right
    widget_display = widget_ui
    state_display = mo.md(f"""
    **State**
    - Time: {widget_ui.value.get('current_time', 0):.3f}s
    - Playing: {'▶️' if widget_ui.value.get('is_playing') else '⏸️'}
    """)

    mo.hstack([widget_display, state_display], widths=[3, 1])
```
**Rationale**: Reduces scrolling, shows reactivity clearly
**Effort**: 15 minutes
**Priority**: P2

#### R4.2: Integrate Table with Widget
**Action**: Show table below widget in same visual context
**Rationale**: Emphasizes two-way sync
**Effort**: 10 minutes
**Priority**: P2

#### R4.3: Consolidate Export Cells
**Action**: Merge export_button_create + export_button_handler
```python
@app.cell
def export_regions(mo, widget_ui):
    """Export regions as JSON."""
    import json
    export_btn = mo.ui.run_button(label="📥 Export Regions")

    if export_btn.value:
        json_output = json.dumps(widget_ui.value.get("regions", []), indent=2)
        result = mo.vstack([
            mo.callout("✅ Exported!", kind="success"),
            mo.ui.code_editor(value=json_output, language="json", disabled=True),
        ])
    else:
        result = export_btn

    result
```
**Rationale**: Clearer flow, fewer cells
**Effort**: 10 minutes
**Priority**: P2

### Category 5: Educational Value (Minor)

#### R5.1: Add Interactive Hints
**Action**: Use mo.callout() to highlight interactive features
```python
mo.callout(
    "💡 **Try this**: Drag the region boundaries to adjust segment timing!",
    kind="info"
)
```
**Rationale**: Guides user exploration
**Effort**: 10 minutes
**Priority**: P2

#### R5.2: Show Code Toggle for Advanced Sections
**Action**: Use `hide_code=True` for complex cells, reveal on demand
**Rationale**: Reduces intimidation for beginners
**Effort**: 5 minutes
**Priority**: P3

---

## Implementation Roadmap

### Phase 1: Critical Blockers (P0) - 2 hours
**Goal**: Make notebook gallery-submittable

1. **Add PEP 723 Block** (R1.1)
   - Add metadata to top of file
   - Test: `marimo run` should install deps automatically
   - ✅ Checkpoint: Dependencies auto-install

2. **Embed Sample Audio** (R1.2)
   - Create/find minimal 3-second audio
   - Base64 encode or use synthetic sine wave
   - Test: Notebook runs without external files
   - ✅ Checkpoint: No file I/O errors

3. **Remove Sys.path Manipulation** (R1.3)
   - Option A: Inline widget code in notebook
   - Option B: Package widget for pip install
   - Test: Import works without sys.path changes
   - ✅ Checkpoint: Clean imports

**Validation**: Notebook runs on fresh marimo install with zero setup

### Phase 2: Major Improvements (P1) - 1.5 hours
**Goal**: Align with gallery quality standards

4. **Condense Documentation** (R2.1)
   - Trim final cell from 114 → 40 lines
   - Move details to widget docstring
   - ✅ Checkpoint: Concise, scannable docs

5. **Simplify load_audio** (R3.1)
   - Replace 44-line cell with 5-10 lines
   - Remove complex fallback logic
   - ✅ Checkpoint: Single responsibility achieved

6. **Streamline Step Intros** (R2.2)
   - Condense step documentation
   - Focus on actions, not explanations
   - ✅ Checkpoint: Faster time-to-first-interaction

7. **Standardize Cell Names** (R3.2)
   - Apply consistent naming pattern
   - ✅ Checkpoint: Improved code navigation

**Validation**: Notebook is < 300 lines, clear flow

### Phase 3: Polish & UX (P2) - 1 hour
**Goal**: Enhance presentation and interactivity

8. **Layout Improvements** (R4.1, R4.2)
   - Combine widget + state display
   - Integrate table with widget
   - ✅ Checkpoint: Less scrolling, clearer reactivity

9. **Consolidate Export** (R4.3)
   - Merge export cells
   - ✅ Checkpoint: Streamlined UX

10. **Interactive Hints** (R5.1)
    - Add callouts for key features
    - ✅ Checkpoint: Better user guidance

**Validation**: Smooth, intuitive user experience

### Phase 4: Final Review (30 minutes)
**Goal**: Gallery submission readiness

11. **Code Quality Check**
    - Remove debug code
    - Verify all cells run in order
    - Check for unused variables

12. **Documentation Review**
    - Spelling/grammar
    - Accurate technical details
    - Links work

13. **Testing**
    - Fresh `marimo run` on clean environment
    - Test all interactive features
    - Verify export functionality

14. **Attribution**
    - Verify "Generated by Claude Sonnet 4.5" comments
    - Add proper credits
    - License information

**Validation**: Ready for `marimo gallery submit`

---

## Gallery Submission Checklist

### Requirements Validation

- [ ] **PEP 723 Compliance**: Script metadata block present and valid
- [ ] **Self-Containment**: Runs without external setup or files
- [ ] **Clean Imports**: No sys.path manipulation or hacky imports
- [ ] **Documentation**: Clear, concise, focused on demo not docs
- [ ] **Interactivity**: Interactive features work and are explained
- [ ] **Code Quality**: Clean, readable, well-organized
- [ ] **Length**: Appropriate (150-400 lines)
- [ ] **Educational Value**: Teaches something useful
- [ ] **Uniqueness**: Demonstrates unique capabilities (custom widget!)
- [ ] **Reproducibility**: Others can run and learn from it

### Pre-Submission Checks

- [ ] Run `marimo run demos/wavesurfer_demo.py` on fresh environment
- [ ] All cells execute without errors
- [ ] Widget displays correctly
- [ ] Two-way sync works (table ↔ waveform)
- [ ] Export produces valid JSON
- [ ] No broken links in documentation
- [ ] No placeholder text (TODO, FIXME, etc.)
- [ ] Proper attribution and license

### Submission Process

1. **Review Gallery Guidelines**: https://github.com/marimo-team/gallery-examples
2. **Fork Repository**: marimo-team/gallery-examples
3. **Add Notebook**: Place in appropriate category (library/external)
4. **Update README**: Add entry to gallery index
5. **Create PR**: Clear description of what demo showcases
6. **Address Feedback**: Respond to maintainer comments

---

## Expected Outcomes

### Before Refactoring
- ❌ Cannot run without external files
- ❌ No dependency declaration
- ⚠️ Documentation is verbose
- ⚠️ Some complex cells
- ✅ Good widget demonstration
- ✅ Clear interactive features

### After Refactoring
- ✅ Self-contained, runs immediately
- ✅ PEP 723 compliant
- ✅ Concise documentation (< 300 lines)
- ✅ Streamlined cell structure
- ✅ Gallery-standard organization
- ✅ Submission-ready

### Success Metrics
1. **Installation Time**: 0 seconds (auto-install deps)
2. **Time to First Interaction**: < 10 seconds from `marimo run`
3. **Learning Curve**: Beginner-friendly
4. **Code Clarity**: Each cell's purpose is obvious
5. **Submission Acceptance**: High likelihood of merge

---

## Risks & Mitigation

### Risk 1: Embedded Audio Too Large
- **Impact**: Bloats notebook file size
- **Likelihood**: Low (3-sec MP3 is ~4-50KB)
- **Mitigation**: Use highly compressed MP3 or synthetic audio
- **Threshold**: Keep notebook < 100KB total

### Risk 2: Inlining Widget Code Adds Complexity
- **Impact**: Notebook becomes harder to read
- **Likelihood**: Medium
- **Mitigation**:
  - Use code folding / hide_code
  - Put widget in separate cell with clear intro
  - Alternative: Package widget for pip install

### Risk 3: Removing Features to Simplify
- **Impact**: Demo loses educational value
- **Likelihood**: Low
- **Mitigation**: Preserve all core features (waveform, regions, sync, export)

### Risk 4: Gallery Standards Change
- **Impact**: Refactoring may not match updated standards
- **Likelihood**: Low
- **Mitigation**: Check gallery repo for recent PRs before final submission

---

## Alternative Approaches Considered

### Approach A: Minimal Demo (Rejected)
- **Description**: Strip down to bare-bones widget display
- **Pros**: Shortest, simplest
- **Cons**: Loses educational value, doesn't showcase full capabilities
- **Verdict**: Too minimal, defeats purpose

### Approach B: Multiple Notebooks (Considered)
- **Description**: Create basic + advanced versions
- **Pros**: Serves multiple skill levels
- **Cons**: Maintenance burden, gallery may not accept both
- **Verdict**: Possible future enhancement, not for initial submission

### Approach C: Interactive Tutorial (Considered)
- **Description**: Add mo.ui.quiz or interactive learning elements
- **Pros**: Highly educational
- **Cons**: Scope creep, not standard for gallery
- **Verdict**: Out of scope for initial version

### Approach D: Live Audio Recording (Rejected)
- **Description**: Use browser audio API to record user's mic
- **Pros**: Ultimate self-containment
- **Cons**: Browser permissions, complexity, not marimo-standard
- **Verdict**: Too complex, browser security issues

---

## Dependencies & Requirements

### Python Version
- **Minimum**: 3.11 (marimo requirement)
- **Recommended**: 3.13 (project standard)

### Core Dependencies
- `marimo >= 0.10.0` - Notebook framework
- `anywidget >= 0.9.0` - Widget framework
- `traitlets >= 5.0.0` - State synchronization

### Optional Dependencies (for development)
- `base64` - Standard library (audio embedding)
- `json` - Standard library (export functionality)

### External Resources (CDN)
- wavesurfer.js v7 (ESM): `https://cdn.jsdelivr.net/npm/wavesurfer.js@7/`
- RegionsPlugin: `https://cdn.jsdelivr.net/npm/wavesurfer.js@7/dist/plugins/regions.esm.js`
- TimelinePlugin: `https://cdn.jsdelivr.net/npm/wavesurfer.js@7/dist/plugins/timeline.esm.js`

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Prioritize recommendations** based on goals
3. **Create minimal audio sample** (3-second clip)
4. **Begin Phase 1** (Critical Blockers)
5. **Test incrementally** after each phase
6. **Iterate based on feedback**
7. **Submit to gallery** when ready

---

## Appendix: Gallery Examples Reference

### Analyzed Notebooks

1. **scatter-demo.py** - Custom widget, 60 lines
   - URL: https://github.com/marimo-team/gallery-examples/blob/main/notebooks/drawdata/scatter-demo.py
   - Key Takeaway: Minimal, focused, PEP 723 compliant

2. **movies.py** - Dashboard, ~15 cells
   - URL: https://github.com/marimo-team/gallery-examples/blob/main/notebooks/dashboard/movies.py
   - Key Takeaway: State management, reactive filtering, layouts

3. **neo4jwidget.py** - External widget
   - URL: https://github.com/marimo-team/gallery-examples/blob/main/notebooks/external/neo4jwidget.py
   - Key Takeaway: Clean external widget integration, PEP 723

4. **altair-demo.py** - Library showcase, 6 cells
   - URL: https://github.com/marimo-team/gallery-examples/blob/main/notebooks/library/altair-demo.py
   - Key Takeaway: Progressive complexity, concise documentation

5. **simpsons-paradox.py** - Educational, ~30 cells
   - URL: https://github.com/marimo-team/gallery-examples/blob/main/notebooks/analysis/simpsons-paradox.py
   - Key Takeaway: Hide code for complex sections, narrative structure

### Gallery Repository
- **Main Repo**: https://github.com/marimo-team/gallery-examples
- **Submission Guidelines**: Check repo README and CONTRIBUTING.md
- **Category Options**:
  - `notebooks/library/` - Library/framework showcases
  - `notebooks/external/` - External widget integrations (our target)
  - `notebooks/dashboard/` - Data dashboards
  - `notebooks/analysis/` - Analytical notebooks

---

## Document Version Control

- **Version**: 1.0
- **Date**: 2026-03-16
- **Author**: Claude Sonnet 4.5
- **Status**: Planning Complete
- **Next Review**: After Phase 1 completion

---

**END OF PLAN**
