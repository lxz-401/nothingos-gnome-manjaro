#!/usr/bin/env bash
set -euo pipefail

# Install the icon component using the official, pinned upstream revision.
readonly upstream=https://github.com/vinceliuice/WhiteSur-icon-theme.git
readonly revision=73d8040da51a9ed74e47c7366e7e9ff437601a5c
apply=true
case "${1:-}" in
  '') ;;
  --no-apply) apply=false ;;
  -h|--help)
    printf '%s\n' 'Usage: ./install.sh [--no-apply]' \
      'Install WhiteSur icons for the current user and select them in GNOME.' \
      '--no-apply: install files only, without changing the desktop setting.'
    exit 0 ;;
  *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
esac
if (( $# > 1 )); then printf '%s\n' 'Too many arguments.' >&2; exit 2; fi
if (( EUID == 0 )); then
  printf '%s\n' 'Run this installer as your desktop user, without sudo.' >&2
  exit 1
fi
for tool in git gtk-update-icon-cache; do
  if ! command -v "$tool" >/dev/null; then
    printf 'Missing dependency: %s (install it with your package manager).\n' "$tool" >&2
    exit 1
  fi
done
previous_icon=
if "$apply"; then
  command -v gsettings >/dev/null || { printf '%s\n' 'gsettings is required.' >&2; exit 1; }
  previous_icon=$(gsettings get org.gnome.desktop.interface icon-theme)
  if [[ $(gsettings writable org.gnome.desktop.interface icon-theme) != true ]]; then
    printf '%s\n' 'GNOME icon-theme is not writable. Use --no-apply to install files only.' >&2
    exit 1
  fi
fi

temporary=
staging=
icons="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
themes=(WhiteSur WhiteSur-light WhiteSur-dark)
saved=()
installed=()
apply_attempted=false
complete=false
cleanup() {
  local status=$?
  trap - EXIT
  if ! "$complete"; then
    for theme in "${installed[@]}"; do rm -rf -- "$icons/$theme"; done
    for theme in "${saved[@]}"; do mv -- "$staging/old/$theme" "$icons/$theme"; done
    if "$apply_attempted"; then
      gsettings set org.gnome.desktop.interface icon-theme "$previous_icon" || true
    fi
  fi
  [[ -z "$temporary" ]] || rm -rf -- "$temporary"
  [[ -z "$staging" ]] || rm -rf -- "$staging"
  exit "$status"
}
trap cleanup EXIT

# Upstream's light/dark installer contains unquoted paths. Build in a path
# without spaces, then copy with quoted paths into the user's XDG directories.
temporary=$(mktemp -d /tmp/nothingos-whitesur.XXXXXXXX)
printf '%s\n' 'Downloading the official WhiteSur icon theme...'
git init --quiet "$temporary/source"
git -C "$temporary/source" remote add origin "$upstream"
git -C "$temporary/source" fetch --quiet --depth=1 origin "$revision"
git -C "$temporary/source" checkout --quiet --detach FETCH_HEAD
bash "$temporary/source/install.sh" --dest "$temporary/icons" --name WhiteSur --theme default
for theme in "${themes[@]}"; do
  test -s "$temporary/icons/$theme/index.theme"
  cp -- "$temporary/source/COPYING" "$temporary/icons/$theme/COPYING"
  # GNOME always provides Adwaita; Breeze need not exist on another device.
  sed -i 's/^Inherits=.*/Inherits=Adwaita,hicolor,breeze/' "$temporary/icons/$theme/index.theme"
  gtk-update-icon-cache --force "$temporary/icons/$theme"
done

mkdir -p -- "$icons"
staging=$(mktemp -d "$icons/.nothingos-whitesur.XXXXXXXX")
mkdir -- "$staging/new" "$staging/old"
for theme in "${themes[@]}"; do
  cp -a -- "$temporary/icons/$theme" "$staging/new/$theme"
done

backup="${XDG_STATE_HOME:-$HOME/.local/state}/nothingos/backups/whitesur-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p -- "$backup/themes"
chmod 700 "$backup"
printf '%s\n' "$previous_icon" > "$backup/icon-theme.gvariant"
for theme in "${themes[@]}"; do
  if [[ -e "$icons/$theme" || -L "$icons/$theme" ]]; then
    cp -a -- "$icons/$theme" "$backup/themes/$theme"
  fi
done

for theme in "${themes[@]}"; do
  if [[ -e "$icons/$theme" || -L "$icons/$theme" ]]; then
    mv -- "$icons/$theme" "$staging/old/$theme"
    saved+=("$theme")
  fi
  mv -- "$staging/new/$theme" "$icons/$theme"
  installed+=("$theme")
done
if "$apply"; then
  apply_attempted=true
  gsettings set org.gnome.desktop.interface icon-theme WhiteSur
  if [[ $(gsettings get org.gnome.desktop.interface icon-theme) != "'WhiteSur'" ]]; then
    printf '%s\n' 'GNOME did not save WhiteSur. Run this inside your desktop session.' >&2
    exit 1
  fi
fi
complete=true
printf 'WhiteSur installed in: %s\nBackup: %s\n' "$icons" "$backup"
if "$apply"; then printf '%s\n' 'GNOME icon theme: WhiteSur'; fi
