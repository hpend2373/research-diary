#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연구 일지 위젯 — 바탕화면에 붙어 있는 메모 한 장.

디자인은 getdesign 의 apple 템플릿 토큰을 따른다.
  · 표면은 흰색(#ffffff) 또는 near-black(#1d1d1f), 그 사이를 나누는 것은 헤어라인뿐
  · 강조색은 Action Blue 하나. 나머지 UI는 뒤로 물러난다
  · 타이포와 여백이 화면을 끌고 간다 — 장식·그림자·테두리 없음

기록: ~/Documents/연구일지/journal.json
"""

import sys, os, json, datetime, tempfile, shutil, subprocess

APP_NAME    = "Research Journal"
APP_VERSION = "3.6.0"
FRAME_FIX   = 1   # 입력 불가 설정을 한 번 되돌리기 위한 표식

def _docs():
    home = os.path.expanduser("~")
    for name in ("Documents", "문서"):
        p = os.path.join(home, name)
        if os.path.isdir(p):
            return os.path.join(p, "연구일지")
    return os.path.join(home, "Documents", "연구일지")

DATA_DIR    = _docs()
DATA_FILE   = os.path.join(DATA_DIR, "journal.json")
CONFIG_FILE = os.path.join(DATA_DIR, "widget.json")

if "--selftest" in sys.argv:
    try:
        import tkinter  # noqa: F401
        print("selftest ok"); sys.exit(0)
    except Exception as e:
        print("selftest failed:", e); sys.exit(1)
if "--version" in sys.argv:
    print(APP_NAME, APP_VERSION); sys.exit(0)

import tkinter as tk
from tkinter import font as tkfont, messagebox, filedialog

# ── 디자인 토큰 (apple) ──────────────────────────────────────────────
THEME = {
    "light": {
        "surface":  "#ffffff",   # colors.canvas
        "parchment":"#f5f5f7",   # colors.canvas-parchment
        "ink":      "#1d1d1f",   # colors.ink
        "muted":    "#7a7a7a",   # colors.ink-muted-48
        "faint":    "#c7c7cc",   # 물러나 있는 컨트롤
        "hairline": "#e0e0e0",   # colors.hairline
        "accent":   "#0066cc",   # colors.primary — Action Blue
        "select":   "#d6e9fb",
    },
    "dark": {
        "surface":  "#1d1d1f",
        "parchment":"#272729",   # colors.surface-tile-1
        "ink":      "#ffffff",
        "muted":    "#98989d",
        "faint":    "#48484a",
        "hairline": "#3a3a3c",
        "accent":   "#2997ff",   # colors.primary-on-dark
        "select":   "#0a4a80",
    },
}

# 메모 태그 — 카드 위쪽 3px 스트라이프와 점으로만 나타난다
TAGS  = {"y": "#ffb340", "p": "#ff375f", "b": "#0a84ff",
         "g": "#30d158", "o": "#40c8e0", "v": "#5e5ce6"}
ORDER = ["y", "p", "b", "g", "o", "v"]

# spacing 토큰
SP_XS, SP_SM, SP_MD, SP_LG = 8, 12, 17, 24

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TEMPLATE = "① Work completed\n\n② Results and observations\n\n③ Limitations\n\n④ Next steps\n"
LEGACY_TEMPLATE = "① 한 일\n\n② 결과·관찰\n\n③ 막힌 점\n\n④ 내일 할 일\n"
HEADS = ("①", "②", "③", "④")
TEMPLATE_HEADINGS = {
    line.lstrip("①②③④ ").strip()
    for template in (TEMPLATE, LEGACY_TEMPLATE)
    for line in template.splitlines() if line
}

# SF Pro 에 한글이 없으므로, SF 계열 한글 폰트를 먼저 찾는다
FONTS = ["Pretendard", "Pretendard Variable", "SF Pro Text", "SF Pro Display",
         "Inter", "Noto Sans CJK KR", "Noto Sans KR", "NanumBarunGothic",
         "NanumGothic", "Malgun Gothic", "Apple SD Gothic Neo", "DejaVu Sans"]


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, obj):
    """임시 파일에 쓰고 교체 — 도중에 끊겨도 원본이 깨지지 않는다."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True, ""
    except Exception as e:
        try: os.unlink(tmp)
        except Exception: pass
        return False, str(e)

def _mix(fg, bg, a):
    """fg 를 bg 위에 a(0~1) 만큼 올린 색."""
    f = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(round(f[i] * a + b[i] * (1 - a))) for i in range(3))

