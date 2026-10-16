#!/usr/bin/env bash
# Use only when YouTube hover previews freeze GNOME with Media Controls enabled.
set -euo pipefail
uuid=mediacontrols@cliffniff.github.com
if ! gnome-extensions info "$uuid" >/dev/null 2>&1; then
    printf '%s\n' 'Media Controls is not installed; no change needed.'
    exit 0
fi
if ! gnome-extensions list --enabled | grep -Fxq "$uuid"; then
    printf '%s\n' 'Media Controls is already disabled; no change needed.'
    exit 0
fi
backup="${XDG_STATE_HOME:-$HOME/.local/state}/nothingos/backups/media-controls-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$backup"
gnome-extensions info "$uuid" > "$backup/extension.txt"
dconf dump /org/gnome/shell/extensions/mediacontrols/ > "$backup/settings.dconf"
gnome-extensions disable "$uuid"
if gnome-extensions list --enabled | grep -Fxq "$uuid"; then
    printf '%s\n' 'Media Controls is still enabled; inspect gnome-extensions info.' >&2
    exit 1
fi
printf 'Media Controls disabled. Backup: %s\n' "$backup"
