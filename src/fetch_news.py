#!/usr/bin/env python3
"""
MA 面試時事日報 — RSS 新聞抓取腳本
從多個 RSS 來源抓取當日財經新聞，輸出結構化 JSON。
"""

import feedparser
import requests
import json
import re
import sys
from datetime import datetime

RSS_SOURCES = {
    # ── 全球宏觀 / 地緣政治 ──
    "CNBC_Top": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "category": "macro", "lang": "en", "name": "CNBC Top News"
    },
    "CNBC_World": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "category": "macro", "lang": "en", "name": "CNBC World"
    },
    "BBC_Business": {
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "category": "macro", "lang": "en", "name": "BBC Business"
    },
    "AlJazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "geopolitics", "lang": "en", "name": "Al Jazeera"
    },
    "NPR_Business": {
        "url": "https://feeds.npr.org/1006/rss.xml",
        "category": "macro", "lang": "en", "name": "NPR Business"
    },
    "FT_Home": {
        "url": "https://www.ft.com/rss/home",
        "category": "macro", "lang": "en", "name": "Financial Times"
    },
    "FT_Companies": {
        "url": "https://www.ft.com/companies?format=rss",
        "category": "finance", "lang": "en", "name": "FT Companies"
    },
    "FT_Markets": {
        "url": "https://www.ft.com/markets?format=rss",
        "category": "finance", "lang": "en", "name": "FT Markets"
    },
    "WSJ_World": {
        "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "category": "macro", "lang": "en", "name": "WSJ World"
    },
    "WSJ_Markets": {
        "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "category": "finance", "lang": "en", "name": "WSJ Markets"
    },
    "WSJ_Business": {
        "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        "category": "finance", "lang": "en", "name": "WSJ Business"
    },
    "WSJ_Tech": {
        "url": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
        "category": "tech", "lang": "en", "name": "WSJ Technology"
    },

    # ── AI / 半導體 / 科技 ──
    "CNBC_Tech": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
        "category": "tech", "lang": "en", "name": "CNBC Technology"
    },
    "TechCrunch": {
        "url": "https://techcrunch.com/feed/",
        "category": "tech", "lang": "en", "name": "TechCrunch"
    },

    # ── 能源 ──
    "CNBC_Energy": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19836768",
        "category": "energy", "lang": "en", "name": "CNBC Energy"
    },

    # ── 金融 / 不動產 / 私募 ──
    "CNBC_Finance": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "category": "finance", "lang": "en", "name": "CNBC Finance"
    },
    "Yahoo_Finance": {
        "url": "https://finance.yahoo.com/news/rssindex",
        "category": "finance", "lang": "en", "name": "Yahoo Finance"
    },

    # ── 台灣 / 亞太 ──
    "UDN_Securities": {
        "url": "https://money.udn.com/rssfeed/news/1001/5590",
        "category": "taiwan", "lang": "zh", "name": "經濟日報 證券"
    },
    "UDN_Intl": {
        "url": "https://money.udn.com/rssfeed/news/1001/5588",
        "category": "taiwan", "lang": "zh", "name": "經濟日報 國際"
    },
    "UDN_Industry": {
        "url": "https://money.udn.com/rssfeed/news/1001/5591",
        "category": "taiwan", "lang": "zh", "name": "經濟日報 產業"
    },
    "UDN_Finance": {
        "url": "https://money.udn.com/rssfeed/news/1001/12017",
        "category": "taiwan", "lang": "zh", "name": "經濟日報 金融"
    },
    "CTEE_Industry": {
        "url": "https://www.ctee.com.tw/rss_web/livenews/industry",
        "category": "taiwan", "lang": "zh", "name": "工商時報 產業"
    },
    "CTEE_Finance": {
        "url": "https://www.ctee.com.tw/rss_web/livenews/finance",
        "category": "taiwan", "lang": "zh", "name": "工商時報 金融"
    },
    "CTEE_World": {
        "url": "https://www.ctee.com.tw/rss_web/livenews/world",
        "category": "taiwan", "lang": "zh", "name": "工商時報 國際"
    },
    "CTEE_Stock": {
        "url": "https://www.ctee.com.tw/rss_web/livenews/stock",
        "category": "taiwan", "lang": "zh", "name": "工商時報 證券"
    },
    "CNA_Finance": {
        "url": "https://feeds.feedburner.com/rsscna/finance",
        "category": "taiwan", "lang": "zh", "name": "中央社 財經"
    },
    "CNA_Intl": {
        "url": "https://feeds.feedburner.com/rsscna/intworld",
        "category": "taiwan", "lang": "zh", "name": "中央社 國際"
    },
    "CNA_Tech": {
        "url": "https://feeds.feedburner.com/rsscna/technology",
        "category": "taiwan", "lang": "zh", "name": "中央社 科技"
    },
    "LTN_Finance": {
        "url": "https://news.ltn.com.tw/rss/business.xml",
        "category": "taiwan", "lang": "zh", "name": "自由財經"
    },
    "MoneyDJ": {
        "url": "https://www.moneydj.com/KMDJ/RssCenter.aspx?svc=NH",
        "category": "taiwan", "lang": "zh", "name": "MoneyDJ 理財網"
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MA-News-Bot/1.0)"}
TIMEOUT = 20


def fetch_all_feeds():
    """Fetch all RSS feeds and return structured articles."""
    all_articles = []
    stats = {"total": 0, "by_source": {}, "by_category": {}, "errors": []}

    for source_id, source in RSS_SOURCES.items():
        try:
            resp = requests.get(source["url"], timeout=TIMEOUT, headers=HEADERS)
            feed = feedparser.parse(resp.content)
            source_count = 0

            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                summary = entry.get("summary", entry.get("description", "")).strip()
                if "<" in summary:
                    summary = re.sub(r"<[^>]+>", "", summary).strip()
                if len(summary) > 500:
                    summary = summary[:500] + "..."

                all_articles.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": summary,
                    "published": entry.get("published", ""),
                    "source_id": source_id,
                    "source_name": source["name"],
                    "category": source["category"],
                    "lang": source["lang"],
                })
                source_count += 1

            stats["by_source"][source["name"]] = source_count
            stats["total"] += source_count
            stats["by_category"][source["category"]] = (
                stats["by_category"].get(source["category"], 0) + source_count
            )
        except Exception as e:
            stats["errors"].append(f"{source['name']}: {type(e).__name__}")

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "fetched_at": datetime.now().isoformat(),
        "stats": stats,
        "articles": all_articles,
    }


if __name__ == "__main__":
    result = fetch_all_feeds()
    print(json.dumps(result, ensure_ascii=False, indent=2))
