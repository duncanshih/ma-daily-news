#!/usr/bin/env python3
"""
MA 時事日報 — GUI 啟動器
雙擊 bat 檔即可啟動，提供日期輸入、一鍵執行全流程、進度條。
"""

import io
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

# Fix encoding
if sys.stdout is None or (hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != "utf-8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Paths ──
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"

# ── Import project modules ──
sys.path.insert(0, str(SRC_DIR))
from fetch_news import fetch_all_feeds
from generate_html import generate_html
from main import ANALYSIS_PROMPT, build_prompt, condense_articles, generate_index


# ══════════════════════════════════════════
#  API Key Handling
# ══════════════════════════════════════════

def get_api_key():
    """Try to find Anthropic API key from env or .env file."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    # Check .env in project root
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def call_claude_api(prompt: str, api_key: str, log_fn=None) -> dict:
    """Call Claude API to analyze news. Returns parsed JSON dict."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    if log_fn:
        log_fn("   呼叫 Claude API（claude-sonnet-4-20250514）...")
        log_fn("   這可能需要 30-90 秒，請耐心等候...")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        if lines[-1].strip() == "```":
            response_text = "\n".join(lines[1:-1])
        else:
            response_text = "\n".join(lines[1:])

    return json.loads(response_text)


# ══════════════════════════════════════════
#  Main GUI Application
# ══════════════════════════════════════════

class MADailyNewsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MA 時事日報")
        self.root.geometry("720x680")
        self.root.configure(bg="#FFFFFF")
        self.root.resizable(True, True)

        # Detect API key
        self.api_key = get_api_key()

        self._build_ui()
        self.running = False

    def _build_ui(self):
        # ── Style ──
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"),
                        foreground="#1A1A1A", background="#FFFFFF")
        style.configure("Sub.TLabel", font=("Segoe UI", 11),
                        foreground="#5F6368", background="#FFFFFF")
        style.configure("TLabel", font=("Segoe UI", 11),
                        foreground="#333333", background="#FFFFFF")
        style.configure("Status.TLabel", font=("Segoe UI", 10),
                        foreground="#5F6368", background="#F8F9FA")
        style.configure("TFrame", background="#FFFFFF")
        style.configure("Card.TFrame", background="#F8F9FA")

        # Progress bar style
        style.configure("Blue.Horizontal.TProgressbar",
                        troughcolor="#E8EAED",
                        background="#1A73E8",
                        thickness=12)

        # Button styles
        style.configure("Run.TButton", font=("Segoe UI", 13, "bold"), padding=(24, 12))
        style.configure("Small.TButton", font=("Segoe UI", 10), padding=(12, 6))

        # ── Main container ──
        container = ttk.Frame(self.root, padding=24)
        container.pack(fill=tk.BOTH, expand=True)

        # ── Header ──
        ttk.Label(container, text="MA 時事日報", style="Title.TLabel").pack(anchor="w")
        ttk.Label(container, text="一鍵收集 RSS → 分析 → 匯出 HTML → 上傳 GitHub",
                  style="Sub.TLabel").pack(anchor="w", pady=(2, 16))

        # ── Settings card ──
        card = ttk.Frame(container, style="Card.TFrame", padding=16)
        card.pack(fill=tk.X, pady=(0, 12))

        settings_row = ttk.Frame(card, style="Card.TFrame")
        settings_row.pack(fill=tk.X)

        # Date
        ttk.Label(settings_row, text="日期：", font=("Segoe UI", 11),
                  background="#F8F9FA").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(settings_row, textvariable=self.date_var,
                               width=14, font=("Segoe UI", 12))
        date_entry.pack(side=tk.LEFT, padx=(4, 20))

        # API Key status
        if self.api_key:
            key_text = f"API Key: ...{self.api_key[-6:]}"
            key_color = "#34A853"
        else:
            key_text = "API Key: 未設定"
            key_color = "#EA4335"

        self.key_label = ttk.Label(settings_row, text=key_text,
                                   font=("Segoe UI", 10), foreground=key_color,
                                   background="#F8F9FA")
        self.key_label.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(settings_row, text="設定 Key", style="Small.TButton",
                   command=self._prompt_api_key).pack(side=tk.LEFT)

        # ── Run button ──
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=(4, 12))

        self.run_btn = ttk.Button(btn_frame, text="  開始執行  ",
                                  style="Run.TButton", command=self._on_run)
        self.run_btn.pack(side=tk.LEFT)

        self.open_btn = ttk.Button(btn_frame, text="開啟網頁", style="Small.TButton",
                                   command=self._open_html, state=tk.DISABLED)
        self.open_btn.pack(side=tk.LEFT, padx=(12, 0))

        # ── Progress section ──
        prog_frame = ttk.Frame(container)
        prog_frame.pack(fill=tk.X, pady=(0, 8))

        self.step_label = ttk.Label(prog_frame, text="準備就緒", style="Sub.TLabel")
        self.step_label.pack(anchor="w")

        self.progress = ttk.Progressbar(prog_frame, style="Blue.Horizontal.TProgressbar",
                                        orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(6, 0))

        self.pct_label = ttk.Label(prog_frame, text="0%", style="Sub.TLabel")
        self.pct_label.pack(anchor="e")

        # ── Log area ──
        log_frame = ttk.Frame(container)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        self.log = scrolledtext.ScrolledText(
            log_frame, height=16, font=("Consolas", 10),
            bg="#F8F9FA", fg="#333333", relief="flat",
            borderwidth=1, wrap=tk.WORD, state=tk.DISABLED
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        # ── Status bar ──
        status_frame = ttk.Frame(self.root, style="Card.TFrame", padding=(16, 8))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(status_frame, text="就緒", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)

        self.html_path = None

    # ── Helpers ──

    def _log(self, msg: str):
        """Thread-safe log append."""
        def _append():
            self.log.configure(state=tk.NORMAL)
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)
        self.root.after(0, _append)

    def _set_progress(self, value: int, step_text: str = None):
        """Thread-safe progress update."""
        def _update():
            self.progress["value"] = value
            self.pct_label.configure(text=f"{value}%")
            if step_text:
                self.step_label.configure(text=step_text)
        self.root.after(0, _update)

    def _set_status(self, text: str):
        def _update():
            self.status_label.configure(text=text)
        self.root.after(0, _update)

    def _enable_buttons(self, running=False):
        def _update():
            if running:
                self.run_btn.configure(state=tk.DISABLED)
            else:
                self.run_btn.configure(state=tk.NORMAL)
        self.root.after(0, _update)

    def _prompt_api_key(self):
        """Popup to enter API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("設定 Anthropic API Key")
        dialog.geometry("520x180")
        dialog.configure(bg="#FFFFFF")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Anthropic API Key：",
                  font=("Segoe UI", 11)).pack(anchor="w")
        ttk.Label(frame, text="從 console.anthropic.com 取得，格式為 sk-ant-...",
                  font=("Segoe UI", 9), foreground="#5F6368").pack(anchor="w", pady=(2, 8))

        key_var = tk.StringVar(value=self.api_key)
        key_entry = ttk.Entry(frame, textvariable=key_var, width=60, font=("Consolas", 10))
        key_entry.pack(fill=tk.X, pady=(0, 12))
        key_entry.focus_set()

        def save():
            key = key_var.get().strip()
            if key:
                self.api_key = key
                # Save to .env
                env_path = ROOT_DIR / ".env"
                env_path.write_text(f'ANTHROPIC_API_KEY="{key}"\n', encoding="utf-8")
                # Add .env to .gitignore if not there
                gitignore = ROOT_DIR / ".gitignore"
                if gitignore.exists():
                    content = gitignore.read_text(encoding="utf-8")
                    if ".env" not in content:
                        with open(gitignore, "a", encoding="utf-8") as f:
                            f.write("\n.env\n")
                self.key_label.configure(text=f"API Key: ...{key[-6:]}", foreground="#34A853")
                self._log(f"API Key 已儲存至 .env")
            dialog.destroy()

        ttk.Button(frame, text="儲存", style="Small.TButton", command=save).pack(side=tk.RIGHT)
        dialog.bind("<Return>", lambda e: save())

    def _open_html(self):
        if self.html_path and self.html_path.exists():
            os.startfile(str(self.html_path))

    # ── Main workflow ──

    def _on_run(self):
        if self.running:
            return
        if not self.api_key:
            messagebox.showwarning("缺少 API Key",
                                   "請先設定 Anthropic API Key 才能自動分析。\n"
                                   "點擊「設定 Key」按鈕輸入。")
            return

        self.running = True
        self._enable_buttons(running=True)

        # Clear log
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

        # Run in background thread
        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _run_pipeline(self):
        """Full pipeline: fetch → analyze → generate → git push."""
        target_date = self.date_var.get().strip()
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            self._log("日期格式錯誤，請使用 YYYY-MM-DD")
            self._finish(success=False)
            return

        try:
            # ════════════════════════════════════════
            #  Step 1: Fetch RSS (0% → 20%)
            # ════════════════════════════════════════
            self._set_progress(0, "Step 1/5：抓取 RSS 新聞...")
            self._set_status("正在抓取 RSS...")
            self._log(f"{'='*50}")
            self._log(f"  MA 時事日報 — {target_date}")
            self._log(f"{'='*50}")
            self._log("")
            self._log("[1/5] 抓取 RSS 新聞...")

            DATA_DIR.mkdir(exist_ok=True)
            DOCS_DIR.mkdir(exist_ok=True)

            rss_data = fetch_all_feeds()
            stats = rss_data["stats"]
            total_articles = stats["total"]
            total_sources = len(stats["by_source"])

            self._log(f"   抓取完成：{total_articles} 則，來自 {total_sources} 個來源")
            if stats["errors"]:
                self._log(f"   失敗：{', '.join(stats['errors'])}")

            # Taiwan stats
            tw_count = sum(v for k, v in stats["by_source"].items()
                          if any(t in k for t in ["經濟", "工商", "中央社", "自由", "MoneyDJ"]))
            self._log(f"   台灣來源：{tw_count} 則")

            # Save raw
            raw_path = DATA_DIR / f"rss_raw_{target_date}.json"
            raw_path.write_text(json.dumps(rss_data, ensure_ascii=False, indent=2), encoding="utf-8")
            self._log(f"   已存檔：{raw_path.name}")

            self._set_progress(20, "Step 2/5：建構分析 Prompt...")

            # ════════════════════════════════════════
            #  Step 2: Build prompt (20% → 25%)
            # ════════════════════════════════════════
            self._log("")
            self._log("[2/5] 建構分析 Prompt...")

            prompt = build_prompt(rss_data)
            prompt_path = DATA_DIR / f"prompt_{target_date}.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            self._log(f"   Prompt 長度：{len(prompt):,} 字元")
            self._log(f"   已存檔：{prompt_path.name}")

            self._set_progress(25, "Step 3/5：Claude API 分析中...")

            # ════════════════════════════════════════
            #  Step 3: Call Claude API (25% → 70%)
            # ════════════════════════════════════════
            self._log("")
            self._log("[3/5] 呼叫 Claude API 進行深度分析...")
            self._set_status("Claude 分析中（約 30-90 秒）...")

            analysis = call_claude_api(prompt, self.api_key, log_fn=self._log)

            # Save analysis
            analysis_path = DATA_DIR / f"analysis_{target_date}.json"
            analysis_path.write_text(
                json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            n_articles = analysis.get("total_articles", 0)
            self._log(f"   分析完成！{n_articles} 則精選新聞")
            self._log(f"   已存檔：{analysis_path.name}")

            # Show top 5
            for i, item in enumerate(analysis.get("top5", [])[:5], 1):
                sec = item.get("section", "")
                summary = item.get("summary", "")[:60]
                self._log(f"   Top {i}: [{sec}] {summary}...")

            self._set_progress(70, "Step 4/5：生成 HTML...")

            # ════════════════════════════════════════
            #  Step 4: Generate HTML (70% → 85%)
            # ════════════════════════════════════════
            self._log("")
            self._log("[4/5] 生成 HTML（Light 主題）...")
            self._set_status("生成 HTML...")

            html_content = generate_html(analysis, theme="light")
            self.html_path = DOCS_DIR / f"{target_date}.html"
            self.html_path.write_text(html_content, encoding="utf-8")
            self._log(f"   HTML：{self.html_path.name}（{len(html_content):,} bytes）")

            # Update index
            generate_index(DOCS_DIR)
            self._log(f"   索引頁已更新")

            self._set_progress(85, "Step 5/5：上傳 GitHub...")

            # ════════════════════════════════════════
            #  Step 5: Git push (85% → 100%)
            # ════════════════════════════════════════
            self._log("")
            self._log("[5/5] 上傳到 GitHub...")
            self._set_status("Git push 中...")

            git_cwd = str(ROOT_DIR)

            # git add
            result = subprocess.run(
                ["git", "add", f"docs/{target_date}.html", "docs/index.html"],
                cwd=git_cwd, capture_output=True, text=True, encoding="utf-8"
            )

            # git commit
            commit_msg = f"Daily news {target_date} (auto-generated)"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=git_cwd, capture_output=True, text=True, encoding="utf-8"
            )
            if result.returncode == 0:
                self._log(f"   Commit: {commit_msg}")
            else:
                if "nothing to commit" in result.stdout:
                    self._log("   無新變更需要 commit")
                else:
                    self._log(f"   Commit 訊息：{result.stdout.strip()}")

            # git push
            result = subprocess.run(
                ["git", "push"],
                cwd=git_cwd, capture_output=True, text=True, encoding="utf-8"
            )
            if result.returncode == 0:
                self._log(f"   Push 成功！")
            else:
                self._log(f"   Push 結果：{result.stderr.strip()}")

            self._set_progress(100, "完成！")
            self._log("")
            self._log(f"{'='*50}")
            self._log(f"  全部完成！")
            self._log(f"  網頁：https://duncanshih.github.io/ma-daily-news/{target_date}.html")
            self._log(f"{'='*50}")

            self._finish(success=True)

        except json.JSONDecodeError as e:
            self._log(f"\n   JSON 解析失敗：{e}")
            self._log("   Claude 回傳的內容可能不是合法 JSON，請重試。")
            self._finish(success=False)
        except Exception as e:
            self._log(f"\n   錯誤：{type(e).__name__}: {e}")
            self._finish(success=False)

    def _finish(self, success: bool):
        def _update():
            self.running = False
            self._enable_buttons(running=False)
            if success:
                self._set_status("完成！GitHub Pages 將在幾分鐘內更新。")
                self.open_btn.configure(state=tk.NORMAL)
            else:
                self._set_status("執行失敗，請查看 Log。")
                self._set_progress(0, "失敗")
        self.root.after(0, _update)


# ══════════════════════════════════════════
#  Entry Point
# ══════════════════════════════════════════

def main():
    root = tk.Tk()
    root.iconname("MA Daily News")

    # Center window
    root.update_idletasks()
    w, h = 720, 680
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    app = MADailyNewsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
