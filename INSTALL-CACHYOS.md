# CachyOS GNOME 51 installation notes

The upstream README paths do not match this repository. Back up existing
files, symlinks and their resolved contents before installing.

## Theme

- Install `gtk-theme/gtk.css` at `~/.local/share/themes/NothingOS-GTK/gtk-3.0/gtk.css`,
  prefixed with `@import url("resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained-dark.css");`.
- Install `gtk-theme/gtk4.css` as the theme's `gtk-4.0/gtk.css`; import it from
  `~/.config/gtk-4.0/gtk.css` and `gtk-dark.css` after backing up old overrides.
- Install `shell-theme/gnome-shell.css` under `NothingOS-Shell/gnome-shell/`.
  Enable the GNOME 51 User Themes extension and select NothingOS-Shell.
- Use the dark color preference, Papirus-Dark icons, Inter UI font and Fira Code.
  Upstream does not include the advertised NothingOS-Icons or dot-pattern asset.
- Copy `alacritty/`, `conky/`, and `eww/` to `~/.config/`. Install the supplied
  NDOT font and Symbols Nerd Font for the Eww icon glyphs.

## Widgets on GNOME Wayland

`eww/start-eww.sh` selects **both** the GTK X11 backend and Eww's X11 session
path on GNOME Wayland. XWayland displays dock, sticky windows below other
applications; no layer-shell support is needed. The launcher opens temperature,
media, quote, date and weather windows. Toshkent weather uses Open-Meteo
without an API key, with coordinates in `eww/weather.json`.
No made-up weather, sensor or notification data is enabled.

Conky uses `output_backend = 'x11'`. The supplied config is compact enough for
1920x1080, uses this machine's wlan0/enp7s0 interfaces, reads a real CPU sensor,
and omits unavailable update data. The broken upstream Cairo hook is disabled.

Conky 1.25.2 has a startup font-cache warning. Build official v1.25.4 for the
theme at `~/.local/lib/nothingos/conky`; `start_conky.sh` selects it without
replacing the distribution package. Build command used:

```sh
cmake -S conky-source -B conky-build -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_WAYLAND=OFF -DBUILD_WLAN=ON -DBUILD_LUA_CAIRO=OFF -DBUILD_LUA_IMLIB2=OFF \
  -DBUILD_LUA_RSVG=OFF -DBUILD_DOCS=OFF -DBUILD_TESTS=OFF
cmake --build conky-build -j 4
```

Use GNOME `.desktop` autostart entries pointing to `conky/start_conky.sh` and
`eww/start-eww.sh`. Do not launch a second Conky while one is already running.
The two-Conky launcher is an optional alternative for X11; it is not autostarted.

Weather data: [Open-Meteo](https://open-meteo.com/),
[API documentation](https://open-meteo.com/en/docs).
