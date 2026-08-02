#!/usr/bin/env bash
# Deploy htdi.by — push main; Cloudflare Pages (htdi-news) builds via Git.
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

echo "==> done. CF Pages htdi-news builds from htdi.by/main"
echo "    check: curl -sS https://htdi.by/api/expert-news | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))'"
