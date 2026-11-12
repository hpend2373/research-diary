# Research Diary

[English](README.md) · [한국어](README.ko.md)

Write a daily record of your research. Each dated entry gives you space for what you did, what you observed, what remains unresolved, and what to do next.

![research diary — a bear in a blue tie writing research notes beside a laptop and a stack of papers](assets/research-diary-bear-banner.jpg)

Research Diary runs on Linux and saves entries locally as you type. You can revisit past entries and export your diary to Markdown.

## Why I built Research Diary

AI helps me review papers and try analyses faster. Some days end with a long trail of answers and drafts, and I still feel drained and less connected to the question I started with.

*Trend Korea 2027* describes **권태사회** (“Age of Ennui Society”) as a paradox of abundance. Even when our days are busy and full of stimulation, it can be hard to find something that holds our interest or feels meaningful. I recognize that feeling in AI-assisted research. As the output piles up, I need a moment to ask what I actually learned and what still needs checking. [Book excerpt, p. 144](https://m.yes24.com/goods/detail/195842609) · [Kim Nan-do’s launch remarks](https://www.yna.co.kr/view/AKR20260930110700005)

I built this widget for researchers who recognize that feeling. A few lines at the end of the day can capture what you tried, what the evidence showed, why you made a decision, and where to pick up tomorrow.

## Quick start

Install Python 3 and Tkinter. On Ubuntu or Debian:

```sh
sudo apt install python3-tk
git clone https://github.com/hpend2373/research-diary.git
cd research-diary
python3 journal_widget.py
```

Fedora packages Tkinter as `python3-tkinter`. On Arch Linux, install `tk`. A graphical Linux desktop is required.

To add a launcher to your applications menu, run `bash install.sh`. The installer uses your home directory and runs without administrator privileges. You can also start the installed app with `~/.local/bin/journal-widget`.

## Use the widget

- Click the note to edit it. Changes autosave after about 0.8 seconds. Press **Ctrl+S** to save immediately.
- Use **‹** and **›** to move between days. Open **⋯ → Past entries** to jump to a saved day.
- Use **⋯ → Insert template** to add sections for work, observations, limitations, and next steps.
- Use **⧉** or **Ctrl+Shift+C** to copy the current entry. Use **⋯ → Export to Markdown** to export all entries.
- Drag the date to move the widget and the lower-right handle to resize it. Use the colored dots to tag entries.
- Press **Ctrl+D** for light or dark mode and **Ctrl+B** to toggle the window frame. If a frameless window cannot take keyboard focus, double-click the date to restore the frame.

On X11, install `xclip` or `xsel` to keep copied text after closing the widget. On Wayland, use `wl-clipboard`.

## Add a note from the command line

```sh
python3 journal_today.py --date 2026-01-15 --write "Reviewed the experiment and recorded follow-up work."
```

The helper appends your text to the selected date. The widget checks for updates to the journal file about every two seconds. The installed helper is at `~/.local/share/journal-widget/journal_today.py`.

Running the helper without `--write` prints a short preview of matching local Codex and Claude Code JSONL records. Preview mode reads a bounded portion of each file and limits the number and length of excerpts. It generates excerpts for review, and you supply the journal text yourself.

## Storage and backup

| File | Contents |
| --- | --- |
| `~/Documents/연구일지/journal.json` | Dated journal entries |
| `~/Documents/연구일지/widget.json` | Window geometry, theme, tag, and stacking preferences |

On systems with a `~/문서` folder and no `~/Documents` folder, the app uses `~/문서/연구일지/`. The Korean directory name is retained for compatibility with existing installs. Back up `journal.json` to keep your notes. The widget and command-line helper operate on local files.

To uninstall the menu launcher and source installation, remove `~/.local/bin/journal-widget`, `~/.local/share/journal-widget/`, `~/.local/share/applications/journal-widget.desktop`, and `~/.local/share/icons/hicolor/256x256/apps/journal-widget.png`.
