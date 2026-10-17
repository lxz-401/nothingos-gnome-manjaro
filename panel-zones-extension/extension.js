import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {hoveredZone} from './zoneLogic.js';

const PILL = 'background-color: rgba(0,0,0,0.92); border-radius: 10px;';
const HIDE_DELAY = 250;

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
        this._enabled = true;
        this._signals = [];
        this._center = new Map();
        this._timer = 0;
        this._compositing = false;
        this._lastZone = -1;
        this._groups = [Main.panel._leftBox, Main.panel._centerBox, Main.panel._rightBox]
            .map(actor => ({...this._snapshot(actor), hideTimer: 0}));
        this._panelStyle = Main.panel.get_style();
        this._boxStyle = Main.layoutManager.panelBox.get_style();
        Main.panel.set_style(`${this._panelStyle ?? ''}; background: transparent; background-color: transparent; background-image: none; border: none; box-shadow: none;`);
        Main.layoutManager.panelBox.set_style(`${this._boxStyle ?? ''}; background: transparent; background-color: transparent; background-image: none; border: none; box-shadow: none;`);
        this._groups.forEach((group, index) => group.actor.set_style(
            `${group.style ?? ''}; ${index === 1 ? 'background-color: transparent;' : PILL}`));
        // Keep the native panel mapped: the clock must survive maximize/F11.
        // No full-width strut is reserved for the transparent gaps.
        const box = Main.layoutManager.panelBox;
        Main.layoutManager.removeChrome(box);
        Main.layoutManager.addChrome(box, {affectsStruts: false, trackFullscreen: false});
        this._ownsChrome = true;
        this._placePanel();

        this._connect(global.backend.get_cursor_tracker(), 'position-invalidated', () => this._queue());
        this._connect(global.stage, 'notify::key-focus', () => this._queue());
        this._connect(global.display, 'in-fullscreen-changed', () => this._queue());
        this._connect(Main.overview, 'showing', () => this._queue());
        this._connect(Main.overview, 'hidden', () => this._queue());
        this._connect(Main.layoutManager, 'monitors-changed', () => {
            this._placePanel();
            this._queue();
        });
        for (const {actor} of this._groups) {
            this._connect(actor, 'notify::allocation', () => this._queue());
            this._connect(actor, 'child-added', () => this._queue());
            this._connect(actor, 'child-removed', () => this._queue());
        }
        // Observe only status changes. Metadata/artwork/position storms do not
        // queue rendering, fetch media, or create player proxies/listeners.
        this._mediaSignal = Gio.DBus.session.signal_subscribe(null,
            'org.freedesktop.DBus.Properties', 'PropertiesChanged',
            '/org/mpris/MediaPlayer2', 'org.mpris.MediaPlayer2.Player',
            Gio.DBusSignalFlags.NONE, (_bus, _sender, _path, _iface, _name, parameters) => {
                const [, changed, invalidated] = parameters.deep_unpack();
                if ('PlaybackStatus' in changed || invalidated.includes('PlaybackStatus'))
                    this._queue();
            });
        this._sync();
    }

    _snapshot(actor) {
        return {actor, style: actor.get_style(), opacity: actor.opacity,
            translation: actor.translation_y, clip: actor.has_clip ? actor.get_clip() : null,
            visible: actor.visible, shown: null};
    }

    _restore(state) {
        const {actor} = state;
        if (state.clip)
            actor.set_clip(...state.clip);
        else
            actor.remove_clip();
        actor.set_style(state.style);
        actor.opacity = state.opacity;
        actor.translation_y = state.translation;
        actor.visible = state.visible;
    }

    _connect(object, signal, callback) {
        this._signals.push([object, object.connect(signal, callback)]);
    }

    _queue(delay = 32) {
        if (!this._enabled || this._timer)
            return;
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
            this._timer = 0;
            this._sync();
            return GLib.SOURCE_REMOVE;
        });
    }

    _placePanel() {
        const monitor = Main.layoutManager.primaryMonitor;
        if (monitor) {
            Main.layoutManager.panelBox.y = monitor.y;
            Main.layoutManager.panelBox.show();
        }
    }

    _owner(actor) {
        return actor ? this._groups.findIndex(group =>
            group.actor === actor || group.actor.contains(actor)) : -1;
    }

    _directChild(box, actor) {
        while (actor && actor.get_parent() !== box)
            actor = actor.get_parent();
        return actor;
    }

    _syncCenter(reveal) {
        const box = this._groups[1].actor;
        const children = box.get_children();
        for (const [actor, state] of this._center) {
            if (!children.includes(actor)) {
                actor.disconnect(state.destroyId);
                this._restore(state);
                this._center.delete(actor);
            }
        }
        const clock = Main.panel.statusArea.dateMenu;
        const media = Main.panel.statusArea['Media Controls'];
        const clockChild = this._directChild(box, clock?.container ?? clock);
        const mediaChild = this._directChild(box, media?.container ?? media);
        const menuChild = this._directChild(box, Main.panel.menuManager.activeMenu?.sourceActor);
        const focusChild = this._directChild(box, global.stage.get_key_focus());
        let playing = false;
        try {
            playing = media?.playerProxy?.playbackStatus === 'Playing';
        } catch {
            // A player can disappear while its native panel button is being removed.
        }
        for (const actor of children) {
            if (!this._center.has(actor)) {
                const state = this._snapshot(actor);
                state.destroyId = actor.connect('destroy', () => {
                    this._center.delete(actor);
                    this._queue();
                });
                this._center.set(actor, state);
                actor.set_style(`${state.style ?? ''}; ${PILL}`);
            }
            const state = this._center.get(actor);
            // Hidden children collapse, so an idle media player leaves no
            // empty media-sized pill and the clock returns to the center.
            const visible = actor === clockChild || reveal || actor === menuChild ||
                actor === focusChild || (actor === mediaChild && playing);
            actor.visible = state.visible && visible;
        }
    }

    _setGroup(group, shown) {
        if (shown && group.hideTimer) {
            GLib.source_remove(group.hideTimer);
            group.hideTimer = 0;
        }
        if (!shown && group.shown && !group.hideTimer) {
            group.hideTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, HIDE_DELAY, () => {
                group.hideTimer = 0;
                this._paintGroup(group, false);
                return GLib.SOURCE_REMOVE;
            });
        } else if (shown || group.shown === null) {
            this._paintGroup(group, shown);
        }
    }

    _paintGroup(group, shown) {
        if (group.shown === shown && group.actor.opacity === (shown ? group.opacity : 0))
            return;
        if (shown) {
            if (group.clip)
                group.actor.set_clip(...group.clip);
            else
                group.actor.remove_clip();
        } else {
            group.actor.set_clip(0, 0, 0, 0);
        }
        group.actor.opacity = shown ? group.opacity : 0;
        group.shown = shown;
    }

    _sync() {
        if (!this._enabled || !Main.layoutManager.primaryMonitor)
            return;
        const monitor = Main.layoutManager.primaryMonitor;
        const [x, y] = global.get_pointer();
        const bounds = this._groups.map(({actor}) => {
            const [left] = actor.get_transformed_position();
            return {left, right: left + actor.width};
        });
        const hovered = hoveredZone(bounds, x, y, monitor.y, Main.panel.height);
        const menu = Main.panel.menuManager.activeMenu;
        const owner = this._owner(menu?.sourceActor);
        const focus = this._owner(global.stage.get_key_focus());
        if (hovered >= 0)
            this._lastZone = hovered;
        for (const [index, group] of this._groups.entries()) {
            const held = hovered === index || owner === index || focus === index ||
                (Main.modalCount > 0 && this._lastZone === index);
            this._setGroup(group, index === 1 || held || Main.overview.visible);
        }
        this._syncCenter(hovered === 1 ||
            (Main.modalCount > 0 && this._lastZone === 1) || Main.overview.visible);
        // The persistent clock is an overlay even on ordinary/maximized
        // windows. Letting those windows use direct scanout can bypass Shell's
        // painting just as fullscreen does. Hold compositing until disable().
        const composite = true;
        if (composite !== this._compositing) {
            if (composite)
                global.compositor.disable_unredirect();
            else
                global.compositor.enable_unredirect();
            this._compositing = composite;
        }
        if (menu || Main.modalCount > 0)
            this._queue(100);
    }

    disable() {
        this._enabled = false;
        if (this._timer)
            GLib.source_remove(this._timer);
        this._timer = 0;
        if (this._mediaSignal)
            Gio.DBus.session.signal_unsubscribe(this._mediaSignal);
        this._mediaSignal = 0;
        for (const [object, id] of this._signals ?? [])
            object.disconnect(id);
        this._signals = [];
        for (const state of this._center?.values() ?? []) {
            state.actor.disconnect(state.destroyId);
            this._restore(state);
        }
        this._center?.clear();
        for (const group of this._groups ?? []) {
            if (group.hideTimer)
                GLib.source_remove(group.hideTimer);
            this._restore(group);
        }
        if (this._compositing)
            global.compositor.enable_unredirect();
        this._compositing = false;
        if (this._groups) {
            Main.panel.set_style(this._panelStyle);
            Main.layoutManager.panelBox.set_style(this._boxStyle);
        }
        if (this._ownsChrome) {
            Main.layoutManager.removeChrome(Main.layoutManager.panelBox);
            Main.layoutManager.addChrome(Main.layoutManager.panelBox, {affectsStruts: true, trackFullscreen: true});
        }
        this._ownsChrome = false;
        this._groups = null;
    }
}
