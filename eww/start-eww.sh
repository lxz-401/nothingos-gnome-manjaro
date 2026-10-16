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
eww --config "$config" daemon
for widget in spotify-now-playing quote-of-the-day cpu-temp day-of-month weather-widget; do
    eww --config "$config" open "$widget"
done
