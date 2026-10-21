#!/usr/bin/env python3
"""Prepare or apply the NothingOS GDM theme without restarting the desktop."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import theme


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare', help='Validate and create a private theme bundle')
    prepare.add_argument('--output', type=Path, required=True)
    prepare.add_argument('--wallpaper', type=Path)
    prepare.add_argument('--blur', type=float, default=32, help='Blur pixels at 1080p (0–128; default 32)')
    apply = commands.add_parser('apply', help='Prepare as user, then show administrator dialog')
    apply.add_argument('--wallpaper', type=Path)
    apply.add_argument('--blur', type=float, default=32, help='Blur pixels at 1080p (0–128; default 32)')
    install = commands.add_parser('install', help='Privileged step, called by apply')
    install.add_argument('--bundle', type=Path, required=True)
    restore = commands.add_parser('restore', help='Restore a recorded managed backup')
    restore.add_argument('--backup', type=Path, required=True)
    args = parser.parse_args()
    if args.command in ('prepare', 'apply') and os.geteuid() == 0:
        parser.error('Run prepare/apply as your desktop user, not root.')
    if args.command == 'prepare':
        print(theme.prepare(args.output, args.wallpaper, blur=args.blur))
    elif args.command == 'apply':
        base = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'nothingos/gdm-prepared'
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        output = Path(tempfile.mkdtemp(prefix='bundle-', dir=base))
        theme.prepare(output, args.wallpaper, blur=args.blur)
        print(f'Validated bundle: {output}', flush=True)
        subprocess.run(['pkexec', '/usr/bin/python3', str(Path(__file__).resolve()),
                        'install', '--bundle', str(output)], check=True)
    elif args.command == 'restore' and os.geteuid() != 0:
        subprocess.run(['pkexec', '/usr/bin/python3', str(Path(__file__).resolve()),
                        'restore', '--backup', str(args.backup.absolute())], check=True)
    else:
        if os.geteuid() != 0:
            parser.error('This installation step requires administrator authentication.')
        os.umask(0o077)
        if args.command == 'install':
            backup = theme.install(args.bundle)
            print(f'Installed. Backup: {backup}')
        else:
            theme.restore(args.backup)
            print('Original managed files restored.')
        print('GDM was not restarted. Changes apply when the next greeter starts.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'GDM setup failed: {error}', file=sys.stderr)
        sys.exit(1)
