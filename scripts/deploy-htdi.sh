#!/usr/bin/env bash
# Deploy htdi.by → Cloudflare Pages (project htdi-news).
# Canonical repo: Lex212mont/htdi.by
# CF Git still builds Lex212mont/htd.by until the Cloudflare GitHub App
# is granted access to htdi.by — this script mirrors after push.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
  echo "Refuse: not on main (on $BRANCH)"
  exit 1
fi

echo "==> push Lex212mont/htdi.by"
git push origin main

SHA="$(git rev-parse --short HEAD)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "==> mirror → Lex212mont/htd.by (CF source)"
git clone --depth 1 "https://github.com/Lex212mont/htd.by.git" "$TMP/htd.by"
rsync -a --delete --exclude '.git' "$ROOT/" "$TMP/htd.by/"
cd "$TMP/htd.by"
git add -A
if git diff --cached --quiet; then
  echo "Mirror already up to date"
else
  git -c user.email='noreply@beltime.by' -c user.name='htdi-deploy' \
    commit -m "sync from htdi.by ${SHA}"
  git push origin HEAD:master
fi

echo "==> done. CF Pages htdi-news will build from htd.by/master"
echo "    check: curl -sS https://htdi.by/api/expert-news | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))'"
