# YouTube hover previews freezing the desktop

On this GNOME 51 installation, the `mediacontrols@cliffniff.github.com`
extension (`2.4.5-gnome51`, https://github.com/lxz-401/media-controls)
caused the whole desktop to freeze when hovering over YouTube previews in Chrome.

The Shell journal contained hundreds of `[Media Controls] Error: Argument
msecs: value is out of range for uint32` messages. Disabling only its track
slider did **not** resolve the freeze. Disabling the entire extension did;
the user retested the same YouTube hover interaction and confirmed recovery.
This identifies the extension interaction; it does not establish one specific
source-code defect as the sole cause. No browser/GPU flags were changed.

If the same symptom occurs with this extension enabled, run:

```sh
./compatibility/media-controls/disable.sh
```

The script backs up this extension's settings and disables only this extension.
It is safe to repeat and does nothing when it is absent/already disabled.
There is no logout requirement. The Eww album-art card, Conky blocks, dock and
theme remain enabled; panel controls supplied by Media Controls disappear.
The pause/play hardware keys and controls inside the player remain available.

To opt back in after installing a verified compatible extension update:

```sh
gnome-extensions enable mediacontrols@cliffniff.github.com
```

Do not apply this workaround universally: it addresses the reproduced
extension conflict on this machine, rather than all Linux video freezes.
