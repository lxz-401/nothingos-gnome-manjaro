#!/usr/bin/env bash
set -euo pipefail
# One service owns all child windows; an unexpected exit restarts the whole set.
config_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
binary="$HOME/.local/lib/nothingos/conky"
children=()
cleanup() {
    trap - EXIT INT TERM
    if (( ${#children[@]} )); then
        kill "${children[@]}" 2>/dev/null || true
        wait "${children[@]}" 2>/dev/null || true
    fi
}
trap cleanup EXIT
trap 'exit 0' INT TERM
# Login can start this service while Shell is still placing desktop actors.
# Do not create windows against an unready compositor or transient geometry.
python3 "$config_dir/wait-for-desktop.py"
for block in clock cpu memory storage network; do
    "$binary" -c "$config_dir/$block.conf" &
    children+=("$!")
done
wait -n "${children[@]}" || exit "$?"
exit 1
