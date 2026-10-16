"""Artwork decoding, caching and offline fallback without remote downloads."""
import base64
import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('media_image',
    Path(__file__).resolve().parents[1] / 'eww/scripts/media-image.py')
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class ArtworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='media artwork ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch.dict(os.environ, XDG_CACHE_HOME=str(self.root / 'cache'))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.image = self.root / 'album cover.png'
        pixbuf = media.GdkPixbuf.Pixbuf.new(media.GdkPixbuf.Colorspace.RGB, False, 8, 2, 2)
        pixbuf.fill(0xff0000ff)
        pixbuf.savev(str(self.image), 'png', [], [])

    def test_local_file_url_with_spaces(self):
        self.assertEqual(media.artwork(self.image.as_uri()), str(self.image))

    def test_data_artwork_is_decoded_and_reused(self):
        url = 'data:image/png;base64,' + base64.b64encode(self.image.read_bytes()).decode()
        path = media.artwork(url)
        self.assertTrue(media.readable_image(Path(path)))
        self.assertEqual(media.artwork(url), path)
        self.assertEqual(len(list((self.root / 'cache/nothingos/media').glob('*.img'))), 1)

    def test_missing_or_invalid_images_are_rejected(self):
        self.assertIsNone(media.artwork((self.root / 'missing.png').as_uri()))
        self.assertIsNone(media.artwork('data:image/png;base64,' + base64.b64encode(b'not an image').decode()))
        self.assertIsNone(media.artwork('http://example.invalid/art.png'))

    def test_download_failure_keeps_title_and_uses_app_icon(self):
        result = SimpleNamespace(returncode=0, stdout='https://example.invalid/art.png')
        with patch.object(media.subprocess, 'run', return_value=result), \
             patch.object(media, 'urlopen', side_effect=OSError('offline')):
            state = media.snapshot('spotify', 'Artist - Title')
        self.assertEqual(state['title'], 'Artist - Title')
        self.assertTrue(Path(state['image']).is_file())


if __name__ == '__main__':
    unittest.main()
