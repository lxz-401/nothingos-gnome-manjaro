"""Notes persist safely without opening dialogs or touching desktop data."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'eww/scripts/reminders.py'
spec = importlib.util.spec_from_file_location('reminders', SCRIPT)
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='reminders test ')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'notes/reminders.json'

    def test_empty_add_and_delete_preserve_other_ids(self):
        self.assertEqual(notes.read(self.path), [])
        notes.mutate(self.path, 'add', 'Birinchi eslatma')
        first = notes.read(self.path)[0]
        notes.mutate(self.path, 'add', 'Ikkinchi eslatma')
        notes.mutate(self.path, 'delete', first['id'])
        self.assertEqual([n['text'] for n in notes.read(self.path)], ['Ikkinchi eslatma'])
        self.assertNotEqual(notes.read(self.path)[0]['id'], first['id'])

    def test_unicode_and_shell_characters_remain_plain_text(self):
        text = 'O‘zbekcha "eslatma" $(touch /tmp/not-executed) <b>salom</b>\nkeyingi qator'
        notes.mutate(self.path, 'add', text)
        self.assertEqual(notes.read(self.path)[0]['text'], text)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_empty_text_is_not_added(self):
        notes.mutate(self.path, 'add', ' \n ')
        self.assertEqual(notes.read(self.path), [])

    def test_invalid_data_is_never_overwritten(self):
        self.path.parent.mkdir()
        self.path.write_text('{broken')
        with self.assertRaises(ValueError): notes.mutate(self.path, 'add', 'new')
        self.assertEqual(self.path.read_text(), '{broken')

    def test_hand_edited_command_id_is_rejected(self):
        self.path.parent.mkdir()
        self.path.write_text(json.dumps({'version': 1, 'items': [{'id': 'x; touch /tmp/no', 'text': 'note'}]}))
        with self.assertRaises(ValueError): notes.read(self.path)

    def test_concurrent_additions_are_not_lost(self):
        env = dict(os.environ, XDG_DATA_HOME=self.temp.name)
        code = "import runpy,sys; m=runpy.run_path(sys.argv[1]); m['mutate'](m['data_path'](), 'add', sys.argv[2])"
        children = [subprocess.Popen([sys.executable, '-c', code, str(SCRIPT), f'Note {i}'], env=env)
                    for i in range(12)]
        for child in children: self.assertEqual(child.wait(timeout=10), 0)
        items = notes.read(Path(self.temp.name) / 'nothingos/reminders.json')
        self.assertEqual(len(items), 12)
        self.assertEqual(len({n['id'] for n in items}), 12)

    def test_cancelled_dialog_does_not_add_note(self):
        with patch.object(notes.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', '')):
            self.assertIsNone(notes.prompt(self.path))
        self.assertEqual(notes.read(self.path), [])

    def test_refresh_sends_json_as_single_argument_without_shell(self):
        notes.mutate(self.path, 'add', '"${HOME}" $(exit 1)')
        with patch.object(notes.subprocess, 'run') as run:
            notes.refresh(self.path)
        args, kwargs = run.call_args
        self.assertFalse(kwargs.get('shell', False))
        self.assertEqual(json.loads(args[0][-1].split('=', 1)[1]), notes.read(self.path))


if __name__ == '__main__':
    unittest.main()
