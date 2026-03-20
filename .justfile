# Torah Audio-Visual Synchronization - Justfile
# Run commands with: just <command>

# Default recipe - show available commands
default:
    @just --list

# Development Setup
# ================

# Install dependencies using UV
install:
    uv sync

# Install all dependencies including dev extras
install-all:
    uv sync --all-extras

# Download Hebrew font
font:
    mkdir -p fonts
    curl -L "https://github.com/google/fonts/raw/main/ofl/frankruhl/FrankRuhl-Regular.ttf" \
      -o fonts/FrankRuhl-Regular.ttf

# Setup project (install deps + font + create directories)
setup: install font
    mkdir -p data/audio
    mkdir -p data/cache
    mkdir -p data/timestamp_maps
    mkdir -p output/videos
    mkdir -p output/logs
    mkdir -p output/errors

# Torah Sync CLI
# ==============

# Process single audio file
sync file:
    uv run torah-sync "{{file}}"

# Process single file with custom output directory
sync-to file output:
    uv run torah-sync -o "{{output}}" "{{file}}"

# Batch process all files in directory
batch dir:
    uv run torah-sync batch "{{dir}}"

# Batch process with parallelism
batch-parallel dir workers="4":
    uv run torah-sync batch --parallel {{workers}} "{{dir}}"

# Retry failed items from manifest
retry manifest:
    uv run torah-sync --retry-failed "{{manifest}}"

# Process with JSON output
sync-json file:
    uv run torah-sync --json "{{file}}"

# Process sample files (Haazinu Rishon and Sheni)
sample:
    uv run torah-sync process "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"
    uv run torah-sync process "data/audio/פרשת האזינו - שני - נוסח אשכנז.mp4"

# Testing
# =======

# Run all tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Run specific test file
test-file file:
    uv run pytest "{{file}}"

# Run tests matching pattern
test-match pattern:
    uv run pytest -k "{{pattern}}"

# Run contract tests only
test-contract:
    uv run pytest tests/contract/

# Run integration tests only
test-integration:
    uv run pytest tests/integration/

# Run unit tests only
test-unit:
    uv run pytest tests/unit/

# Code Quality
# ============

# Run all linting checks
lint:
    uv run ruff check .

# Run linting with auto-fix
lint-fix:
    uv run ruff check . --fix

# Format code
format:
    uv run ruff format .

# Type checking
types:
    uv run mypy src/

# Run all quality checks (lint + types + tests)
check: lint types test

# Pre-commit
# ==========

# Install pre-commit hooks
pre-commit-install:
    uv run pre-commit install

# Run pre-commit on all files
pre-commit:
    uv run pre-commit run --all-files

# Run pre-commit on staged files only
pre-commit-staged:
    uv run pre-commit run

# Configuration
# =============

# Validate configuration file
config-validate:
    uv run python -c "from dynaconf import Dynaconf; settings = Dynaconf(settings_files=['settings.toml']); print('Config valid')"

# Show current configuration
config-show:
    uv run python -c "from dynaconf import Dynaconf; settings = Dynaconf(settings_files=['settings.toml']); print(settings.as_dict())"

# Utilities
# =========

# Clean cache and temporary files
clean:
    rm -rf .cache
    rm -rf data/cache/*
    rm -rf __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -rf .ruff_cache
    rm -rf htmlcov
    rm -rf .coverage

# Clean output files
clean-output:
    rm -rf output/videos/*
    rm -rf output/logs/*
    rm -rf output/errors/*

# Clean everything (cache + output)
clean-all: clean clean-output

# Check audio file naming convention
validate-audio dir="data/audio":
    @echo "Validating audio filenames in {{dir}}..."
    @find "{{dir}}" -type f \( -name "*.mp4" -o -name "*.mp3" -o -name "*.wav" \) | while read file; do \
        basename="$$(basename "$$file")"; \
        if echo "$$basename" | grep -qE '^פרשת .+ - (ראשון|שני|שלישי|רביעי|חמישי|שישי|שביעי|מפטיר|הפטרה) - נוסח אשכנז\.(mp4|mp3|wav)$$'; then \
            echo "✓ $$basename"; \
        else \
            echo "✗ $$basename (invalid format)"; \
        fi; \
    done

# List all audio files
list-audio dir="data/audio":
    @find "{{dir}}" -type f \( -name "*.mp4" -o -name "*.mp3" -o -name "*.wav" \) -exec basename {} \;

# Show video file info
video-info file:
    ffprobe -v error -show_entries stream=width,height,codec_name,duration -of default=noprint_wrappers=1 "{{file}}"

# Play output video (macOS)
play file:
    open "{{file}}"

# Development
# ===========

# Start development shell with venv activated
shell:
    @echo "Starting UV shell..."
    uv run bash

# Run Python REPL with project context
repl:
    uv run python

# Watch and run tests on file changes (requires pytest-watch)
watch:
    uv run ptw

# Specification Workflow
# ======================

# Run specification workflow
specify:
    @echo "Run: /speckit.specify"

# Run clarification workflow
clarify:
    @echo "Run: /speckit.clarify"

# Run planning workflow
plan:
    @echo "Run: /speckit.plan"

# Generate tasks
tasks:
    @echo "Run: /speckit.tasks"

# Git
# ===

# Stage all spec files
git-add-specs:
    git add specs/001-torah-audio-text-sync/

# Commit with conventional commit format
git-commit msg:
    git commit -m "{{msg}}"

# Quick commit of spec changes
commit-spec msg:
    git add specs/001-torah-audio-text-sync/
    git commit -m "docs(spec): {{msg}}"

# Quick commit of plan changes
commit-plan msg:
    git add specs/001-torah-audio-text-sync/
    git commit -m "docs(plan): {{msg}}"

# Help
# ====

# Show help for torah-sync CLI
help:
    uv run torah-sync --help

# Show version
version:
    uv run torah-sync --version

demo-wave:
    uv run marimo edit demos/wavesurfer_demo.py --watch

run-app:
    uv run marimo edit src/apps/alignment_editor.py --watch

kill-db:
    kill -9 $(lsof -t data/torah_sync.duckdb)

# render-video {aliya_id}: