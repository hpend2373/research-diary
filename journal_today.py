#!/usr/bin/env python3
"""Preview or collect local Codex and Claude Code messages, or append a diary entry."""

import argparse
from collections import Counter
from contextlib import contextmanager
import datetime
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from journal_paths import journal_directory

TAIL = 24 * 1024 * 1024
MAXLEN = 300
MAXMSG = 20
NOISE = ("<INSTRUCTIONS>", "# AGENTS.md instructions", "<environment_context>",
         "The following is the Codex agent history", "<system-reminder>",
         "Caveat: The messages below")


@contextmanager
def open_log(path):
    if path.suffix != ".zst":
        with path.open(encoding="utf-8-sig", errors="replace") as stream:
            yield stream
        return

    try:
        from compression import zstd
    except ImportError:
        executable = shutil.which("zstd")
        if not executable:
            raise OSError("reading .zst archives requires Python 3.14+ or zstd on PATH")
        with subprocess.Popen(
            [executable, "-dc", "--", str(path)], stdout=subprocess.PIPE,
            encoding="utf-8", errors="replace",
        ) as process:
            with process.stdout as stream:
                yield stream
            if process.wait():
                raise OSError("zstd could not decompress the archive")
    else:
        with zstd.open(path, "rt", encoding="utf-8", errors="replace") as stream:
            yield stream


def tail_lines(path):
    with path.open("rb") as stream:
        size = stream.seek(0, os.SEEK_END)
        stream.seek(max(0, size - TAIL))
        if size > TAIL:
            stream.readline()
        with io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace") as reader:
            yield from reader


def records(lines):
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def local_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.astimezone()
    except (ValueError, OSError, OverflowError):
        return None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block["text"] for block in content
            if isinstance(block, dict)
            and block.get("type") in ("text", "input_text", "output_text")
            and isinstance(block.get("text"), str)
        )
    return ""


def message_text(text, role):
    text = text.strip()
    if role == "user" and text.startswith("# Files mentioned by the user"):
        # Keep the actual request, while dropping the generated attachment listing.
        text = text.partition("## My request:")[2].strip() or text
    if role == "user" and text.startswith(NOISE):
        return ""
    return text


class Session:
    def __init__(self, source, path):
        self.source = source
        self.path = path
        self.where = path.parent.name if source == "Claude Code" else "-"
        self.messages = []

    @property
    def span(self):
        first = min(stamp for stamp, _, _ in self.messages).strftime("%H:%M")
        last = max(stamp for stamp, _, _ in self.messages).strftime("%H:%M")
        return first if first == last else f"{first}–{last}"


def read_session(source, path, lines, date, full, first_record=None):
    session = Session(source, path)
    canonical = Counter()
    fallback = []
    skip = False

    def inspect_record(record):
        nonlocal skip
        if source == "Codex" and record.get("type") == "session_meta":
            meta = record.get("payload") or {}
            origin = meta.get("source")
            skip = (isinstance(origin, dict) and bool(origin.get("subagent"))
                    or meta.get("thread_source") in ("guardian_review", "compact", "auto_review"))
            session.where = Path(meta.get("cwd") or "").name or "-"
            return

        if skip:
            return
        stamp = local_timestamp(record.get("timestamp"))
        if stamp is None or stamp.date() != date:
            return

        kind = record.get("type")
        if source == "Codex":
            payload = record.get("payload") or {}
            event_roles = {"user_message": "user", "agent_message": "assistant"}
            if kind == "event_msg" and payload.get("type") in event_roles:
                role = event_roles[payload["type"]]
                text = text_of(payload.get("message"))
            elif full and kind == "response_item" and payload.get("type") == "message":
                role = payload.get("role")
                if role not in ("user", "assistant"):
                    return
                text = message_text(text_of(payload.get("content")), role)
                if text:
                    fallback.append((stamp, role, text))
                return
            else:
                return
        else:
            if record.get("isSidechain") or record.get("isMeta") or kind not in ("user", "assistant"):
                return
            role = kind
            text = text_of((record.get("message") or {}).get("content"))
            if record.get("cwd"):
                session.where = Path(record["cwd"]).name or session.where

        text = message_text(text, role)
        if text:
            session.messages.append((stamp, role, text))
            if full and source == "Codex":
                canonical[role, text] += 1

    if first_record is not None:
        inspect_record(first_record)
    for record in records(lines):
        inspect_record(record)

    for stamp, role, text in fallback:
        if canonical[role, text]:
            canonical[role, text] -= 1
        else:
            session.messages.append((stamp, role, text))
    session.messages.sort(key=lambda message: message[0])
    return session


