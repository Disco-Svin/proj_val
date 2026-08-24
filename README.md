# proj_val

Ежедневная Cursor-автоматизация пишет `reports/outbox.md` и пушит его. В Telegram отчёт шлёт GitHub Action — Cursor-секреты в VM автоматизации не инжектятся.

Секреты кладите сюда, не в git:

https://github.com/Disco-Svin/proj_val/settings/secrets/actions

Имена: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_USER_ID`. Перед первой отправкой напишите боту `/start`.

Локально, если секреты есть в окружении:

```
python3 -m telegram_notify check
python3 -m telegram_notify send --file reports/outbox.md
```

Промпт автоматизации: `prompts/daily-automation.md`.
