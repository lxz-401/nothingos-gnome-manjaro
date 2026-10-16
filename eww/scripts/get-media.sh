#!/usr/bin/env bash
# The first MPRIS player can be a stopped messenger with stale metadata.
# Prefer a player that is actually playing; paused media is the fallback.
set -u
emit() {
    if [[ ${1:-} == --json ]]; then
        local directory
        directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
        /usr/bin/python3 "$directory/media-image.py" "$2" "$3"
    else
        printf '%s\n' "$3"
    fi
}
mapfile -t available < <(playerctl -l 2>/dev/null)
# For equally active players, prefer Spotify to match this widget's identity.
players=()
for player in "${available[@]}"; do
    case "${player,,}" in
        spotify|spotify.*) players=("$player" "${players[@]}") ;;
        *) players+=("$player") ;;
    esac
done
statuses=()
for player in "${players[@]}"; do
    statuses+=("$(playerctl --player="$player" status 2>/dev/null || true)")
done
for wanted in Playing Paused; do
    for i in "${!players[@]}"; do
        [[ ${statuses[$i]} == "$wanted" ]] || continue
        track=$(playerctl --player="${players[$i]}" metadata \
            --format '{{artist}} - {{title}}' 2>/dev/null) || continue
        [[ -n ${track//[[:space:]-]/} ]] || continue
        emit "${1:-}" "${players[$i]}" "$track"
        exit 0
    done
done
emit "${1:-}" '' 'No media playing'
