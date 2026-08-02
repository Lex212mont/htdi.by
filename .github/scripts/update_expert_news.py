#!/usr/bin/env python3
"""Update expert-news.json from curated RSS (for htdi.by медиалента).

Does NOT post to Telegram / @beltime_news.
Stdlib only (urllib + ElementTree) — no feedparser required locally.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "expert-news.json"
MAX_ITEMS = 24
UA = "htdi-expert-news/1.0 (+https://htdi.by/)"

SOURCES = [
    {"url": "https://www.belta.by/rss/", "name": "БЕЛТА", "category": "by"},
    {"url": "https://www.park.by/rss.xml", "name": "ПВТ", "category": "by"},
    {"url": "https://mpt.gov.by/rss.xml", "name": "Минцифры BY", "category": "by"},
    {"url": "https://tass.ru/rss/v2.xml", "name": "ТАСС", "category": "ru"},
    {"url": "https://ria.ru/export/rss2/archive/index.xml", "name": "РИА", "category": "ru"},
    {"url": "https://cnews.ru/inc/rss/news.xml", "name": "CNews", "category": "ru"},
    {"url": "https://habr.com/ru/rss/news/", "name": "Habr", "category": "world"},
    {"url": "https://dcunion.ru/feed/", "name": "АУО ЦОД", "category": "ru"},
    {"url": "https://www.anti-malware.ru/rss.xml", "name": "Anti-Malware", "category": "ru"},
]

IT_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])(?:ИИ|AI|ML|LLM|GPT)(?![A-Za-zА-Яа-яЁё])"
    r"|искусственн\w*\s+интеллект|нейросет|машинн\w*\s+обучен"
    r"|цифров(ая|ой|ые|ых|ую|ому)?\s+(экономик|трансформац|инфраструктур|платформ)"
    r"|digital\s+(economy|infrastructure|transform)"
    r"|кибербезопас|информационн\w*\s+безопасност|ransomware|malware"
    r"|центров?\s+обработк\w*\s+данных|\bЦОД\b|data\s*cent(?:er|re)|colocation"
    r"|облачн\w*\s+(сервис|вычислен|инфраструктур|платформ)|cloud\s+(comput|native|service)|IaaS|SaaS|PaaS"
    r"|\bПВТ\b|минцифр|резидент\w*\s+парка"
    r"|open\s*source|программн\w*\s+обеспечен|software\s+(engineer|develop)"
    r"|openai|nvidia|microsoft|google\s+cloud|deepseek|chatgpt",
    re.I,
)
BLOCK_RE = re.compile(r"dev\.by", re.I)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def item_id(link: str) -> str:
    return hashlib.sha1(link.encode("utf-8")).hexdigest()[:12]


def parse_date(s: str) -> str:
    if not s:
        return dt.date.today().isoformat()
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except Exception:
        try:
            return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
        except Exception:
            return dt.date.today().isoformat()


def entry_link(node: ET.Element) -> str:
    for child in node:
        if local(child.tag) != "link":
            continue
        href = child.attrib.get("href") or child.attrib.get("HREF")
        if href:
            return href.strip()
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def fetch_url(url: str) -> str | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"SKIP {url[:60]}: {e}", file=sys.stderr)
        return None


def parse_feed(xml_text: str, source: dict) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    out: list[dict] = []
    for node in root.iter():
        if local(node.tag) not in ("item", "entry"):
            continue
        title = link = summary = date_raw = ""
        for child in node:
            t = local(child.tag)
            if t == "title" and not title:
                title = text(child)
            elif t in ("description", "summary", "content") and not summary:
                summary = text(child) or "".join(child.itertext())
            elif t in ("pubDate", "published", "updated", "date") and not date_raw:
                date_raw = text(child)
        if not link:
            link = entry_link(node)
        title, summary = clean(title), clean(summary)
        if not title or not link:
            continue
        if BLOCK_RE.search(f"{title} {link} {summary}"):
            continue
        if not IT_RE.search(f"{title} {summary}"):
            continue
        if len(summary) > 280:
            summary = summary[:277] + "…"
        out.append(
            {
                "id": item_id(link),
                "title": title,
                "summary": summary,
                "link": link,
                "source": source["name"],
                "date": parse_date(date_raw),
                "category": source["category"],
            }
        )
        if len(out) >= 8:
            break
    return out


def fetch() -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for src in SOURCES:
        body = fetch_url(src["url"])
        if not body:
            continue
        for it in parse_feed(body, src):
            if it["link"] in seen:
                continue
            seen.add(it["link"])
            items.append(it)
        time.sleep(0.25)
    items.sort(key=lambda x: x.get("date") or "", reverse=True)
    return items[:MAX_ITEMS]


def main() -> int:
    items = fetch()
    if not items:
        print("WARN: no items fetched; keeping previous file")
        return 0 if OUT.exists() else 1
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} items={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
