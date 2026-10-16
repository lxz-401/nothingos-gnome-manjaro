#!/bin/bash
# Read real temperature; avoid upstream's fabricated fallback and unbounded log.
for sensor in /sys/class/hwmon/hwmon*; do
    name=$(cat "$sensor/name" 2>/dev/null) || continue
    case "$name" in
        coretemp|k10temp|zenpower)
            for input in "$sensor"/temp*_input; do
                [[ -r $input ]] || continue
                awk '{printf "%.0f\n", $1/1000}' "$input"
                exit 0
            done ;;
    esac
done
for input in /sys/class/thermal/thermal_zone*/temp; do
    [[ -r $input ]] || continue
    awk '{printf "%.0f\n", $1/1000}' "$input"
    exit 0
done
printf '%s\n' '--'
