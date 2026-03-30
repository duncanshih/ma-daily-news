#!/usr/bin/env python3
"""
MA 時事日報 — HTML 生成器（Apple Style Theme）
讀取 Claude 產出的 JSON 分析結果，生成蘋果風自包含 HTML。
設計參考：geekjourneyx/ai-daily-skill Apple Style Theme
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
    --bg-color: #000000;
    --glow-start: #0A1929;
    --glow-end: #1A3A52;
    --title-color: #FFFFFF;
    --text-color: #E3F2FD;
    --accent-color: #42A5F5;
    --secondary-color: #B0BEC5;
    --surface: rgba(255, 255, 255, 0.05);
    --surface-hover: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.10);
    --border-hover: rgba(255, 255, 255, 0.20);
    --interview: #FFA726;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
    background: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

/* ── Background Glow ── */
.background-glow {
    position: fixed;
    bottom: -20%;
    right: -20%;
    width: 70%;
    height: 70%;
    background: radial-gradient(
        circle at center,
        var(--glow-end) 0%,
        var(--glow-start) 40%,
        transparent 80%
    );
    opacity: 0.6;
    filter: blur(80px);
    z-index: -2;
    pointer-events: none;
}

.background-glow-2 {
    position: fixed;
    top: -15%;
    left: -15%;
    width: 50%;
    height: 50%;
    background: radial-gradient(
        circle at center,
        rgba(66, 165, 245, 0.08) 0%,
        transparent 70%
    );
    filter: blur(60px);
    z-index: -2;
    pointer-events: none;
}

/* ── Geometric Lines ── */
.geometric-lines {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(90deg, transparent 49%, var(--accent-color) 50%, transparent 51%),
        linear-gradient(0deg, transparent 49%, var(--accent-color) 50%, transparent 51%);
    background-size: 200px 200px;
    opacity: 0.04;
    z-index: -1;
    pointer-events: none;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 20px 60px;
    position: relative;
    z-index: 1;
}

/* ── Header ── */
header {
    text-align: center;
    padding: 60px 0 40px;
}

.logo-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: 20px;
    background: rgba(66, 165, 245, 0.15);
    font-size: 32px;
    margin-bottom: 20px;
    animation: glow-pulse 3s ease-in-out infinite;
}

@keyframes glow-pulse {
    0%, 100% { box-shadow: 0 0 30px rgba(66,165,245,0.3), 0 0 60px rgba(66,165,245,0.1); }
    50% { box-shadow: 0 0 40px rgba(66,165,245,0.5), 0 0 80px rgba(66,165,245,0.2); }
}

header h1 {
    font-size: 36px;
    font-weight: 700;
    color: var(--title-color);
    letter-spacing: -0.5px;
    margin-bottom: 12px;
}

.date-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    background: rgba(66, 165, 245, 0.12);
    border: 1px solid rgba(66, 165, 245, 0.2);
    color: var(--accent-color);
    font-size: 15px;
    font-weight: 500;
}

.stats {
    font-size: 14px;
    color: var(--secondary-color);
    margin-top: 12px;
}

/* ── Summary Card ── */
.summary-card {
    background: var(--surface);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 40px;
    transition: border-color 0.3s ease;
}

.summary-card:hover {
    border-color: var(--border-hover);
}

.summary-card h2 {
    font-size: 18px;
    font-weight: 600;
    color: var(--title-color);
    margin-bottom: 20px;
}

.summary-card ol {
    list-style: none;
    counter-reset: top5;
}

.summary-card ol li {
    counter-increment: top5;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 15px;
    line-height: 1.6;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}

.summary-card ol li:last-child { border-bottom: none; padding-bottom: 0; }

.summary-card ol li::before {
    content: counter(top5);
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 26px;
    height: 26px;
    background: var(--accent-color);
    color: #000;
    border-radius: 50%;
    font-size: 13px;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 2px;
}

/* ── Tags ── */
.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    white-space: nowrap;
    margin-right: 6px;
}

/* ── Section ── */
.section {
    margin-bottom: 40px;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

.section-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 8px currentColor;
}

.section-header h2 {
    font-size: 22px;
    font-weight: 600;
    color: var(--title-color);
    letter-spacing: -0.3px;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 14px;
    transition: all 0.3s ease;
    animation: fadeIn 0.5s ease forwards;
    opacity: 0;
}

.card:hover {
    background: var(--surface-hover);
    border-color: var(--accent-color);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.card-major {
    border-left: 3px solid var(--section-color, var(--accent-color));
}

.card h3 {
    font-size: 17px;
    font-weight: 600;
    color: var(--title-color);
    margin-bottom: 14px;
    line-height: 1.5;
}

.card .label {
    font-size: 12px;
    font-weight: 700;
    color: var(--accent-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.card .body {
    font-size: 15px;
    color: var(--text-color);
    margin-bottom: 12px;
    line-height: 1.7;
}

.card .interview-angle {
    font-size: 14px;
    color: var(--interview);
    padding: 10px 14px;
    background: rgba(255, 167, 38, 0.08);
    border: 1px solid rgba(255, 167, 38, 0.15);
    border-radius: 10px;
    margin: 14px 0;
    line-height: 1.6;
}

.card .sources {
    font-size: 13px;
    color: var(--secondary-color);
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.06);
}

.card .sources a {
    color: var(--accent-color);
    text-decoration: none;
    transition: opacity 0.2s;
}

.card .sources a:hover { opacity: 0.7; }

/* ── Brief card ── */
.card-brief {
    padding: 16px 24px;
}

.card-brief p {
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-color);
}

.card-brief strong {
    color: var(--title-color);
}

/* ── Footer ── */
footer {
    text-align: center;
    padding: 40px 0;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin-top: 32px;
}

footer p {
    font-size: 13px;
    color: var(--secondary-color);
    margin-bottom: 6px;
}

.keywords-footer {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    margin-top: 16px;
}

.keywords-footer span {
    padding: 4px 12px;
    border-radius: 20px;
    background: rgba(66, 165, 245, 0.08);
    border: 1px solid rgba(66, 165, 245, 0.15);
    color: var(--accent-color);
    font-size: 12px;
    font-weight: 500;
}

/* ── Animation ── */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

.card:nth-child(1) { animation-delay: 0.05s; }
.card:nth-child(2) { animation-delay: 0.1s; }
.card:nth-child(3) { animation-delay: 0.15s; }
.card:nth-child(4) { animation-delay: 0.2s; }
.card:nth-child(5) { animation-delay: 0.25s; }

/* ── Responsive ── */
@media (max-width: 480px) {
    .container { padding: 20px 14px 40px; }
    header { padding: 40px 0 24px; }
    header h1 { font-size: 28px; }
    .card { padding: 18px; }
    .summary-card { padding: 20px; }
    .section-header h2 { font-size: 19px; }
}
"""


