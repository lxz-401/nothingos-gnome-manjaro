# Larger Alt+Tab window previews

GNOME 51 hardcodes window previews to 128 logical pixels in `WindowIcon._init`.
CSS thumbnail width affects the separate app-group thumbnail popup, not Alt+Tab
when `switch-windows` is bound to it.

This independent extension wraps that constructor through GNOME's
`InjectionManager`, then sizes its window clone and container to 192 logical
pixels (1.5 times the default). It respects DPI, aspect ratio, app-icon-only
mode and small source windows. App icon overlays, bindings, labels and native
scrolling are unchanged. There are no timers or metadata subscriptions.
Disabling restores the original constructor for subsequent switcher openings.
It does not require Panel Zones.

Copy this folder to
`~/.local/share/gnome-shell/extensions/nothingos-window-previews@local`, then
enable **NothingOS Larger Window Previews** in Extensions. A newly installed
extension may require logout/login before GNOME discovers it. Change
`PREVIEW_SIZE` in `extension.js` to tune the size, then logout/login after a code
change because GJS modules are cached. Only GNOME 51 has been checked.

Validation: `python3 -m unittest discover -s tests -p test_window_previews.py`.
The harness executes the actual extension against mocked actors and checks
DPI, aspect ratio, icon-only behavior and restoring the constructor. Live
rendering is a separate check: hold Alt, press Tab, and inspect the previews.
