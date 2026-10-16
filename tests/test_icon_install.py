"""Installer transactions without network access or changes to the real desktop."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"


@unittest.skipIf(os.geteuid() == 0, "The installer intentionally refuses sudo/root")
class IconInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="WhiteSur test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.data = self.root / "data with spaces"
        self.state = self.root / "state with spaces"
        self.setting = self.root / "icon-setting"
        self.setting.write_text("'Adwaita'\n")
        self.env = dict(os.environ, HOME=str(self.root), XDG_DATA_HOME=str(self.data),
                        XDG_STATE_HOME=str(self.state), MOCK_SETTING=str(self.setting),
                        PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        self.command("git", '''import os, pathlib, sys
args = sys.argv[1:]
if args[0] == 'init': pathlib.Path(args[-1]).mkdir(parents=True)
if 'fetch' in args:
    if os.environ.get('FAIL_FETCH'): sys.exit(128)
    dest = pathlib.Path(args[1])
    (dest/'COPYING').write_text('Test license fixture')
    (dest/'install.sh').write_text(''' + repr('''#!/bin/bash
set -eu
dest="$2"
for theme in WhiteSur WhiteSur-light WhiteSur-dark; do
  mkdir -p "$dest/$theme"
  printf '[Icon Theme]\\nName=%s\\nInherits=hicolor,breeze\\n' "$theme" > "$dest/$theme/index.theme"
done
''') + ''')
''')
        self.command("gtk-update-icon-cache", "")
        self.command("gsettings", '''import os, pathlib, sys
p = pathlib.Path(os.environ['MOCK_SETTING'])
args = sys.argv[1:]
if args[0] == 'get': print(p.read_text().strip())
elif args[0] == 'writable': print('true')
elif args[0] == 'set':
    value = args[3]
    if os.environ.get('FAIL_APPLY') and value == 'WhiteSur': sys.exit(0)
    p.write_text((value if value.startswith("'") else "'"+value+"'")+'\\n')
''')

    def command(self, name, body):
        p = self.bin / name
        p.write_text(f"#!{sys.executable}\n" + body)
        p.chmod(0o755)

    def run_installer(self, *args, **environment):
        result = subprocess.run([str(INSTALLER), *args], env=dict(self.env, **environment),
                                text=True, capture_output=True, timeout=30)
        return result

    def add_old_theme(self):
        theme = self.data / "icons/WhiteSur"
        theme.mkdir(parents=True)
        (theme / "custom-icon").write_text("keep this")
        return theme

    def test_fresh_install_applies_whitesur_with_spaced_xdg_paths(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.setting.read_text().strip(), "'WhiteSur'")
        for name in ["WhiteSur", "WhiteSur-light", "WhiteSur-dark"]:
            theme = self.data / "icons" / name
            self.assertIn("Inherits=Adwaita,hicolor,breeze", (theme / "index.theme").read_text())
            self.assertTrue((theme / "COPYING").is_file())

    def test_repeat_install_preserves_existing_files_and_setting_in_backup(self):
        self.assertEqual(self.run_installer().returncode, 0)
        (self.data / "icons/WhiteSur/custom-icon").write_text("keep this")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.state / "nothingos/backups").glob("whitesur-*/themes/WhiteSur/custom-icon"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "keep this")
        self.assertEqual((backups[0].parents[2] / "icon-theme.gvariant").read_text().strip(), "'WhiteSur'")

    def test_download_failure_does_not_touch_existing_theme(self):
        theme = self.add_old_theme()
        result = self.run_installer(FAIL_FETCH="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((theme / "custom-icon").read_text(), "keep this")
        self.assertEqual(self.setting.read_text().strip(), "'Adwaita'")

    def test_silent_settings_failure_rolls_back_files_and_selection(self):
        theme = self.add_old_theme()
        result = self.run_installer(FAIL_APPLY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((theme / "custom-icon").read_text(), "keep this")
        self.assertFalse((self.data / "icons/WhiteSur-light").exists())
        self.assertFalse((self.data / "icons/WhiteSur-dark").exists())
        self.assertEqual(self.setting.read_text().strip(), "'Adwaita'")

    def test_no_apply_preserves_icon_selection(self):
        result = self.run_installer("--no-apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.setting.read_text().strip(), "'Adwaita'")


if __name__ == "__main__":
    unittest.main()
