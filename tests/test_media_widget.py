"""Exercise player selection without controlling the user's media sessions."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'eww/scripts/get-media.sh'


class MediaWidgetTests(unittest.TestCase):
    def select(self, players):
        with tempfile.TemporaryDirectory(prefix='media widget ') as folder:
            command = Path(folder) / 'playerctl'
            command.write_text(f'#!{sys.executable}\n' + '''import json, os, sys
players = json.loads(os.environ['TEST_PLAYERS'])
args = sys.argv[1:]
if args == ['-l']:
    print('\\n'.join(players))
    sys.exit(0 if players else 1)
player = args[0].split('=', 1)[1]
data = players[player]
if args[1] == 'status': print(data[0])
elif data[1] is None: sys.exit(1)
else: print(data[1])
''')
            command.chmod(0o755)
            result = subprocess.run([str(SCRIPT)], env=dict(os.environ,
                PATH=folder+os.pathsep+os.environ['PATH'], TEST_PLAYERS=json.dumps(players)),
                capture_output=True, text=True, check=True, timeout=10)
            return result.stdout.strip()

    def test_stopped_messenger_does_not_hide_playing_spotify(self):
        self.assertEqual(self.select({'AyuGramDesktop': ['Stopped', 'ASAD'],
            'chromium': ['Paused', 'Old video'], 'spotify': ['Playing', 'Artist - Song']}),
            'Artist - Song')

    def test_spotify_wins_a_tie_but_playing_browser_beats_paused_spotify(self):
        self.assertEqual(self.select({'chromium': ['Paused', 'Old video'],
            'spotify': ['Paused', 'Spotify song']}), 'Spotify song')
        self.assertEqual(self.select({'chromium': ['Playing', 'Live video'],
            'spotify': ['Paused', 'Spotify song']}), 'Live video')

    def test_paused_player_is_used_when_nothing_is_playing(self):
        self.assertEqual(self.select({'messenger': ['Stopped', 'ASAD'],
            'spotify': ['Paused', 'Artist - Song']}), 'Artist - Song')

    def test_stopped_and_absent_players_clear_stale_track(self):
        self.assertEqual(self.select({'messenger': ['Stopped', 'ASAD']}), 'No media playing')
        self.assertEqual(self.select({}), 'No media playing')

    def test_disappearing_player_and_empty_metadata_are_skipped(self):
        self.assertEqual(self.select({'closed': ['Playing', None],
            'empty': ['Playing', ' - '], 'spotify': ['Playing', 'Live track']}), 'Live track')


if __name__ == '__main__':
    unittest.main()
