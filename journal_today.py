#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preview local Codex and Claude Code excerpts or append a journal entry.

  python3 journal_today.py
  python3 journal_today.py --date 2026-01-15
  python3 journal_today.py --date 2026-01-15 --write "Reviewed the experiment."
"""
import argparse
import datetime
import glob
import io
import json
import os
import tempfile

DAY   = datetime.date.today().isoformat()
HOME  = os.path.expanduser("~")
TAIL  = 24 * 1024 * 1024      # 큰 파일은 뒤에서 이만큼만 읽는다 (오늘 기록은 파일 끝에 있다)
MAXLEN = 300                  # 메시지 1건당 글자 수 상한
MAXMSG = 20                   # 세션 1건당 보여줄 '내 요청' 수 상한

def day_start_ts():
    d = datetime.date.fromisoformat(DAY)
    return datetime.datetime(d.year, d.month, d.day).timestamp()

def touched_today(path):
    try:
        return os.path.getmtime(path) >= day_start_ts()
    except OSError:
        return False

def tail_lines(path):
    """파일 끝 TAIL 바이트를 줄 단위로 읽는다. 첫 줄은 잘렸을 수 있으므로 버린다."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > TAIL:
            f.seek(size - TAIL)
            f.readline()
        for raw in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            yield raw

def first_line(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.readline()

def clip(s):
    s = " ".join((s or "").split())
    return s[:MAXLEN] + ("…" if len(s) > MAXLEN else "")

def local_timestamp(ts):
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().isoformat()
    except (AttributeError, ValueError):
        return ""


def hhmm(ts):
    return ts[11:16] or "?"

NOISE = ("<INSTRUCTIONS>", "# AGENTS.md instructions",
         "The following is the Codex agent history",
         "<system-reminder>", "Caveat: The messages below",
         "# Files mentioned by the user")

def is_noise(t):
    t = (t or "").lstrip()
    return (not t) or t.startswith(NOISE)


class Session:
    def __init__(self, source, where, path):
        self.source, self.where, self.path = source, where, path
        self.mine, self.theirs, self.stamps = [], [], []

    def add(self, who, text, ts):
        (self.mine if who == "user" else self.theirs).append(text)
        if ts:
            self.stamps.append(ts)

    @property
    def span(self):
        if not self.stamps:
            return "?"
        a, b = min(self.stamps), max(self.stamps)
        return hhmm(a) if hhmm(a) == hhmm(b) else "%s~%s" % (hhmm(a), hhmm(b))

    @property
    def count(self):
        return len(self.mine) + len(self.theirs)


# ── Codex ───────────────────────────────────────────────────────────
def codex_sessions():
    out = []
    pat = os.path.join(HOME, ".codex", "sessions", "*", "*", "*", "rollout-*.jsonl")
    for path in sorted(glob.glob(pat)):
        if not touched_today(path):
            continue
        # 첫 줄의 session_meta 로 보조 에이전트 세션을 걸러낸다
        cwd, skip = "", False
        try:
            meta = json.loads(first_line(path)).get("payload", {})
            cwd = meta.get("cwd", "")
            source = meta.get("source")
            if (isinstance(source, dict) and source.get("subagent")) or \
               meta.get("thread_source") in ("guardian_review", "compact", "auto_review"):
                skip = True
        except Exception:
            pass
        if skip:
            continue

        se = Session("Codex", os.path.basename(cwd) or "-", path)
        for raw in tail_lines(path):
            raw = raw.strip()
            if not raw:
                continue
            try:
                o = json.loads(raw)
            except Exception:
                continue
            ts = local_timestamp(o.get("timestamp", ""))
            if not ts.startswith(DAY):
                continue
            if o.get("type") != "event_msg":
                continue
            pl = o.get("payload", {})
            if pl.get("type") == "user_message":
                t = pl.get("message") or ""
                if not is_noise(t):
                    se.add("user", clip(t), ts)
            elif pl.get("type") == "agent_message":
                t = pl.get("message") or ""
                if t and not t.lstrip().startswith("{"):
                    se.add("Codex", clip(t), ts)
        if se.count:
            out.append(se)
    return out


# ── Claude Code ─────────────────────────────────────────────────────
def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
        return "\n".join(parts)
    return ""

def claude_sessions():
    out = []
    pat = os.path.join(HOME, ".claude", "projects", "*", "*.jsonl")
    for path in sorted(glob.glob(pat)):
        if not touched_today(path):
            continue
        project = os.path.basename(os.path.dirname(path)).strip("-").split("-")[-1] or "-"
        se = Session("Claude", project, path)
        for raw in tail_lines(path):
            raw = raw.strip()
            if not raw:
                continue
            try:
                o = json.loads(raw)
            except Exception:
                continue
            ts = local_timestamp(o.get("timestamp", ""))
            if not ts.startswith(DAY):
                continue
            if o.get("isSidechain") or o.get("isMeta"):
                continue
            role = o.get("type")
            if role not in ("user", "assistant"):
                continue
            t = text_of((o.get("message") or {}).get("content"))
            if role == "user":
                if not is_noise(t):
                    se.add("user", clip(t), ts)
            elif t:
                se.add("Claude", clip(t), ts)
        if se.count:
            out.append(se)
    return out


# ── 일지에 기록 ─────────────────────────────────────────────────────
def journal_path():
    for name in ("Documents", "문서"):
        p = os.path.join(HOME, name)
        if os.path.isdir(p):
            return os.path.join(p, "연구일지", "journal.json")
    return os.path.join(HOME, "Documents", "연구일지", "journal.json")

def write_journal(line):
    path = journal_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("The journal file must contain a JSON object.")
    entry = data.get(DAY, {})
    old = (entry.get("text") or "").rstrip()
    line = line.strip()
    if line and line not in old:
        entry["text"] = (old + "\n" + line).strip() if old else line
    entry.setdefault("color", "y")
    entry["updated"] = datetime.datetime.now().strftime("%m/%d %H:%M")
    data[DAY] = entry
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                     dir=os.path.dirname(path), delete=False) as f:
        tmp = f.name
        try:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.close()
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    print("Saved %s (%s)" % (path, DAY))
    print(entry["text"])


