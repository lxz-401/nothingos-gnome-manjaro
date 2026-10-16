#!/usr/bin/env bash
# The first MPRIS player can be a stopped messenger with stale metadata.
# Prefer a player that is actually playing; paused media is the fallback.
set -u
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
        printf '%s\n' "$track"
        exit 0
    done
done
printf '%s\n' 'No media playing'
