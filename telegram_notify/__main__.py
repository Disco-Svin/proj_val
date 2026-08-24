from __future__ import annotations

import argparse
import sys

from .client import TelegramError, check, send_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m telegram_notify")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verify TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID")

    send_parser = sub.add_parser("send", help="Send a text file to Telegram")
    send_parser.add_argument("--file", required=True, help="Path to the report file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            result = check()
            bot = result["bot"]
            chat = result["chat"]
            username = bot.get("username") or bot.get("first_name") or "?"
            print(f"ok: bot @{username}, chat {chat.get('id')}")
            return 0
        if args.command == "send":
            sent = send_file(args.file)
            print(f"sent: {args.file} ({len(sent)} message(s))")
            return 0
    except TelegramError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
