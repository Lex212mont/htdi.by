# Deployment Guide — HTDI.by

## Канон (порядок)

| Что | Значение |
|-----|----------|
| **Править / пушить** | только **`Lex212mont/htdi.by`** (`main`) |
| Cloudflare Pages | проект **`htdi-news`** |
| Домены | `htdi.by`, `www.htdi.by` |
| Account ID | `188d8d792aabe0caf22fd04e414a9920` |
| **Деплой** | `./scripts/deploy-htdi.sh` |

Скрипт: пушит `htdi.by` и зеркалит в **`Lex212mont/htd.by`** (`master`) — от него CF ещё собирает, пока GitHub App Cloudflare не получит доступ к `htdi.by`.

**Архив:** `htd.by` / старый `htdi-news` — не править руками.

Стек: статика + `_worker.js`. `/api/expert-news` читает `expert-news.json` с GitHub raw (`Lex212mont/htdi.by`).

## Как выкатить

```bash
cd /Users/lex/Projects/htdi.by
# …правки, commit…
./scripts/deploy-htdi.sh
curl -sS https://htdi.by/api/expert-news | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))'
```

## Когда станет совсем чисто

1. GitHub → Settings → Applications → **Cloudflare Pages** → Repository access → добавить **`htdi.by`**.
2. CF → htdi-news → Settings → Builds → Disconnect → Connect **`Lex212mont/htdi.by`**, branch **`main`**.
3. Тогда достаточно `git push origin main`; скрипт-зеркало можно убрать.

## Переменные Cloudflare Pages

Dashboard → **htdi-news** → Settings → Variables (Production + Preview):

| Variable | Назначение |
|----------|------------|
| `ADMIN_PASSWORD` | админ-форма |
| `GITHUB_TOKEN` | fine-grained PAT на `Lex212mont/htdi.by` (Contents R/W), если форма пишет в репо |

## Workflows в `htdi.by`

| Файл | Роль |
|------|------|
| `update-expert-news.yml` | обновление `expert-news.json` (без Telegram) |
| `deploy.yml` | ручной wrangler backup → `--project-name=htdi-news` |
| `daily-ntdi-news.yml` | legacy TG, только dispatch |

## Troubleshooting

- Старые новости → забыли `./scripts/deploy-htdi.sh` (пушнули только в `htdi.by`).
- Wrangler 10000 → битый `CLOUDFLARE_API_TOKEN`; основной путь — Git через зеркало, не wrangler.
- Project name всегда **`htdi-news`**, не `htdi-by`.

Обновлено: 2026-08-02
