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
        ids.add(item['id'])
    return items


def mutate(path, action, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        items = read(path)
        if action == 'add':
            text = value.strip()
            if not text:
                return
            if len(text) > 2000:
                raise ValueError('Eslatma 2000 belgidan oshmasligi kerak')
            items.append({'id': uuid.uuid4().hex, 'text': text})
        else:
            items = [item for item in items if item['id'] != value]
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
    parser.add_argument('action', choices=['list', 'add', 'delete'])
    parser.add_argument('value', nargs='?')
    args = parser.parse_args()
    path = data_path()
    try:
        if args.action == 'list':
            print(json.dumps(read(path), ensure_ascii=False))
        else:
            value = args.value
            if args.action == 'add' and value is None:
                value = prompt(path)
                if value is None:
                    return 0
            if value is None:
                parser.error('delete requires an ID')
            mutate(path, args.action, value)
            refresh(path)
    except (OSError, ValueError) as error:
        print(f'Reminders: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
