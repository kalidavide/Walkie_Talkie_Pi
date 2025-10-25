#!/bin/bash
set -euo pipefail

# Session-Variablen setzen (wichtig für GUI über VNC)
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=${XDG_RUNTIME_DIR}/bus

# Kurze Pause, bis Netzwerk und Audio bereit sind
sleep 10

# Python-Fallback starten
exec /home/user01/mumble_fallback.py
