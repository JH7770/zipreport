---
name: draft-wordpress-post
description: Draft zipreport.kr WordPress-ready Markdown articles from this repository's real estate data, report generators, templates, and local assets. Use when the user asks to write, generate, prepare, revise, or make a blog post draft before WordPress upload, including monthly apartment reports, apartment living-infrastructure reports, market-data summaries, or article drafts that should stay local as Markdown.
---

# Draft WordPress Post

## Overview

Create local Markdown drafts for zipreport.kr using the repository's existing scripts and content standards. Keep publishing separate: use this skill to produce and audit drafts, then use `$publish-wordpress-post` only when the user asks to upload or update WordPress.

## Choose The Draft Type

- Monthly region report: use `scripts/generate_post.py`.
- Batch monthly drafts: use `scripts/run_batch.py` without `--publish`.
- Apartment living-infrastructure report: use `scripts/generate_apartment_living_report.py`.
- Existing Markdown polish or quality check: use `scripts/audit_markdown.py` and edit the draft directly when requested.

Prefer generated reports over freeform writing when the required data exists in SQLite or collectors. Do not invent transaction numbers, rankings, school counts, subway access, prices, or source dates.

## Preflight

1. Work from the repository root.
2. Check the requested region code, deal month, apartment name, or source Markdown path.
3. Confirm required data exists locally unless the user explicitly asks to collect live data.
4. Keep `.env` values private. Report missing variable names only.
5. Inspect `--help` for a script when arguments may have changed.

## Generate Drafts

Use the smallest command matching the request.

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605
```

For all report variants from one region/month:

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605 --all
```

For LLM-polished wording and a featured image, only when `LLM_API_KEY` or `OPENAI_API_KEY` is configured:

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605 --all --use-llm --generate-image
```

For living-infrastructure drafts:

```powershell
python scripts/generate_apartment_living_report.py --lawd-cd 11710 --deal-ym 202605 --apartment-name "올림픽파크포레온"
```

For batch drafts without publishing:

```powershell
python scripts/run_batch.py --deal-ym 202605 --skip-collect
```

## Writing Rules

- Preserve factual values from collectors, analyzers, templates, and user-provided source files.
- Use Korean suitable for a practical real estate blog: specific, restrained, and useful to readers comparing neighborhoods or apartments.
- Explain caveats when data is missing, sparse, old, or based on a limited sample.
- Keep WordPress-ready Markdown structure: one `#` title, clear `##` sections, tables where comparison helps, and image Markdown only when the referenced asset exists.
- Avoid unsupported investment promises, exaggerated certainty, and fabricated local details.

## Audit And Output

Run the Markdown audit before handing off a draft:

```powershell
python scripts/audit_markdown.py output/REPORT.md
```

If the audit fails, fix the Markdown or explain the unresolved issue. In the final response, report the generated file path, audit result, and any missing data or assumptions.

Do not upload the draft from this skill. If the user asks to upload, invoke `$publish-wordpress-post` after the draft passes audit.
