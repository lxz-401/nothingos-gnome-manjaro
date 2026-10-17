// Keep geometry decisions independent of Shell so they can be tested offline.
export function hoveredZone(bounds, x, y, top, height) {
    if (y < top || y >= top + height)
        return -1;
    return bounds.findIndex(({left, right}) => right > left && x >= left && x < right);
}

export function visibleZones(count, hovered, menuOwner, overview, focused = -1) {
    return Array.from({length: count}, (_, index) =>
        overview || index === hovered || index === menuOwner || index === focused);
}
