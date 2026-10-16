# Media Controls preview optimization

Media Controls stays enabled. This patch targets the `2.4.5-gnome51` sources
at `dc4ece6` in https://github.com/lxz-401/media-controls (MIT licensed).
The optimized source commit is `16ed1a8`; regression tests live in that source
checkout under `tests/preview-performance.test.js`.

The fixes use stable listener IDs and detach metadata/Seeked callbacks when
switching players. Metadata bursts coalesce over 150 ms. Closed popups do not
build artwork, labels, or timelines. Artwork decoding is bounded to 384 px;
late image results cannot modify closed/destroyed widgets. Timeline duration
is validated and marker allocation is limited to 121, including very long videos.
Parent-owned actors are no longer explicitly destroyed a second time.

## Apply to a matching installed build

Back up the extension directory and its settings first. From this repository:

```sh
extension="$HOME/.local/share/gnome-shell/extensions/mediacontrols@cliffniff.github.com"
patch --dry-run --forward -p2 -d "$extension" < compatibility/media-controls/optimized-preview.patch
patch --forward -p2 -d "$extension" < compatibility/media-controls/optimized-preview.patch
gnome-extensions enable mediacontrols@cliffniff.github.com
```

Stop if the dry run fails: another build needs a reviewed patch. Log out and
back in to load the changed modules. A disable/enable in the same session
still uses cached JavaScript. After a fresh login the Shell journal contains
`Preview optimization active: bounded listeners, lazy popup, bounded timeline`.
Test YouTube hover previews and open the Media Controls popup to verify artwork
and seeking. Code tests/build do not substitute for that live Shell retest.

## Current machine

The extension is active. Until fresh login, only Chrome's MPRIS player is
temporarily excluded from the panel; Spotify/other players and Eww artwork work.
The user confirmed that the restored panel works and YouTube no longer freezes
in this temporary state. The installed `preview-fix-pending.json` records only
the temporary exclusions; the patched extension removes these on fresh load
without clearing unrelated user exclusions.

Source/settings backups are in
`~/.local/state/nothingos/backups/media-controls-optimize-20261016/`.

`disable.sh` is retained solely as an optional emergency rollback for older
builds; disabling the extension is no longer the recommended configuration.
