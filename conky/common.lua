-- Shared desktop-window settings for the five independent blocks.
return {
    -- Window settings
    alignment = 'bottom_left',
    gap_x = 20,
    gap_y = 30,
    minimum_height = 180,
    minimum_width = 300,
    maximum_width = 300,

    -- Transparency and no window border
    own_window = true,
    own_window_type = 'desktop',
    own_window_class = 'NothingOSConky',
    own_window_title = 'NothingOS System Monitor',
    output_backend = 'x11',
    own_window_color = '#00000000',
    own_window_hints = 'undecorated,sticky,skip_taskbar,skip_pager',

    -- No background
    background = false,

    -- Text settings
    use_xft = true,
    font = 'JetBrains Mono:size=9',
    override_utf8_locale = true,
    text_buffer_size = 2048,

    -- Colors
    default_color = 'white',
    color1 = 'white',
    color2 = 'AAAAAA',

    -- No borders or outlines
    border_width = 0,
    stippled_borders = 0,

    -- Update settings
    update_interval = 1.0,
    cpu_avg_samples = 2,
    net_avg_samples = 2,
    double_buffer = true,
    no_buffers = true,

    -- Misc settings
    draw_borders = false,
    draw_graph_borders = false,
    draw_outline = false,
    draw_shades = false,
    uppercase = false,

}
