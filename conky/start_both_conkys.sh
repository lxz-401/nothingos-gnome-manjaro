#!/bin/sh
set -eu
# Compatibility entry point: the service owns all five desktop blocks.
exec "${XDG_CONFIG_HOME:-$HOME/.config}/conky/start_conky.sh"
