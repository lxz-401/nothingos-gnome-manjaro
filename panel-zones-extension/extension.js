import GLib from 'gi://GLib';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {hoveredZone, visibleZones} from './zoneLogic.js';

const HIDE_DELAY_MS = 250;
const POINTER_INTERVAL_MS = 32;

export default class PanelZones extends Extension {
    enable() {
        try {
            this._enable();
        } catch (error) {
            this.disable();
            throw error;
        }
    }

    _enable() {
        this._signals = [];
        this._timer = 0;
        this._hideTimer = 0;
        this._pendingHide = null;
        this._lastHovered = -1;
        this._enabled = true;
        this._panelStyle = Main.panel.get_style();
        this._groups = [Main.panel._leftBox, Main.panel._centerBox, Main.panel._rightBox]
            .map(actor => ({actor, style: actor.get_style(),
                opacity: actor.opacity, translation: actor.translation_y,
                clip: actor.has_clip ? actor.get_clip() : null,
                shown: null}));
        Main.panel.set_style(`${this._panelStyle ?? ''}; background-color: transparent; border: none; box-shadow: none;`);
        for (const group of this._groups)
            group.actor.set_style(`${group.style ?? ''}; background-color: rgba(0,0,0,0.92); border-radius: 10px;`);

        const tracker = global.backend.get_cursor_tracker();
        this._connect(tracker, 'position-invalidated', () => this._queue());
        this._connect(global.stage, 'notify::key-focus', () => this._queue());
        this._connect(Main.overview, 'showing', () => this._sync(true));
        this._connect(Main.overview, 'hidden', () => this._sync());
        this._connect(Main.layoutManager, 'monitors-changed', () => this._queue());
        this._connect(Main.layoutManager.panelBox, 'notify::y', () => this._queue());
        for (const {actor} of this._groups)
            this._connect(actor, 'notify::allocation', () => this._queue());
        this._sync();
    }

    _connect(object, signal, callback) {
        this._signals.push([object, object.connect(signal, callback)]);
    }

    _queue(delay = POINTER_INTERVAL_MS) {
        if (!this._enabled || this._timer)
            return;
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
            this._timer = 0;
            this._sync();
            return GLib.SOURCE_REMOVE;
        });
    }

    _owner(actor) {
        if (!actor)
            return -1;
        return this._groups.findIndex(group => group.actor === actor || group.actor.contains(actor));
    }

    _sync(overview = Main.overview.visible) {
        if (!this._enabled)
            return;
        const monitor = Main.layoutManager.primaryMonitor;
        if (!monitor)
            return;
        const [x, y] = global.get_pointer();
        const height = Math.max(1, Main.panel.height);
        const bounds = this._groups.map(({actor}) => {
            const [left] = actor.get_transformed_position();
            return {left, right: left + actor.width};
        });
        const hovered = hoveredZone(bounds, x, y, monitor.y, height);
        const menu = Main.panel.menuManager.activeMenu;
        const menuOwner = this._owner(menu?.sourceActor);
        const focused = this._owner(global.stage.get_key_focus());
        let visible = visibleZones(this._groups.length, hovered, menuOwner, overview, focused);
        // A tray popup may use its own manager. Keep the last group while
        // such a popup owns the modal grab, without leaving all groups visible.
        if (Main.modalCount > 0 && menuOwner < 0 && !overview && this._lastHovered >= 0)
            visible[this._lastHovered] = true;

        if (hovered >= 0)
            this._lastHovered = hovered;
        const somethingVisible = visible.some(Boolean);
        if (!somethingVisible && this._groups.some(group => group.shown)) {
            if (!this._hideTimer) {
                this._pendingHide = visible;
                this._hideTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, HIDE_DELAY_MS, () => {
                    this._hideTimer = 0;
                    this._apply(this._pendingHide);
                    this._pendingHide = null;
                    return GLib.SOURCE_REMOVE;
                });
            }
        } else {
            if (this._hideTimer) {
                GLib.source_remove(this._hideTimer);
                this._hideTimer = 0;
                this._pendingHide = null;
            }
            this._apply(visible);
        }
        // Only poll while a menu/modal grab is open. Cursor changes are
        // signal-driven and coalesced; there is no permanent polling loop.
        if (menu || Main.modalCount > 0)
            this._queue(100);
    }

    _apply(visible) {
        if (!this._enabled || !visible)
            return;
        this._groups.forEach((group, index) => {
            const shown = visible[index];
            // Keep native allocation widths stable, but move hidden groups
            // above the panel; zero clipping also prevents invisible input
            // on a second monitor positioned above the primary monitor.
            const translation = shown ? group.translation : -Math.max(Main.panel.height, 1) - 8;
            if (group.shown === shown && group.actor.translation_y === translation)
                return;
            group.actor.remove_all_transitions();
            if (!shown)
                group.actor.set_clip(0, 0, 0, 0);
            else if (group.clip)
                group.actor.set_clip(...group.clip);
            else
                group.actor.remove_clip();
            group.actor.opacity = shown ? group.opacity : 0;
            group.actor.translation_y = translation;
            group.shown = shown;
        });
    }

    disable() {
        this._enabled = false;
        for (const name of ['_timer', '_hideTimer']) {
            if (this[name])
                GLib.source_remove(this[name]);
            this[name] = 0;
        }
        for (const [object, id] of this._signals ?? [])
            object.disconnect(id);
        this._signals = [];
        for (const group of this._groups ?? []) {
            group.actor.remove_all_transitions();
            if (group.clip)
                group.actor.set_clip(...group.clip);
            else
                group.actor.remove_clip();
            group.actor.set_style(group.style);
            group.actor.opacity = group.opacity;
            group.actor.translation_y = group.translation;
        }
        if (this._groups)
            Main.panel.set_style(this._panelStyle);
        this._groups = null;
        this._pendingHide = null;
    }
}
