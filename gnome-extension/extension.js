import Meta from 'gi://Meta';
import {Extension, InjectionManager} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {prunePreviews} from './filter.js';

export default class NothingOSWidgets extends Extension {
    enable() {
        this._injections = new InjectionManager();
        this._installed = false;
        this._warned = false;
        this._monitorsChanged = Main.layoutManager.connect('monitors-changed', () => this._install());
        this._install();
    }

    _install() {
        if (this._installed)
            return;
        const selector = Main.screenshotUI?._windowSelectors?.[0];
        if (!selector)
            return;
        const prototype = Object.getPrototypeOf(selector);
        if (typeof prototype.capture !== 'function' || !selector._layoutManager)
            throw new Error('Unsupported GNOME screenshot selector structure');

        const extension = this;
        this._injections.overrideMethod(prototype, 'capture', original => function (...args) {
            // Leave an already populated picker alone until its next opening.
            if (this.windows().length !== 0)
                return original.apply(this, args);

            const workspace = global.workspace_manager.get_active_workspace();
            const candidates = global.get_window_actors()
                .map(actor => actor.metaWindow)
                .filter(window => !window.is_override_redirect() &&
                    window.located_on_workspace(workspace) &&
                    window.get_monitor() === this._monitorIndex)
                .map(window => ({window, rect: window.get_frame_rect()}));

            const result = original.apply(this, args);
            const removed = prunePreviews(this, candidates, Meta.WindowType.DESKTOP);
            if (removed < 0 && !extension._warned) {
                extension._warned = true;
                console.warn('NothingOS Widgets: screenshot layout changed; leaving all choices visible');
            } else if (removed > 0) {
                console.log(`NothingOS Widgets: omitted ${removed} desktop widgets from screenshot window choices`);
            }
            return result;
        });
        this._installed = true;
    }

    disable() {
        if (this._monitorsChanged)
            Main.layoutManager.disconnect(this._monitorsChanged);
        this._monitorsChanged = 0;
        this._injections?.clear();
        this._injections = null;
        this._installed = false;
    }
}
