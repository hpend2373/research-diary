# Research Diary

[English](README.md) · [한국어](README.ko.md)

Turn a day's work across Codex and Claude Code into one research diary entry. Bring together the analyses, paper reviews, decisions, and open questions that are spread across separate chats.

![research diary — a bear in a blue tie writing research notes beside a laptop and a stack of papers](assets/research-diary-bear-banner.jpg)

Research Diary runs on Windows, macOS, and Linux. The desktop widget saves entries locally as you type. You can revisit past entries and export your diary to Markdown.

## Why I built Research Diary

AI helps me review papers and try analyses faster. Some days I finish with a screen full of answers and drafts and feel worn out. The question I started with can feel a long way off.

The chapter on **권태사회** (“Age of Ennui Society”) in *Trend Korea 2027* describes how a busy day can still feel dull. Having little to do is one source of boredom. The chapter focuses on boredom that can come from too much stimulation. You might already be watching a show and still be looking for something more interesting. A day full of activity can leave little time to get absorbed in any one thing. [Book excerpt, p. 144](https://m.yes24.com/goods/detail/195842609) · [Book launch coverage](https://www.yna.co.kr/view/AKR20260930110700005) · [Examples discussed at the launch](https://www.dailian.co.kr/news/view/1696181)

I built this widget for researchers who have days like that. I wanted a place to bring together what I tried with each agent, what I checked for myself, and why I made a decision. The next morning I can open the previous entry and pick up a question I left there.

## Quick start

Clone the repository with `git clone https://github.com/hpend2373/research-diary.git` or download and extract its ZIP. Open a terminal in the extracted or cloned folder.

### Windows

Install Python 3 with Tcl/Tk and the `py` launcher from [python.org](https://www.python.org/downloads/windows/). Run these commands in PowerShell. The first opens a test window. Close it before starting the widget.

```powershell
py -3 -m tkinter
py -3 journal_widget.py
```

### macOS

Install Python 3 from [python.org](https://www.python.org/downloads/macos/). Close the Tk test window before running the second command.

```sh
python3 -m tkinter
python3 journal_widget.py
```

### Linux

On Ubuntu or Debian, install Tkinter and start the widget.

```sh
sudo apt install python3-tk
python3 journal_widget.py
```

Fedora packages Tkinter as `python3-tkinter`. On Arch Linux, install `tk`. A graphical Linux desktop is required.

On Linux, run `bash install.sh` to add the widget to your applications menu. The installer uses your home directory and runs without administrator privileges. You can also start the installed app with `~/.local/bin/journal-widget`.

## Use the widget

Use **Command** in place of **Ctrl** for the shortcuts below on macOS.

- Click the note to edit it. Changes autosave after about 0.8 seconds. Press **Ctrl+S** to save immediately.
- Use **‹** and **›** to move between days. Open **⋯ → Past entries** to jump to a saved day.
- Use **⋯ → Insert template** to add sections for work, observations, limitations, and next steps.
- Use **⧉** or **Ctrl+Shift+C** to copy the current entry. Use **⋯ → Export to Markdown** to export all entries.
- Drag the date to move the widget and the lower-right handle to resize it. Use the colored dots to tag entries.
- Press **Ctrl+D** for light or dark mode and **Ctrl+B** to toggle the window frame. If a frameless window cannot take keyboard focus, double-click the date to restore the frame.

On X11, install `xclip` or `xsel` to keep copied text after closing the widget. On Wayland, use `wl-clipboard`.

## Combine Codex and Claude Code work into one entry

1. Collect the user requests and assistant replies for the date you want. The example saves a UTF-8 file in your home directory. Keep it outside the Git checkout since it can contain private research.

   macOS or Linux

   ```sh
   python3 journal_today.py --date 2026-01-15 --collect "$HOME/diary-sessions-2026-01-15.txt"
   ```

   Windows PowerShell

   ```powershell
   py -3 journal_today.py --date 2026-01-15 --collect "$HOME/diary-sessions-2026-01-15.txt"
   ```

2. Review the file yourself or ask Codex or Claude Code to read it and draft one entry. For example, use this prompt.

   > Read this file as a record of the day's work. Combine related work across Codex and Claude Code and keep only research activity. Record what I tried, what the records show was checked, why a decision was made when the reason is recorded, and what still needs checking. Note any missing source or incomplete coverage.

3. Paste the reviewed entry into the widget on the matching date, or save it as a UTF-8 text file and append it with `--write-file`.

   ```sh
   python3 journal_today.py --date 2026-01-15 --write-file "$HOME/diary-note-2026-01-15.txt"
   ```

   On Windows, use `py -3` in place of `python3`.

The collector scans local Codex `sessions` and `archived_sessions`, and Claude Code `projects` under `~/.claude`. Set `CODEX_HOME` or `CLAUDE_CONFIG_DIR` if the respective tool stores sessions elsewhere. It selects messages by timestamp in the computer's local time zone and reports matching sessions and files it could not read. Python 3.14+ or `zstd` on PATH is required to include compressed Codex archives.

The export covers text from local Codex and Claude Code conversations. Attachments, raw tool output, and web-only chats are outside its coverage. The collector runs locally and the drafting step happens in the agent you choose.

## Add a note from the command line

```sh
python3 journal_today.py --date 2026-01-15 --write "Reviewed the experiment and recorded follow-up work."
```

The helper appends your text to the selected date. The widget checks for updates to the journal file about every two seconds. On Linux, the installed helper is at `~/.local/share/journal-widget/journal_today.py`.

Run the helper with just `--date` for a short preview of active local sessions.

## Storage and backup

| File | Contents |
| --- | --- |
| `~/Documents/연구일지/journal.json` | Dated journal entries |
| `~/Documents/연구일지/widget.json` | Window geometry, theme, tag, and stacking preferences |

On Windows, `~` is your user profile folder. On systems with a `~/문서` folder and no `~/Documents` folder, the app uses `~/문서/연구일지/`. Set `RESEARCH_DIARY_DIR` to a custom directory before launching the widget and helper if you use a redirected Documents folder or want a different location. Back up `journal.json` to keep your notes.

To uninstall the Linux menu launcher and source installation, remove `~/.local/bin/journal-widget`, `~/.local/share/journal-widget/`, `~/.local/share/applications/journal-widget.desktop`, and `~/.local/share/icons/hicolor/256x256/apps/journal-widget.png`.
