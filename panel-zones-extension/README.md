# NothingOS Panel Zones (GNOME 51)

Reveals only the native left, center or right panel group under the pointer.
Native workspace/application items, Media Controls/clock and tray/system items
retain their existing order and menu handlers. Empty gaps remain transparent.
The group owning an open menu or keyboard focus stays visible. Overview shows
all three groups. Exiting a zone schedules one 250 ms delayed hide; entering
another zone selects it immediately. Hidden actors keep their allocation but
move above the screen, so their invisible buttons do not intercept clicks.

The companion does not patch GNOME functions or replace Hide Top Bar. Use
[Hide Top Bar](https://extensions.gnome.org/extension/545/hide-top-bar/) for edge
reveal and reclaimed desktop space. In its preferences enable mouse-edge
reveal, disable Intellihide, and reduce pressure threshold to 1 if immediate
edge reveal is preferred. Without Hide Top Bar, zones still reveal separately,
but GNOME keeps the usual top-panel work-area reservation.

## Install

Copy this directory to
`${XDG_DATA_HOME:-$HOME/.local/share}/gnome-shell/extensions/nothingos-panel-zones@local/`.
Log out and back in once for GNOME to discover a newly installed local extension,
then run `gnome-extensions enable nothingos-panel-zones@local` if needed.
Do not restart GNOME Shell with Alt+F2 `r` in a Wayland session.

The separate dotfiles export's NothingOS profile also includes these assets.
Keep Hide Top Bar installed separately when using it for whole-panel movement.
No third-party extension code is modified or bundled here.

## Disable / restore

`gnome-extensions disable nothingos-panel-zones@local` restores the panel/group
styles, opacity and position. Hide Top Bar remains independently configurable.
To return to a constantly visible native panel, disable Hide Top Bar as well.
Settings before this installation are saved privately in the printed
`~/.local/state/nothingos/backups/panel-zones-*/settings.json` backup. That file
records only the three changed Hide Top Bar keys and prior extension choices.
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
