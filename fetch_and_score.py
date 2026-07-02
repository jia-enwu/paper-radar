#!/usr/bin/env python3
"""Paper Radar：從 Crossref 抓取期刊新文章，依興趣模型評分，輸出 docs/papers.json。

只用 Python 標準函式庫，無需安裝任何套件。
用法：python3 fetch_and_score.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT = ROOT / "docs" / "papers.json"

API = "https://api.crossref.org/journals/{issn}/works"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def http_get(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "paper-radar/1.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except Exception as e:
            if attempt == retries - 1:
                print(f"  跳過（{e}）", file=sys.stderr)
                return None
            time.sleep(2 * (attempt + 1))


def clean_abstract(raw):
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)          # 去掉 JATS XML 標籤
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(ABSTRACT|Abstract)\s*", "", text)
    return text


def fetch_journal(journal, cfg):
    since = (datetime.now(timezone.utc) - timedelta(days=cfg["days_back"])).date()
    params = {
        "filter": f"from-created-date:{since},type:journal-article",
        "rows": str(cfg["max_per_journal"]),
        "sort": "created",
        "order": "desc",
        "mailto": cfg["mailto"],
    }
    url = API.format(issn=journal["issn"]) + "?" + urllib.parse.urlencode(params)
    data = http_get(url)
    if not data:
        return []
    papers = []
    for item in data["message"]["items"]:
        title = " ".join(item.get("title") or []).strip()
        if not title:
            continue
        authors = [
            " ".join(filter(None, [a.get("given"), a.get("family")]))
            for a in item.get("author", [])
        ]
        created = item["created"]["date-time"][:10]
        papers.append({
            "doi": item["DOI"],
            "title": title,
            "abstract": clean_abstract(item.get("abstract")),
            "authors": authors,
            "journal": journal["name"],
            "url": f"https://doi.org/{item['DOI']}",
            "date": created,
        })
    return papers


def count_hits(keyword, text):
    return min(len(re.findall(re.escape(keyword), text)), 3)


def score_paper(paper, model):
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    score = 0.0
    matched = []
    for kw, weight in model["keywords"].items():
        k = kw.lower()
        # 短關鍵字（如 psm）用全字比對避免誤中
        if len(k) <= 4:
            pattern = r"\b" + re.escape(k) + r"\b"
            hits_t = min(len(re.findall(pattern, title)), 3)
            hits_a = min(len(re.findall(pattern, abstract)), 3)
        else:
            hits_t = count_hits(k, title)
            hits_a = count_hits(k, abstract)
        if hits_t or hits_a:
            score += weight * (hits_t * 2 + hits_a)
            matched.append(kw)
    score += model.get("journal_bonus", {}).get(paper["journal"], 0)
    paper["score"] = round(score, 1)
    paper["matched"] = matched
    return paper


def main():
    cfg = load_json(ROOT / "config.json")
    model = load_json(ROOT / "interest_model.json")

    # 讀舊資料，保留 first_seen
    old = {}
    if OUTPUT.exists():
        for p in load_json(OUTPUT).get("papers", []):
            old[p["doi"]] = p

    seen = {}
    for journal in cfg["journals"]:
        print(f"抓取 {journal['name']} ...")
        for p in fetch_journal(journal, cfg):
            if p["doi"] not in seen:
                seen[p["doi"]] = p
        time.sleep(1)  # Crossref polite rate limit

    cutoff = (datetime.now(timezone.utc) - timedelta(days=cfg["keep_days"])).date().isoformat()
    today = datetime.now(timezone.utc).date().isoformat()

    papers = []
    for doi, p in seen.items():
        p["first_seen"] = old.get(doi, {}).get("first_seen", today)
        papers.append(score_paper(p, model))
    # 舊資料裡還沒過期、但這次抓取範圍外的也保留
    for doi, p in old.items():
        if doi not in seen and p.get("first_seen", today) >= cutoff:
            papers.append(score_paper(p, model))

    papers.sort(key=lambda p: (-p["score"], p["date"]), reverse=False)
    result = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "papers": papers,
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"完成：共 {len(papers)} 篇，寫入 {OUTPUT}")


if __name__ == "__main__":
    main()
