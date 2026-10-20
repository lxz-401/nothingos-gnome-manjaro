# NothingOS GDM login theme

## Approved intent

Match the PC's login screen to its current NothingOS desktop. The user selected
the current desktop wallpaper, JetBrains Mono, and white text, and approved
charcoal user/password surfaces with mint focus and login actions. Commit and
push the completed implementation to the user's GitHub fork.

This covers GDM before login. The already implemented user-session lockscreen
remains a separate component. Do not change its Inter clock or other desktop
preferences as part of this task.

## Verified host context

- CachyOS, GNOME Shell 51.1, GDM under systemd.
- `gnome-session@gnome-login.target` requires `org.gnome.Shell@gdm.service`.
- Shell's `org.gnome.Shell@.service` launches `gnome-shell --mode=%i`.
- Native CSS lives in `/usr/share/gnome-shell/gnome-shell-theme.gresource`.
- JetBrains Mono is installed system-wide in `/usr/share/fonts/TTF/`.
- Current light/dark wallpaper settings refer to the same local JPEG.
- `pkexec` and `glib-compile-resources` exist; passwordless sudo is unavailable.

## Design

Keep native GDM placement, scaling, user selection, accessibility controls,
keyboard/session choices, error feedback and authentication behavior. Use
JetBrains Mono and white text for the login UI. Use charcoal cards and password
entry, muted secondary labels, and mint focus/default-login states. Preserve
red error/critical states and readable disabled controls.

Display the current desktop wallpaper, centered and covering the screen. Copy
the selected image to a root-owned deployment directory so the greeter does not
need access to a private/encrypted home. The wallpaper is an installation-time
snapshot: changing the desktop wallpaper later requires reapplying this setup.
Accept an explicit local wallpaper override; otherwise detect the active dark
or light desktop wallpaper as the desktop user before privilege escalation.
Abort on missing/unsupported images or a missing system-wide JetBrains Mono
font rather than silently substituting a different design.

## Integration and scope

Use GIO's `G_RESOURCE_OVERLAYS` for the GDM Shell instance only. Add an owned
drop-in under `/etc/systemd/user/org.gnome.Shell@gdm.service.d/` pointing the
`/org/gnome/shell/theme` resource prefix at `/usr/local/share/nothingos-gdm/`.
This service instance is verified locally; do not apply an environment override
to the GDM daemon or all user Shell instances.

At apply time, extract the installed native light/dark stylesheets using Gio,
append scoped login rules, and deploy those CSS files plus the wallpaper.
Unmodified resource assets continue to resolve from the installed resource.
Do not override the native high-contrast stylesheet. Check source resource
names, GNOME major version and service template before installation; initially
support the verified GNOME 51 layout only.

Do not modify the packaged gresource, GNOME JavaScript, PAM, auto-login,
passwords, accounts, keyrings, notification privacy or authentication settings.
Do not install or enable another desktop extension for GDM.

## Installer and rollback

Provide a user-facing preparation/apply entry point, generated preview files,
and a root installation/restore path. Preflight font, image, CSS parsing,
service instance and output paths before changing system files. Use the normal
system administrator authentication dialog for the root step; never request
the user's password in chat.

Back up the prior owned drop-in and deployment files, including whether each
existed, into a private root-owned state directory. Validate and stage before
atomically replacing files, and roll back owned files on an installation error.
Restore must remove only files introduced by this setup or restore their exact
previous contents, preserving unrelated drop-ins. Reject unexpected symlinks
or conflicting deployment targets.

Do not restart GDM, log out the desktop, or reboot automatically. Activating a
new greeter may require the user's next logout/reboot; the installer must state
that requirement rather than claiming the running greeter has changed.

The generated CSS is based on the installed GNOME release. Record the source
resource hash/version and instruct the user to reapply after a GNOME Shell
upgrade. No automatic package-manager hook is included in this first version.

## Verification and acceptance

1. Parse prepared native-plus-custom light/dark CSS using the installed St
   parser before the privileged install.
2. Test dark/light wallpaper selection, missing image/font rejection, scoped
   service configuration, preservation of unrelated files, failed-install
   rollback and backup/restore using temporary fixtures.
3. Check the generated drop-in with available systemd verification, inspect the
   actual installed files and permissions after apply, and verify source
   packaged resources and ordinary-user Shell configuration are unchanged.
4. Where an isolated GDM-mode Shell preview is available, use it to inspect the
   background, typography, entry focus, user-card states and contrast. Label an
   isolated preview as a preview, not proof of actual GDM authentication.
5. Actual greeter rendering and normal password/fingerprint login require a
   user-controlled logout/reboot. Never simulate credentials or bypass a lock.
   Report and record this verification as pending if it cannot be completed in
   the active desktop session.
6. Review the diff, run relevant checks, create a focused Conventional Commit,
   push to `fork/main` without force, and verify the remote commit ID. Keep
   personal wallpaper bytes, root backups and runtime data out of Git.

## Source and limits

GIO resource overlays are documented at
<https://docs.gtk.org/gio/struct.Resource.html>. The greeter service selection
above is established from this host's installed systemd and GNOME session
files. Overlay delivery and actual GDM rendering must be verified; the design
does not assume that parsing CSS alone proves the greeter is themed.
