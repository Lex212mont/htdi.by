# Deployment Guide — HTDI.by

## Обзор деплоя

Проект деплоится на **Cloudflare Pages** (статический сайт + `_worker.js` как Functions).

- Frontend: один файл `index.html` (всё в нём).
- Динамика: `_worker.js` (RSS-прокси + API экспертных новостей).
- Ежедневный Telegram-дайджест: отдельный GitHub Action.

## Обязательные секреты и переменные окружения

### 1. GitHub Secrets (Settings → Secrets and variables → Actions)

| Secret                    | Для чего                              | Как получить |
|---------------------------|---------------------------------------|--------------|
| `CLOUDFLARE_API_TOKEN`    | Деплой через wrangler-action          | Cloudflare Dashboard → My Profile → API Tokens (нужен `Account: Cloudflare Pages:Edit`) |
| `CLOUDFLARE_ACCOUNT_ID`   | Деплой на конкретный аккаунт          | Cloudflare Dashboard → боковая панель (внизу) |
| `TELEGRAM_BOT_TOKEN`      | Ежедневный дайджест в Telegram        | @BotFather |

### 2. Cloudflare Pages Environment Variables (НЕ в GitHub!)

Перейди в Cloudflare Dashboard → Pages → твой проект `htdi-by` → **Settings → Environment variables**

**Production + Preview** (обязательно для обоих):

| Variable            | Значение                              | Примечание |
|---------------------|---------------------------------------|----------|
| `ADMIN_PASSWORD`    | Сложный пароль для публикации экспертных новостей через форму на сайте | Придумать самостоятельно |
| `GITHUB_TOKEN`      | Fine-grained Personal Access Token    | **Обязательно** с правами только на этот репозиторий: `Contents: Read and write` |

**Как создать GITHUB_TOKEN:**
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens.
2. Repository access: только `Lex212mont/htdi.by`.
3. Permissions → Repository permissions → **Contents** → Read and write.
4. Сгенерировать и сохранить.

**Важно:** эти две переменные **не** должны быть в GitHub Secrets. Они читаются воркером во время выполнения на Cloudflare (`env.ADMIN_PASSWORD`, `env.GITHUB_TOKEN`).

## Настройка проекта Cloudflare Pages

1. Создай новый проект Pages.
2. Подключи репозиторий `Lex212mont/htdi.by`.
3. Build settings:
   - Framework preset: **None**
   - Build command: **оставь пустым**
   - Output directory: **.** (корень)
4. Добавь переменные окружения (см. выше).
5. После первого деплоя через GitHub Action проект подхватится.

## Как работает деплой

- При `push` в ветку `main` срабатывает `.github/workflows/deploy.yml`.
- Используется `cloudflare/wrangler-action`.
- Команда: `pages deploy . --project-name=htdi-by`.

Ручной триггер деплоя:
- Можно закоммитить пустой файл `.trigger-deploy` (в нём просто timestamp).
- Или запустить workflow вручную через GitHub UI.

## Ежедневный дайджест в Telegram

Workflow `daily-ntdi-news.yml`:
- Запускается по cron (08:30 MSK) + можно запустить вручную (`workflow_dispatch`).
- Требует только `TELEGRAM_BOT_TOKEN` (GitHub Secret).
- Скрипт: `.github/scripts/post_news.py`.

## Проверка после деплоя

- Открой сайт.
- Нажми "Обновить" — должно загрузиться много источников.
- Проверь раздел "Экспертные материалы НТДИ".
- Чтобы протестировать публикацию экспертной новости — открой админ-форму (пароль из `ADMIN_PASSWORD`).

## Troubleshooting

- **Деплой падает** — проверь, что `CLOUDFLARE_API_TOKEN` и `CLOUDFLARE_ACCOUNT_ID` свежие и имеют нужные права.
- **Экспертные новости не грузятся / не добавляются** — убедись, что `ADMIN_PASSWORD` и `GITHUB_TOKEN` добавлены именно в Cloudflare Pages Environment variables (а не только в GitHub).
- **GITHUB_TOKEN не работает** — убедись, что токен fine-grained и имеет права Contents: Read and write именно на этот репозиторий.
- **Кэш** — после изменений в `_headers` или воркере может потребоваться purge cache в Cloudflare.

## Полезные команды (локально)

```bash
# Деплой вручную (если установлен wrangler)
wrangler pages deploy . --project-name=htdi-by

# Посмотреть логи воркера
# В Cloudflare Pages → Functions → Logs
```

## Безопасность

- `GITHUB_TOKEN` даёт право писать в репозиторий. Держи его в секрете.
- `ADMIN_PASSWORD` — используй длинный случайный пароль.
- Рекомендуется периодически ротировать токены.

---

Обновлено: 2026-07-27 (миграция в htdi.by)
