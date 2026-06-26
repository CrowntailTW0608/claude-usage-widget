#!/usr/bin/env python3
"""Claude Pro 用量 GUI 懸浮視窗 — 每分鐘自動更新，可調透明度"""

import tkinter as tk
from tkinter import ttk
import threading
import sys
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("請先安裝 requests：pip install requests")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claude_usage import fetch_usage, format_reset_time, SESSION_KEY, ORG_ID

REFRESH_MS = 60_000 # 60秒更新一次
BG     = "#1c1c1c"
HDR    = "#252525"
FG     = "#e0e0e0"
SUB    = "#777777"
BAR_BG = "#383838"
SEV_MAP = {
    "normal":   ("#44cc66", "✓"),
    "warning":  ("#f0a030", "⚠"),
    "critical": ("#ff4444", "●"),
}
LABELS = {
    "session":    "Current Session  (5hr)",
    "weekly_all": "Weekly Limit       (7d)",
}
IMPACT_COLOR = {
    "critical": "#ff4444",
    "major":    "#f0a030",
    "minor":    "#f0d060",
    "none":     "#888888",
}
STATUS_ZH = {
    "investigating": "調查中",
    "identified":    "已確認",
    "monitoring":    "監控中",
    "resolved":      "已解決",
    "postmortem":    "事後分析",
}


