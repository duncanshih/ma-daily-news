# MA 時事日報

金融業 MA 面試時事新聞系統。從 19 個 RSS 來源抓取財經新聞，透過 Claude 分析篩選，產出蘋果風格的 HTML 日報。

**不需要 API Key** — 全部在本機跑，分析步驟用你的 Claude 訂閱（桌面版或 claude.ai）。

## 快速開始

### 1. 安裝

```bash
git clone https://github.com/duncanshih/ma-daily-news.git
cd ma-daily-news
pip install -r requirements.txt
```

### 2. 每日使用（3 步驟）

```bash
cd src

# Step 1: 抓 RSS + 產生 prompt（自動複製到剪貼簿）
python main.py fetch

# Step 2: 打開 Claude 桌面版 → Ctrl+V 貼上 → 等回覆 JSON

# Step 3: 回來產生 HTML（會請你貼回 JSON）
python main.py generate
```

或一次跑完整互動流程：

```bash
python main.py
```

### 3. 部署到 GitHub Pages

```bash
git add docs/
git commit -m "📰 Daily news $(date +%Y-%m-%d)"
git push
```

Push 後 GitHub Actions 會自動部署到 Pages。

## CLI 指令

| 指令 | 說明 |
|------|------|
| `python main.py` | 完整互動流程 |
| `python main.py fetch` | 只抓 RSS + 複製 prompt |
| `python main.py generate` | 貼回 JSON → 產出 HTML |
| `python main.py generate FILE` | 從檔案讀取 JSON → 產出 HTML |
| `python main.py help` | 顯示說明 |

## RSS 來源（19 個）

| 來源 | 類型 | 語言 |
|------|------|------|
| CNBC (Top/World/Tech/Energy/Finance) | 全球財經 | EN |
| BBC Business | 全球財經 | EN |
| Financial Times (Home/Companies/Markets) | 深度分析 | EN |
| WSJ (World/Markets/Business/Tech) | 深度分析 | EN |
| Al Jazeera | 地緣政治 | EN |
| Yahoo Finance | 美股市場 | EN |
| TechCrunch | 科技創投 | EN |
| NPR Business | 深度報導 | EN |
| 經濟日報 (證券/國際) | 台灣財經 | ZH |

## 目錄結構

```
ma-daily-news/
├── src/
│   ├── main.py              # 主入口（3 步驟 CLI）
│   ├── fetch_news.py         # RSS 抓取
│   └── generate_html.py      # HTML 生成（蘋果風主題）
├── data/                     # 暫存資料（.gitignore）
│   ├── rss_raw_YYYY-MM-DD.json
│   ├── prompt_YYYY-MM-DD.txt
│   └── analysis_YYYY-MM-DD.json
├── docs/                     # 產出的 HTML（GitHub Pages）
├── .github/workflows/
│   └── daily-news.yml        # Pages 自動部署
└── requirements.txt
```
