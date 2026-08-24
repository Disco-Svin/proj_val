from __future__ import annotations

import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from telegram_notify.client import (
    TelegramError,
    api_call,
    check,
    send_file,
    send_text,
    split_message,
)
from telegram_notify.__main__ import main


def _http_error(status: int, payload: dict) -> HTTPError:
    raw = json.dumps(payload).encode("utf-8")
    return HTTPError(
        "https://api.telegram.org/botTOKEN/getMe",
        status,
        "Error",
        hdrs=None,
        fp=io.BytesIO(raw),
    )


class SplitMessageTests(unittest.TestCase):
    def test_short_message_stays_one_chunk(self) -> None:
        self.assertEqual(split_message("hello"), ["hello"])

    def test_empty_message_fails(self) -> None:
        with self.assertRaises(TelegramError):
            split_message("   ")

    def test_long_message_splits_on_paragraph(self) -> None:
        first = "A" * 100
        second = "B" * 100
        chunks = split_message(f"{first}\n\n{second}", limit=150)
        self.assertEqual(chunks, [first, second])


class ClientTests(unittest.TestCase):
    def test_missing_token(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(TelegramError, "TELEGRAM_BOT_TOKEN"):
                api_call("getMe")

    def test_check_success(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_USER_ID": "99"}
        with patch.dict("os.environ", env, clear=True):
            with patch("telegram_notify.client.urllib.request.urlopen") as urlopen:
                urlopen.side_effect = [
                    _response({"ok": True, "result": {"username": "val_bot"}}),
                    _response({"ok": True, "result": {"id": 99, "type": "private"}}),
                ]
                result = check()
        self.assertEqual(result["bot"]["username"], "val_bot")
        self.assertEqual(result["chat"]["id"], 99)

    def test_chat_not_found_is_humanized(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_USER_ID": "99"}
        error = _http_error(400, {"ok": False, "description": "Bad Request: chat not found"})
        with patch.dict("os.environ", env, clear=True):
            with patch("telegram_notify.client.urllib.request.urlopen", side_effect=error):
                with self.assertRaisesRegex(TelegramError, r"/start"):
                    check()

    def test_send_file(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_USER_ID": "99"}
        report = Path("reports") / "sample.md"
        report.parent.mkdir(exist_ok=True)
        report.write_text("# status\nall good\n", encoding="utf-8")
        with patch.dict("os.environ", env, clear=True):
            with patch("telegram_notify.client.urllib.request.urlopen") as urlopen:
                urlopen.return_value = _response({"ok": True, "result": {"message_id": 1}})
                sent = send_file(report)
        self.assertEqual(len(sent), 1)
        request = urlopen.call_args[0][0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["chat_id"], "99")
        self.assertIn("all good", payload["text"])

    def test_send_missing_file(self) -> None:
        with self.assertRaisesRegex(TelegramError, "File not found"):
            send_file("reports/does-not-exist.md")

    def test_network_error(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_USER_ID": "99"}
        with patch.dict("os.environ", env, clear=True):
            with patch(
                "telegram_notify.client.urllib.request.urlopen",
                side_effect=URLError("timed out"),
            ):
                with self.assertRaisesRegex(TelegramError, "request failed"):
                    send_text("hi")


class CliTests(unittest.TestCase):
    def test_check_cli(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_USER_ID": "99"}
        with patch.dict("os.environ", env, clear=True):
            with patch("telegram_notify.client.urllib.request.urlopen") as urlopen:
                urlopen.side_effect = [
                    _response({"ok": True, "result": {"username": "val_bot"}}),
                    _response({"ok": True, "result": {"id": 99}}),
                ]
                code = main(["check"])
        self.assertEqual(code, 0)

    def test_send_cli_requires_file(self) -> None:
        with self.assertRaises(SystemExit):
            main(["send"])


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _response(payload: dict) -> _FakeResponse:
    return _FakeResponse(payload)


if __name__ == "__main__":
    unittest.main()