def _fetch_incidents() -> list:
    url = "https://status.claude.com/api/v2/incidents.json"
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    today = datetime.now().date()
    result = []
    for inc in r.json().get("incidents", []):
        try:
            created = datetime.fromisoformat(
                inc["created_at"].replace("Z", "+00:00")
            ).astimezone()
        except Exception:
            continue
        if created.date() == today:
            result.append({
                "name":   inc["name"],
                "status": inc.get("status", ""),
                "impact": inc.get("impact", "none"),
            })
    return result


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude 用量")
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.88)
        self.root.geometry("300x200+80+80")
        self._ox = self._oy = 0
        self._timer = None
        self._compact = False
        self._pcts = {"session": 0, "weekly_all": 0}
        self._sevs = {"session": FG, "weekly_all": FG}
        self._build()
        self._refresh()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_header()
        self._compact_frame = tk.Frame(self.root, bg=BG)
        pct_row = tk.Frame(self._compact_frame, bg=BG)
        pct_row.pack(pady=7)
        self._compact_s_lbl = tk.Label(pct_row, text="—%", bg=BG, fg=FG,
                                        font=("Segoe UI", 14, "bold"))
        self._compact_s_lbl.pack(side=tk.LEFT)
        tk.Label(pct_row, text=" / ", bg=BG, fg=SUB,
                 font=("Segoe UI", 14)).pack(side=tk.LEFT)
        self._compact_w_lbl = tk.Label(pct_row, text="—%", bg=BG, fg=FG,
                                        font=("Segoe UI", 14, "bold"))
        self._compact_w_lbl.pack(side=tk.LEFT)
        self._build_body()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=HDR, height=30)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        self._title_lbl = tk.Label(hdr, text="Claude Pro Usage", bg=HDR, fg=FG,
                                    font=("Segoe UI", 9, "bold"), padx=10)
        self._title_lbl.pack(side=tk.LEFT, pady=5)
        title = self._title_lbl

        btn_x = tk.Label(hdr, text="✕", bg=HDR, fg="#777",
                         font=("Segoe UI", 10), padx=8, cursor="hand2")
        btn_x.pack(side=tk.RIGHT, pady=5)
        btn_x.bind("<Button-1>", lambda _: self.root.destroy())

        self._spin = tk.Label(hdr, text="↺", bg=HDR, fg="#555",
                              font=("Segoe UI", 11), padx=4, cursor="hand2")
        self._spin.pack(side=tk.RIGHT, pady=5)
        self._spin.bind("<Button-1>", lambda _: self._refresh())

        self._toggle_btn = tk.Label(hdr, text="⊟", bg=HDR, fg="#555",
                                    font=("Segoe UI", 10), padx=4, cursor="hand2")
        self._toggle_btn.pack(side=tk.RIGHT, pady=5)
        self._toggle_btn.bind("<Button-1>", lambda _: self._toggle_mode())

        for w in (hdr, title):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

    def _build_body(self):
        self._body_frame = tk.Frame(self.root, bg=BG, padx=12, pady=6)
        self._body_frame.pack(fill=tk.BOTH, expand=True)
        self._rows = {k: self._make_row(self._body_frame) for k in ("session", "weekly_all")}
        self._err = tk.Label(self._body_frame, text="", bg=BG, fg="#cc4444", font=("Segoe UI", 8))
        self._err.pack(anchor=tk.W)
        self._build_incident_section(self._body_frame)

    def _build_incident_section(self, parent):
        self._inc_sep   = tk.Frame(parent, bg="#2a2a2a", height=1)
        self._inc_frame = tk.Frame(parent, bg=BG)

    def _build_footer(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Horizontal.TScale",
                        troughcolor=BAR_BG,
                        background=HDR,
                        sliderthickness=12)

        self._foot_frame = tk.Frame(self.root, bg=HDR, padx=10, pady=5)
        self._foot_frame.pack(fill=tk.X)
        tk.Label(self._foot_frame, text="透明度", bg=HDR, fg=SUB, font=("Segoe UI", 8)).pack(side=tk.LEFT)
        v = tk.DoubleVar(value=0.88)
        ttk.Scale(self._foot_frame, from_=0.15, to=1.0, orient=tk.HORIZONTAL, variable=v,
                  command=lambda val: self.root.wm_attributes("-alpha", float(val)),
                  length=140, style="Dark.Horizontal.TScale").pack(side=tk.RIGHT)

    def _make_row(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill=tk.X, pady=2)

        top = tk.Frame(f, bg=BG)
        top.pack(fill=tk.X)
        icon  = tk.Label(top, text="", bg=BG, font=("Segoe UI", 9), width=2, anchor=tk.W)
        icon.pack(side=tk.LEFT)
        name  = tk.Label(top, text="—", bg=BG, fg=SUB, font=("Segoe UI", 9))
        name.pack(side=tk.LEFT)
        pct   = tk.Label(top, text="", bg=BG, fg=FG, font=("Segoe UI", 9, "bold"))
        pct.pack(side=tk.RIGHT)

        bar   = tk.Canvas(f, bg=BG, height=7, highlightthickness=0, bd=0)
        bar.pack(fill=tk.X, pady=(2, 0))

        reset = tk.Label(f, text="", bg=BG, fg=SUB, font=("Segoe UI", 8))
        reset.pack(anchor=tk.W)

        return {"icon": icon, "name": name, "pct": pct, "bar": bar, "reset": reset}

    def _draw_bar(self, canvas, pct, color):
        def draw(event=None):
            w = canvas.winfo_width()
            if w < 2:
                return
            canvas.delete("all")
            canvas.create_rectangle(0, 0, w, 7, fill=BAR_BG, outline="")
            canvas.create_rectangle(0, 0, max(1, int(w * pct / 100)), 7, fill=color, outline="")
        canvas.bind("<Configure>", draw)
        canvas.after(50, draw)

    def _update_row(self, row, kind, pct, resets, sev):
        color, icon_ch = SEV_MAP.get(sev, ("#4a9eff", "●"))
        row["icon"].config(text=icon_ch, fg=color)
        row["name"].config(text=LABELS.get(kind, kind), fg=FG)
        row["pct"].config(text=f"{pct}%")
        row["reset"].config(text=resets)
        self._draw_bar(row["bar"], pct, color)

    def _toggle_mode(self):
        self._compact = not self._compact
        x, y = self.root.winfo_x(), self.root.winfo_y()
        if self._compact:
            self._body_frame.pack_forget()
            self._foot_frame.pack_forget()
            self._compact_frame.pack(fill=tk.X)
            self._toggle_btn.config(text="⊞")
            self._title_lbl.config(text="Usage")
            self.root.geometry(f"140x65+{x}+{y}")
        else:
            self._compact_frame.pack_forget()
            self._body_frame.pack(fill=tk.BOTH, expand=True)
            self._foot_frame.pack(fill=tk.X)
            self._toggle_btn.config(text="⊟")
            self._title_lbl.config(text="Claude Pro Usage")
            self.root.update_idletasks()
            h = max(200, self.root.winfo_reqheight())
            self.root.geometry(f"300x{h}+{x}+{y}")

    # ── Drag ────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._ox, self._oy = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._ox
        y = self.root.winfo_y() + e.y - self._oy
        self.root.geometry(f"+{x}+{y}")

    # ── Data ────────────────────────────────────────────────────────────────

    def _refresh(self):
        if self._timer:
            self.root.after_cancel(self._timer)
        self._err.config(text="")
        self._spin.config(fg="#4a9eff")

        def fetch():
            try:
                data = fetch_usage(SESSION_KEY, ORG_ID)
                self.root.after(0, lambda: self._apply(data))
            except Exception as e:
                msg = str(e)[:45]
                self.root.after(0, lambda: self._err.config(text=f"❌ {msg}"))

            try:
                incidents = _fetch_incidents()
            except Exception:
                incidents = []
            self.root.after(0, lambda: self._apply_incidents(incidents))

            self.root.after(0, lambda: self._spin.config(fg="#555"))

        threading.Thread(target=fetch, daemon=True).start()
        self._timer = self.root.after(REFRESH_MS, self._refresh)

    def _apply_incidents(self, incidents: list):
        for w in self._inc_frame.winfo_children():
            w.destroy()

        if not incidents:
            self._inc_sep.pack_forget()
            self._inc_frame.pack_forget()
            if not self._compact:
                x, y = self.root.winfo_x(), self.root.winfo_y()
                self.root.geometry(f"300x200+{x}+{y}")
            return

        self._inc_sep.pack(fill=tk.X, pady=(4, 0))
        self._inc_frame.pack(fill=tk.X, pady=(2, 0))

        tk.Label(self._inc_frame, text="⚠ 今日事故通報", bg=BG, fg="#cc6644",
                 font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, pady=(2, 1))

        for inc in incidents:
            color  = IMPACT_COLOR.get(inc["impact"], "#888888")
            status = STATUS_ZH.get(inc["status"], inc["status"])
            tk.Label(self._inc_frame,
                     text=f"● {inc['name']}  [{status}]",
                     bg=BG, fg=color, font=("Segoe UI", 8),
                     wraplength=270, justify=tk.LEFT, anchor=tk.W,
                     ).pack(fill=tk.X, anchor=tk.W)

        if not self._compact:
            self.root.update_idletasks()
            h = self.root.winfo_reqheight()
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"300x{h}+{x}+{y}")

    def _apply(self, data):
        for lim in data.get("limits", []):
            kind = lim["kind"]
            if kind not in self._rows:
                continue
            if not lim.get("is_active") and lim.get("percent", 0) == 0:
                continue
            sev = lim.get("severity", "normal")
            self._pcts[kind] = lim["percent"]
            self._sevs[kind], _ = SEV_MAP.get(sev, (FG, ""))
            self._update_row(
                self._rows[kind], kind,
                lim["percent"],
                format_reset_time(lim["resets_at"]),
                sev,
            )
        self._compact_s_lbl.config(text=f"{self._pcts['session']}%",
                                    fg=self._sevs["session"])
        self._compact_w_lbl.config(text=f"{self._pcts['weekly_all']}%",
                                    fg=self._sevs["weekly_all"])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if not SESSION_KEY:
        print("❌ 請先在 .env 設定 CLAUDE_SESSION_KEY")
        sys.exit(1)
    App().run()
