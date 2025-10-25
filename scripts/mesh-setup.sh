# create file with: sudo nano /usr/local/bin/mesh-setup.sh
# After saving, make the script executable: sudo chmod +x /usr/local/bin/mesh-setup.sh


#!/bin/bash

# WLAN-Interface in Ad-hoc Modus versetzen
ip link set wlan1 down
iwconfig wlan1 mode ad-hoc
iwconfig wlan1 essid WalkieMesh
iwconfig wlan1 channel 1
ip link set wlan1 up

# batman-adv aktivieren
modprobe batman-adv
batctl if add wlan1
ip link set up dev bat0

# statische IP-Adresse setzen
# Hinweis: neuer Adressbereich!
ip addr add 10.30.5.10/24 dev bat0
