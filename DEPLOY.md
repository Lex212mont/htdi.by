# Deployment Guide — HTDI.by

## Канон

| Что | Значение |
|-----|----------|
| Репозиторий | **`Lex212mont/htdi.by`** (`main`) |
| Cloudflare Pages | проект **`htdi-news`** |
| Домены | `htdi.by`, `www.htdi.by` |
| Account ID | `188d8d792aabe0caf22fd04e414a9920` |
| Деплой | **`git push origin main`** → CF Git auto-build |

Архив `Lex212mont/htd.by` — не трогать.

Стек: статика + `_worker.js`. `/api/expert-news` читает `expert-news.json` с GitHub raw (`Lex212mont/htdi.by`).

## Как выкатить

```bash
cd /Users/lex/Projects/htdi.by
# правки → commit
git push origin main
curl -sS https://htdi.by/api/expert-news | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))'
```

## Переменные Cloudflare Pages

Dashboard → **htdi-news** → Settings → Variables (Production + Preview):

| Variable | Назначение |
|----------|------------|
| `ADMIN_PASSWORD` | админ-форма |
| `GITHUB_TOKEN` | fine-grained PAT на `Lex212mont/htdi.by` (Contents R/W) |

## Workflows

| Файл | Роль |
|------|------|
| *(CF Git)* | основной деплой при push в `main` |
| `deploy.yml` | ручной wrangler backup → `--project-name=htdi-news` |
| `update-expert-news.yml` | обновление `expert-news.json` (без Telegram) |
| `daily-ntdi-news.yml` | legacy TG, только dispatch |

## Troubleshooting

- Старые новости → CF не на `htdi.by`: Settings → Builds → Connect `Lex212mont/htdi.by`, branch `main`.
- Wrangler 10000 → битый токен; основной путь — Git, не wrangler.
- Project name: **`htdi-news`**, не `htdi-by`.

Обновлено: 2026-08-02
