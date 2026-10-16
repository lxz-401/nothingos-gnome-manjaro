#!/usr/bin/python3
"""Produce one media snapshot with validated cached artwork or an app icon."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf, Gtk

LIMIT = 4 * 1024 * 1024


def readable_image(path):
    try:
        if not path.is_file() or path.stat().st_size > LIMIT:
            return False
        return GdkPixbuf.Pixbuf.get_file_info(str(path))[0] is not None
    except Exception:
        return False


def artwork(url):
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme == 'file' and parsed.netloc in ('', 'localhost'):
        path = Path(unquote(parsed.path))
        return str(path) if readable_image(path) else None
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'nothingos/media'
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + '.img')
    if readable_image(path):
        return str(path)
    if url.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,', 'data:image/webp;base64,')):
        if len(url) > LIMIT * 2:
            return None
        data = base64.b64decode(url.split(',', 1)[1], validate=True)
    elif parsed.scheme == 'https':
        with urlopen(url, timeout=2) as response:
            if urlparse(response.geturl()).scheme != 'https':
                return None
            data = response.read(LIMIT + 1)
    else:
        return None
    if len(data) > LIMIT:
        return None
    temporary = path.with_suffix('.tmp')
    try:
        temporary.write_bytes(data)
        if not readable_image(temporary):
            return None
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    # Keep a small bounded cache; the current artwork is the newest file.
    images = sorted(cache.glob('*.img'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in images[16:]:
        old.unlink(missing_ok=True)
    return str(path)


def app_icon(player):
    player = player.lower()
    if player.startswith('spotify'):
        names = ['spotify']
    elif player.startswith(('chromium', 'chrome')):
        names = ['google-chrome', 'chromium']
    elif 'ayugram' in player:
        names = ['com.ayugram.desktop', 'telegram']
    elif 'telegram' in player:
        names = ['telegram', 'org.telegram.desktop']
    else:
        names = [player.split('.')[0]]
    theme = Gtk.IconTheme.get_default()
    if theme:
        for name in names + ['audio-x-generic', 'audio-x-generic-symbolic']:
            info = theme.lookup_icon(name, 64, 0)
            if info and info.get_filename():
                return info.get_filename()
    return str(Path(__file__).with_name('media-fallback.svg'))


def snapshot(player, title):
    image = None
    if player:
        try:
            result = subprocess.run(['playerctl', '--player=' + player, 'metadata',
                                     '--format', '{{mpris:artUrl}}'],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                image = artwork(result.stdout.strip())
        except Exception:
            # Artwork is optional; player selection/title still work offline.
            pass
    return {'title': title, 'image': image or app_icon(player)}


if __name__ == '__main__':
    print(json.dumps(snapshot(sys.argv[1], sys.argv[2]), ensure_ascii=False))
