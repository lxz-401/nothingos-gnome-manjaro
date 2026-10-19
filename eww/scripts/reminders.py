#!/usr/bin/python3
"""Persistent desktop notes; user text is always data, never a shell command."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid


def data_path():
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'nothingos/reminders.json'


def read(path):
    if not path.exists():
        return []
    state = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(state, dict) or state.get('version') != 1 or not isinstance(state.get('items'), list):
        raise ValueError('Unsupported reminders file; existing data was not changed')
    items = state['items']
    ids = set()
    for item in items:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not re.fullmatch('[0-9a-f]{32}', item['id']) or item['id'] in ids
                or not isinstance(item.get('text'), str) or not item['text'].strip()):
            raise ValueError('Invalid reminders file; existing data was not changed')
        if 'key' in item and (not isinstance(item['key'], str) or not item['key'].strip()
                              or len(item['key']) > 200):
            raise ValueError('Invalid reminder key; existing data was not changed')
        ids.add(item['id'])
    return items


def mutate(path, action, value, key=None, text=None, expected_text=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        items = read(path)
        if action == 'add':
            text = value.strip()
            if not text:
                return {'changed': False, 'item': None}
            if len(text) > 2000:
                raise ValueError('Eslatma 2000 belgidan oshmasligi kerak')
            if key is not None and (not key.strip() or len(key) > 200):
                raise ValueError('Reminder key must contain 1–200 characters')
            item = next((item for item in items if key is not None and item.get('key') == key), None)
            if item is not None:
                if item['text'] == text:
                    return {'changed': False, 'item': item}
                item['text'] = text
            else:
                item = {'id': uuid.uuid4().hex, 'text': text}
                if key is not None:
                    item['key'] = key
                items.append(item)
            result = {'changed': True, 'item': item}
        elif action == 'update':
            item = next((item for item in items if item['id'] == value), None)
            if item is None:
                raise ValueError('Eslatma o‘chirilgan yoki topilmadi')
            if expected_text is not None and item['text'] != expected_text:
                raise ValueError('Eslatma boshqa joyda o‘zgartirilgan. Yoping va qayta oching.')
            text = (text or '').strip()
            if not text or len(text) > 2000:
                raise ValueError('Eslatma 1–2000 belgidan iborat bo‘lishi kerak')
            if item['text'] == text:
                return {'changed': False, 'item': item}
            item['text'] = text
            result = {'changed': True, 'item': item}
        elif action == 'delete':
            removed = next((item for item in items if item['id'] == value), None)
            if removed is None:
                return {'changed': False, 'item': None}
            items = [item for item in items if item['id'] != value]
            result = {'changed': True, 'item': removed}
        else:
            raise ValueError('Unknown reminder action')
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
                temporary = Path(file.name)
                json.dump({'version': 1, 'items': items}, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
        return result


def prompt(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.dialog.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None
        result = subprocess.run(['zenity', '--entry', '--title=Yangi eslatma',
            '--text=Eslatma matnini kiriting:', '--entry-text=', '--width=380',
            '--ok-label=Qo‘shish', '--cancel-label=Bekor qilish'], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None


def show_note(path, note_id):
    if not re.fullmatch('[0-9a-f]{32}', note_id):
        raise ValueError('Invalid reminder ID')
    item = next((item for item in read(path) if item['id'] == note_id), None)
    if item is None:
        raise ValueError('Eslatma topilmadi')
    # One viewer per note; add dialog and other note viewers remain independent.
    with path.with_name(f'.reminder-{note_id}.dialog.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gdk, Gtk

        dialog = Gtk.Dialog(title='Eslatma', modal=True)
        dialog.set_default_size(480, 320)
        dialog.set_position(Gtk.WindowPosition.CENTER)
        dialog.get_style_context().add_class('reminder-dialog')
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .reminder-dialog { background-color: #f5f5f5; color: #171717; font-family: Inter; }
            .reminder-dialog textview, .reminder-dialog textview text {
                background-color: #f5f5f5; color: #171717; font-size: 14px; }
            .reminder-dialog button { border-radius: 8px; padding: 8px 14px; }
            .reminder-dialog .suggested-action { background-image: none;
                background-color: #45ffbc; color: #062419; }
        """)
        screen = dialog.get_screen()
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        content = dialog.get_content_area()
        content.set_border_width(16)
        content.set_spacing(12)
        hint = Gtk.Label(label='Matnni belgilab Ctrl+C bilan nusxalashingiz mumkin.', xalign=0)
        hint.set_line_wrap(True)
        content.pack_start(hint, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        view = Gtk.TextView()
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        view.set_editable(False)
        view.set_cursor_visible(False)
        view.set_left_margin(8)
        view.set_right_margin(8)
        buffer = view.get_buffer()
        buffer.set_text(item['text'])
        scroll.add(view)
        content.pack_start(scroll, True, True, 0)
        close = dialog.add_button('Yopish', Gtk.ResponseType.CLOSE)
        edit = dialog.add_button('Tahrirlash', 1)
        dialog.connect('key-press-event', lambda widget, event:
                       (dialog.response(Gtk.ResponseType.CLOSE) or True)
                       if event.keyval == Gdk.KEY_Escape else False)
        editing = False
        dialog.show_all()
        view.grab_focus()
        try:
            while dialog.run() == 1:
                if not editing:
                    editing = True
                    view.set_editable(True)
                    view.set_cursor_visible(True)
                    edit.set_label('Saqlash')
                    edit.get_style_context().add_class('suggested-action')
                    close.set_label('Bekor qilish')
                    hint.set_text('Eslatmani tahrirlang. Saqlash tugmasi o‘zgarishni saqlaydi.')
                    view.grab_focus()
                    continue
                text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                try:
                    result = mutate(path, 'update', note_id, text=text, expected_text=item['text'])
                except (OSError, ValueError) as error:
                    warning = Gtk.MessageDialog(transient_for=dialog, modal=True,
                        message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CLOSE,
                        text=str(error))
                    warning.run()
                    warning.destroy()
                    continue
                item = result['item'].copy()
                buffer.set_text(item['text'])
                if result['changed']:
                    refresh(path)
                editing = False
                view.set_editable(False)
                view.set_cursor_visible(False)
                edit.set_label('Tahrirlash')
                edit.get_style_context().remove_class('suggested-action')
                close.set_label('Yopish')
                hint.set_text('Saqlandi. Matnni belgilab nusxalashingiz mumkin.')
        finally:
            dialog.destroy()
            Gtk.StyleContext.remove_provider_for_screen(screen, css)


def refresh(path):
    try:
        # argv avoids shell interpolation of arbitrary reminder text.
        subprocess.run(['eww', '--no-daemonize', '--config', str(Path(__file__).resolve().parent.parent),
            'update', 'REMINDERS=' + json.dumps(read(path), ensure_ascii=False)],
            capture_output=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        pass  # Persisted data is picked up by the next poll even without Eww.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'add', 'delete', 'show'])
    parser.add_argument('value', nargs='?')
    parser.add_argument('--key', help='Stable task key: update the matching note instead of duplicating it')
    parser.add_argument('--json', action='store_true', help='Noninteractive machine-readable results')
    args = parser.parse_args()
    if args.key is not None and args.action != 'add':
        parser.error('--key is only supported for add')
    if args.json and args.action != 'list' and args.value is None:
        parser.error('Noninteractive add/delete requires a value')
    if args.action == 'show' and (args.json or args.value is None):
        parser.error('show requires an ID and is only available interactively')
    path = data_path()
    try:
        if args.action == 'list':
            print(json.dumps(read(path), ensure_ascii=False))
        elif args.action == 'show':
            show_note(path, args.value)
        else:
            value = args.value
            if args.action == 'add' and value is None:
                value = prompt(path)
                if value is None:
                    return 0
            if value is None:
                parser.error('delete requires an ID')
            if args.json and args.action == 'add' and not value.strip():
                raise ValueError('Reminder text must not be empty')
            result = mutate(path, args.action, value, args.key)
            if result['changed']:
                refresh(path)
            if args.json:
                print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError) as error:
        message = json.dumps({'error': str(error)}, ensure_ascii=False) if args.json else f'Reminders: {error}'
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
