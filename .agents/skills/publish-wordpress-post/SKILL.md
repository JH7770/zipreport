---
name: publish-wordpress-post
description: Upload this project's generated Markdown reports to WordPress, update an existing WordPress post, attach a featured image, and assign categories or tags through the repository's publishing scripts. Use when the user asks to upload, register, publish, draft, republish, or update a WordPress article from a Markdown file in this project, or asks to generate reports and send them to WordPress.
---

# Publish WordPress Post

Use the repository's existing Python scripts from the project root. Keep credentials in `.env`; never print `WORDPRESS_APP_PASSWORD` or include it in commands, logs, or responses.

## Choose The Operation

- Create a new post from Markdown: use `scripts/publish_to_wordpress.py`.
- Update an existing post ID: use `scripts/update_wordpress_post.py`.
- Generate monthly reports and upload them in one run: use `scripts/run_batch.py --publish`.

Default to WordPress `draft`. Use `--status publish` only when the user explicitly asks to make the post publicly visible. Treat words such as "upload" or "register" as a draft request unless public publication is unambiguous.

## Preflight

1. Run commands from the repository root.
2. Confirm the Markdown file exists and contains a non-empty `# ` title.
3. Confirm `.env` provides non-empty `WORDPRESS_URL`, `WORDPRESS_USERNAME`, and `WORDPRESS_APP_PASSWORD` without displaying their values.
4. Confirm an optional featured image exists before uploading.
5. Inspect `python scripts/publish_to_wordpress.py --help` if the script arguments have changed.

Stop before making a network request when required input is missing. Report only the missing variable or file name.

## Create A Post

Run the smallest command matching the request:

```powershell
python scripts/publish_to_wordpress.py --file output/REPORT.md --status draft
```

Add optional metadata only when supplied or clearly inferable:

```powershell
python scripts/publish_to_wordpress.py `
  --file output/REPORT.md `
  --status draft `
  --featured-image output/images/FEATURED.png `
  --category 12 `
  --tag-name "실거래가" `
  --slug "seoul-apartment-report" `
  --excerpt "서울 아파트 실거래가 월간 요약"
```

Repeat `--category`, `--tag`, or `--tag-name` for multiple values. Prefer `--tag-name` when the user gives names; the publisher looks up an existing tag or creates it.

## Update A Post

Require the WordPress post ID and Markdown path:

```powershell
python scripts/update_wordpress_post.py --post-id 123 --file output/REPORT.md
```

Use `--featured-image` to replace the featured image. Add `--delete-old-featured` only when the user explicitly requests deletion of the previous media item, because deletion is irreversible. This update script saves the post as a draft.

## Generate And Upload

For a full monthly run:

```powershell
python scripts/run_batch.py --deal-ym 202605 --publish --status draft
```

Use `--skip-collect` when the user asks to use existing database data. Use `--generate-image` to create and attach one featured image per region. Repeat `--lawd-cd`, `--category`, or `--tag` as needed.

## Verify The Result

Capture the command output and report the returned post ID, status, and link. If the request fails, summarize the HTTP status or exception without exposing credentials. Do not retry with `publish` after a draft failure, and do not claim success unless the script returns successfully.
