# HTDI.by

**HTDI.by** — IT-агрегатор новостей Беларуси и мировых трендов в области высоких технологий, цифровой инфраструктуры, ИИ, кибербезопасности и регулирования.

Репозиторий создан 27.07.2026 как основная рабочая версия (миграция с `htdi-news`).

## Структура

- `index.html` — основной фронтенд (всё в одном файле)
- `_worker.js` — Cloudflare Pages Functions (RSS-прокси + API экспертных новостей)
- `data/sources.json` — список RSS-источников
- `expert-news.json` — экспертные материалы НТДИ
- `.github/workflows/` — деплой и ежедневный Telegram-дайджест
- `DEPLOY.md` — подробная инструкция по настройке Cloudflare Pages и секретов

## Быстрый старт

1. Подключи репозиторий к Cloudflare Pages (project name: `htdi-by`)
2. Добавь Environment Variables в Cloudflare:
   - `ADMIN_PASSWORD`
   - `GITHUB_TOKEN` (fine-grained, Contents: Read and write на этот репозиторий)
3. Добавь GitHub Secrets:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
   - `TELEGRAM_BOT_TOKEN` (для дайджеста)

Подробности — в [DEPLOY.md](DEPLOY.md).

---
© 2026 HTDI.by
