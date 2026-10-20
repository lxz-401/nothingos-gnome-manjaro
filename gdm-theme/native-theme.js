// Only preparation/validation helpers; this never changes a resource or setting.
const Gio = imports.gi.Gio;
const mode = ARGV.shift();
if (mode === 'extract') {
    const resource = Gio.Resource.load(ARGV[0]);
    const styles = {};
    for (const name of ['gnome-shell-light.css', 'gnome-shell-dark.css']) {
        const bytes = resource.lookup_data(`/org/gnome/shell/theme/${name}`, 0);
        styles[name] = new TextDecoder().decode(bytes.toArray());
    }
    print(JSON.stringify(styles));
} else if (mode === 'validate') {
    const St = imports.gi.St;
    const theme = new St.Theme();
    for (const path of ARGV)
        theme.load_stylesheet(Gio.File.new_for_path(path));
    print('CSS OK');
} else if (mode === 'image') {
    const GdkPixbuf = imports.gi.GdkPixbuf;
    const [format, width, height] = GdkPixbuf.Pixbuf.get_file_info(ARGV[0]);
    if (!format || !['jpeg', 'png', 'webp'].includes(format.get_name()))
        throw new Error('Only decodable JPEG, PNG or WebP images are supported');
    if (width < 1 || height < 1 || width > 32768 || height > 32768)
        throw new Error('Unsupported wallpaper dimensions');
    GdkPixbuf.Pixbuf.new_from_file(ARGV[0]);
    print(JSON.stringify({format: format.get_name(), width, height}));
} else {
    throw new Error('Expected extract, validate or image');
}