def generate_html(analysis_json: dict) -> str:
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
    <span class="section-dot" style="background:{sec_info['color']};color:{sec_info['color']}"></span>
    <h2>{sec_info['icon']} {sec_info['name']}</h2>
  </div>
  {cards_html}
</section>
'''

    # Keywords
    keywords = ["#Fed", "#油價", "#台股", "#AI", "#TSMC", "#Micron", "#LNG", "#荷莫茲", "#SpaceX", "#PE"]
    keywords_html = "".join(f'<span>{k}</span>' for k in keywords)

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MA 時事日報 — {date}</title>
  <style>{APPLE_THEME_CSS}</style>
</head>
<body>
  <div class="background-glow"></div>
  <div class="background-glow-2"></div>
  <div class="geometric-lines"></div>

  <div class="container">
    <header>
      <div class="logo-icon">📰</div>
      <h1>MA 時事日報</h1>
      <div class="date-badge">{date}（{day}）</div>
      <p class="stats">{total} 則精選新聞 · {src_count} 個來源</p>
    </header>

    <section class="summary-card">
      <h2>🔴 今日 Top 5 必讀</h2>
      <ol>{top5_html}</ol>
    </section>

    {sections_html}

    <footer>
      <p>由 Claude 分析產出 · MA 面試準備用</p>
      <p>RSS: CNBC · BBC · FT · WSJ · Al Jazeera · Yahoo Finance · 經濟日報 · TechCrunch</p>
      <div class="keywords-footer">{keywords_html}</div>
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
