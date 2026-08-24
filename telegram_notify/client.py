from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = "https://api.telegram.org"
MESSAGE_LIMIT = 4096
REQUEST_TIMEOUT_SEC = 30


class TelegramError(RuntimeError):
    """Raised when Telegram credentials or API calls fail."""


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise TelegramError(f"{name} is not set")
    return value


def token() -> str:
    return _require_env("TELEGRAM_BOT_TOKEN")


def chat_id() -> str:
    return _require_env("TELEGRAM_USER_ID")


def api_call(method: str, payload: dict[str, Any] | None = None, *, bot_token: str | None = None) -> Any:
    auth = bot_token if bot_token is not None else token()
    url = f"{API_ROOT}/bot{auth}/{method}"
    body = json.dumps(payload or {}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SEC) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise TelegramError(_format_http_error(method, exc.code, raw)) from exc
    except urllib.error.URLError as exc:
        raise TelegramError(f"Telegram API request failed ({method}): {exc.reason}") from exc
    except TimeoutError as exc:
        raise TelegramError(f"Telegram API timed out ({method})") from exc

    if not parsed.get("ok"):
        raise TelegramError(_format_api_error(method, parsed))
    return parsed.get("result")


def _format_http_error(method: str, status: int, raw: str) -> str:
    description = raw
    try:
        parsed = json.loads(raw)
        description = str(parsed.get("description") or raw)
    except json.JSONDecodeError:
        pass
    return _humanize_error(method, status, description)


def _format_api_error(method: str, payload: dict[str, Any]) -> str:
    description = str(payload.get("description") or "unknown telegram error")
    status = payload.get("error_code")
    return _humanize_error(method, status, description)


def _humanize_error(method: str, status: int | None, description: str) -> str:
    lowered = description.lower()
    if "chat not found" in lowered:
        return (
            "Chat not found. Open the bot in Telegram and send /start "
            "so TELEGRAM_USER_ID can receive messages."
        )
    if "unauthorized" in lowered:
        return "Telegram rejected TELEGRAM_BOT_TOKEN (unauthorized)."
    prefix = f"Telegram API {status}: " if status is not None else "Telegram API: "
    return f"{prefix}{description} ({method})"


def check() -> dict[str, Any]:
    bot = api_call("getMe")
    try:
        chat = api_call("getChat", {"chat_id": chat_id()})
    except TelegramError:
        raise
    return {"bot": bot, "chat": chat}


def split_message(text: str, limit: int = MESSAGE_LIMIT) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        raise TelegramError("Message is empty")
    if len(cleaned) <= limit:
        return [cleaned]

    chunks: list[str] = []
    remaining = cleaned
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        window = remaining[:limit]
        cut = window.rfind("\n\n")
        if cut < limit // 4:
            cut = window.rfind("\n")
        if cut < limit // 4:
            cut = window.rfind(" ")
        if cut < limit // 4:
            cut = limit
        piece = remaining[:cut].rstrip()
        if not piece:
            piece = remaining[:limit]
            cut = limit
        chunks.append(piece)
        remaining = remaining[cut:].lstrip()
    return chunks


def send_text(text: str) -> list[Any]:
    destination = chat_id()
    results = []
    for chunk in split_message(text):
        results.append(
            api_call(
                "sendMessage",
                {
                    "chat_id": destination,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
            )
        )
    return results


def send_file(path: str | Path) -> list[Any]:
    file_path = Path(path)
    if not file_path.is_file():
        raise TelegramError(f"File not found: {file_path}")
    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        raise TelegramError(f"File is empty: {file_path}")
    return send_text(text)
