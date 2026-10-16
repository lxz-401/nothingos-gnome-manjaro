#!/bin/sh
set -eu
if [ "$#" -eq 0 ]; then
    exec "${XDG_CONFIG_HOME:-$HOME/.config}/conky/start_conky.sh"
fi
# Preserve the normal CLI for version checks and explicit configurations.
exec "$HOME/.local/lib/nothingos/conky" "$@"