_CIRCLE_CACHE = {}

def circle_image(box, diam, color, bg, hole=0):
    """Tk 캔버스에는 안티앨리어싱이 없다. 원을 직접 그려 이미지로 넘긴다.
    hole 을 주면 가운데가 뚫린 고리가 된다."""
    key = (box, diam, color, bg, hole)
    if key in _CIRCLE_CACHE:
        return _CIRCLE_CACHE[key]
    img = tk.PhotoImage(width=box, height=box)
    c, r, ri, ss = (box - 1) / 2.0, diam / 2.0, hole / 2.0, 3
    rows = []
    for y in range(box):
        row = []
        for x in range(box):
            hits = 0
            for sy in range(ss):
                for sx in range(ss):
                    px = x + (sx + 0.5) / ss - 0.5
                    py = y + (sy + 0.5) / ss - 0.5
                    d2 = (px - c) ** 2 + (py - c) ** 2
                    if d2 <= r * r and d2 >= ri * ri:
                        hits += 1
            row.append(_mix(color, bg, hits / float(ss * ss)))
        rows.append("{" + " ".join(row) + "}")
    img.put(" ".join(rows))
    _CIRCLE_CACHE[key] = img
    return img


def today_key():
    return datetime.date.today().isoformat()

def parse_key(k):
    try:    return datetime.date.fromisoformat(k)
    except Exception: return None

def big_date(k):
    d = parse_key(k)
    return d.strftime("%b %d").replace(" 0", " ") if d else k

def day_name(k):
    d = parse_key(k)
    return DAYS[d.weekday()] if d else ""


