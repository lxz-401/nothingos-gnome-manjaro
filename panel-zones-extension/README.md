# NothingOS Panel Islands (GNOME 51)

- Left/workspace and right/tray groups reveal only inside their own native bounds.
- The clock stays visible in normal/maximized windows. True fullscreen (F11 or
  a fullscreen video) hides every island, including the clock, even on hover.
- Media Controls is also visible while its selected player is Playing. Paused or
  stopped media collapses; hovering the center or opening its menu reveals it
  for resuming playback. With no Media Controls extension the clock still works.
- No full-width background or desktop strut is drawn/reserved. The center group
  stays transparent and only the visible clock/media children receive pill
  backgrounds. Overview and keyboard/menu focus retain access to native items.

This controller owns the panel's visibility. **Keep Hide Top Bar disabled**;
its whole-panel slide would also hide the persistent clock. The earlier
hidetopbar-maximized.patch/windowPolicy.js setup is obsolete for this mode and
is not used. The upstream extension can remain installed, disabled.

## Install / apply an update

Back up the old extension and enabled-extension settings, disable Hide Top Bar
with `gnome-extensions disable hidetopbar@mathieu.bidon.ca`, and copy this directory
to `${XDG_DATA_HOME:-$HOME/.local/share}/gnome-shell/extensions/nothingos-panel-zones@local/`.
Enable `nothingos-panel-zones@local`. A new or modified GJS module requires
Logout → Login to be loaded; changing files does not replace cached live code.
No shell restart or logout is performed by this extension.

The separate dotfiles export's NothingOS profile includes these assets and
records Hide Top Bar as a conflicting extension to disable with scoped backup.
Keep Media Controls in its native Center position; no MPRIS players, metadata,
artwork, playlists or transport settings are modified by this companion.

## Media updates and resource use

The controller reads only Media Controls' cached selected-player PlaybackStatus.
One D-Bus PropertiesChanged subscription queues updates only for PlaybackStatus;
Metadata and position signals do not queue UI work or trigger image/network
requests. Child additions/removals handle enabling/disabling Media Controls.
Motion/status storms coalesce to one 32 ms update. Side groups have at most one
250 ms hide timer each, and 100 ms checks run only while a popup/modal is open.
There is no permanent player polling or extra player-proxy listener tree.

## Disable / restore

`gnome-extensions disable nothingos-panel-zones@local` restores original styles,
clipping, visibility and the normal full-width panel strut/fullscreen policy.
It releases signals, timers, D-Bus subscription and its paired compositing hold.
The persistent clock is a Shell overlay even in maximized windows, so the hold
stays active while islands can be visible. True fullscreen hides all islands
and releases the hold; leaving fullscreen reacquires it for normal/maximized
windows. This prevents direct scanout from bypassing clock/panel painting.
Hide Top Bar is not automatically re-enabled: restore that previous user choice
explicitly from the private installation backup if desired. The old compatibility
patch remains inert while Hide Top Bar is disabled.

## Verification

Run `python3 -m unittest discover -s tests -p test_panel_zones.py` at repository
root. It runs the actual controller with mocked actors/D-Bus: permanent clock,
playing/paused/missing media, independent hover geometry, menus, fullscreen
compositing, metadata/status storms, cleanup and failed-enable rollback.
A real login must still verify appearance and pointer/menu interaction in Shell.
GNOME panel APIs are private; metadata intentionally targets GNOME 51 only.
