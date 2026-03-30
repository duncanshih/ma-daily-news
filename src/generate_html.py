#!/usr/bin/env python3
"""
MA 時事日報 — HTML 生成器
讀取 Claude 產出的 JSON 分析結果，生成蘋果風自包含 HTML。
"""

import json
import sys
from datetime import datetime

# ── 版塊色碼 ──
SECTION_COLORS = {
    "macro": {"name": "總經 / 地緣政治", "color": "#42A5F5", "icon": "🌍"},
    "realestate": {"name": "不動產 / 私募", "color": "#AB47BC", "icon": "🏢"},
    "tech": {"name": "AI / 半導體", "color": "#66BB6A", "icon": "🤖"},
    "energy": {"name": "能源 / 基建", "color": "#FFA726", "icon": "⚡"},
    "taiwan": {"name": "台灣 / 亞太", "color": "#EF5350", "icon": "🇹🇼"},
}

APPLE_THEME_CSS = """
:root {
    --bg: #000000;
    --surface: rgba(255, 255, 255, 0.05);
    --surface-hover: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.15);
    --text-primary: #f5f5f7;
    --text-secondary: #86868b;
    --text-tertiary: #6e6e73;
    --accent: #42A5F5;
    --interview: #FFA726;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.container {
    max-width: 680px;
    margin: 0 auto;
    padding: 24px 16px 48px;
}

/* ── Header ── */
header {
    text-align: center;
    padding: 48px 0 32px;
}

header h1 {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}

header .date {
    font-size: 17px;
    color: var(--text-secondary);
    font-weight: 400;
}

header .stats {
    font-size: 14px;
    color: var(--text-tertiary);
    margin-top: 4px;
}

/* ── Top 5 ── */
.top5 {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
}

.top5 h2 {
    font-size: 17px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-primary);
}

.top5 ol {
    list-style: none;
    counter-reset: top5;
}

.top5 ol li {
    counter-increment: top5;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-size: 15px;
    line-height: 1.5;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.top5 ol li:last-child { border-bottom: none; }

.top5 ol li::before {
    content: counter(top5);
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    background: var(--accent);
    color: #000;
    border-radius: 50%;
    font-size: 13px;
    font-weight: 700;
    margin-top: 1px;
}

/* ── Tags ── */
.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    white-space: nowrap;
}

/* ── Sections ── */
.section {
    margin-bottom: 32px;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

.section-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

.section-header h2 {
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.3px;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
    animation: fadeIn 0.4s ease forwards;
    opacity: 0;
}

.card:hover {
    background: var(--surface-hover);
    border-color: var(--border-hover);
    transform: translateY(-1px);
}

.card-major {
    border-left: 3px solid var(--section-color, var(--accent));
}

.card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    line-height: 1.4;
}

.card .label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 2px;
}

.card .body {
    font-size: 15px;
    color: var(--text-secondary);
    margin-bottom: 10px;
    line-height: 1.6;
}

.card .interview-angle {
    font-size: 14px;
    color: var(--interview);
    padding: 8px 12px;
    background: rgba(255, 167, 38, 0.08);
    border-radius: 8px;
    margin: 12px 0;
}

.card .sources {
    font-size: 13px;
    color: var(--text-tertiary);
    margin-top: 12px;
}

.card .sources a {
    color: var(--accent);
    text-decoration: none;
    transition: opacity 0.2s;
}

.card .sources a:hover { opacity: 0.7; }

/* ── Brief card ── */
.card-brief {
    padding: 14px 20px;
}

.card-brief p {
    font-size: 14px;
    line-height: 1.5;
}

/* ── Footer ── */
footer {
    text-align: center;
    padding: 32px 0;
    border-top: 1px solid var(--border);
    margin-top: 24px;
}

footer p {
    font-size: 13px;
    color: var(--text-tertiary);
    margin-bottom: 4px;
}

/* ── Animation ── */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.card:nth-child(1) { animation-delay: 0.05s; }
.card:nth-child(2) { animation-delay: 0.1s; }
.card:nth-child(3) { animation-delay: 0.15s; }
.card:nth-child(4) { animation-delay: 0.2s; }
.card:nth-child(5) { animation-delay: 0.25s; }

/* ── Responsive ── */
@media (max-width: 480px) {
    .container { padding: 16px 12px 32px; }
    header { padding: 32px 0 24px; }
    header h1 { font-size: 24px; }
    .card { padding: 16px; }
}
"""


