#!/bin/sh
set -eu
# Repeated launches reuse the same monitored instance.
if [ -n "${DISPLAY:-}" ]; then
    systemctl --user import-environment DISPLAY
fi
if [ -n "${XAUTHORITY:-}" ]; then
    systemctl --user import-environment XAUTHORITY
fi
exec systemctl --user start nothingos-conky.service
