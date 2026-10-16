#!/bin/sh
set -eu
# Eww detects session type separately from GTK; both must use X11 on GNOME.
if [ "${XDG_SESSION_TYPE:-}" = wayland ]; then
    case "${XDG_CURRENT_DESKTOP:-}" in
        *GNOME*)
            export XDG_SESSION_TYPE=x11 GDK_BACKEND=x11
            unset WAYLAND_DISPLAY
            ;;
    esac
fi
config="${XDG_CONFIG_HOME:-$HOME/.config}/eww"
runtime="${XDG_RUNTIME_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}}"
mkdir -p "$runtime"
umask 077
exec 9>"$runtime/nothingos-eww-start.lock"
flock -w 15 9

# An early open used to fork a second daemon before the first was ready.
if ! eww --config "$config" ping >/dev/null 2>&1; then
    logs="${XDG_CACHE_HOME:-$HOME/.cache}/eww"
    mkdir -p "$logs"
    # Eww only redirects terminal FDs itself; avoid inheriting login/pipe FDs.
    eww --config "$config" daemon 9>&- </dev/null >>"$logs/eww_nothingos.log" 2>&1
fi
attempt=0
until eww --config "$config" ping >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 100 ]; then
        printf '%s\n' 'Eww daemon did not become ready; see eww logs.' >&2
        exit 1
    fi
    sleep 0.1
done
for widget in spotify-now-playing quote-of-the-day cpu-temp day-of-month weather-widget; do
    eww --no-daemonize --config "$config" open "$widget"
done
