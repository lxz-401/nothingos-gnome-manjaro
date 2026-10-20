# NothingOS GDM login screen

GNOME 51's GDM login screen uses the current desktop wallpaper, white JetBrains
Mono text, charcoal user/password surfaces and mint focus/login actions. Native
placement, scaling, accessibility, error feedback and authentication are retained.
The user-session lockscreen is a separate component under `shell-theme/`.

## Apply

Requirements: GNOME Shell 51, GDM using `org.gnome.Shell@gdm.service`, Python 3,
GJS with Gio/St/GdkPixbuf, fontconfig, PolicyKit and system-wide JetBrains Mono.
The current implementation validates the Arch/CachyOS GNOME 51 library layout.

From the repository as your desktop user, run:

```sh
python3 gdm-theme/nothingos-gdm.py apply
```

Preparation reads the active light/dark wallpaper URI, decodes a local JPEG,
PNG or WebP, checks the font, extracts installed native CSS and validates both
combined stylesheets with St. Files are kept privately under
`~/.local/state/nothingos/gdm-prepared/`. The system administrator authentication
dialog then authorizes the installation; do not run preparation with sudo.
An explicit wallpaper can be selected without changing the desktop setting:

```sh
python3 gdm-theme/nothingos-gdm.py apply --wallpaper '/absolute/path/my wallpaper.jpg'
```

The chosen image is a snapshot, copied to a public, root-owned location. It is
visible to everyone who can see the login screen and no longer depends on an
unlocked home directory. Changing desktop wallpaper later requires reapplying.
Personal image bytes, prepared bundles and root backups are not stored in Git.

GDM is **not restarted**, and no session is logged out by the installer. Check
the result when you next log out or reboot. A greeter that is already running
may continue using its old theme until it starts again. Normal password or
fingerprint login must be verified by the user on that real login screen.

## Scope and backups

Only these owned paths are changed:

- `/usr/local/share/nothingos-gdm/`: native-plus-custom light/dark CSS, image and manifest.
- `/etc/systemd/user/org.gnome.Shell@gdm.service.d/60-nothingos-theme.conf`: GIO resource overlay for the GDM Shell instance.

The packaged gresource is unchanged. There is no override for the ordinary user
Shell or GDM daemon, no extra extension, and no change to PAM, accounts,
passwords, automatic login, keyrings or authentication policy. Native
high-contrast CSS is not overlaid. Another tool's conflicting target or a
symlink is rejected instead of overwritten.

Every apply records the old owned files, their existence, modes and hashes in
`/var/lib/nothingos-gdm/backups/`; the installer prints the exact directory.
To restore one of those backups, run as your desktop user:

```sh
python3 gdm-theme/nothingos-gdm.py restore --backup /var/lib/nothingos-gdm/backups/EXACT_BACKUP
```

The administrator dialog appears again. Restore removes newly introduced files
or reinstates their previous contents; unrelated drop-ins are preserved. GDM is
not restarted. From a root recovery terminal the same restore command can be
used directly; it does not require an active graphical session.

On an install failure, owned files are rolled back. If rollback itself fails,
the error reports the backup and retained previous deployment tree; keep both
for recovery. Do not delete unrelated system configuration to recover a theme.

## GNOME updates and verification

Reapply after upgrading GNOME Shell: generated CSS contains the installed
release's native base. Prepared bundles are rejected if the Shell version or
source resource hash has changed. There is no automatic update hook.

```sh
python3 -m unittest discover -s tests -p test_gdm_theme.py -v
python3 gdm-theme/nothingos-gdm.py prepare --output /absolute/path/to/empty-private-directory
```

Tests cover wallpaper selection, private font rejection, payload/source changes,
scope, symlink/conflict rejection, readable greeter paths under root's private
umask, backup/restore, failed-install rollback and retaining recovery files when
rollback fails. GIO overlay lookup and a systemd fixture are also checked on the
development machine. A headless GNOME GDM-mode session loaded the overlay with
no St CSS warnings, but its greeter proxy denied an already logged-in user;
that preview does not prove real GDM rendering or authentication.

References: [GIO resource overlays](https://docs.gtk.org/gio/struct.Resource.html).
St centers background images by default; this uses `background-size: cover`
without unsupported position keywords (see the
[GNOME 51 renderer](https://github.com/GNOME/gnome-shell/blob/51.0/src/st/st-theme-node-drawing.c#L452-L472)).
