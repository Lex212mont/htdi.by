#!/usr/bin/env python3
"""Daily НТДИ news digest → @BELTIME_NEWS"""
import os, time, datetime, requests, feedparser, re, json
from html import escape

TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "-1003929211757"

SENT_FILE = ".sent-news.json"
MAX_SENT = 150

def load_sent_links():
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("links", []))
    except Exception:
        return set()

def save_sent_links(links):
    try:
        to_save = list(links)[-MAX_SENT:]
        with open(SENT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "updated": datetime.datetime.utcnow().isoformat() + "Z",
                "links": to_save
            }, f, indent=2, ensure_ascii=False)
    except Exception as ex:
        print("WARN: cannot save sent state:", ex)

SOURCES = [
    # BY
    {"url": "https://www.belta.by/rss/", "name": "БЕЛТА", "region": "by"},
    {"url": "https://www.park.by/rss.xml", "name": "ПВТ", "region": "by"},
    {"url": "https://mpt.gov.by/rss.xml", "name": "Минцифры", "region": "by"},
    # RU
    {"url": "https://tass.ru/rss/v2.xml", "name": "ТАСС", "region": "ru"},
    {"url": "https://ria.ru/export/rss2/archive/index.xml", "name": "РИА", "region": "ru"},
    {"url": "https://rbc.ru/arc/rssfeeds/v1/main/full", "name": "РБК", "region": "ru"},
    {"url": "https://www.kommersant.ru/RSS/news.xml", "name": "Коммерсантъ", "region": "ru"},
    {"url": "https://cnews.ru/inc/rss/news.xml", "name": "CNews", "region": "ru"},
    # Spec
    {"url": "https://habr.com/ru/rss/news/", "name": "Habr", "region": "spec"},
    {"url": "http://feeds.reuters.com/reuters/technologyNews", "name": "Reuters Tech", "region": "spec"},
    {"url": "https://dcunion.ru/feed/", "name": "DC Union", "region": "spec"},
    {"url": "https://www.anti-malware.ru/rss.xml", "name": "Anti-Malware", "region": "spec"},
    {"url": "https://www.infowatch.ru/rss", "name": "InfoWatch", "region": "spec"},
]

REGION_SCORE = {"by": 60, "ru": 50, "spec": 35}
BY_RE = re.compile(r'беларус|белорус|минск|пвт|htp|htdi|нтди|belarus|minsk', re.I)
RU_RE = re.compile(r'россия|российск|москва|russoft|апкит|арпп|russia|russian', re.I)
AI_RE = re.compile(r'\bai\b|искусственн|нейросет|llm|gpt|машинн|ml\b', re.I)
CY_RE = re.compile(r'кибер|хакер|уязвим|вирус|утечк|взлом|security|cyber', re.I)

# IT relevance — must match at least one keyword to pass filter
IT_RE = re.compile(
    r'\bai\b|искусственн|нейросет|llm|gpt|машинн обучени|deep.?learn'
    r'|цифров|диджитал|digital|software|программ|разработ'
    r'|кибер|хакер|уязвим|вирус|утечк|взлом|security|malware|ransomware'
    r'|облак|cloud|дата.?центр|data.?cent|сервер|server'
    r'|стартап|startup|tech|технолог|ит.отрасл|it.индустр'
    r'|интернет|internet|сеть|network|5g|6g|wifi|broadband'
    r'|приложени|app\b|платформ|platform|сервис|saas|paas'
    r'|блокчейн|blockchain|крипто|crypto|nft|web3'
    r'|робот|автоматиз|automat|беспилот|drone'
    r'|смартфон|smartphone|гаджет|gadget|электроник'
    r'|пвт|park.?ht|минцифр|цифровая.?экономик|e-gov'
    r'|microsoft|google|apple|amazon|meta\b|openai|nvidia|intel|amd'
    r'|huawei|samsung|xiaomi|alibaba|tencent|yandex|сбер|vk\b',
    re.I
)

def is_it(item):
    t = item.get("title","") + " " + item.get("summary","")
    return bool(IT_RE.search(t))

def score(item, region):
    s = REGION_SCORE.get(region, 0)
    t = (item.get("title","") + " " + item.get("summary",""))
    if BY_RE.search(t): s += 30
    if RU_RE.search(t): s += 20
    if AI_RE.search(t): s += 25
    if CY_RE.search(t): s += 20
    # recency bonus
    published = item.get("published_parsed")
    if published:
        age_h = (time.time() - time.mktime(published)) / 3600
        if age_h < 6:   s += 30
        elif age_h < 12: s += 15
        elif age_h < 24: s += 5
    return s

def fetch_all():
    items = []
    for src in SOURCES:
        try:
            feed = feedparser.parse(src["url"])
            for e in feed.entries[:5]:
                items.append({
                    "title":  e.get("title","").strip(),
                    "link":   e.get("link",""),
                    "source": src["name"],
                    "region": src["region"],
                    "published_parsed": e.get("published_parsed"),
                    "summary": e.get("summary",""),
                    "score": 0,
                })
        except Exception as ex:
            print(f"SKIP {src['name']}: {ex}")
    # Keep only IT-relevant news
    items = [it for it in items if is_it(it)]
    for it in items:
        it["score"] = score(it, it["region"])
    items.sort(key=lambda x: -x["score"])
    return items

FLAG = {"by":"🇧🇾","ru":"🇷🇺","spec":"🔬"}

def build_messages(items):
    today = datetime.datetime.now().strftime("%d.%m.%Y")
    header = f'🗞 <b>Утренний IT-обзор НТДИ | {today}</b>\n\n'
    top7 = items[:7]
    lines = []
    for i, it in enumerate(top7, 1):
        flag = FLAG.get(it["region"],"")
        title = escape(it["title"])
        link  = it["link"]
        name  = escape(it["source"])
        lines.append(
            f'<b>{i}. <a href="{link}">{title}</a></b> {flag}\n'
            f'📌 {name}'
        )
    body = "\n\n".join(lines)
    full = header + body
    # split at ~3800 chars
    if len(full) <= 4096:
        return [full]
    mid = len(top7) // 2
    p1 = header + "\n\n".join(lines[:mid])
    p2 = "\n\n".join(lines[mid:])
    return [p1, p2]

def send(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text,
              "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=20,
    )
    r.raise_for_status()
    print("Sent OK, msg_id:", r.json()["result"]["message_id"])

if __name__ == "__main__":
    sent = load_sent_links()
    items = fetch_all()
    new_items = [it for it in items if it.get("link") and it["link"] not in sent]
    print(f"Fetched {len(items)} items, {len(new_items)} new (after dedup)")

    if not new_items:
        print("No new items to send, skipping digest.")
        save_sent_links(sent)
        exit(0)

    print(f"Top score of new: {new_items[0]['score'] if new_items else 0}")
    for msg in build_messages(new_items):
        send(msg)
        time.sleep(1)

    # Запоминаем отправленные (чтобы не повторяться в следующие дни)
    for it in new_items[:25]:
        if it.get("link"):
            sent.add(it["link"])
    save_sent_links(sent)
    print("Sent state updated.")
