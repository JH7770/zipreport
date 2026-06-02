from __future__ import annotations

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, Request, build_opener

try:
    import requests
except ImportError:  # pragma: no cover - exercised in dependency-free environments.
    requests = None


@dataclass(frozen=True)
class WordpressPostResult:
    post_id: int
    link: str | None
    status: str


class WordpressPublisher:
    def __init__(self, url: str, username: str, app_password: str, timeout: int = 20) -> None:
        if not url or not username or not app_password:
            raise ValueError("WORDPRESS_URL, WORDPRESS_USERNAME, and WORDPRESS_APP_PASSWORD are required.")
        self.url = url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.timeout = timeout

    def publish_markdown_file(
        self,
        markdown_path: Path,
        status: str = "draft",
        categories: list[int] | None = None,
        tags: list[int] | None = None,
    ) -> WordpressPostResult:
        markdown = markdown_path.read_text(encoding="utf-8")
        title = extract_title(markdown)
        content = markdown_to_basic_html(markdown)
        payload: dict[str, Any] = {"title": title, "content": content, "status": status}
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags

        endpoint = f"{self.url}/wp-json/wp/v2/posts"
        if requests is not None:
            response = requests.post(
                endpoint,
                json=payload,
                auth=(self.username, self.app_password),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        else:
            data = self._post_with_urllib(endpoint, payload)
        return WordpressPostResult(post_id=int(data["id"]), link=data.get("link"), status=data.get("status", status))

    def _post_with_urllib(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, endpoint, self.username, self.app_password)
        opener = build_opener(HTTPBasicAuthHandler(password_mgr))
        body = json.dumps(payload).encode("utf-8")
        request = Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with opener.open(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"WordPress API failed: HTTP {exc.code} {message}") from exc


def extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "아파트 실거래가 리포트"


def markdown_to_basic_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html: list[str] = []
    in_table = False
    table_rows: list[str] = []

    for line in lines:
        if "|" in line and line.strip().startswith("|"):
            in_table = True
            table_rows.append(line)
            continue
        if in_table:
            html.extend(_table_to_html(table_rows))
            table_rows = []
            in_table = False

        if line.startswith("# "):
            html.append(f"<h1>{_escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2>{_escape(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            html.append(f"<p>{_escape(line)}</p>")
        elif line.strip():
            html.append(f"<p>{_escape(line.strip())}</p>")

    if table_rows:
        html.extend(_table_to_html(table_rows))

    return "\n".join(html)


def _table_to_html(rows: list[str]) -> list[str]:
    parsed = [[cell.strip() for cell in row.strip("|").split("|")] for row in rows]
    parsed = [row for row in parsed if not all(re.fullmatch(r":?-+:?", cell) for cell in row)]
    if not parsed:
        return []
    html = ["<table>"]
    header, *body = parsed
    html.append("<thead><tr>" + "".join(f"<th>{_escape(cell)}</th>" for cell in header) + "</tr></thead>")
    html.append("<tbody>")
    for row in body:
        html.append("<tr>" + "".join(f"<td>{_escape(cell)}</td>" for cell in row) + "</tr>")
    html.append("</tbody></table>")
    return html


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
