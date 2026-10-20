#!/usr/bin/env python3
"""Apply scoped lockscreen CSS and keep User Themes active while locked."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess

UUID = 'user-theme@gnome-shell-extensions.gcampax.github.com'
BEGIN = '/* BEGIN NothingOS lock screen */'
END = '/* END NothingOS lock screen */'


def merge_lock_styles(current, source):
    block = source[source.index(BEGIN):source.index(END) + len(END)]
    if BEGIN in current:
        start = current.index(BEGIN)
        finish = current.index(END, start) + len(END)
        return current[:start] + block + current[finish:]
    return current.rstrip() + '\n\n' + block + '\n'


def reload_theme():
    data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    schemas = data / 'gnome-shell/extensions' / UUID / 'schemas'
    command = ['gsettings', '--schemadir', str(schemas)]
    schema = 'org.gnome.shell.extensions.user-theme'
    current = subprocess.check_output(command + ['get', schema, 'name'], text=True).strip()
    # Toggle the existing theme setting, not the extension's enabled state.
    # GNOME 51 no longer implements ReloadExtension; metadata needs next login.
    try:
        subprocess.run(command + ['set', schema, 'name', "''"], check=True)
    finally:
        subprocess.run(command + ['set', schema, 'name', current], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', type=Path, help='Restore a backup directory')
    parser.add_argument('--no-reload', action='store_true', help='Only update files')
    args = parser.parse_args()
    data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    css = data / 'themes/NothingOS-Shell/gnome-shell/gnome-shell.css'
    metadata = data / 'gnome-shell/extensions' / UUID / 'metadata.json'
    if not metadata.is_file():
        parser.error('Install User Themes in the user extension directory first.')
    if args.restore:
        saved = args.restore
        old_metadata = json.loads((saved / 'metadata.json').read_text())
        if old_metadata.get('uuid') != UUID:
            parser.error('Backup belongs to a different extension.')
        # Read and validate the backup before modifying either installed file.
        old_css = (saved / 'gnome-shell.css').read_text()
        metadata.write_text(json.dumps(old_metadata, indent=2) + '\n')
        css.write_text(old_css)
        print(f'Restored {saved}')
    else:
        source = (Path(__file__).parent / 'gnome-shell.css').read_text()
        current = css.read_text() if css.exists() else source
        updated = merge_lock_styles(current, source)
        info = json.loads(metadata.read_text())
        if info.get('uuid') != UUID:
            parser.error('Unexpected User Themes extension metadata.')
        modes = list(info.get('session-modes', ['user']))
        if 'unlock-dialog' not in modes:
            modes.append('unlock-dialog')
        info['session-modes'] = modes
        state = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state'))
        backup = state / 'nothingos/backups' / datetime.datetime.now().strftime(
            'lockscreen-%Y%m%dT%H%M%S-%f')
        backup.mkdir(parents=True, mode=0o700)
        shutil.copy2(metadata, backup / 'metadata.json')
        (backup / 'gnome-shell.css').write_text(current)
        css.parent.mkdir(parents=True, exist_ok=True)
        try:
            css.write_text(updated)
            metadata.write_text(json.dumps(info, indent=2) + '\n')
            if not args.no_reload:
                reload_theme()
        except Exception:
            css.write_text(current)
            shutil.copy2(backup / 'metadata.json', metadata)
            raise
        print(f'Applied lockscreen styles. Backup: {backup}')
        print('Log out and back in once to activate the unlock-dialog session mode.')
        return
    if not args.no_reload:
        reload_theme()
    print('Log out and back in once to reload the restored session modes.')


if __name__ == '__main__':
    main()
