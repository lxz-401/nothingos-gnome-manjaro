# CachyOS GNOME 51 installation notes

The upstream README paths do not match this repository. Install `alacritty/`,
`conky/` and `eww/` under `~/.config/`; preserve existing files and symlink targets first.
The supplied icon theme and dot-pattern asset are absent.

Local fixes remove missing theme assets, replace GTK color variables in Shell CSS
with literal colors, preserve the default terminal shell, and use the Conky 1.25
X11 output backend through XWayland on GNOME. The broken Cairo hook is disabled.
`start_conky.sh` opens the system monitor; the two-widget launcher uses the
non-Lua Spotify configuration and no longer kills other Conky processes.

GTK3 installation should import Adwaita dark before applying the supplied GTK CSS.
GNOME libadwaita applications use the system dark preference; old custom GTK4 CSS
must be backed up before removing its active overrides.

GNOME Wayland does not provide layer-shell desktop positioning for Eww.
The launcher therefore reports the limitation there; do not autostart Eww on it.
Weather remains disabled until WEATHERAPI_KEY and WEATHER_CITY are set.
Temperature reports real sensor readings or -- rather than invented values.
