#!/bin/bash
set -eu
config_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
config="$config_dir/weather.json"
unavailable() {
    jq -nc --arg description "$1" '{temp:"--",description:$description}'
}
if ! jq -e '(.latitude|type)=="number" and (.longitude|type)=="number" and (.city|type)=="string"' "$config" >/dev/null 2>&1; then
    unavailable 'Ob-havo sozlanmagan'
    exit 0
fi
latitude=$(jq -r '.latitude' "$config")
longitude=$(jq -r '.longitude' "$config")
city=$(jq -r '.city' "$config")
if ! response=$(curl --fail --silent --show-error --max-time 12 --get \
    https://api.open-meteo.com/v1/forecast \
    --data-urlencode "latitude=$latitude" --data-urlencode "longitude=$longitude" \
    --data 'current=temperature_2m,weather_code' --data 'timezone=auto' 2>/dev/null); then
    unavailable "$city: aloqa yo'q"
    exit 0
fi
if ! result=$(jq -ce --arg city "$city" '
    (.current.temperature_2m | numbers | round | tostring) as $temp |
    (.current.weather_code | numbers) as $code |
    (if $code == 0 then "Ochiq"
     elif $code <= 2 then "Qisman bulutli"
     elif $code == 3 then "Bulutli"
     elif $code == 45 or $code == 48 then "Tuman"
     elif $code >= 51 and $code <= 57 then "Mayda yomgir"
     elif $code >= 61 and $code <= 67 then "Yomgir"
     elif $code >= 71 and $code <= 77 then "Qor"
     elif $code >= 80 and $code <= 82 then "Jala"
     elif $code == 85 or $code == 86 then "Qor"
     elif $code >= 95 then "Momaqaldiroq"
     else "Ob-havo" end) as $description |
    {temp:$temp,description:($city + "\n" + $description)}' <<< "$response"); then
    unavailable "$city: malumot yo'q"
    exit 0
fi
printf '%s\n' "$result"
