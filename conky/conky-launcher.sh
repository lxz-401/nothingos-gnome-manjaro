#!/bin/sh
set -eu
# Desktop launchers commonly supply only daemon/pause flags. They still mean
# the managed five-block desktop, while explicit CLI requests use the binary.
managed=true
pause_value=false
for argument do
    if [ "$pause_value" = true ]; then
        pause_value=false
        continue
    fi
    case "$argument" in
        -d|--daemonize|-q|--quiet|--pause=*) ;;
        -p|--pause) pause_value=true ;;
        *) managed=false; break ;;
    esac
done
if [ "$managed" = true ] && [ "$pause_value" = false ]; then
    exec "${XDG_CONFIG_HOME:-$HOME/.config}/conky/start_conky.sh"
fi
# Preserve version checks, help, and explicit configuration arguments.
if [ -x "$HOME/.local/lib/nothingos/conky" ]; then
    exec "$HOME/.local/lib/nothingos/conky" "$@"
fi
# Absolute system path avoids recursing into this wrapper on portable installs.
exec /usr/bin/conky "$@"
