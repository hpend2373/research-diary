# 연구일지

[English](README.md) · [한국어](README.ko.md)

오늘 한 연구를 날짜별로 기록하세요. 한 일, 결과와 관찰, 남은 한계, 다음 할 일을 한곳에 정리할 수 있습니다.

![노트북과 펼친 공책을 놓고 연구일지를 쓰는 모습](assets/research-diary-cover.jpg)

Linux 바탕화면에서 글을 쓰면 컴퓨터에 자동 저장됩니다. 지난 일지를 다시 열거나 전체 기록을 Markdown으로 내보낼 수 있습니다.

## 시작하기

Python 3와 Tkinter가 필요합니다. Ubuntu 또는 Debian에서는 아래 명령을 실행하세요.

```sh
sudo apt install python3-tk
git clone https://github.com/hpend2373/research-journal-widget.git
cd research-journal-widget
python3 journal_widget.py
```

Fedora에서는 `python3-tkinter`, Arch Linux에서는 `tk`를 설치하세요. 그래픽 데스크톱 환경이 필요합니다.

앱 목록에 등록하려면 `bash install.sh`를 실행하세요. 홈 디렉터리에 설치되며 관리자 권한은 필요하지 않습니다. 설치한 앱은 앱 목록 또는 `~/.local/bin/journal-widget`에서 실행할 수 있습니다.

## 사용법

- 메모 영역을 클릭해 작성합니다. 약 0.8초 뒤 자동 저장되며, **Ctrl+S**로 즉시 저장할 수 있습니다.
- **‹**, **›**로 날짜를 넘깁니다. **⋯ → Past entries**에서 저장한 날짜로 이동합니다.
- **⋯ → Insert template**으로 한 일, 결과·관찰, 한계, 다음 할 일 양식을 넣습니다.
- **⧉** 또는 **Ctrl+Shift+C**로 현재 일지를 복사합니다. **⋯ → Export to Markdown**으로 전체 일지를 내보냅니다.
- 날짜를 끌어 위치를 옮기고 오른쪽 아래 손잡이로 크기를 조절합니다. 아래의 색 점으로 태그를 지정합니다.
- **Ctrl+D**는 밝은 화면과 어두운 화면을, **Ctrl+B**는 창 테두리를 전환합니다. 테두리 없는 상태에서 키보드 입력이 안 되면 날짜를 두 번 클릭해 테두리를 복원하세요.

위젯을 닫은 뒤에도 복사한 텍스트를 유지하려면 X11에서 `xclip` 또는 `xsel`, Wayland에서 `wl-clipboard`를 설치하세요.

## 명령줄에서 일지 추가하기

```sh
python3 journal_today.py --date 2026-01-15 --write "실험 결과를 검토하고 후속 작업을 정리했다."
```

입력한 글을 해당 날짜의 기존 기록에 덧붙입니다. 위젯은 약 2초마다 일지 파일의 변경을 확인합니다. 설치한 도구는 `~/.local/share/journal-widget/journal_today.py`에 있습니다.

`--write` 없이 실행하면 조건에 맞는 로컬 Codex·Claude Code JSONL 대화 일부를 출력합니다. 파일을 읽는 범위, 메시지 수와 길이에 제한이 있는 미리보기입니다. 일지 본문은 사용자가 작성해 전달합니다.

## 저장 위치와 백업

| 파일 | 내용 |
| --- | --- |
| `~/Documents/연구일지/journal.json` | 날짜별 일지 |
| `~/Documents/연구일지/widget.json` | 창 위치와 크기, 테마, 태그, 창 순서 설정 |

`~/Documents`가 없고 `~/문서`가 있으면 `~/문서/연구일지/`를 사용합니다. 기존 설치와 호환되도록 저장 폴더 이름을 유지했습니다. `journal.json`을 복사해 일지를 백업할 수 있습니다. 위젯과 명령줄 도구는 로컬 파일을 사용합니다.

설치한 위젯을 제거하려면 `~/.local/bin/journal-widget`, `~/.local/share/journal-widget/`, `~/.local/share/applications/journal-widget.desktop`, `~/.local/share/icons/hicolor/256x256/apps/journal-widget.png`를 삭제하세요.