def collect_sessions(date, full):
    codex = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
    sources = [
        ("Codex", codex / "sessions", "**/rollout-*.jsonl"),
        ("Claude Code", claude / "projects", "*/*.jsonl"),
    ]
    if full:
        sources[1:1] = [
            ("Codex", codex / "sessions", "**/rollout-*.jsonl.zst"),
            ("Codex", codex / "archived_sessions", "**/rollout-*.jsonl"),
            ("Codex", codex / "archived_sessions", "**/rollout-*.jsonl.zst"),
        ]
    start = datetime.datetime.combine(date, datetime.time.min).timestamp()
    sessions, warnings = [], []
    checked = Counter()
    for source, directory, pattern in sources:
        for path in sorted(directory.glob(pattern)):
            try:
                if full:
                    with open_log(path) as lines:
                        session = read_session(source, path, lines, date, full)
                else:
                    if path.stat().st_mtime < start:
                        continue
                    first = None
                    if source == "Codex":
                        with open_log(path) as lines:
                            first = next(records([lines.readline()]), None)
                    session = read_session(source, path, tail_lines(path), date, full, first)
            except (OSError, EOFError) as exc:
                warnings.append(f"{source} · {path.name}: {exc}")
                continue
            checked[source] += 1
            if session.messages:
                sessions.append(session)
    sessions.sort(key=lambda session: session.messages[0][0])
    return sessions, checked, warnings


def render_sessions(output, date, sessions, checked, warnings, full):
    title = "local chat messages" if full else "local chat preview"
    print(f"# {date.isoformat()} {title}", file=output)
    print("\nDates and times use this computer's local time zone.", file=output)
    for source in ("Codex", "Claude Code"):
        matches = sum(session.source == source for session in sessions)
        print(f"- {source}: {checked[source]} files read, {matches} matching sessions", file=output)
    if warnings:
        print("\nFiles skipped or unreadable:", file=output)
        for warning in warnings:
            print(f"- {warning}", file=output)
    if not sessions:
        print("\nNo matching local sessions.", file=output)
        return

    for index, session in enumerate(sessions, 1):
        users = [text for _, role, text in session.messages if role == "user"]
        replies = len(session.messages) - len(users)
        print(f"\n## [{index}/{len(sessions)}] {session.source} · {session.where} · {session.span}"
              f" ({len(users)} user messages, {replies} replies)", file=output)
        if full:
            print(f"Source file: {session.path.name}", file=output)
            for stamp, role, text in session.messages:
                print(f"\n[{stamp.isoformat(timespec='seconds')}] {role}\n{text}", file=output)
            continue

        shown = users or [text for _, _, text in session.messages]
        if not users:
            print("   (Showing replies because no user messages matched.)", file=output)
        for text in shown[:MAXMSG]:
            excerpt = " ".join(text.split())
            print("- " + excerpt[:MAXLEN] + ("…" if len(excerpt) > MAXLEN else ""), file=output)
        if len(shown) > MAXMSG:
            print(f"- ({len(shown) - MAXMSG} additional messages omitted)", file=output)


def write_journal(date, text):
    path = journal_directory() / "journal.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("The journal file must contain a JSON object.")
    key = date.isoformat()
    entry = data.setdefault(key, {})
    old = (entry.get("text") or "").rstrip()
    if text not in old:
        entry["text"] = (old + "\n" + text).strip() if old else text
    entry.setdefault("color", "y")
    entry["updated"] = datetime.datetime.now().strftime("%m/%d %H:%M")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                     dir=path.parent, suffix=".tmp", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Saved {path} ({key})")
    print(entry["text"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=datetime.date.fromisoformat,
                        default=datetime.date.today(), help="local date (YYYY-MM-DD)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", metavar="TEXT", help="append text to the selected date")
    mode.add_argument("--write-file", metavar="FILE", type=Path, help="append a UTF-8 note")
    mode.add_argument("--collect", metavar="FILE", type=Path,
                      help="create a UTF-8 file of matching user and assistant messages")
    args = parser.parse_args()
    # Keep Windows console/redirect output usable with Unicode diary entries.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    try:
        if args.write is not None or args.write_file is not None:
            text = args.write if args.write is not None else args.write_file.read_text(encoding="utf-8-sig")
            if not text.strip():
                parser.error("the diary entry must contain text")
            write_journal(args.date, text.strip())
            return

        full = args.collect is not None
        sessions, checked, warnings = collect_sessions(args.date, full)
        if full:
            with args.collect.open("x", encoding="utf-8", newline="\n") as output:
                render_sessions(output, args.date, sessions, checked, warnings, full)
            print(f"Collected {len(sessions)} sessions in {args.collect}. Skipped files: {len(warnings)}.")
        else:
            render_sessions(sys.stdout, args.date, sessions, checked, warnings, full)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
