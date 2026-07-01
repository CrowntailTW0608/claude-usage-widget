#!/usr/bin/env python3
"""Claude Pro 用量查詢共用邏輯"""

import os
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


def fetch_incidents() -> list:
    url = "https://status.claude.com/api/v2/incidents.json"
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    today_utc = datetime.now(timezone.utc).date()
    result = []
    for inc in r.json().get("incidents", []):
        try:
            created = datetime.fromisoformat(
                inc["created_at"].replace("Z", "+00:00")
            )
        except Exception:
            continue
        if created.date() == today_utc:
            result.append({
                "name":   inc["name"],
                "status": inc.get("status", ""),
                "impact": inc.get("impact", "none"),
            })
    return result
