"""Real GTK dialog behavior; opt in on an isolated Broadway/X11 display."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'eww/scripts/reminders.py'
spec = importlib.util.spec_from_file_location('reminder_dialog', SCRIPT)
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


@unittest.skipUnless(os.environ.get('NOTHINGOS_TEST_GTK') == '1', 'isolated GTK display required')
class DialogTest(unittest.TestCase):
    def test_full_text_selection_edit_save_cancel_and_escape(self):
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, Gdk, GLib

        def descendants(widget):
            yield widget
            if isinstance(widget, Gtk.Container):
                for child in widget.get_children():
                    yield from descendants(child)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'notes.json'
            original = ('Uzun eslatma <b>oddiy matn</b> $(literal)\n' * 30).strip()
            note_id = notes.mutate(path, 'add', original, key='test:reader')['item']['id']
            errors = []
            phase = [0]

            def interact():
                dialog = next(w for w in Gtk.Window.list_toplevels() if w.get_title() == 'Eslatma')
                try:
                    view = next(w for w in descendants(dialog) if isinstance(w, Gtk.TextView))
                    buffer = view.get_buffer()
                    if phase[0] == 0:
                        self.assertFalse(view.get_editable())
                        self.assertEqual(buffer.get_line_count(), 30)
                        self.assertEqual(view.get_wrap_mode(), Gtk.WrapMode.WORD_CHAR)
                        self.assertEqual(buffer.get_text(*buffer.get_bounds(), True), original)
                        buffer.select_range(*buffer.get_bounds())
                        self.assertTrue(buffer.get_has_selection())
                        notes.show_note(path, note_id)  # duplicate click does not open another window
                        self.assertEqual(sum(w.get_title() == 'Eslatma' for w in Gtk.Window.list_toplevels()), 1)
                        dialog.response(1)
                    elif phase[0] == 1:
                        self.assertTrue(view.get_editable())
                        buffer.set_text('Tahrirlangan matn\nIkkinchi qator')
                        dialog.response(1)
                    elif phase[0] == 2:
                        self.assertFalse(view.get_editable())
                        self.assertEqual(notes.read(path)[0]['text'], 'Tahrirlangan matn\nIkkinchi qator')
                        dialog.response(1)
                    elif phase[0] == 3:
                        buffer.set_text('Bu o‘zgarish bekor qilinadi')
                        event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
                        event.keyval = Gdk.KEY_Escape
                        self.assertTrue(dialog.emit('key-press-event', event))
                        return False
                    phase[0] += 1
                    return True
                except BaseException as error:
                    errors.append(error)
                    dialog.response(Gtk.ResponseType.CLOSE)
                    return False

            timer = GLib.timeout_add(100, interact)
            def timeout():
                errors.append(AssertionError('Dialog interaction timed out'))
                for w in Gtk.Window.list_toplevels():
                    if isinstance(w, Gtk.Dialog):
                        w.response(Gtk.ResponseType.CLOSE)
                return False
            watchdog = GLib.timeout_add_seconds(5, timeout)
            with patch.object(notes, 'refresh') as refresh:
                notes.show_note(path, note_id)
                self.assertEqual(refresh.call_count, 1)
            GLib.source_remove(watchdog)
            if errors:
                raise errors[0]
            self.assertEqual(phase[0], 3)
            item = notes.read(path)[0]
            self.assertEqual(item['text'], 'Tahrirlangan matn\nIkkinchi qator')
            self.assertEqual(item['id'], note_id)
            self.assertEqual(item['key'], 'test:reader')
