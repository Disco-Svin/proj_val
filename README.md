# proj_val

Репозиторий для ежедневной Cursor-автоматизации. Отправка в Telegram — стандартной библиотекой Python, без pip-зависимостей.

```
python3 -m telegram_notify check
python3 -m telegram_notify send --file reports/latest.md
```

Секреты: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_USER_ID`. Промпт автоматизации: `prompts/daily-automation.md`. Перед первой отправкой напишите боту `/start`.
