"""CLI routing contract for desktop launches and deliberate Conky commands."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


LAUNCHER = Path(__file__).resolve().parents[1] / "conky/conky-launcher.sh"


class ConkyLauncherTest(unittest.TestCase):
    def test_desktop_defaults_reuse_service_and_explicit_commands_pass_through(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            for relative, label in [
                (".config/conky/start_conky.sh", "managed"),
                (".local/lib/nothingos/conky", "binary"),
            ]:
                script = home / relative
                script.parent.mkdir(parents=True, exist_ok=True)
                script.write_text('#!/bin/sh\nprintf "' + label + ':%s\\n" "$*"\n')
                script.chmod(0o755)
            environment = {**os.environ, "HOME": directory}
            environment.pop("XDG_CONFIG_HOME", None)
            cases = [
                ([], "managed:"),
                (["--daemonize", "--pause=1"], "managed:"),
                (["-d", "-p", "1"], "managed:"),
                (["--version"], "binary:--version"),
                (["--help"], "binary:--help"),
                (["-c", "custom.conf"], "binary:-c custom.conf"),
                (["--daemonize", "-c", "custom.conf"], "binary:--daemonize -c custom.conf"),
            ]
            for arguments, expected in cases:
                with self.subTest(arguments=arguments):
                    output = subprocess.check_output(
                        [str(LAUNCHER), *arguments], env=environment, text=True
                    ).strip()
                    self.assertEqual(output, expected)

    @unittest.skipUnless(Path("/usr/bin/conky").is_file(), "system Conky unavailable")
    def test_portable_explicit_command_uses_system_binary_without_local_build(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = {**os.environ, "HOME": directory}
            environment.pop("XDG_CONFIG_HOME", None)
            expected = subprocess.run(
                ["/usr/bin/conky", "--version"], capture_output=True, env=environment
            )
            actual = subprocess.run(
                [str(LAUNCHER), "--version"], capture_output=True, env=environment
            )
            self.assertEqual(actual.returncode, expected.returncode)
            self.assertEqual(actual.stdout, expected.stdout)


if __name__ == "__main__":
    unittest.main()
