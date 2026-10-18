import Clutter from 'gi://Clutter';
import St from 'gi://St';
import {Extension, InjectionManager} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as AltTab from 'resource:///org/gnome/shell/ui/altTab.js';

// GNOME 51 uses 128 logical pixels. Enlarge only real window previews, leaving
// the overlaid app icon, labels and native scrolling/keyboard handling intact.
const PREVIEW_SIZE = 192;

export default class LargerWindowPreviews extends Extension {
    enable() {
        this._injections = new InjectionManager();
        this._injections.overrideMethod(AltTab.WindowIcon.prototype, '_init', original =>
            function (...args) {
                original.apply(this, args);
                const clones = this._icon.get_children()
                    .filter(child => child instanceof Clutter.Clone);
                if (!clones.length)
                    return; // Respect the user's app-icon-only mode.
                const size = PREVIEW_SIZE * St.ThemeContext.get_for_stage(global.stage).scale_factor;
                for (const clone of clones) {
                    if (!clone.source)
                        continue;
                    const [width, height] = clone.source.get_size();
                    if (width <= 0 || height <= 0)
                        continue;
                    // Preserve aspect ratio and never upscale tiny source windows.
                    const scale = Math.min(1, size / width, size / height);
                    clone.set_size(width * scale, height * scale);
                }
                this._icon.set_size(size, size);
            });
    }

    disable() {
        this._injections?.clear();
        this._injections = null;
    }
}
