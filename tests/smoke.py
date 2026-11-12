"""Exercise the desktop widget and collector with disposable research records."""

import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def write_jsonl(path, *records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as folder:
        home = Path(folder) / "연구 기록"
        codex = home / "codex"
        claude = home / "claude"
        diary = home / "journal"
        os.environ.update(CODEX_HOME=str(codex), CLAUDE_CONFIG_DIR=str(claude),
                          RESEARCH_DIARY_DIR=str(diary))
        import journal_widget

        today = datetime.date.today()
        previous = today - datetime.timedelta(days=1)
        stamp = datetime.datetime.combine(previous, datetime.time(12)).astimezone()
        timestamp = stamp.astimezone(datetime.timezone.utc).isoformat()
        outside = (stamp + datetime.timedelta(days=1)).isoformat()
        codex_reply = "자료를 확인했습니다. " * 40 + "Full reply marker."
        codex_file = codex / "archived_sessions" / "rollout-fixture.jsonl"
        write_jsonl(
            codex_file,
            {"type": "session_meta", "payload": {"cwd": str(home)}},
            {"timestamp": timestamp, "type": "event_msg",
             "payload": {"type": "user_message", "message": "Review the results."}},
            {"timestamp": timestamp, "type": "response_item",
             "payload": {"type": "message", "role": "assistant",
                         "content": [{"type": "output_text", "text": codex_reply}]}},
            {"timestamp": timestamp, "type": "event_msg",
             "payload": {"type": "agent_message", "message": codex_reply}},
            {"timestamp": outside, "type": "event_msg",
             "payload": {"type": "agent_message", "message": "Different day marker."}},
        )
        if sys.version_info >= (3, 14):
            from compression import zstd

            codex_file.with_suffix(".jsonl.zst").write_bytes(zstd.compress(codex_file.read_bytes()))
            codex_file.unlink()
        elif shutil.which("zstd"):
            compressed = subprocess.check_output(["zstd", "-q", "-c", "--", str(codex_file)])
            codex_file.with_suffix(".jsonl.zst").write_bytes(compressed)
            codex_file.unlink()

        write_jsonl(
            claude / "projects" / "research" / "session.jsonl",
            {"timestamp": timestamp, "type": "user",
             "message": {"content": "Check the method."}},
            {"timestamp": timestamp, "type": "assistant",
             "message": {"content": [{"type": "text", "text": "Claude found a limitation."}]}},
        )

        def helper(date, *args):
            return subprocess.run(
                [sys.executable, str(REPO / "journal_today.py"), "--date", date.isoformat(), *args],
                check=True, capture_output=True,
            )

        transcript = home / "messages.txt"
        helper(previous, "--collect", str(transcript))
        text = transcript.read_text(encoding="utf-8")
        assert "Review the results." in text
        assert text.count(codex_reply) == 1, text
        assert "Check the method." in text and "Claude found a limitation." in text
        assert "Different day marker." not in text

        note = home / "summary.txt"
        note.write_text("분석과 문헌 검토를 종합했다.\n다음 할 일: 한계 확인.", encoding="utf-8-sig")
        helper(previous, "--write", "Original entry.")
        helper(previous, "--write-file", str(note))
        stored = json.loads((diary / "journal.json").read_text(encoding="utf-8"))
        assert stored[previous.isoformat()]["text"] == "Original entry.\n" + note.read_text(
            encoding="utf-8-sig")

        root = tk.Tk()
        window_system = root.tk.call("tk", "windowingsystem")
        app = journal_widget.Widget(root)
        root.update()
        try:
            assert app.shortcut == ("Command" if sys.platform == "darwin" else "Ctrl")
            assert app.key == today.isoformat()
            app.shift(-1)
            assert app.text.get("1.0", "end-1c") == stored[previous.isoformat()]["text"]
            app.shift(1)
            assert app.text.get("1.0", "end-1c") == journal_widget.TEMPLATE
            app.text.delete("1.0", "end")
            app.text.insert("1.0", "위젯에서 작성한 일지")
            app.save()
            assert app.to_clipboard("연구 기록")
            if window_system == "aqua":
                assert subprocess.check_output(["pbpaste"]).decode("utf-8") == "연구 기록"
            elif window_system == "win32":
                assert root.clipboard_get() == "연구 기록"
        finally:
            app.quit()
        stored = json.loads((diary / "journal.json").read_text(encoding="utf-8"))
        assert stored[today.isoformat()]["text"] == "위젯에서 작성한 일지"
        assert "Original entry." in stored[previous.isoformat()]["text"]
        print(f"Passed diary smoke test on {sys.platform} using Tk {window_system}.")


if __name__ == "__main__":
    main()
