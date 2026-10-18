"""Prevent startup against transient or unavailable compositor state."""
import importlib.util
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'conky/wait-for-desktop.py'
spec = importlib.util.spec_from_file_location('conky_readiness', PATH)
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


class ReadinessTest(unittest.TestCase):
    def run_wait(self, probe, timeout=12):
        clock = [0.0]
        def sleep(seconds):
            clock[0] += seconds
        with patch('builtins.print'):
            result = readiness.wait_for_desktop(
                probe=probe, timeout=timeout, settle=3,
                now=lambda: clock[0], sleep=sleep)
        return result, clock[0]

    def test_waits_for_compositor_then_stable_geometry(self):
        calls = [None, None, ('GNOME', (800, 600), True),
                 ('GNOME', (1920, 1080), True),
                 ('GNOME', (1920, 1080), False)]
        final = calls[-1]
        result, elapsed = self.run_wait(lambda: calls.pop(0) if calls else final)
        self.assertTrue(result)
        self.assertEqual(elapsed, 5)

    def test_readiness_loss_resets_settling(self):
        calls = ['ready'] * 5 + [None] + ['ready']
        result, elapsed = self.run_wait(lambda: calls.pop(0) if calls else 'ready')
        self.assertTrue(result)
        self.assertEqual(elapsed, 6)

    def test_unavailable_or_failing_display_times_out(self):
        def failing():
            raise RuntimeError('display not available')
        for probe in [lambda: None, failing]:
            with self.subTest(probe=probe):
                result, elapsed = self.run_wait(probe, timeout=4)
                self.assertFalse(result)
                self.assertEqual(elapsed, 4)


class RunnerReadinessTest(unittest.TestCase):
    def test_unready_desktop_never_launches_conky(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binary = home / '.local/lib/nothingos/conky'
            binary.parent.mkdir(parents=True)
            marker = home / 'started'
            binary.write_text('#!/bin/sh\ntouch "$HOME/started"\n')
            binary.chmod(0o755)
            runner = home / 'run-blocks.sh'
            runner.write_bytes((PATH.parent / 'run-blocks.sh').read_bytes())
            (home / 'wait-for-desktop.py').write_text('raise SystemExit(1)\n')
            result = subprocess.run(['bash', str(runner)],
                                    env={**os.environ, 'HOME': directory},
                                    capture_output=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())
