import {isNothingOSWidget, prunePreviews} from '../filter.js';

const DESKTOP = 1;
const rect = {x: 10, y: 50, width: 150, height: 150};
function assert(condition, message) {
    if (!condition)
        throw new Error(message);
}
function window(wmClass, title, type = DESKTOP) {
    return {get_wm_class: () => wmClass, get_title: () => title, get_window_type: () => type};
}
const widget = window('Eww', 'Eww - cpu-temp');
const normal = window('org.gnome.Settings', 'Settings', 0);
assert(isNothingOSWidget(widget, DESKTOP), 'Configured desktop widget should match');
assert(isNothingOSWidget(window('NothingOSConky', 'NothingOS System Monitor'), DESKTOP), 'Theme monitor should match');
assert(!isNothingOSWidget(window('conky', 'Other monitor'), DESKTOP), 'Other Conky instances must remain');
assert(!isNothingOSWidget(window('Eww', 'Eww - custom'), DESKTOP), 'Other Eww configs must remain');
assert(!isNothingOSWidget(window('Eww', 'Eww - cpu-temp', 0), DESKTOP), 'Normal app windows must remain');

function selector(count) {
    const previews = Array.from({length: count}, () => ({
        boundingBox: {...rect},
        destroyed: false,
        destroy() { this.destroyed = true; },
    }));
    const layout = {
        _sortedWindows: previews,
        _windowSlots: ['old-slot'],
        _layout: {},
        get windows() { return this._sortedWindows; },
        layout_changed() { this.changed = true; },
    };
    return {_layoutManager: layout};
}
const candidates = [{window: normal, rect}, {window: widget, rect}];
const target = selector(2);
const [appPreview, widgetPreview] = target._layoutManager.windows;
assert(prunePreviews(target, candidates, DESKTOP) === 1, 'Remove exactly one widget');
assert(target._layoutManager.windows[0] === appPreview && !appPreview.destroyed,
    'Ordinary app with identical geometry must remain');
assert(widgetPreview.destroyed && target._layoutManager.changed, 'Dispose snapshot and refresh layout');
assert(target._layoutManager._windowSlots.length === 0 && target._layoutManager._layout === null,
    'Invalidate cached slots');

const mismatch = selector(1);
assert(prunePreviews(mismatch, candidates, DESKTOP) === -1, 'Count mismatch must fail open');
assert(!mismatch._layoutManager.windows[0].destroyed, 'Mismatch must preserve all choices');
const changedGeometry = selector(2);
changedGeometry._layoutManager.windows[1].boundingBox.x++;
assert(prunePreviews(changedGeometry, candidates, DESKTOP) === -1, 'Changed actor order/geometry must fail open');
assert(changedGeometry._layoutManager.windows.every(p => !p.destroyed), 'No partial filtering on mismatch');
print('Screenshot filtering: scope, identical geometry, cleanup and fail-open checks passed');
