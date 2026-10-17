# NothingOS Panel Zones (GNOME 51)

Keeps all three native panel groups visible on the desktop and with normal or
maximized windows. On a fullscreen primary monitor, reveals only the left,
center or right panel group under the pointer.
Native workspace/application items, Media Controls/clock and tray/system items
retain their existing order and menu handlers. Empty gaps remain transparent.
The group owning an open menu or keyboard focus stays visible. Overview shows
all three groups. Exiting a zone schedules one 250 ms delayed hide; entering
another zone selects it immediately. Hidden actors keep their allocation but
move above the screen, so their invisible buttons do not intercept clicks.

The companion does not patch GNOME functions or replace Hide Top Bar. Use
[Hide Top Bar](https://extensions.gnome.org/extension/545/hide-top-bar/) for edge
reveal and reclaimed desktop space. Apply the version-127 compatibility patch
from this repository, then enable Intellihide, turn off its active-window-only
filter, enable mouse-edge reveal and set pressure threshold to 1. The patch
makes parent-panel hiding depend on actual fullscreen state, rather than any
normal/maximized window overlapping the top edge:

```sh
patch --forward -p1 -d "$HOME/.local/share/gnome-shell/extensions/hidetopbar@mathieu.bidon.ca" < compatibility/hidetopbar-fullscreen-only.patch
```

Back up that extension before patching. A successfully patched copy must be
loaded by a fresh Logout → Login; an already loaded GJS module stays cached. Without Hide Top Bar, zones still reveal separately,
but GNOME keeps the usual top-panel work-area reservation.

## Install

Copy this directory to
`${XDG_DATA_HOME:-$HOME/.local/share}/gnome-shell/extensions/nothingos-panel-zones@local/`.
Log out and back in once for GNOME to discover a newly installed local extension,
then run `gnome-extensions enable nothingos-panel-zones@local` if needed.
Do not restart GNOME Shell with Alt+F2 `r` in a Wayland session.

The separate dotfiles export's NothingOS profile also includes these assets.
Keep Hide Top Bar installed separately when using it for whole-panel movement.
Hide Top Bar is installed separately; its small compatibility patch is kept
separately under compatibility/ rather than vendoring the upstream extension.

## Disable / restore

`gnome-extensions disable nothingos-panel-zones@local` restores the panel/group
styles, opacity and position. Hide Top Bar remains independently configurable.
To return to a constantly visible native panel, disable Hide Top Bar as well.
For the unmodified upstream behavior, restore its backed-up intellihide.js and
preferences, then log out and back in.
Settings before this installation are saved privately in the printed
`~/.local/state/nothingos/backups/panel-zones-*/settings.json` backup. That file
records the changed Hide Top Bar keys; the first install also records prior
extension choices. The later panel-fullscreen-* backup includes the upstream
intellihide.js before the fullscreen-only patch.
Restore only the relevant keys; do not overwrite unrelated later choices.

## Verification and limits

`python3 -m unittest discover -s tests -p test_panel_zones.py` from the repository
root exercises actual extension logic with mock actors: region boundaries,
menus, focus, overview, movement coalescing, delayed hide cancellation, cleanup,
and failed-enable cleanup. No permanent polling runs: movement updates coalesce
to one callback per 32 ms, and 100 ms checks run only while a popup is active.
This does not constitute a live Shell hover test. The first real login after
installation must still verify all three regions and menu interaction.

Native GNOME panel group APIs are private; metadata deliberately targets only
GNOME 51. Lock-screen handling is left to GNOME's normal user-extension lifecycle.
