#!/usr/bin/env python3
"""
MA 時事日報 — 主入口
完整流程：RSS 抓取 → Claude 分析 → HTML 生成 → 儲存
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from fetch_news import fetch_all_feeds
from analyze_news import analyze_with_claude
from generate_html import generate_html


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== MA 時事日報 — {today} ===\n")

    # Step 1: Fetch RSS
    print("[1/4] 抓取 RSS 新聞...")
    rss_data = fetch_all_feeds()
    stats = rss_data["stats"]
    print(f"  ✅ 抓取完成：{stats['total']} 則，來自 {len(stats['by_source'])} 個來源")
    if stats["errors"]:
        print(f"  ⚠️  失敗來源：{', '.join(stats['errors'])}")

    # Step 2: Analyze with Claude
    print("\n[2/4] Claude 分析中...")
    analysis = analyze_with_claude(rss_data)
    total = analysis.get("total_articles", 0)
    print(f"  ✅ 分析完成：{total} 則精選新聞")

    # Step 3: Generate HTML
    print("\n[3/4] 生成 HTML...")
    html_content = generate_html(analysis)
    print(f"  ✅ HTML 生成完成（{len(html_content):,} bytes）")

    # Step 4: Save files
    print("\n[4/4] 儲存檔案...")
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    html_path = docs_dir / f"{today}.html"
    json_path = docs_dir / f"{today}.json"

    html_path.write_text(html_content, encoding="utf-8")
    json_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  ✅ HTML: {html_path}")
    print(f"  ✅ JSON: {json_path}")

    # Generate index.html (list of all reports)
    generate_index(docs_dir)

    # Summary
    print(f"\n{'='*50}")
    print(f"📊 完成摘要")
    print(f"  日期：{today}")
    print(f"  RSS 來源：{len(stats['by_source'])} 個成功 / {len(stats['errors'])} 個失敗")
    print(f"  精選新聞：{total} 則")
    print(f"  Top 5 必讀：")
    for i, item in enumerate(analysis.get("top5", [])[:5], 1):
        print(f"    {i}. [{item.get('section', '')}] {item.get('summary', '')}")

    return 0


def generate_index(docs_dir: Path):
    """Generate index.html listing all daily reports."""
    html_files = sorted(docs_dir.glob("????-??-??.html"), reverse=True)

    links = ""
    for f in html_files:
        date = f.stem
        links += f'<li><a href="{f.name}">{date}</a></li>\n'

    index_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MA 時事日報 — 歷史期數</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      background: #000;
      color: #f5f5f7;
      max-width: 680px;
      margin: 0 auto;
      padding: 48px 16px;
    }}
    h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 32px; text-align: center; }}
    ul {{ list-style: none; padding: 0; }}
    li {{
      padding: 16px 20px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      margin-bottom: 8px;
      transition: all 0.2s;
    }}
    li:hover {{ background: rgba(255,255,255,0.08); transform: translateY(-1px); }}
    a {{ color: #42A5F5; text-decoration: none; font-size: 17px; font-weight: 500; }}
    a:hover {{ opacity: 0.7; }}
    .count {{ color: #86868b; font-size: 14px; margin-top: 8px; }}
  </style>
</head>
<body>
  <h1>MA 時事日報</h1>
  <p class="count">共 {len(html_files)} 期</p>
  <ul>{links}</ul>
</body>
</html>"""

    (docs_dir / "index.html").write_text(index_html, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
