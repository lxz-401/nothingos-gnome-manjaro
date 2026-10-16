#!/bin/sh
set -eu
config="${XDG_CONFIG_HOME:-$HOME/.config}/conky/nothing-phone-conky.conf"
# Use the fixed upstream release for this theme only; leave pacman files intact.
binary="$HOME/.local/lib/nothingos/conky"
if [ ! -x "$binary" ]; then binary=/usr/bin/conky; fi
exec "$binary" -c "$config"
