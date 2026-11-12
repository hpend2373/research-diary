"""Resolve the data directory shared by the widget and command-line helper."""

import os
from pathlib import Path


def journal_directory():
    override = os.environ.get("RESEARCH_DIARY_DIR")
    if override:
        return Path(override).expanduser().resolve()

    home = Path.home()
    for name in ("Documents", "문서"):
        if (home / name).is_dir():
            return home / name / "연구일지"
    return home / "Documents" / "연구일지"
