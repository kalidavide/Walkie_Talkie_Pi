#!/usr/bin/env python3
import os
import RPi.GPIO as GPIO
import time
import subprocess

# Konfiguration aus env-Datei laden
env_path = "/etc/walkietalkie/ptt.env"
config = {}
with open(env_path) as f:
    for line in f:
        if "=" in line:
            k,v = line.strip().split("=",1)
            config[k] = v

PIN = int(config["GPIO_PIN"])
CARD_INDEX = config["ALSA_CARD_INDEX"]
CONTROL = config["ALSA_CAPTURE_CONTROL"]
DEBOUNCE = int(config["DEBOUNCE_MS"]) / 1000.0

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_state = GPIO.input(PIN)
 
try:
    while True:
        state = GPIO.input(PIN)
        if state != last_state:
            time.sleep(DEBOUNCE)
            if state == GPIO.LOW:  # Taste gedrückt
                subprocess.run(["amixer","-c",CARD_INDEX,"sset",CONTROL,"cap"])
            else:  # Taste losgelassen
                subprocess.run(["amixer","-c",CARD_INDEX,"sset",CONTROL,"nocap"])
            last_state = state
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()
