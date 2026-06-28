#!/usr/bin/env python3
"""
Claude Pro 用量查詢腳本
取得 current session % 和 weekly limit % 資訊

使用方式：
  python claude_usage.py

設定：
  編輯下方 SESSION_KEY 和 ORG_ID 變數
  或設定環境變數 CLAUDE_SESSION_KEY / CLAUDE_ORG_ID
"""

import os
import json
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("請先安裝 requests：pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("提示：安裝 python-dotenv 可從 .env 讀取設定：pip install python-dotenv")

# ── 設定區 ────────────────────────────────────────────────────────────────────
SESSION_KEY = os.environ.get("CLAUDE_SESSION_KEY", "")
ORG_ID      = os.environ.get("CLAUDE_ORG_ID", "cc8c9b06-a7ba-4870-bb5a-8c56e745675d")
# ─────────────────────────────────────────────────────────────────────────────


def fetch_usage(session_key: str, org_id: str) -> dict:
    url = f"https://claude.ai/api/organizations/{org_id}/usage"
    headers = {
        "Cookie": f"sessionKey={session_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://claude.ai//settings",
    }
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def format_reset_time(iso_str) -> str:
    """把 UTC 時間轉成本地時間並格式化"""
    if not iso_str:
        return "—"
    dt = datetime.fromisoformat(iso_str).astimezone()
    now = datetime.now(timezone.utc).astimezone()
    delta = dt - now
    total_minutes = int(delta.total_seconds() / 60)
    hours, minutes = divmod(total_minutes, 60)

    if hours > 0:
        remaining = f"Reset in {hours}hr {minutes}min"
    else:
        remaining = f"Reset in {minutes}min"

    return f"{dt.strftime('%m/%d %H:%M')} ({remaining})"


def bar(percent: int, width: int = 30) -> str:
    filled = int(width * percent / 100)
    return "█" * filled + "░" * (width - filled)


def severity_label(s: str) -> str:
    return {"warning": "⚠️ ", "critical": "🔴", "normal": "✅"}.get(s, "")


def print_usage(data: dict):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Claude Pro 用量")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for limit in data.get("limits", []):
        kind = limit["kind"]
        pct = limit["percent"]
        sev = limit.get("severity", "normal")
        resets = format_reset_time(limit["resets_at"])

        if kind == "session":
            label = "Current Session (5hr)"
        elif kind == "weekly_all":
            label = "Weekly Limit     (7d)"
        else:
            label = kind

        icon = severity_label(sev)
        print(f"\n  {icon} {label}")
        print(f"     {bar(pct)}  {pct}%")
        print(f"     {resets}")

    # extra usage
    extra = data.get("extra_usage", {})
    if extra.get("is_enabled"):
        used = extra.get("used_credits", 0)
        limit_val = extra.get("monthly_limit")
        print(f"\n  💳 Extra Usage Credits: ${used} / ${limit_val}")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def main():
    if not SESSION_KEY:
        print("❌ 請先設定 CLAUDE_SESSION_KEY")
        print("   在腳本同目錄建立 .env 檔案，內容：")
        print("   CLAUDE_SESSION_KEY=sk-ant-sid01-...")
        print("   CLAUDE_ORG_ID=cc8c9b06-...")  
        sys.exit(1)

    try:
        data = fetch_usage(SESSION_KEY, ORG_ID)
        print_usage(data)

        # 選用：輸出完整 JSON
        if "--json" in sys.argv:
            print(json.dumps(data, indent=2, ensure_ascii=False))

    except requests.HTTPError as e:
        print(f"❌ HTTP 錯誤 {e.response.status_code}：sessionKey 可能已過期，請重新從 DevTools 取得")
    except Exception as e:
        print(f"❌ 錯誤：{e}")


if __name__ == "__main__":
    main()