def generate_html(analysis_json: dict) -> str:
    """
    Generate self-contained Apple-style HTML from Claude's analysis output.

    Expected analysis_json structure:
    {
        "date": "2026-03-30",
        "day_of_week": "星期一",
        "total_articles": 18,
        "source_count": 12,
        "top5": [
            {"section": "macro", "summary": "..."},
            ...
        ],
        "sections": {
            "macro": {
                "articles": [
                    {
                        "format": "A",
                        "title": "...",
                        "what_happened": "...",
                        "why_important": "...",
                        "interview_angle": "...",
                        "sources": [{"name": "...", "url": "..."}]
                    },
                    ...
                ]
            },
            ...
        }
    }
    """
    date = analysis_json.get("date", "")
    day = analysis_json.get("day_of_week", "")
    total = analysis_json.get("total_articles", 0)
    src_count = analysis_json.get("source_count", 0)
    top5 = analysis_json.get("top5", [])
    sections = analysis_json.get("sections", {})

    # Build Top 5
    top5_html = ""
    for item in top5:
        sec = item.get("section", "macro")
        info = SECTION_COLORS.get(sec, SECTION_COLORS["macro"])
        top5_html += f'<li><span class="tag" style="background:rgba({_hex_to_rgb(info["color"])},0.15);color:{info["color"]}">{info["icon"]} {info["name"].split("/")[0].strip()}</span>{item["summary"]}</li>\n'

    # Build sections
    sections_html = ""
    for sec_key, sec_info in SECTION_COLORS.items():
        sec_data = sections.get(sec_key, {})
        articles = sec_data.get("articles", [])
        if not articles:
            continue

        cards_html = ""
        for art in articles:
            fmt = art.get("format", "A")
            sources_links = " ｜ ".join(
                f'<a href="{s["url"]}" target="_blank">{s["name"]}</a>'
                for s in art.get("sources", [])
            )

            if fmt in ("A", "B"):
                tracking = ""
                if fmt == "B":
                    tracking = "🔄 "

                what = art.get("what_happened", art.get("latest_development", ""))
                why = art.get("why_important", "")
                angle = art.get("interview_angle", "")
                key_data = art.get("key_data", "")

                body_parts = []
                if what:
                    body_parts.append(f'<p class="label">發生什麼事</p><p class="body">{what}</p>')
                if key_data:
                    body_parts.append(f'<p class="label">關鍵數據</p><p class="body">{key_data}</p>')
                if why:
                    body_parts.append(f'<p class="label">為什麼重要</p><p class="body">{why}</p>')

                angle_html = ""
                if angle:
                    angle_html = f'<div class="interview-angle">💡 面試角度：{angle}</div>'

                cards_html += f'''<article class="card card-major" style="--section-color:{sec_info['color']}">
  <h3>{tracking}{art.get("title", "")}</h3>
  {"".join(body_parts)}
  {angle_html}
  <div class="sources">{sources_links}</div>
</article>
'''
            else:  # Format C
                cards_html += f'''<article class="card card-brief">
  <p>📎 <strong>{art.get("title", "")}：</strong>{art.get("summary", "")}</p>
  <div class="sources">{sources_links}</div>
</article>
'''

        sections_html += f'''<section class="section">
  <div class="section-header">
    <span class="section-dot" style="background:{sec_info['color']}"></span>
    <h2>{sec_info['icon']} {sec_info['name']}</h2>
  </div>
  {cards_html}
</section>
'''

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MA 時事日報 — {date}</title>
  <style>{APPLE_THEME_CSS}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>MA 時事日報</h1>
      <p class="date">{date}（{day}）</p>
      <p class="stats">{total} 則新聞 · {src_count} 個來源</p>
    </header>

    <section class="top5">
      <h2>🔴 今日 Top 5 必讀</h2>
      <ol>{top5_html}</ol>
    </section>

    {sections_html}

    <footer>
      <p>由 Claude 分析產出 · MA 面試準備用</p>
      <p>RSS: CNBC · BBC · FT · WSJ · Al Jazeera · Yahoo Finance · 經濟日報 · TechCrunch</p>
    </footer>
  </div>
</body>
</html>"""
    return html


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #RRGGBB to 'R,G,B'."""
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    print(generate_html(data))
