#!/usr/bin/env python3
"""
MA 時事日報 — Claude 分析引擎
讀取 RSS 原始新聞，呼叫 Claude API 進行篩選、分類、分析，輸出結構化 JSON。
"""

import json
import os
import sys
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("Error: pip install anthropic", file=sys.stderr)
    sys.exit(1)

ANALYSIS_PROMPT = """你是一位專為台灣金融業 MA（儲備幹部）面試準備的時事新聞研究員。

我給你今天從 RSS 抓到的原始新聞列表（JSON 格式）。請你：

1. 從中篩選出最重要的 15-20 則新聞
2. 分類到 5 個版塊：macro（總經/地緣政治）、realestate（不動產/私募）、tech（AI/半導體）、energy（能源/基建）、taiwan（台灣/亞太）
3. 每個版塊 3-5 則
4. 每則新聞標記格式：A（重要新故事）、B（持續追蹤事件）、C（簡要更新）

篩選標準：
- 有具體數字（匯率、股指、金額、百分比）
- 有因果關係可分析
- 跟 MA 面試可能被問到的主題相關
- 有跨領域連結（例如油價 → 通膨 → 央行政策）

請用以下 JSON 格式回覆（不要加任何 markdown 標記，純 JSON）：

{
  "date": "YYYY-MM-DD",
  "day_of_week": "星期X",
  "total_articles": 18,
  "source_count": 12,
  "top5": [
    {"section": "macro", "summary": "一句話摘要"},
    {"section": "tech", "summary": "一句話摘要"},
    {"section": "energy", "summary": "一句話摘要"},
    {"section": "taiwan", "summary": "一句話摘要"},
    {"section": "realestate", "summary": "一句話摘要"}
  ],
  "sections": {
    "macro": {
      "articles": [
        {
          "format": "A",
          "title": "新聞標題 — 一句話總結",
          "what_happened": "2-3 句話，包含具體數字",
          "why_important": "1-2 句話，解釋影響",
          "interview_angle": "1 句話，面試切入點",
          "sources": [{"name": "來源名稱", "url": "https://..."}]
        },
        {
          "format": "B",
          "title": "事件名稱（持續追蹤）",
          "latest_development": "今天的新發展",
          "key_data": "2-3 個關鍵數字",
          "sources": [{"name": "來源名稱", "url": "https://..."}]
        },
        {
          "format": "C",
          "title": "標題",
          "summary": "一句話摘要，含關鍵數字",
          "sources": [{"name": "來源名稱", "url": "https://..."}]
        }
      ]
    },
    "realestate": { "articles": [...] },
    "tech": { "articles": [...] },
    "energy": { "articles": [...] },
    "taiwan": { "articles": [...] }
  }
}

品質要求：
- 數字要精確（匯率精確到小數點後2位、百分比精確到小數點後1位）
- 不要用「大幅」「顯著」等模糊詞
- 「面試角度」要具體實用
- 每則新聞的 sources 必須包含實際可訪問的 URL
- 中文來源至少佔 30%（如果 RSS 中文來源不足，可以標注建議補充搜尋的關鍵字）
"""


def analyze_with_claude(rss_data: dict) -> dict:
    """Send RSS data to Claude for analysis."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    # Prepare a condensed version of articles to save tokens
    condensed = []
    for art in rss_data.get("articles", []):
        condensed.append({
            "title": art["title"],
            "link": art["link"],
            "summary": art["summary"][:300],
            "source": art["source_name"],
            "category": art["category"],
            "lang": art["lang"],
        })

    user_msg = f"""以下是今天 {rss_data['date']} 從 RSS 抓到的 {len(condensed)} 則原始新聞：

{json.dumps(condensed, ensure_ascii=False)}

請按照指定格式分析並回覆 JSON。"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": ANALYSIS_PROMPT + "\n\n" + user_msg}
        ],
    )

    # Extract JSON from response
    text = response.content[0].text.strip()

    # Try to parse JSON (handle potential markdown wrapping)
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    return json.loads(text)


if __name__ == "__main__":
    rss_data = json.load(sys.stdin)
    result = analyze_with_claude(rss_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
