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
and media actions, Shell entries/dialogs, switches, OSD, Alt+Tab, app folders and
the session lockscreen.
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

Alt+Tab preview dimensions are controlled by Shell JavaScript, not this CSS.
The independent `alt-tab-extension/` component enlarges the actual window
previews to 192 logical pixels; see its README for installation.

## Session lockscreen

The clock uses large, light Inter text, a smaller gray date, charcoal password
and notification surfaces, and mint keyboard focus. GNOME retains the existing
background, authentication, notification privacy settings and layout/scaling.
The system GDM login screen is a separate process and is not modified.

User Themes normally runs only in the `user` session mode and unloads its CSS
when the screen locks. After validating CSS as above, apply the lockscreen with:

```sh
python3 shell-theme/apply-lockscreen.py
```

This requires User Themes installed in the user's extension directory and enabled
with NothingOS-Shell selected. It merges only the marked lockscreen CSS block,
preserving local topbar/button overrides, and adds `unlock-dialog` to User Themes'
`session-modes` metadata. CSS is refreshed by toggling the selected theme setting
away and back, without changing extension enable/disable choices. GNOME 51 caches
extension metadata and no longer implements the advertised ReloadExtension
D-Bus method: **log out and back in once to activate lockscreen support**.
The helper does not log out or restart Shell. Both original files are backed up
under `~/.local/state/nothingos/backups/lockscreen-*`. Restore with:

```sh
python3 shell-theme/apply-lockscreen.py --restore /absolute/path/to/backup
```

Log out and back in after restoring the extension's original session modes.
An upstream User Themes update may replace its metadata. Run the helper again
after such an update. `--no-reload` updates files only for an offline profile;
the next login loads the metadata. These changes do not add authentication code
or change which other extensions are allowed to run on the lockscreen.

Verify using Super+L: clock/date size, readability over the existing wallpaper,
password field keyboard focus, and normal password/fingerprint unlocking. The
user must unlock their session themselves. Check at the user's text scale and
monitor size; CSS parsing is not a substitute for that visual check.
