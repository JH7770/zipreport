# Repository Guidelines

## Project Purpose

This repository exists to generate and publish WordPress blog posts for https://zipreport.kr/.

## Project Structure & Module Organization

This is a Python report-generation project. Core package code lives in `app/`: collectors fetch external data, analyzers shape market insights, generators render Markdown and images, publishers handle WordPress output, and `db/` owns SQLite models and persistence. Operational entry points are in `scripts/`, reusable report layouts are in `templates/`, static images and captures are in `assets/`, setup notes are in `docs/`, tests are in `tests/`, and generated files belong in `output/` or `data/`.

## Build, Test, and Development Commands

Create a local environment and install runtime dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Useful local commands:

```powershell
python scripts/load_sample_data.py
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605
python scripts/run_batch.py --deal-ym 202605 --skip-collect
python scripts/audit_markdown.py output/202605_11500_monthly_report.md
python -m unittest discover -s tests
```

Use live collection or WordPress publishing commands only after `.env` is configured.

## Coding Style & Naming Conventions

Use Python 3.12-compatible code, 4-space indentation, type hints for public functions and data structures, and `from __future__ import annotations` in new modules when annotations are used. Keep modules named in `snake_case.py`, classes in `PascalCase`, functions and variables in `snake_case`, and constants in `UPPER_SNAKE_CASE`. Prefer small functions around one responsibility: fetching, parsing, analyzing, rendering, or publishing.

## Testing Guidelines

Tests use the standard `unittest` framework and live under `tests/` with filenames like `test_pipeline.py` and methods named `test_*`. Mock network calls and WordPress requests; avoid tests that require real API keys. Add coverage for collectors, parsers, report rendering, database writes, and Markdown audit behavior when changing those areas.

## Commit & Pull Request Guidelines

The current history uses concise imperative commit subjects, for example `Add batch report generation and WordPress publishing`. Keep commits focused and mention the user-visible behavior changed. Pull requests should include a short summary, test command output, linked issue or task when available, and sample generated Markdown or screenshots when report layout or image output changes.

## Security & Configuration Tips

Copy `.env.example` to `.env` and keep real API keys, WordPress credentials, and LLM keys out of git. Prefer `DEFAULT_STATUS=draft` for publishing tests. Treat `data/`, `output/`, and `logs/` as local/generated artifacts unless a fixture is intentionally added.
