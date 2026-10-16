#!/bin/bash
# Set WEATHERAPI_KEY and WEATHER_CITY locally before enabling the weather window.
if [[ -z ${WEATHERAPI_KEY:-} || -z ${WEATHER_CITY:-} ]]; then
    printf 'WEATHER_TEMP=--\nWEATHER_DESC=Weather not configured\n'
    exit 0
fi
response=$(curl --fail --silent --show-error --max-time 10 --get 'https://api.weatherapi.com/v1/current.json' --data-urlencode "key=$WEATHERAPI_KEY" --data-urlencode "q=$WEATHER_CITY" --data 'aqi=no') || exit 1
jq -r 'if .current then "WEATHER_TEMP=\(.current.temp_c | round)\nWEATHER_DESC=\(.current.condition.text)" else error("Weather data unavailable") end' <<< "$response"
