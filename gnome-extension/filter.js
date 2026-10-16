const EWW_TITLES = new Set([
    'Eww - cpu-temp',
    'Eww - spotify-now-playing',
    'Eww - quote-of-the-day',
    'Eww - weather-widget',
    'Eww - day-of-month',
]);

export function isNothingOSWidget(window, desktopType) {
    if (window.get_window_type() !== desktopType)
        return false;

    const wmClass = window.get_wm_class();
    const title = window.get_title();
    return (wmClass === 'NothingOSConky' && title === 'NothingOS System Monitor') ||
        (wmClass === 'Eww' && EWW_TITLES.has(title));
}

function sameRect(a, b) {
    return a && b && ['x', 'y', 'width', 'height'].every(key => a[key] === b[key]);
}

// GNOME 51 capture() creates one preview per eligible actor, synchronously.
// Check the complete correspondence before removing anything; fail open if
// another extension or a Shell update changes that contract.
export function prunePreviews(selector, candidates, desktopType) {
    const layout = selector._layoutManager;
    const previews = layout?.windows;
    if (!Array.isArray(previews) || previews.length !== candidates.length ||
        previews !== layout._sortedWindows ||
        !previews.every((preview, i) => sameRect(preview.boundingBox, candidates[i].rect)))
        return -1;

    const excluded = new Set(previews.filter((_, i) =>
        isNothingOSWidget(candidates[i].window, desktopType)));
    if (excluded.size === 0)
        return 0;

    layout._sortedWindows = previews.filter(preview => !excluded.has(preview));
    layout._windowSlots = [];
    layout._layout = null;
    for (const preview of excluded)
        preview.destroy();
    layout.layout_changed();
    return excluded.size;
}
