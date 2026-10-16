#!/usr/bin/python3
"""Install local agent access to the desktop reminder widget."""
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from datetime import datetime, timezone


def install():
    source = Path(__file__).resolve().parent
    home = Path.home()
    config = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    codex = Path(os.environ.get('CODEX_HOME', home / '.codex'))
    state = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state'))
    instructions = codex / 'AGENTS.md'
    old = instructions.read_text() if instructions.exists() else ''
    fragment = (source / 'reminders-AGENTS.md').read_text().strip()
    begin = '<!-- BEGIN NOTHINGOS DESKTOP REMINDERS -->'
    end = '<!-- END NOTHINGOS DESKTOP REMINDERS -->'
    if (begin in old) != (end in old):
        raise ValueError('Incomplete managed reminder instructions; repair the markers first')
    if begin in old:
        updated = re.sub(re.escape(begin) + '.*?' + re.escape(end), lambda _: fragment, old, flags=re.S)
    else:
        updated = old.rstrip() + ('\n\n' if old.strip() else '') + fragment + '\n'
    targets = [
        ('backend.py', config / 'eww/scripts/reminders.py', (source.parent / 'eww/scripts/reminders.py').read_bytes(), True),
        ('nothingos-reminders', home / '.local/bin/nothingos-reminders', (source / 'nothingos-reminders').read_bytes(), True),
        ('SKILL.md', codex / 'skills/desktop-reminders/SKILL.md', (source / 'desktop-reminders/SKILL.md').read_bytes(), False),
        ('AGENTS.md', instructions, updated.encode(), False),
    ]
    backup = state / 'nothingos/backups' / ('reminder-agent-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid()))
    manifest = []
    for name, target, data, executable in targets:
        if target.exists() and target.read_bytes() == data and (not executable or os.access(target, os.X_OK)):
            continue
        backup.mkdir(parents=True, exist_ok=True, mode=0o700)
        existed = target.exists()
        if existed:
            shutil.copy2(target, backup / name)
        manifest.append({'path': str(target), 'existed': existed, 'backup': name if existed else None})
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = (stat.S_IMODE(target.stat().st_mode) if existed else 0o644) | (0o111 if executable else 0)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(data)
        try:
            temporary.chmod(mode)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Agent command: ' + str(home / '.local/bin/nothingos-reminders'))
    print('Codex skill: ' + str(codex / 'skills/desktop-reminders/SKILL.md'))
    print('Backup: ' + str(backup) if manifest else 'Already installed; no files changed.')


if __name__ == '__main__':
    install()