def main():
    global DAY
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", type=datetime.date.fromisoformat,
                        default=datetime.date.today(), help="local date (YYYY-MM-DD)")
    parser.add_argument("--write", metavar="TEXT", help="append text to the selected date")
    args = parser.parse_args()
    DAY = args.date.isoformat()
    if args.write is not None:
        if not args.write.strip():
            parser.error("--write requires nonempty text")
        write_journal(args.write)
        return

    sessions = codex_sessions() + claude_sessions()
    sessions.sort(key=lambda s: (s.stamps and min(s.stamps)) or "")
    n = len(sessions)
    cx = sum(1 for s in sessions if s.source == "Codex")
    cl = n - cx

    print("# %s local chat preview" % DAY)
    if not n:
        print("\nNo matching local sessions.")
        return

    print("\nMatching sessions: %d (Codex %d, Claude Code %d)." % (n, cx, cl))
    print("Review the excerpts from all %d matching sessions." % n)

    for i, s in enumerate(sessions, 1):
        print("\n## [%d/%d] %s · %s · %s  (%d user messages, %d replies)"
              % (i, n, s.source, s.where, s.span, len(s.mine), len(s.theirs)))
        shown = s.mine[:MAXMSG]
        if not shown:                        # 내 요청이 안 잡히면 응답으로라도 맥락을 준다
            shown = s.theirs[:MAXMSG]
            print("   (Showing replies because no user messages matched.)")
        for t in shown:
            print("- %s" % t)
        rest = len(s.mine) - len(shown) if s.mine else 0
        if rest > 0:
            print("- (%d additional messages omitted)" % rest)

    print("\n## Sessions in this preview")
    print("Review these %d sessions when drafting the entry." % n)
    for i, s in enumerate(sessions, 1):
        print("  [%d] %s · %s · %s" % (i, s.source, s.where, s.span))


if __name__ == "__main__":
    main()
