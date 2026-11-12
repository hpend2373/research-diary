# 연구일지

[English](README.md) · [한국어](README.ko.md)

Codex와 Claude Code에서 하루 동안 진행한 연구를 날짜별 일지 한 편으로 정리합니다. 여러 채팅에 흩어진 분석, 논문 검토, 판단 근거와 남은 질문을 모을 수 있습니다.

![research diary — 파란 넥타이를 맨 곰이 노트북과 연구 자료 옆에서 일지를 쓰는 모습](assets/research-diary-bear-banner.jpg)

Windows, macOS, Linux에서 위젯에 글을 쓰면 컴퓨터에 자동 저장됩니다. 지난 일지를 다시 열거나 전체 기록을 Markdown으로 내보낼 수 있습니다.

## 이 위젯을 만든 이유

AI를 쓰면서 논문을 검토하고 분석을 시도하는 일이 빨라졌습니다. 답변과 초안이 잔뜩 쌓인 화면 앞에서 기운이 빠지는 날도 있습니다. 그런 날에는 처음 풀고 싶었던 질문도 멀게 느껴집니다.

『트렌드 코리아 2027』의 **권태사회**는 바쁘고 볼거리도 많은데 하루가 무료하게 느껴지는 일상을 다룹니다. 할 일이 없어 생기는 무료함을 ‘결핍형 권태’라고 합니다. 책은 일정이 빽빽하고 새로운 자극이 계속 들어오는 날에 생기는 무료함을 ‘과잉형 권태’라고 부릅니다. 영상을 틀어 놓고도 더 재미있는 것을 찾는 모습이 한 예입니다. 그렇게 하루를 보내면 한 가지에 오래 마음을 쏟을 틈이 줄어들 수 있습니다. [책의 공개 발췌문, 144쪽](https://m.yes24.com/goods/detail/195842609) · [출간 간담회 보도](https://www.yna.co.kr/view/AKR20260930110700005) · [간담회에서 소개한 사례](https://www.dailian.co.kr/news/view/1696181)

비슷한 날을 보내는 연구자들을 위해 이 위젯을 만들었습니다. 각 도구에서 해본 일과 직접 확인한 결과를 모으고, 왜 그런 판단을 했는지도 남겨 둘 자리가 필요했습니다. 다음 날에는 지난 일지를 열어, 남겨 둔 질문부터 다시 시작할 수 있습니다.

## 시작하기

`git clone https://github.com/hpend2373/research-diary.git`으로 내려받거나 GitHub에서 ZIP을 받아 압축을 풉니다. 내려받은 폴더에서 터미널을 여세요.

### Windows

[python.org](https://www.python.org/downloads/windows/)에서 Tcl/Tk와 `py` 런처를 포함해 Python 3를 설치하세요. PowerShell에서 첫 번째 명령을 실행한 뒤, Tk 테스트 창을 닫고 두 번째 명령을 실행하세요.

```powershell
py -3 -m tkinter
py -3 journal_widget.py
```

### macOS

[python.org](https://www.python.org/downloads/macos/)에서 Python 3를 설치하세요. 첫 번째 명령으로 연 Tk 테스트 창을 닫고 두 번째 명령을 실행하세요.

```sh
python3 -m tkinter
python3 journal_widget.py
```

### Linux

Ubuntu 또는 Debian에서는 Tkinter를 설치하고 위젯을 실행하세요.

```sh
sudo apt install python3-tk
python3 journal_widget.py
```

Fedora에서는 `python3-tkinter`, Arch Linux에서는 `tk`를 설치하세요. 그래픽 데스크톱 환경이 필요합니다.

Linux 앱 목록에 등록하려면 `bash install.sh`를 실행하세요. 홈 디렉터리에 설치되며 관리자 권한은 필요하지 않습니다. 설치한 앱은 앱 목록 또는 `~/.local/bin/journal-widget`에서 실행할 수 있습니다.

## 사용법

macOS에서는 아래 단축키의 **Ctrl** 대신 **Command**를 사용하세요.

- 메모 영역을 클릭해 작성합니다. 약 0.8초 뒤 자동 저장되며, **Ctrl+S**로 즉시 저장할 수 있습니다.
- **‹**, **›**로 날짜를 넘깁니다. **⋯ → Past entries**에서 저장한 날짜로 이동합니다.
- **⋯ → Insert template**으로 한 일, 결과·관찰, 한계, 다음 할 일 양식을 넣습니다.
- **⧉** 또는 **Ctrl+Shift+C**로 현재 일지를 복사합니다. **⋯ → Export to Markdown**으로 전체 일지를 내보냅니다.
- 날짜를 끌어 위치를 옮기고 오른쪽 아래 손잡이로 크기를 조절합니다. 아래의 색 점으로 태그를 지정합니다.
- **Ctrl+D**는 밝은 화면과 어두운 화면을, **Ctrl+B**는 창 테두리를 전환합니다. 테두리 없는 상태에서 키보드 입력이 안 되면 날짜를 두 번 클릭해 테두리를 복원하세요.

위젯을 닫은 뒤에도 복사한 텍스트를 유지하려면 X11에서 `xclip` 또는 `xsel`, Wayland에서 `wl-clipboard`를 설치하세요.

## Codex와 Claude Code 작업을 일지 한 편으로 정리하기

1. 원하는 날짜의 사용자 요청과 AI 답변을 한 파일에 모읍니다. 아래 명령은 홈 폴더에 UTF-8 파일을 만듭니다. 비공개 연구 내용이 들어갈 수 있으니 Git 저장소 밖에 두세요.

   macOS 또는 Linux

   ```sh
   python3 journal_today.py --date 2026-01-15 --collect "$HOME/diary-sessions-2026-01-15.txt"
   ```

   Windows PowerShell

   ```powershell
   py -3 journal_today.py --date 2026-01-15 --collect "$HOME/diary-sessions-2026-01-15.txt"
   ```

2. 직접 기록을 검토하거나 Codex 또는 Claude Code에 일지 초안을 요청하세요.

   > 이 파일을 하루 작업의 기록으로 읽고, 두 도구에서 진행한 일 중 같은 연구를 묶어 일지 한 편으로 정리해줘. 연구 활동만 담고, 해본 일과 기록에서 확인된 결과, 이유가 남아 있는 판단, 아직 확인할 질문을 적어줘. 빠진 자료나 확인하지 못한 범위가 있으면 밝혀줘.

3. 검토한 일지를 위젯의 해당 날짜에 붙여넣으세요. UTF-8 텍스트 파일로 저장했다면 `--write-file`로 덧붙일 수 있습니다.

   ```sh
   python3 journal_today.py --date 2026-01-15 --write-file "$HOME/diary-note-2026-01-15.txt"
   ```

   Windows에서는 `python3` 대신 `py -3`를 사용하세요.

수집 도구는 로컬 Codex의 `sessions`, `archived_sessions`와 Claude Code의 `~/.claude/projects`를 읽습니다. 도구별 저장 위치를 바꿨다면 `CODEX_HOME` 또는 `CLAUDE_CONFIG_DIR`로 지정하세요. 컴퓨터의 시간대를 기준으로 해당 날짜의 메시지를 골라내고, 찾은 세션과 읽지 못한 파일을 표시합니다. 압축된 Codex 기록을 읽으려면 Python 3.14 이상 또는 PATH에 등록된 `zstd`가 필요합니다.

내보내는 범위는 로컬 Codex·Claude Code 대화의 텍스트입니다. 첨부 파일, 도구 실행 원문, 웹에만 있는 채팅은 범위 밖입니다. 기록은 컴퓨터에서 모으고, 일지 초안은 선택한 에이전트에서 작성합니다.

## 명령줄에서 일지 추가하기

```sh
python3 journal_today.py --date 2026-01-15 --write "실험 결과를 검토하고 후속 작업을 정리했다."
```

입력한 글을 해당 날짜의 기존 기록에 덧붙입니다. 위젯은 약 2초마다 일지 파일의 변경을 확인합니다. Linux에 설치한 도구는 `~/.local/share/journal-widget/journal_today.py`에 있습니다.

`--date`만 지정하면 활성 로컬 세션의 짧은 미리보기를 볼 수 있습니다.

## 저장 위치와 백업

| 파일 | 내용 |
| --- | --- |
| `~/Documents/연구일지/journal.json` | 날짜별 일지 |
| `~/Documents/연구일지/widget.json` | 창 위치와 크기, 테마, 태그, 창 순서 설정 |

Windows에서 `~`는 사용자 프로필 폴더입니다. `~/Documents`가 없고 `~/문서`가 있으면 `~/문서/연구일지/`를 사용합니다. 문서 폴더를 옮겼거나 다른 위치에 보관하려면 위젯과 명령줄 도구를 실행하기 전에 `RESEARCH_DIARY_DIR`에 저장 경로를 지정하세요. `journal.json`을 복사해 일지를 백업할 수 있습니다.

Linux에 설치한 위젯을 제거하려면 `~/.local/bin/journal-widget`, `~/.local/share/journal-widget/`, `~/.local/share/applications/journal-widget.desktop`, `~/.local/share/icons/hicolor/256x256/apps/journal-widget.png`를 삭제하세요.
