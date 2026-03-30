#!/usr/bin/env python3
"""
MA 時事日報 — 主入口（本機版，不需 API Key）

流程：
  1. python main.py fetch    → 抓 RSS，存 JSON，複製 prompt 到剪貼簿
  2. 你貼進 Claude 桌面版   → 拿到分析 JSON
  3. python main.py generate → 貼回 JSON 或指定檔案 → 產出 HTML

或直接 python main.py 跑完整互動流程。
"""

import io
import json
import os
import subprocess
import platform
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows CMD encoding (cp950 can't print emoji)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from fetch_news import fetch_all_feeds
from generate_html import generate_html

# ── 資料夾 ──
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"

# ── Claude 分析 Prompt（從原 analyze_news.py 搬過來）──
ANALYSIS_PROMPT = """你是一位專為台灣金融業 MA（儲備幹部）面試準備的時事新聞研究員。

## 目標職位（面試角度要對應這些職位）

1. **國泰 CIM（投資金融家）** — 股票/債券/外匯，前中後台輪調，重點：金融工具知識、投資組合思維
2. **中信 MA 投資專案** — 大型專案評估、私募基金、不動產投資，重點：財務模型、投資風險管理、跨產業研究
3. **元大 投行法金** — 投資銀行 / 法人金融業務
4. **開發資本 基礎建設投資** — 產業研究、投資案評估（營運/財務/市場）、投後管理、基金募集，重點：基建/能源/實體資產
5. **富邦證券 投資銀行組** — IPO/SPO 輔導、股權資本規劃、國內外籌資，重點：企業上市流程、資本市場實務

撰寫「面試角度」時，請具體指出哪個職位可能問、怎麼問。例如：
- 「開發資本面試可能問：這對基建投資的 IRR 假設有什麼影響？」
- 「國泰 CIM 會關注：這對債券殖利率曲線的含義」
- 「中信投資專案角度：這筆交易的風險怎麼定價？」

我給你今天從 RSS 抓到的原始新聞列表（JSON 格式）。請你：

1. 從中篩選出最重要的 15-20 則新聞
2. 分類到 5 個版塊：macro（總經/地緣政治）、realestate（不動產/私募）、tech（AI/半導體）、energy（能源/基建）、taiwan（台灣/亞太）
3. 每個版塊 3-5 則
4. 每則新聞標記格式：A（重要新故事）、B（持續追蹤事件）、C（簡要更新）

## 分析思考框架

每則 A/B 格式新聞，請依序過以下六個檢查點思考（不是每個都要寫出來，但思考時要過一遍，有料的才寫）：

1. **傳導鏈**：這個事件會怎麼一路傳下去？A → B → C → 誰受益、誰受害？
   例：油價漲 → 運輸成本升 → CPI 上行 → 央行延後降息 → 高收債承壓
2. **結構 vs. 週期**：這是長期結構性改變（出口管制、能源轉型），還是短期週期波動（庫存回補、季節性需求）？
3. **矛盾/訊號衝突**：市場上有什麼說法互相矛盾？哪個訊號在騙人？
   例：超級雲端商預付 3 年記憶體訂單 vs. 市場說 AI capex 見頂
4. **分叉情境**：如果 X 發生則...，如果 Y 發生則...（條件組合，不給單點預測）
5. **預期差**：市場已經 price in 什麼？還有什麼沒被反映？
6. **週期定位**：我們在這個產業/經濟週期的哪個階段？（擴張/高峰/收縮/谷底）

## 篩選標準
- 有具體數字（匯率、股指、金額、百分比）
- 有因果關係可分析（能寫出傳導鏈）
- 跟 MA 面試可能被問到的主題相關
- 有跨領域連結

## JSON 格式

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
          "what_happened": "4-6 句話，包含具體數字、背景脈絡、各方立場。不只說發生什麼，要說清楚為什麼發生、誰做了什麼、數字是多少。",
          "interpretation": "你的判斷：市場反應是情緒面還是基本面？這個變化的本質是什麼？2-3 句話，有立場、有邏輯。",
          "transmission": "傳導鏈，用 → 連接，至少 4 個節點",
          "structural_or_cyclical": "結構/週期，一句話說明判斷依據",
          "contradiction": "市場上的矛盾訊號（若無則省略此欄位）",
          "scenarios": "如果 X 則...；如果 Y 則...（兩個分叉情境，要有具體數字和時間條件）",
          "outlook": {
            "short_term": "短期（1個月內）：具體預判，含前提條件和數字區間",
            "mid_term": "中期（3-6個月）：結構性趨勢判斷，含關鍵變數",
            "long_term": "長期（1年以上）：這件事對產業/市場格局的永久性影響"
          },
          "watch_list": ["持續追蹤指標1", "持續追蹤指標2", "持續追蹤指標3"],
          "interview_angle": "面試可以怎麼切入，具體指出哪個職位會問什麼",
          "interview_verbal": "面試口說版：一段完整的話（2-3句），可以直接在面試中說出來，要具體、有數字、有判斷、提到相關職位的切入點",
          "sources": [{"name": "來源名稱", "url": "https://..."}]
        },
        {
          "format": "B",
          "title": "事件名稱（持續追蹤）",
          "latest_development": "今天的新發展，3-4 句話",
          "key_data": "2-3 個關鍵數字",
          "interpretation": "你的判斷",
          "transmission": "傳導鏈",
          "outlook": {
            "short_term": "短期展望",
            "mid_term": "中期展望"
          },
          "scenarios": "分叉情境（若有）",
          "interview_verbal": "面試口說版",
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
    "realestate": { "articles": [] },
    "tech": { "articles": [] },
    "energy": { "articles": [] },
    "taiwan": { "articles": [] }
  }
}

## 品質要求
- 數字精確（匯率小數後2位、百分比小數後1位）
- 禁用模糊詞（「大幅」「顯著」「相當」），用數字代替
- 傳導鏈至少 4 個節點，用 → 連接
- 分叉情境要有具體條件和數字，不要「如果情況好轉」這種空話
- 三層展望每層都要有具體數字區間和前提條件
- 面試口說版要能直接唸出來，2-3 句話，有數字有判斷有職位切入
- sources 必須多元：同一則新聞至少引用 2 個不同來源（例如 CNBC + FT、BBC + WSJ、經濟日報 + Al Jazeera）
- 每則新聞的 sources 必須包含實際可訪問的 URL
- 中文來源至少佔 30%（如果 RSS 中文來源不足，可以標注建議補充搜尋的關鍵字）
"""


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    try:
        if platform.system() == "Windows":
            # clip.exe on Windows expects UTF-16LE via stdin
            process = subprocess.Popen(
                ["clip.exe"], stdin=subprocess.PIPE, shell=False
            )
            process.communicate(text.encode("utf-16le"))
            return process.returncode == 0
        elif platform.system() == "Darwin":
            process = subprocess.Popen(
                ["pbcopy"], stdin=subprocess.PIPE, shell=False
            )
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        else:
            # Linux: try xclip
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, shell=False
            )
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
    except Exception:
        return False


