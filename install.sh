#!/usr/bin/env bash
set -euo pipefail

src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app="$HOME/.local/share/journal-widget"
bin="$HOME/.local/bin"
desktop="$HOME/.local/share/applications"
icons="$HOME/.local/share/icons/hicolor/256x256/apps"

if ! python3 "$src/journal_widget.py" --selftest >/dev/null 2>&1; then
    printf '%s\n' 'Python 3 and Tkinter are required.' \
        'Ubuntu/Debian: sudo apt install python3-tk' \
        'Fedora: sudo dnf install python3-tkinter' \
        'Arch Linux: sudo pacman -S tk' >&2
    exit 1
fi

mkdir -p "$app" "$bin" "$desktop" "$icons"
install -m 644 "$src/journal_widget.py" "$src/journal_today.py" "$src/journal_paths.py" "$app/"
install -m 644 "$src/journal-widget.png" "$icons/journal-widget.png"

{
    printf '%s\n' '#!/usr/bin/env bash'
    printf 'exec python3 %q "$@"\n' "$app/journal_widget.py"
} > "$bin/journal-widget"
chmod +x "$bin/journal-widget"

cat > "$desktop/journal-widget.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Research Journal Widget
Comment=Write and browse daily research notes
Exec="$bin/journal-widget"
Icon=journal-widget
Terminal=false
Categories=Utility;Office;
EOF

printf 'Installed Research Journal Widget.\nLaunch it from your applications menu or run:\n  "%s"\n' "$bin/journal-widget"
