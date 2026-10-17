// Both panel visibility controllers share this policy. A tiled/half-maximized
// window is not maximized; minimized and other-workspace/monitor windows do not count.
export function shouldAutohide(windows, monitorIndex, workspace) {
    return windows.some(window => window &&
        window.get_monitor() === monitorIndex &&
        !window.minimized && window.located_on_workspace(workspace) &&
        window.showing_on_its_workspace() &&
        (window.is_fullscreen() ||
            (window.maximized_horizontally && window.maximized_vertically)));
}
