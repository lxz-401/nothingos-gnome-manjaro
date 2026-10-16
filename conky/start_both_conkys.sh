#!/bin/sh
conky -c "$HOME/.config/conky/nothing-phone-conky.conf" &
exec conky -c "$HOME/.config/conky/spotify_nolua.conkyrc"
