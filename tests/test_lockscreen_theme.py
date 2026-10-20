import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'lock_theme', ROOT / 'shell-theme/apply-lockscreen.py')
theme = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(theme)


class LockscreenThemeTests(unittest.TestCase):
    def test_merge_preserves_local_overrides_and_rules_after_block(self):
        source = (ROOT / 'shell-theme/gnome-shell.css').read_text()
        local = '#panel { height: 28px; }\n'
        result = theme.merge_lock_styles(local, source)
        result += '\n.local-rule { color: red; }\n'
        again = theme.merge_lock_styles(result, source)
        self.assertEqual(again, result)
        self.assertIn(local, again)
        self.assertTrue(again.endswith('.local-rule { color: red; }\n'))

    def test_apply_backup_restore_keeps_original_metadata_and_css(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / 'data'
            state = Path(temporary) / 'state'
            css = data / 'themes/NothingOS-Shell/gnome-shell/gnome-shell.css'
            metadata = data / 'gnome-shell/extensions' / theme.UUID / 'metadata.json'
            css.parent.mkdir(parents=True)
            metadata.parent.mkdir(parents=True)
            original = '#panel { height: 28px; }\n'
            info = {'uuid': theme.UUID, 'session-modes': ['user'], 'version': 78}
            css.write_text(original)
            metadata.write_text(json.dumps(info))
            with patch.dict(os.environ, {'XDG_DATA_HOME': str(data),
                                         'XDG_STATE_HOME': str(state)}):
                with patch.object(sys, 'argv', ['apply-lockscreen.py', '--no-reload']):
                    theme.main()
                backup, = (state / 'nothingos/backups').iterdir()
                self.assertEqual(json.loads(metadata.read_text())['session-modes'],
                                 ['user', 'unlock-dialog'])
                self.assertIn(original.strip(), css.read_text())
                with patch.object(sys, 'argv', ['apply-lockscreen.py', '--restore',
                                               str(backup), '--no-reload']):
                    theme.main()
                self.assertEqual(css.read_text(), original)
                self.assertEqual(json.loads(metadata.read_text()), info)

    def test_failed_reload_rolls_back_both_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / 'data'
            css = data / 'themes/NothingOS-Shell/gnome-shell/gnome-shell.css'
            metadata = data / 'gnome-shell/extensions' / theme.UUID / 'metadata.json'
            css.parent.mkdir(parents=True)
            metadata.parent.mkdir(parents=True)
            css.write_text('/* original CSS */')
            metadata.write_text(json.dumps({'uuid': theme.UUID, 'version': 78}))
            originals = css.read_bytes(), metadata.read_bytes()
            with patch.dict(os.environ, {'XDG_DATA_HOME': str(data),
                                         'XDG_STATE_HOME': str(Path(temporary) / 'state')}), \
                 patch.object(sys, 'argv', ['apply-lockscreen.py']), \
                 patch.object(theme, 'reload_theme', side_effect=[RuntimeError('test'), None]):
                with self.assertRaises(RuntimeError):
                    theme.main()
            self.assertEqual((css.read_bytes(), metadata.read_bytes()), originals)


if __name__ == '__main__':
    unittest.main()
