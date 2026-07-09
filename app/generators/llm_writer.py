from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:  # pragma: no cover - exercised in dependency-free environments.
    requests = None


@dataclass(frozen=True)
class LlmRewriteConfig:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.75


def rewrite_markdown_with_llm(
    markdown: str,
    config: LlmRewriteConfig,
    report_type: str = "monthly_region_report",
) -> str:
    if not config.api_key:
        raise ValueError("LLM_API_KEY or OPENAI_API_KEY is required when --use-llm is set.")

    payload = {
        "model": config.model,
        "temperature": config.temperature,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Korean real-estate blog editor. Rewrite the provided Markdown so it "
                    "does not feel templated. Preserve every numeric value, table row, apartment name, "
                    "region name, month, disclaimer, and Markdown heading/table syntax. Do not add "
                    "investment advice or unsupported claims. Keep the result in Korean Markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Report type: {report_type}\n\n"
                    "Rewrite this report with a more natural structure and varied wording while keeping "
                    "the factual data unchanged:\n\n"
                    f"{markdown}"
                ),
            },
        ],
    }
    data = _post_chat_completion(config, payload)
    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"LLM response did not contain generated content: {data}") from exc

    if not content.startswith("#"):
        return markdown
    return content + "\n"


def _post_chat_completion(config: LlmRewriteConfig, payload: dict[str, object]) -> dict[str, object]:
    endpoint = f"{config.base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}

    if requests is not None:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    body = json.dumps(payload).encode("utf-8")
    request = Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API failed: HTTP {exc.code} {message}") from exc
