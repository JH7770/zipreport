from __future__ import annotations

import re
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
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


@dataclass(frozen=True)
class WordpressMediaResult:
    media_id: int
    link: str | None


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
        featured_image_path: Path | None = None,
        slug: str | None = None,
        excerpt: str | None = None,
    ) -> WordpressPostResult:
        markdown = markdown_path.read_text(encoding="utf-8")
        title = extract_title(markdown)
        content = markdown_to_basic_html(markdown)
        payload: dict[str, Any] = {"title": title, "content": content, "status": status}
        if slug:
            payload["slug"] = slug
        if excerpt:
            payload["excerpt"] = excerpt
        if featured_image_path is not None:
            payload["featured_media"] = self.upload_media(featured_image_path).media_id
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags

        data = self._post_json("posts", payload)
        return WordpressPostResult(post_id=int(data["id"]), link=data.get("link"), status=data.get("status", status))

    def get_or_create_tags(self, names: list[str]) -> list[int]:
        return [self.get_or_create_term("tags", name) for name in names]

    def get_or_create_term(self, route: str, name: str) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Term name must not be empty.")

        matches = self._get_json(route, {"search": clean_name, "per_page": 100})
        for item in matches:
            if str(item.get("name", "")).strip().lower() == clean_name.lower():
                return int(item["id"])

        data = self._post_json(route, {"name": clean_name})
        return int(data["id"])

    def upload_media(self, image_path: Path) -> WordpressMediaResult:
        if not image_path.exists():
            raise FileNotFoundError(f"Featured image does not exist: {image_path}")

        mime_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
        headers = {
            "Content-Disposition": f'attachment; filename="{image_path.name}"',
            "Content-Type": mime_type,
        }
        data = image_path.read_bytes()
        result = self._post_file("media", data, headers)
        return WordpressMediaResult(media_id=int(result["id"]), link=result.get("link"))

    def _route_endpoints(self, route: str) -> list[str]:
        clean_route = route.strip("/")
        return [
            f"{self.url}/wp-json/wp/v2/{clean_route}",
            f"{self.url}/?rest_route=/wp/v2/{clean_route}",
        ]

    def _post_json(self, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        endpoints = self._route_endpoints(route)
        for index, endpoint in enumerate(endpoints):
            last_attempt = index == len(endpoints) - 1
            if requests is not None:
                response = requests.post(
                    endpoint,
                    json=payload,
                    auth=(self.username, self.app_password),
                    timeout=self.timeout,
                )
                if response.status_code == 404 and not last_attempt:
                    continue
                response.raise_for_status()
                return response.json()
            try:
                return self._post_with_urllib(endpoint, payload)
            except RuntimeError as exc:
                if "HTTP 404" in str(exc) and not last_attempt:
                    continue
                raise
        raise RuntimeError(f"WordPress API failed for route: {route}")

    def _get_json(self, route: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        endpoints = [_append_query(endpoint, params) for endpoint in self._route_endpoints(route)]
        for index, endpoint in enumerate(endpoints):
            last_attempt = index == len(endpoints) - 1
            if requests is not None:
                response = requests.get(
                    endpoint,
                    auth=(self.username, self.app_password),
                    timeout=self.timeout,
                )
                if response.status_code == 404 and not last_attempt:
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    raise RuntimeError(f"WordPress API returned unexpected payload for route: {route}")
                return data
            try:
                return self._get_with_urllib(endpoint)
            except RuntimeError as exc:
                if "HTTP 404" in str(exc) and not last_attempt:
                    continue
                raise
        raise RuntimeError(f"WordPress API failed for route: {route}")

    def _post_file(self, route: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        endpoints = self._route_endpoints(route)
        for index, endpoint in enumerate(endpoints):
            last_attempt = index == len(endpoints) - 1
            if requests is not None:
                response = requests.post(
                    endpoint,
                    data=body,
                    headers=headers,
                    auth=(self.username, self.app_password),
                    timeout=self.timeout,
                )
                if response.status_code == 404 and not last_attempt:
                    continue
                response.raise_for_status()
                return response.json()
            try:
                return self._post_file_with_urllib(endpoint, body, headers)
            except RuntimeError as exc:
                if "HTTP 404" in str(exc) and not last_attempt:
                    continue
                raise
        raise RuntimeError(f"WordPress media upload failed for route: {route}")

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

    def _post_file_with_urllib(self, endpoint: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, endpoint, self.username, self.app_password)
        opener = build_opener(HTTPBasicAuthHandler(password_mgr))
        request = Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with opener.open(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"WordPress media upload failed: HTTP {exc.code} {message}") from exc

    def _get_with_urllib(self, endpoint: str) -> list[dict[str, Any]]:
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, endpoint, self.username, self.app_password)
        opener = build_opener(HTTPBasicAuthHandler(password_mgr))
        request = Request(endpoint, method="GET")
        try:
            with opener.open(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"WordPress API failed: HTTP {exc.code} {message}") from exc
        if not isinstance(data, list):
            raise RuntimeError("WordPress API returned unexpected payload.")
        return data


def extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "아파트 실거래가 리포트"


def markdown_to_basic_html(markdown: str) -> str:
    lines = markdown.splitlines()
    first_heading = next((index for index, line in enumerate(lines) if line.startswith("# ")), None)
    if first_heading is not None:
        lines = lines[first_heading:]
    html: list[str] = []
    in_table = False
    table_rows: list[str] = []
    list_items: list[str] = []
    quote_lines: list[str] = []

    for line in lines:
        if line.startswith(">"):
            if in_table:
                html.extend(_table_to_html(table_rows))
                table_rows = []
                in_table = False
            if list_items:
                html.extend(_list_to_html(list_items))
                list_items = []
            quote_lines.append(line[1:].lstrip())
            continue
        if quote_lines:
            html.extend(_blockquote_to_html(quote_lines))
            quote_lines = []

        if "|" in line and line.strip().startswith("|"):
            if list_items:
                html.extend(_list_to_html(list_items))
                list_items = []
            in_table = True
            table_rows.append(line)
            continue
        if in_table:
            html.extend(_table_to_html(table_rows))
            table_rows = []
            in_table = False

        if line.startswith("- "):
            list_items.append(line[2:].strip())
            continue
        if list_items:
            html.extend(_list_to_html(list_items))
            list_items = []

        if line.startswith("# "):
            html.append(f"<h1>{_inline_markdown(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2>{_inline_markdown(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            html.append(f"<h3>{_inline_markdown(line[4:].strip())}</h3>")
        elif line.startswith("!["):
            image = _image_markdown_to_html(line.strip())
            if image:
                html.append(image)
        elif line.strip() == "---":
            html.append("<hr />")
        elif line.strip():
            html.append(f"<p>{_inline_markdown(line.strip())}</p>")

    if table_rows:
        html.extend(_table_to_html(table_rows))
    if list_items:
        html.extend(_list_to_html(list_items))
    if quote_lines:
        html.extend(_blockquote_to_html(quote_lines))

    return "\n".join(html)


def _table_to_html(rows: list[str]) -> list[str]:
    parsed = [[cell.strip() for cell in row.strip("|").split("|")] for row in rows]
    parsed = [row for row in parsed if not all(re.fullmatch(r":?-+:?", cell) for cell in row)]
    if not parsed:
        return []
    html = ["<table>"]
    header, *body = parsed
    html.append("<thead><tr>" + "".join(f"<th>{_inline_markdown(cell)}</th>" for cell in header) + "</tr></thead>")
    html.append("<tbody>")
    for row in body:
        html.append("<tr>" + "".join(f"<td>{_inline_markdown(cell)}</td>" for cell in row) + "</tr>")
    html.append("</tbody></table>")
    return html


def _list_to_html(items: list[str]) -> list[str]:
    if not items:
        return []
    html = ["<ul>"]
    html.extend(f"<li>{_inline_markdown(item)}</li>" for item in items)
    html.append("</ul>")
    return html


def _blockquote_to_html(lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    if not paragraphs:
        return []
    html = ["<blockquote>"]
    html.extend(f"<p>{_inline_markdown(paragraph)}</p>" for paragraph in paragraphs)
    html.append("</blockquote>")
    return html


def _inline_markdown(value: str) -> str:
    escaped = _escape(value)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def _image_markdown_to_html(value: str) -> str | None:
    match = re.fullmatch(r"!\[([^\]]*)\]\((https?://[^)]+)\)", value)
    if not match:
        return None
    alt = _escape(match.group(1).strip())
    src = _escape(match.group(2).strip())
    return f'<figure><img src="{src}" alt="{alt}" loading="lazy" /></figure>'


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _append_query(endpoint: str, params: dict[str, Any] | None) -> str:
    if not params:
        return endpoint
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}{urlencode(params)}"
