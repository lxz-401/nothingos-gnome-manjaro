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
- Run `./install.sh` to install and automatically select WhiteSur icons.
  It uses the official pinned source, preserves previous WhiteSur files/icon
  selection, and respects XDG data/state directories. `--no-apply` installs
  files for provisioning without changing GNOME settings. See README for dependencies.
- Use the dark color preference, Inter UI font and Fira Code.
  Upstream does not include the advertised NothingOS-Icons or dot-pattern asset.
- Copy `alacritty/`, `conky/`, and `eww/` to `~/.config/`. Install the supplied
  NDOT font and Symbols Nerd Font for the Eww icon glyphs.

## Widgets on GNOME Wayland

`eww/start-eww.sh` selects **both** the GTK X11 backend and Eww's X11 session
path on GNOME Wayland. XWayland displays desktop, sticky windows below other
applications; no layer-shell support is needed. The launcher opens temperature,
media, quote, date and weather windows. Toshkent weather uses Open-Meteo
without an API key, with coordinates in `eww/weather.json`.
The media card selects a playing MPRIS player first, preferring Spotify when
states tie, and falls back to paused media. It shows album art or the selected
app's icon. Copy `scripts/get-media.sh`, `scripts/media-image.py`, and
`scripts/media-fallback.svg` together. Artwork needs Python 3 with PyGObject,
GTK 3 and GdkPixbuf (`python-gobject gtk3 gdk-pixbuf2` on Arch). HTTPS covers
are cached under `$XDG_CACHE_HOME/nothingos/media` (default `~/.cache`), with
at most 16 downloaded images; offline/missing covers use the app icon.

No made-up weather, sensor or notification data is enabled. Startup is serialized
and waits for a ready daemon before opening windows. Explicit opens cannot spawn
a second daemon. Startup output is kept in `~/.cache/eww/eww_nothingos.log`.

Conky and Eww use the `desktop` window type without a separate `below` hint,
so Mutter assigns the desktop layer itself. Keep Eww `wm-ignore=false` to retain
normal compositor stacking instead of overlaying applications.

GNOME's screenshot Window selector does not honor desktop/skip-taskbar exclusion.
Install the version-pinned local fix in `gnome-extension/` and enable
`nothingos-desktop-widgets@local` for the next login. The fix filters only these
widget thumbnails; screen/area screenshots still show the desktop widgets.
See `gnome-extension/README.md` for validation and reversal.

Conky uses `output_backend = 'x11'`. The supplied block layout fits
1920x1080, uses this machine's wlan0/enp7s0 interfaces, reads a real CPU sensor,
and omits unavailable update data. The broken upstream Cairo hook is disabled.

Conky 1.25.2 has a startup font-cache warning. Build official v1.25.4 for the
theme at `~/.local/lib/nothingos/conky`; the user service selects it without
replacing the distribution package. Build command used:

```sh
cmake -S conky-source -B conky-build -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_WAYLAND=OFF -DBUILD_WLAN=ON -DBUILD_LUA_CAIRO=OFF -DBUILD_LUA_IMLIB2=OFF \
  -DBUILD_LUA_RSVG=OFF -DBUILD_DOCS=OFF -DBUILD_TESTS=OFF
cmake --build conky-build -j 4
```

Install `conky/nothingos-conky.service` under `~/.config/systemd/user/` and
run `systemctl --user daemon-reload` and `systemctl --user enable nothingos-conky.service`.
`conky/start_conky.sh` imports the display environment and starts that service.
GNOME `.desktop` autostart invokes the same launcher; repeated starts reuse one
service. `conky/run-blocks.sh` supervises five child processes: clock, CPU, memory,
storage/battery and network. Copy `common.lua`, the five matching `.conf` files
and the executable launcher together to `~/.config/conky/`. The service restarts
on failure and stops with the graphical session.

Install `conky/conky-launcher.sh` as executable `~/.local/bin/conky`. With no
arguments it starts the service; explicit arguments use the fixed binary.
Link `~/.conkyrc` to `~/.config/conky/nothing-phone-conky.conf` so the distribution
binary also finds the X11 config when an existing shell still caches its path.
Use `rehash` in such a zsh session to pick up the new launcher.

Keep the Eww `.desktop` autostart pointing to `eww/start-eww.sh`.
The two-Conky launcher is an optional alternative for X11; it is not autostarted.

Weather data: [Open-Meteo](https://open-meteo.com/),
[API documentation](https://open-meteo.com/en/docs).

## Moving individual Conky blocks

The default layout targets 1920×1080: clock at the top right with a 110 px
right margin, four 300 px blocks at the bottom with left margins of 350, 680,
1010 and 1340 px. This leaves the left Eww widgets and right dock clear.
Edit `alignment`, `gap_x`, and `gap_y` in `clock.conf`, `cpu.conf`,
`memory.conf`, `storage.conf`, or `network.conf`, then run:

```sh
systemctl --user restart nothingos-conky.service
```

Shared fonts, colors, window hints and widths are in `common.lua`. Keep the
class/title unchanged for the screenshot integration. For smaller displays,
reduce block widths and left margins before starting. The old
`nothing-phone-conky.conf` remains an optional single-window configuration;
do not launch it alongside the managed blocks.

## YouTube hover preview freezes

Keep Media Controls enabled with the [preview performance patch](compatibility/media-controls/README.md).
It fixes listener cleanup and bounds metadata, artwork and timeline work.
Install the patch for the matching build and log out/back in to load its JS.
On the current machine the panel is active; Chrome is temporarily excluded
until fresh login, when the patched extension restores it automatically.
The user confirmed the panel works without freezes in that temporary state.
A live retest with the new code after login is still needed. Browser/GPU flags,
Conky, Eww artwork and the theme are unchanged.
