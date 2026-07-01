# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案說明

- **`claude_usage_gui.py`** — GUI 懸浮視窗，常駐螢幕，每分鐘自動更新
- **`claude_usage_utils.py`** — 共用邏輯（API 呼叫、時間格式化、事故通報查詢）

## 環境設定

`.env` 檔案（不提交到版控，範本見 `.env.example`）：

```
CLAUDE_SESSION_KEY=sk-ant-sid01-...
CLAUDE_ORG_ID=cc8c9b06-...
```

`SESSION_KEY` 需從瀏覽器 DevTools 的 Cookie 中取得，屬於短效憑證，過期需重新取得。`ORG_ID` 固定，已在 `claude_usage_utils.py` 中設有預設值。

## 執行指令

```bash
# 安裝依賴（只需一次）
pip install -r requirements.txt

# GUI 懸浮視窗（不會出現 cmd 視窗）
start_gui.vbs
```

虛擬環境位於 `.venv/`，使用 Python 3.10。

## 架構

### `claude_usage_utils.py`（共用邏輯）

GUI 直接 import 此模組的函式，不重複實作：

- `fetch_usage(session_key, org_id)` — 呼叫 `https://claude.ai/api/organizations/{org_id}/usage`，回傳原始 JSON
- `format_reset_time(iso_str)` — UTC ISO 字串 → 本地時間 + 剩餘分鐘
- `fetch_incidents()` — 呼叫 `https://status.claude.com/api/v2/incidents.json`，回傳今日事故清單
- `SESSION_KEY`, `ORG_ID` — 模組層級常數，從 `.env` 讀取

API 回傳的 `limits[].kind` 有兩種值：`session`（5 小時窗口）與 `weekly_all`（7 日窗口）。

### `claude_usage_gui.py`（GUI）

tkinter 懸浮視窗，`overrideredirect(True)` 無系統邊框，`-topmost` 常駐最上層。

**主要方法：**

- `_refresh()` — 每 60 秒觸發一次，在背景執行緒同時呼叫：
  - `fetch_usage()` → `_apply()` 更新用量列
  - `fetch_incidents()` → `_apply_incidents()` 更新事故區塊
- `_toggle_mode()` — 切換完整／精簡模式，動態 pack/forget 各 Frame 並重設視窗尺寸
- `_apply_incidents()` — 從 `https://status.claude.com/api/v2/incidents.json` 取得今日事故，有則顯示，無則隱藏並恢復視窗高度

**兩種顯示模式：**

| 模式 | 視窗尺寸 | 顯示內容 |
|------|----------|----------|
| 完整（預設） | 300×200（有事故時自動撐高） | 進度條、標籤、重置時間、事故通報 |
| 精簡 | 160×65 | `Session% / Weekly%`，顏色對應嚴重度 |

**嚴重度對應（`SEV_MAP`）：**

- `normal` → 綠 `#44cc66`
- `warning` → 橘 `#f0a030`
- `critical` → 紅 `#ff4444`