def condense_articles(rss_data: dict) -> list:
    """Condense RSS articles for the prompt (save tokens)."""
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
    return condensed


def build_prompt(rss_data: dict) -> str:
    """Build the full prompt with RSS data embedded."""
    condensed = condense_articles(rss_data)
    user_msg = f"""以下是今天 {rss_data['date']} 從 RSS 抓到的 {len(condensed)} 則原始新聞：

{json.dumps(condensed, ensure_ascii=False)}

請按照指定格式分析並回覆 JSON。"""

    return ANALYSIS_PROMPT + "\n\n" + user_msg


def wait_for_analysis_json() -> dict:
    """Wait for user to paste Claude's JSON response."""
    print("\n" + "=" * 50)
    print("📋 請將 Claude 回覆的 JSON 貼在下方")
    print("   貼完後按兩次 Enter 確認")
    print("   （或輸入檔案路徑，例如 data/analysis_2026-03-30.json）")
    print("=" * 50)

    lines = []
    empty_count = 0

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip() == "" :
            empty_count += 1
            if empty_count >= 2 and lines:
                break
        else:
            empty_count = 0
            lines.append(line)

    text = "\n".join(lines).strip()

    # Check if it's a file path
    if (text.endswith(".json") or text.startswith("/") or text.startswith("C:")) and "\n" not in text:
        path = Path(text)
        if not path.is_absolute():
            path = ROOT_DIR / path
        print(f"  📂 讀取檔案：{path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Strip markdown fences if present
    if text.startswith("```"):
        text_lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        if text_lines[-1].strip() == "```":
            text = "\n".join(text_lines[1:-1])
        else:
            text = "\n".join(text_lines[1:])

    return json.loads(text)


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


# ══════════════════════════════════════════
#  Phase 1: Fetch RSS
# ══════════════════════════════════════════
def phase_fetch():
    """Fetch RSS feeds, save raw JSON, build & copy prompt."""
    today = datetime.now().strftime("%Y-%m-%d")
    DATA_DIR.mkdir(exist_ok=True)

    print(f"=== MA 時事日報 — {today} ===\n")

    # Fetch
    print("[1/2] 抓取 RSS 新聞...")
    rss_data = fetch_all_feeds()
    stats = rss_data["stats"]
    print(f"  ✅ 抓取完成：{stats['total']} 則，來自 {len(stats['by_source'])} 個來源")
    if stats["errors"]:
        print(f"  ⚠️  失敗來源：{', '.join(stats['errors'])}")

    # Save raw
    raw_path = DATA_DIR / f"rss_raw_{today}.json"
    raw_path.write_text(json.dumps(rss_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  💾 原始資料：{raw_path}")

    # Build prompt
    print("\n[2/2] 產生 Claude prompt...")
    prompt = build_prompt(rss_data)
    prompt_path = DATA_DIR / f"prompt_{today}.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"  💾 Prompt 備份：{prompt_path}")

    # Copy to clipboard
    if copy_to_clipboard(prompt):
        print(f"  📋 已複製到剪貼簿！（{len(prompt):,} 字元）")
    else:
        print(f"  ⚠️  無法複製到剪貼簿，請手動開啟 {prompt_path}")

    print(f"\n{'='*50}")
    print("📌 下一步：")
    print("  1. 打開 Claude 桌面版（或 claude.ai）")
    print("  2. Ctrl+V 貼上 prompt")
    print("  3. 等 Claude 回覆 JSON")
    print("  4. 複製 JSON，回來執行：python main.py generate")
    print(f"{'='*50}")

    return rss_data


# ══════════════════════════════════════════
#  Phase 2+3: Generate HTML from analysis
# ══════════════════════════════════════════
def phase_generate(analysis_path: str = None, theme: str = "apple"):
    """Read analysis JSON (from file or stdin), generate HTML.

    Args:
        analysis_path: Path to analysis JSON file. If None, prompts for input.
        theme: HTML theme name ('apple', 'ocean', 'autumn').
    """
    from generate_html import THEMES
    today = datetime.now().strftime("%Y-%m-%d")
    DOCS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    # Validate theme
    if theme not in THEMES:
        print(f"⚠️  未知主題 '{theme}'，可選：{', '.join(THEMES.keys())}，使用預設 apple")
        theme = "apple"

    theme_label = THEMES[theme]["label"]
    print(f"🎨 主題：{theme_label}")

    # Get analysis JSON
    if analysis_path:
        path = Path(analysis_path)
        if not path.is_absolute():
            path = ROOT_DIR / path
        print(f"📂 讀取分析檔案：{path}")
        with open(path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
    else:
        analysis = wait_for_analysis_json()

    # Save analysis
    analysis_save_path = DATA_DIR / f"analysis_{today}.json"
    analysis_save_path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  💾 分析結果：{analysis_save_path}")

    # Generate HTML
    total = analysis.get("total_articles", 0)
    print(f"\n🔨 生成 HTML...（{total} 則精選新聞）")
    html_content = generate_html(analysis, theme=theme)

    html_path = DOCS_DIR / f"{today}.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"  ✅ HTML：{html_path}（{len(html_content):,} bytes）")

    # Update index
    generate_index(DOCS_DIR)
    print(f"  ✅ 索引頁已更新")

    # Summary
    print(f"\n{'='*50}")
    print(f"📊 完成摘要")
    print(f"  日期：{today}")
    print(f"  主題：{theme_label}")
    print(f"  精選新聞：{total} 則")
    print(f"  Top 5 必讀：")
    for i, item in enumerate(analysis.get("top5", [])[:5], 1):
        print(f"    {i}. [{item.get('section', '')}] {item.get('summary', '')}")
    print(f"\n💡 執行 git add docs/ && git commit && git push 即可部署")

    return 0


# ══════════════════════════════════════════
#  CLI Entry Point
# ══════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        # Full interactive flow
        phase_fetch()
        print("\n⏳ 請完成 Claude 分析後繼續...")
        phase_generate()
        return 0

    cmd = sys.argv[1].lower()

    # Parse --theme flag from any position
    theme = "light"
    remaining_args = []
    for arg in sys.argv[2:]:
        if arg.startswith("--theme="):
            theme = arg.split("=", 1)[1]
        elif arg == "--theme":
            # handle --theme ocean (space separated)
            pass  # will be picked up by next iteration
        elif sys.argv[sys.argv.index(arg) - 1] == "--theme":
            theme = arg
        else:
            remaining_args.append(arg)

    if cmd == "fetch":
        phase_fetch()
        return 0

    elif cmd == "generate":
        # Optional: pass a file path as argument
        path = remaining_args[0] if remaining_args else None
        phase_generate(path, theme=theme)
        return 0

    elif cmd == "help":
        print("""
MA 時事日報 — 使用方式

  python main.py                        完整互動流程
  python main.py fetch                  只抓 RSS + 產生 prompt
  python main.py generate               貼回 Claude 的 JSON → 產出 HTML
  python main.py generate FILE          從檔案讀取分析 JSON → 產出 HTML
  python main.py generate --theme=ocean 指定主題（apple / ocean / autumn）
  python main.py help                   顯示此說明

主題選項：
  apple   — Apple Style（深黑底 + 藍色光暈）
  ocean   — Ocean Calm 深海藍（沈穩商務風）
  autumn  — Autumn Warm 秋日暖陽（溫暖咖啡金）
  light   — Light 清新白（白色底 + 藍色強調，預設）
        """)
        return 0

    else:
        print(f"❌ 未知指令：{cmd}")
        print("   執行 python main.py help 查看使用方式")
        return 1


if __name__ == "__main__":
    sys.exit(main())
