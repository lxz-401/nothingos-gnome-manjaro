# NothingOS desktop screenshot integration

GNOME Shell 51's screenshot window selector includes desktop/dock windows even
when they have skip-taskbar hints. This local extension removes only the five
named NothingOS Eww widget previews and the NothingOS system-monitor preview.
It leaves the actual widgets visible in desktop/area screenshots.

Install this directory as
`~/.local/share/gnome-shell/extensions/nothingos-desktop-widgets@local` and enable
that UUID. A newly installed local extension needs a new GNOME Wayland login to
be discovered. The current installer preserves other enabled extensions.

## Compatibility and safety

- GNOME 51 only: this uses the private screenshot selector's capture method.
- No system files or global window-enumeration functions are changed.
- Only desktop windows with exact NothingOS classes/titles are matched.
- Capture creates previews synchronously in actor order. The filter checks the
  entire preview count and all frame rectangles before changing the layout.
  A mismatch leaves all windows selectable.
- Full-screen/area image capture and normal application previews are untouched.
- Monitor rebuilds use the same patched selector prototype. Disabling restores
  its original capture method; close/reopen an already-open picker afterward.

Run the safety checks with:

```sh
gjs -m gnome-extension/tests/filter.test.js
```

After the next login, verify:

```sh
gnome-extensions info nothingos-desktop-widgets@local
journalctl --user -b -o cat | rg 'NothingOS Widgets'
```

Open the screenshot UI in Window mode. Normal applications should remain as
choices; the widget previews should be absent. A successful filter logs the
number omitted. To revert this part only:

```sh
gnome-extensions disable nothingos-desktop-widgets@local
```

Source of the GNOME 51 capture contract:
https://gitlab.gnome.org/GNOME/gnome-shell/-/blob/51.1/js/ui/screenshot.js