class Widget:
    def __init__(self, root):
        self.root = root
        os.makedirs(DATA_DIR, exist_ok=True)
        self.notes   = read_json(DATA_FILE, {})
        self.config  = read_json(CONFIG_FILE, {})
        self.tag     = self.config.get("color", "b")
        self.mode    = self.config.get("theme", "light")
        self.stack   = self._initial_stack()
        # 테두리 없는 창은 창 관리자에 따라 키보드 포커스를 아예 못 받는다.
        # 적을 수 없는 메모는 쓸모가 없으므로 기본값은 '테두리 있는 창'.
        self.framed  = bool(self.config.get("framed", True))
        if self.config.get("frame_fix") != FRAME_FIX:
            self.framed = True          # 입력이 막히던 설정을 한 번 되돌린다
            self.config["frame_fix"] = FRAME_FIX
        self.key     = today_key()
        self.job     = None
        self.hot     = False          # 창 위에 포인터가 있는가
        self._file_mtime = 0
        self._last_saved = ""         # 이 날짜로 마지막에 저장한 본문

        root.title(APP_NAME)
        if "--window" in sys.argv:
            self.framed = True
        root.overrideredirect(not self.framed)
        self.apply_stack()
        root.geometry(self.config.get("geometry") or "360x470+80+80")
        root.minsize(280, 260)

        fams = set(tkfont.families(root))
        def f(px, weight="normal"):
            for name in FONTS:
                if name in fams:
                    return tkfont.Font(root=root, family=name, size=-px, weight=weight)
            return tkfont.Font(root=root, size=-px, weight=weight)
        # typography 토큰 (px)
        self.f_date  = f(21, "bold")   # display 계열
        self.f_sub   = f(13)           # caption
        self.f_body  = f(15)           # body
        self.f_head  = f(12, "bold")   # 본문 안 소제목
        self.f_fine  = f(11)           # fine-print
        self.f_ctrl  = f(15)           # 컨트롤 글리프

        self._build()
        self._menu()
        self.apply_theme()
        self.load_day(self.key)

        root.bind("<Enter>", self._enter, add="+")
        root.bind("<Leave>", self._leave, add="+")
        root.bind("<FocusOut>", self._sink, add="+")   # '항상 아래'는 다시 내려보낸다
        root.protocol("WM_DELETE_WINDOW", self.quit)
        root.after(60000, self._midnight_check)

        self._file_mtime = self._mtime()
        root.after(2000, self._watch_file)
        root.after(200, self.take_focus)
        root.after(260, lambda: self.text.focus_set())

    # ── 창 순서 ──────────────────────────────────────────────────────
    # normal : 보통 — 다른 창이 위로 올라올 수 있다 (기본)
    # top    : 항상 위
    # back   : 항상 아래 — 바탕화면에 붙어 있고 다른 창에 늘 가린다
    STACKS = ["normal", "top", "back"]
    STACK_NAME = {"normal": "Normal", "top": "Always on top", "back": "Keep below"}

    def _initial_stack(self):
        s = self.config.get("stack")
        if s in self.STACKS:
            return s
        # 예전 설정(topmost) 이관 — 늘 위에 뜨던 동작은 '보통'으로 내린다
        return "normal"

    def apply_stack(self):
        self.root.attributes("-topmost", self.stack == "top")
        if self.stack == "back":
            self.root.lower()

    def cycle_stack(self):
        self.stack = self.STACKS[(self.STACKS.index(self.stack) + 1) % len(self.STACKS)]
        self.set_stack(self.stack)

    def set_stack(self, s):
        self.stack = s
        self.apply_stack()
        self.apply_theme()
        self.stack_var.set(s)
        self.status.configure(text="Window stacking · " + self.STACK_NAME[s])
        self.save_config()

    def _sink(self, _=None):
        if self.stack == "back":
            self.root.lower()

    def toggle_frame(self):
        """테두리 없는 창에서 글자가 안 들어갈 때를 위한 탈출구.
        창 관리자가 관리하는 일반 창으로 바꾸면 입력은 반드시 된다."""
        self.framed = not self.framed
        geo = self.root.geometry()
        self.root.withdraw()                       # X11 은 다시 매핑해야 반영된다
        self.root.overrideredirect(not self.framed)
        self.root.deiconify()
        self.root.geometry(geo)
        self.apply_stack()
        self.root.after(80, self.take_focus)
        self.root.after(120, lambda: self.text.focus_set())
        self.status.configure(
            text="Window frame " + ("shown" if self.framed else "hidden"))
        self.save_config()

    def take_focus(self, _=None):
        """테두리 없는 창(overrideredirect)은 창 관리자가 입력 포커스를 주지 않는다.
        눌렀을 때 직접 가져와야 글자가 들어간다."""
        try:
            self.root.focus_force()
        except tk.TclError:
            pass

    # ── 구조 ─────────────────────────────────────────────────────────
    def _build(self):
        r = self.root
        # 헤어라인 1px — apple 은 테두리 대신 이 선 하나로 면을 나눈다
        self.border = tk.Frame(r)
        self.border.pack(fill="both", expand=True)
        self.card = tk.Frame(self.border)
        self.card.pack(fill="both", expand=True, padx=1, pady=1)

        self.stripe = tk.Frame(self.card, height=3)
        self.stripe.pack(fill="x")

        # 머리말
        self.head = tk.Frame(self.card, padx=SP_MD, pady=SP_SM)
        self.head.pack(fill="x")

        left = tk.Frame(self.head); left.pack(side="left")
        self.lbl_date = tk.Label(left, font=self.f_date, anchor="w", cursor="fleur")
        self.lbl_date.pack(side="top", anchor="w")
        self.lbl_sub = tk.Label(left, font=self.f_sub, anchor="w", cursor="fleur")
        self.lbl_sub.pack(side="top", anchor="w")
        self.head_box = left

        self.ctrls = tk.Frame(self.head); self.ctrls.pack(side="right")
        self.btn_close = self._ctrl(self.ctrls, "✕", self.quit)
        self.btn_more  = self._ctrl(self.ctrls, "⋯", None)
        self.btn_more.bind("<Button-1>", self.popup)
        self.btn_next  = self._ctrl(self.ctrls, "›", lambda: self.shift(1))
        self.btn_prev  = self._ctrl(self.ctrls, "‹", lambda: self.shift(-1))
        self.btn_copy  = self._ctrl(self.ctrls, "⧉", self.copy_note)
        self.pin_dot   = tk.Label(self.ctrls, bd=0, highlightthickness=0, cursor="hand2")
        self.pin_dot.pack(side="right", padx=(0, SP_XS), pady=(5, 0))
        self.pin_dot.bind("<Button-1>", lambda e: self.cycle_stack())

        # 본문 — 화면의 주인공
        self.text = tk.Text(self.card, font=self.f_body, wrap="word", relief="flat",
                            bd=0, padx=SP_MD, pady=2, highlightthickness=0,
                            undo=True, spacing1=2, spacing2=5, spacing3=9,
                            height=4, width=10, cursor="xterm")
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("head", font=self.f_head, spacing1=10, spacing3=3)
        self.text.bind("<KeyRelease>", lambda e: (self.mark_heads(), self.schedule()))

        # 꼬리말
        self.rule = tk.Frame(self.card, height=1); self.rule.pack(fill="x")
        self.foot = tk.Frame(self.card, padx=SP_MD, pady=10); self.foot.pack(fill="x")
        self.status = tk.Label(self.foot, font=self.f_fine, anchor="w")
        self.status.pack(side="left")

        self.grip = tk.Label(self.foot, bd=0, highlightthickness=0,
                             cursor="bottom_right_corner")
        self.grip.pack(side="right", padx=(SP_SM, 0))
        self.dots = {}
        box = tk.Frame(self.foot); box.pack(side="right")
        self.dot_box = box
        for c in ORDER:
            lb = tk.Label(box, bd=0, highlightthickness=0, cursor="hand2")
            lb.bind("<Button-1>", lambda e, c=c: self.set_tag(c))
            lb.pack(side="left", padx=2)
            self.dots[c] = lb

        # 어디를 누르든 입력 포커스를 가져온다 — 안 그러면 글자가 안 들어간다
        for w in (self.card, self.head, self.head_box, self.foot, self.stripe,
                  self.lbl_date, self.lbl_sub, self.status):
            w.bind("<Button-1>", lambda e: (self.take_focus(), self.text.focus_set()),
                   add="+")
        self.text.bind("<Button-1>", self.take_focus, add="+")

        # 끌어서 이동 / 크기 조절
        for w in (self.head, self.head_box, self.lbl_date, self.lbl_sub, self.stripe):
            w.bind("<Button-1>", self._drag_start, add="+")
            w.bind("<B1-Motion>", self._drag_move, add="+")
        for w in (self.lbl_date, self.lbl_sub):
            w.bind("<Double-Button-1>", lambda e: self.toggle_frame(), add="+")
        self.grip.bind("<Button-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_move)

    def _ctrl(self, parent, glyph, cmd):
        lb = tk.Label(parent, text=glyph, font=self.f_ctrl, cursor="hand2", padx=5)
        lb.pack(side="right")
        if cmd:
            lb.bind("<Button-1>", lambda e: cmd())
        lb.bind("<Enter>", lambda e, w=lb: w.configure(fg=self.C["accent"]))
        lb.bind("<Leave>", lambda e, w=lb: w.configure(fg=self._ctrl_fg()))
        return lb

    def _menu(self):
        self.menu = tk.Menu(self.root, tearoff=0, font=self.f_fine)
        self.menu.add_command(label="Toggle window frame",
                              command=self.toggle_frame)
        self.menu.add_separator()
        self.menu.add_command(label="Copy entry            Ctrl+Shift+C",
                              command=lambda: self.copy_note(False))
        self.menu.add_command(label="Copy entry with date",
                              command=lambda: self.copy_note(True))
        self.menu.add_separator()
        self.menu.add_command(label="Go to today", command=lambda: self.load_day(today_key()))
        self.menu.add_command(label="Insert template", command=self.insert_template)
        self.menu.add_separator()
        self.menu.add_command(label="Past entries", command=self.show_list)
        self.menu.add_command(label="Export to Markdown", command=self.export_md)
        self.menu.add_command(label="Open journal folder", command=self.open_folder)
        self.menu.add_separator()
        self.menu.add_command(label="Toggle light/dark mode", command=self.toggle_mode)
        self.stack_var = tk.StringVar(value=self.stack)
        order = tk.Menu(self.menu, tearoff=0, font=self.f_fine)
        for s in self.STACKS:
            order.add_radiobutton(label=self.STACK_NAME[s], value=s,
                                  variable=self.stack_var,
                                  command=lambda s=s: self.set_stack(s))
        self.menu.add_cascade(label="Window stacking", menu=order)
        self.order_menu = order
        self.menu.add_command(label="Help", command=self.help)
        self.menu.add_command(label="Quit", command=self.quit)
        self.root.bind("<Button-3>", self.popup)
        self.root.bind("<Control-s>", lambda e: self.save(manual=True))
        self.root.bind("<Control-d>", lambda e: self.toggle_mode())
        self.root.bind("<Control-b>", lambda e: self.toggle_frame())
        # Ctrl+C 는 Text 의 '선택 영역 복사'로 남겨 둔다
        self.root.bind("<Control-Shift-C>", lambda e: self.copy_note(False))
        self.root.bind("<Control-Shift-c>", lambda e: self.copy_note(False))

    def popup(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ── 테마 ─────────────────────────────────────────────────────────
    @property
    def C(self):
        return THEME[self.mode]

    def _ctrl_fg(self):
        return self.C["muted"] if self.hot else self.C["faint"]

    def apply_theme(self):
        c = self.C
        self.root.configure(bg=c["surface"])
        self.border.configure(bg=c["hairline"])
        for w in (self.card, self.head, self.head_box, self.ctrls,
                  self.foot, self.dot_box):
            w.configure(bg=c["surface"])
        self.stripe.configure(bg=TAGS[self.tag])
        self.rule.configure(bg=c["hairline"])
        self.lbl_date.configure(bg=c["surface"], fg=c["ink"])
        self.lbl_sub.configure(bg=c["surface"], fg=c["muted"])
        self.status.configure(bg=c["surface"], fg=c["muted"])
        self.text.configure(bg=c["surface"], fg=c["ink"],
                            insertbackground=c["accent"],
                            selectbackground=c["select"], selectforeground=c["ink"])
        self.text.tag_configure("head", foreground=c["muted"])
        for w in (self.btn_copy, self.btn_prev, self.btn_next,
                  self.btn_more, self.btn_close):
            w.configure(bg=c["surface"], fg=self._ctrl_fg())
        # 창 순서 표시 — 찬 점(항상 위) / 고리(보통) / 작은 점(항상 아래)
        if self.stack == "top":
            dot = circle_image(8, 7, c["accent"], c["surface"])
        elif self.stack == "back":
            dot = circle_image(8, 4, c["faint"], c["surface"])
        else:
            dot = circle_image(8, 7, c["muted"], c["surface"], hole=4)
        self.pin_dot.configure(bg=c["surface"], image=dot)
        # 태그 점 — 고른 것만 크게
        for k, lb in self.dots.items():
            lb.configure(bg=c["surface"],
                         image=circle_image(14, 12 if k == self.tag else 7,
                                            TAGS[k], c["surface"]))
        # 크기 조절 손잡이 — 점 세 개
        self.grip.configure(bg=c["surface"], image=self._grip_image(c))
        self.menu.configure(bg=c["surface"], fg=c["ink"],
                            activebackground=c["accent"], activeforeground="#ffffff",
                            bd=0, relief="flat")

    _grip_cache = {}

    def _grip_image(self, c):
        key = (c["faint"], c["surface"])
        if key in Widget._grip_cache:
            return Widget._grip_cache[key]
        box = 12
        img = tk.PhotoImage(width=box, height=box)
        img.put(" ".join("{" + " ".join([c["surface"]] * box) + "}" for _ in range(box)))
        dot = circle_image(4, 3, c["faint"], c["surface"])
        for ox, oy in ((8, 3), (3, 8), (8, 8)):
            img.tk.call(img, "copy", dot, "-to", ox, oy)
        Widget._grip_cache[key] = img
        return img

    def toggle_mode(self):
        self.mode = "dark" if self.mode == "light" else "light"
        self.apply_theme(); self.save_config()

    def set_tag(self, c):
        self.tag = c
        self.apply_theme(); self.save(silent=True); self.save_config()

    def _enter(self, _):
        self.hot = True
        self.take_focus()
        for w in (self.btn_copy, self.btn_prev, self.btn_next,
                  self.btn_more, self.btn_close):
            w.configure(fg=self.C["muted"])

    def _leave(self, _):
        self.hot = False
        for w in (self.btn_copy, self.btn_prev, self.btn_next,
                  self.btn_more, self.btn_close):
            w.configure(fg=self.C["faint"])

    # ── 본문 소제목 강조 ─────────────────────────────────────────────
    def mark_heads(self):
        self.text.tag_remove("head", "1.0", "end")
        total = int(self.text.index("end-1c").split(".")[0])
        for i in range(1, total + 1):
            line = self.text.get("%d.0" % i, "%d.end" % i).lstrip()
            if line.startswith(HEADS):
                self.text.tag_add("head", "%d.0" % i, "%d.end" % i)

    # ── 날짜 ─────────────────────────────────────────────────────────
    def load_day(self, key):
        if self.key and key != self.key:
            self.save(silent=True)
        self.key = key
        note = self.notes.get(key, {})
        self.text.delete("1.0", "end")
        self.text.insert("1.0", note.get("text", "") or TEMPLATE)
        self.mark_heads()
        if note.get("color") in TAGS:
            self.tag = note["color"]
        self.lbl_date.configure(text=big_date(key))
        self.lbl_sub.configure(
            text=day_name(key) + ("  ·  Today" if key == today_key() else ""))
        self.status.configure(
            text=("Saved " + note["updated"]) if note.get("updated") else "New entry")
        self._last_saved = note.get("text", "") or ""
        self.apply_theme()
        self.text.focus_set()

    def shift(self, delta):
        d = parse_key(self.key) or datetime.date.today()
        self.load_day((d + datetime.timedelta(days=delta)).isoformat())

    def insert_template(self):
        self.text.insert("end", "\n" + TEMPLATE)
        self.mark_heads(); self.schedule()

    def _midnight_check(self):
        if self.key != today_key() and not self.job:
            cur = self.text.get("1.0", "end-1c").strip()
            if cur in ("", TEMPLATE.strip()):
                self.load_day(today_key())
        self.root.after(60000, self._midnight_check)

    # ── 복사 ─────────────────────────────────────────────────────────
    def to_clipboard(self, text):
        """Tk 클립보드에 넣고, 가능하면 외부 도구로도 넘긴다.
        Tk 는 프로그램이 살아 있는 동안만 클립보드 주인이라, 위젯을 닫으면
        내용이 사라진다. xclip/wl-copy 를 거치면 닫은 뒤에도 남는다."""
        ok = False
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
            ok = True
        except tk.TclError:
            pass

        wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        x11 = [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]
        cands = ([["wl-copy"]] + x11) if wayland else (x11 + [["wl-copy"]])
        for cmd in cands:
            if not shutil.which(cmd[0]):
                continue
            try:
                subprocess.run(cmd, input=text.encode("utf-8"),
                               timeout=3, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue
        return ok

    def copy_note(self, with_date=False):
        self.save(silent=True)
        body = self.text.get("1.0", "end-1c").strip()
        if body in ("", TEMPLATE.strip(), LEGACY_TEMPLATE.strip()):
            self.status.configure(text="Nothing to copy")
            return
        text = body
        if with_date:
            text = "%s (%s)\n%s" % (self.key, day_name(self.key)[:3], body)
        if self.to_clipboard(text):
            self.status.configure(text="Copied · %d characters" % len(text))
        else:
            self.status.configure(text="Copy failed")

    # ── 바깥에서 들어온 기록 ─────────────────────────────────────────
    # journal-digest 스킬처럼 다른 프로그램이 journal.json 에 쓰면,
    # 위젯을 다시 켜지 않아도 화면에 올라오게 한다.
    def _mtime(self):
        try:
            return os.path.getmtime(DATA_FILE)
        except OSError:
            return 0

    def _watch_file(self):
        m = self._mtime()
        if m and m != self._file_mtime:
            self._file_mtime = m
            self._absorb()
        self.root.after(2000, self._watch_file)

    def _absorb(self):
        fresh = read_json(DATA_FILE, None)
        if not isinstance(fresh, dict):
            return
        mem  = (self.notes.get(self.key) or {}).get("text", "")
        disk = (fresh.get(self.key) or {}).get("text", "")
        self.notes = fresh
        if disk == mem:
            return

        shown = self.text.get("1.0", "end-1c")
        untouched = (self.job is None) and (shown == (mem or TEMPLATE))
        if untouched:
            # 손대지 않은 상태 — 그대로 바꿔 놓는다
            self.text.delete("1.0", "end")
            self.text.insert("1.0", disk or TEMPLATE)
        else:
            # 작성 중이면 덮어쓰지 않고, 새로 들어온 줄만 뒤에 붙인다
            added = [ln for ln in disk.splitlines()
                     if ln.strip() and ln not in shown]
            if not added:
                return
            if not shown.endswith("\n"):
                self.text.insert("end", "\n")
            self.text.insert("end", "\n".join(added))
        self.mark_heads()
        self.save(silent=True)
        self.status.configure(text="Loaded an external journal update")

    # ── 저장 ─────────────────────────────────────────────────────────
    def schedule(self):
        if self.job:
            self.root.after_cancel(self.job)
        self.status.configure(text="Editing…")
        self.job = self.root.after(800, lambda: self.save(silent=True))

    def save(self, silent=False, manual=False):
        if self.job:
            self.root.after_cancel(self.job); self.job = None
        body = self.text.get("1.0", "end-1c")

        # 쓰기 직전에 디스크를 다시 읽어 합친다. 내가 적는 동안 스킬이 붙인 줄을
        # 덮어쓰지 않기 위해서다 — 다른 날짜 항목도 디스크 쪽을 살린다.
        disk = read_json(DATA_FILE, None)
        if not isinstance(disk, dict) and os.path.exists(DATA_FILE):
            self.status.configure(text="Could not read the journal file")
            if manual:
                messagebox.showerror(APP_NAME, "Check that journal.json contains valid journal data.")
            return
        if isinstance(disk, dict):
            outside = (disk.get(self.key) or {}).get("text", "")
            # 내가 마지막으로 저장한 뒤 '새로 생긴' 줄만 합친다.
            # 내가 지운 줄은 이미 _last_saved 에 있으므로 되살아나지 않는다.
            seen = self._last_saved
            added = [ln for ln in outside.splitlines()
                     if ln.strip() and ln not in body and ln not in seen]
            if added:
                body = (body.rstrip() + "\n" + "\n".join(added)).strip()
                self.text.delete("1.0", "end")
                self.text.insert("1.0", body)
                self.mark_heads()
            base = dict(disk)
            base.update({k: v for k, v in self.notes.items() if k not in disk})
            self.notes = base

        if body.strip() in ("", TEMPLATE.strip(), LEGACY_TEMPLATE.strip()):
            self.notes.pop(self.key, None)
            write_json(DATA_FILE, self.notes)
            self._file_mtime = self._mtime()
            self._last_saved = ""
            self.status.configure(text="Empty entry")
            return
        stamp = datetime.datetime.now().strftime("%m/%d %H:%M")
        self.notes[self.key] = {"text": body, "color": self.tag, "updated": stamp}
        ok, err = write_json(DATA_FILE, self.notes)
        self._file_mtime = self._mtime()          # 내가 쓴 것은 다시 읽지 않는다
        if ok:
            self._last_saved = body
        self.status.configure(text=("Saved " + stamp) if ok else "Save failed")
        if not ok and manual:
            messagebox.showerror(APP_NAME, "Could not save the entry.\n\n%s" % err)

    def save_config(self):
        self.config.pop("topmost", None)          # 예전 키는 정리한다
        self.config.update({"geometry": self.root.geometry(), "color": self.tag,
                            "stack": self.stack, "theme": self.mode,
                            "framed": self.framed, "frame_fix": FRAME_FIX})
        write_json(CONFIG_FILE, self.config)

    # ── 끌기 / 크기 조절 ─────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry("+%d+%d" % (e.x_root - self._dx, e.y_root - self._dy))

    def _resize_start(self, e):
        self._rx, self._ry = e.x_root, e.y_root
        self._rw, self._rh = self.root.winfo_width(), self.root.winfo_height()

    def _resize_move(self, e):
        w = max(280, self._rw + e.x_root - self._rx)
        h = max(260, self._rh + e.y_root - self._ry)
        self.root.geometry("%dx%d" % (w, h))

    # ── 부가 기능 ────────────────────────────────────────────────────
    def show_list(self):
        self.save(silent=True)
        c = self.C
        win = tk.Toplevel(self.root)
        win.title("Past entries")
        win.geometry("440x480")
        win.configure(bg=c["surface"])
        tk.Label(win, text="Past entries", font=self.f_date, bg=c["surface"],
                 fg=c["ink"]).pack(anchor="w", padx=SP_LG, pady=(SP_LG, 2))
        tk.Label(win, text="Double-click an entry to open it", font=self.f_fine,
                 bg=c["surface"], fg=c["muted"]).pack(anchor="w", padx=SP_LG)
        tk.Frame(win, height=1, bg=c["hairline"]).pack(fill="x", padx=SP_LG, pady=SP_SM)
        lb = tk.Listbox(win, font=self.f_body, bg=c["surface"], fg=c["ink"],
                        relief="flat", bd=0, highlightthickness=0, activestyle="none",
                        selectbackground=c["accent"], selectforeground="#ffffff")
        lb.pack(fill="both", expand=True, padx=SP_MD, pady=(0, SP_LG))
        keys = sorted(self.notes, reverse=True)
        for k in keys:
            head = ""
            for line in (self.notes[k].get("text") or "").splitlines():
                s = line.strip().lstrip("①②③④").strip()
                if s and s not in TEMPLATE_HEADINGS:
                    head = s; break
            lb.insert("end", "  %s   %s" % (k, head[:34]))
        def go(_=None):
            sel = lb.curselection()
            if sel:
                self.load_day(keys[sel[0]]); win.destroy()
        lb.bind("<Double-Button-1>", go)
        lb.bind("<Return>", go)

    def export_md(self):
        self.save(silent=True)
        path = filedialog.asksaveasfilename(
            title="Export to Markdown", defaultextension=".md",
            initialdir=DATA_DIR, initialfile="research-journal_%s.md" % today_key(),
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")])
        if not path:
            return
        out = ["# Research Journal\n"]
        for k in sorted(self.notes, reverse=True):
            out.append("## %s (%s)\n\n%s\n" %
                       (k, day_name(k), self.notes[k].get("text", "").strip()))
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(out))
            self.status.configure(text="Exported " + os.path.basename(path))
        except Exception as e:
            messagebox.showerror(APP_NAME, "Could not export the journal.\n\n%s" % e)

    def open_folder(self):
        try:
            if sys.platform.startswith("win"):
                os.startfile(DATA_DIR)                       # noqa
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, DATA_DIR], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception:
            messagebox.showinfo(APP_NAME, DATA_DIR)

    def help(self):
        messagebox.showinfo(
            APP_NAME,
            "Drag the date to move the widget. Drag the lower-right handle to resize it.\n"
            "Edits save after 0.8 seconds. Ctrl+S saves immediately.\n"
            "Use ‹ and › to browse dates. Click ⋯ or right-click to open the menu.\n"
            "Use ⧉ or Ctrl+Shift+C to copy the current entry.\n"
            "Ctrl+D switches the theme. Ctrl+B toggles the window frame.\n"
            "If typing fails in frameless mode, double-click the date to restore the frame.\n"
            "Use the colored dots to tag entries and the top dot to change window stacking.\n\n"
            "Journal file\n%s" % DATA_FILE)

    def quit(self):
        self.save(silent=True)
        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    Widget(root)
    root.mainloop()


if __name__ == "__main__":
    main()
