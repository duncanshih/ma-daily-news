# MA 時事日報

自動化的金融業 MA 面試時事新聞系統。每天從 19 個 RSS 來源抓取財經新聞，透過 Claude AI 分析篩選，產出蘋果風格的 HTML 日報。

## 快速開始

### 1. Clone & 安裝

```bash
git clone https://github.com/YOUR_USERNAME/ma-daily-news.git
cd ma-daily-news
pip install -r requirements.txt
```

### 2. 設定 API Key

```bash
cp .env.example .env
# 編輯 .env，填入你的 Anthropic API Key
```

### 3. 手動執行一次

```bash
cd src
python main.py
```

產出的 HTML 會在 `docs/` 資料夾。

### 4. 設定 GitHub Actions 自動化

1. 到 repo 的 Settings → Secrets and variables → Actions
2. 新增 secret: `ANTHROPIC_API_KEY`
3. 到 Settings → Pages → Source 選 "GitHub Actions"
4. 完成！每天台灣時間 09:00 自動執行

## RSS 來源

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
│   ├── main.py              # 主入口
│   ├── fetch_news.py         # RSS 抓取
│   ├── analyze_news.py       # Claude AI 分析
│   └── generate_html.py      # HTML 生成（蘋果風主題）
├── docs/                     # 產出的 HTML（GitHub Pages 來源）
├── .github/workflows/
│   └── daily-news.yml        # GitHub Actions 自動化
├── requirements.txt
└── .env.example
```
