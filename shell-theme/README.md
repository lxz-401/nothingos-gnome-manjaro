# NothingOS Shell theme

GNOME Shell 51 selectors are used for menus and notification stacks. Legacy
app-well selectors remain for older Shell releases; those versions have not
been verified. This styles the user session, not the system GDM login screen.

The palette is `#111111` for outer surfaces, `#1b1b1b` for cards, `#303030`
for borders, `#f5f5f5` for text and `#45ffbc` for active/focus states. Destructive
buttons stay red, disabled labels stay muted, and volume overdrive stays red.
Native spacing, scaling, RTL layout and control geometry are retained except
for existing Quick Settings sizing and small calendar padding.

Coverage: panel popovers and device submenus, calendar/date cards, notifications
and media actions, Shell entries/dialogs, switches, OSD, Alt+Tab and app folders.
No extension enable/disable setting or GTK3 selection is required to apply it.

## Validate and apply

On Arch/CachyOS with GNOME 51, parse before installing:

```sh
GI_TYPELIB_PATH=/usr/lib/gnome-shell:/usr/lib/mutter-51 \
LD_LIBRARY_PATH=/usr/lib/gnome-shell:/usr/lib/mutter-51 \
gjs -c 'const St=imports.gi.St; const Gio=imports.gi.Gio; const theme=new St.Theme(); theme.load_stylesheet(Gio.File.new_for_path(ARGV[0])); print("CSS OK");' "$PWD/shell-theme/gnome-shell.css"
```

Back up the installed stylesheet and any local size overrides, then copy this
file to `~/.local/share/themes/NothingOS-Shell/gnome-shell/gnome-shell.css`.
Restore local panel-height/corner changes selectively rather than replacing
unrelated customizations. In GNOME Tweaks, switch the Shell theme away and back
to NothingOS-Shell to reload CSS. Shell JavaScript does not need a restart.

For visual verification, open Quick Settings and a device submenu, the clock
menu, Alt+Tab, the app grid/folder and the volume or brightness OSD. Check hover,
keyboard focus, disabled controls and notification actions. Authentication and
session dialogs use the shared control palette; cancel them after inspection.
A successful CSS parse alone does not establish visual correctness.
