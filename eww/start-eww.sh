#!/bin/sh
# GNOME Wayland has no layer-shell support. Do not open misplaced windows there.
if [ "${XDG_SESSION_TYPE:-}" = wayland ]; then
    case "${XDG_CURRENT_DESKTOP:-}" in
        *GNOME*) printf '%s\n' 'Eww desktop widgets require layer-shell or an X11 session.' >&2; exit 1 ;;
    esac
fi
eww daemon || exit
for widget in spotify-now-playing quote-of-the-day cpu-temp day-of-month; do
    eww open "$widget" || exit
done
if [ -n "${WEATHERAPI_KEY:-}" ] && [ -n "${WEATHER_CITY:-}" ]; then
    eww open weather-widget
fi
