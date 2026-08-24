"""Send automation reports to Telegram using stdlib only."""

from .client import TelegramError, check, send_file, send_text

__all__ = ["TelegramError", "check", "send_file", "send_text"]
