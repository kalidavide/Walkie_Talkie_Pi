# Walkie-Talkie Pi
*Developed by Davide Bossi (TEKO Zürich, 2025)*  

---

## Overview

**Walkie-Talkie Pi** is a decentralized, push-to-talk voice communication system built entirely on open-source software and low-cost Raspberry Pi hardware.  
Each node combines a Raspberry Pi Zero 2 WH with a WM8960 Audio HAT and connects to others through a self-organizing WLAN mesh network using **batman-adv**.  
This setup enables local, encrypted voice communication **without any central router or Internet access**.  

The project was created as part of a diploma thesis at TEKO Zürich, demonstrating that fully autonomous digital voice systems can be realized with simple components and Linux-based software.

---

## Key Features

- 🗣️ Encrypted voice communication via **Mumble VoIP**
- 🔁 Automatic **server fallback and reconnection**
- 🔊 Hardware-based **push-to-talk (PTT)** button
- 📶 Layer-2 **mesh networking** with batman-adv
- ⚙️ Fully automated **systemd-based startup**
- 🔋 Runs on battery-powered Raspberry Pi Zero 2 WH
- 🌐 Operates completely offline

---

## How It Works

Each node runs both a **Mumble Server** and a **Mumble Client**.  
At startup, the node joins the mesh network, launches the VoIP services, and connects automatically to the primary server.  
If that server goes offline, a Python fallback script reconnects the client to the next reachable node.  
The PTT service controls audio capture at the ALSA layer through PulseAudio: the microphone is only active while the hardware button is pressed.

---

## Hardware Setup

| Component | Purpose |
|------------|----------|
| **Raspberry Pi Zero 2 WH** | Core single-board computer |
| **WM8960 Audio HAT** | Integrated sound card, microphone & speaker |
| **USB Wi-Fi Adapter** | Dedicated mesh interface (Ad-Hoc / 802.11s mode) |
| **USB On-The-Go Adapter (USB OTG)** | Adapter for Wi-Fi |
| **Micro SD Card (32–128 GB)** | System storage |
| **Power Bank ≥ 2 A output** | Portable power supply |
| **PTT Button (GPIO 17)** | Activates microphone while pressed |

---

## Software Stack

| Layer | Component | Description |
|--------|------------|-------------|
| **Application** | Mumble Client + Server | Encrypted VoIP communication |
| **Audio** | PulseAudio → ALSA | Sound routing and device control |
| **Mesh Networking** | batman-adv | Layer-2 routing between nodes |
| **Control** | Python Scripts + systemd Units | PTT control, fallback, autostart |
| **Time Sync** | chrony | Local NTP across mesh nodes |
| **OS** | Raspberry Pi OS (32-bit) | Base operating system |

---

## Network Concept

- **Mesh Network (bat0 on wlan1):** 10.30.5.0/24
  - pi-node-1 → 10.30.5.10
  - pi-node-2 → 10.30.5.20
  - pi-node-3 → 10.30.5.30
- **Optional Management Network (wlan0):** 172.30.5.0/24 (development only)

---

## System Architecture

![System Architecture](images/system_architecture.png)

This diagram shows the full system architecture, including hardware and software components used to build the VoIP mesh network.

---

## Configuration Files

| File | Purpose |
|------|----------|
| `/etc/mumble-server.ini` | Local Mumble Server settings |
| `/usr/local/bin/ptt.py` | GPIO PTT script |
| `/usr/local/bin/mumble_fallback.py` | Server failover logic |
| `/usr/local/bin/mesh-setup.sh` | Mesh initialization script |
| `/etc/systemd/system/*.service` | Autostart unit files |
| `/etc/chrony/chrony.conf` | Local time sync |

---

## Getting Started

This guide walks you through preparing the complete system. Where configuration is required, refer to the **sample files in this repository** instead of copying inline snippets.

---

###
For a complete, step‑by‑step explanation of the installation, configuration, and testing process — including screenshots, command examples, and troubleshooting — please refer to the **Diploma Thesis (PDF)** included in this repository.

The detailed documentation describes:
- Preparing and flashing the microSD card using Raspberry Pi Imager  
- Initial OS setup, SSH/VNC access, and static IP assignment  
- Installing and verifying the WM8960 Audio HAT  
- Integrating the Push‑to‑Talk function and Mumble VoIP services  
- Setting up Autostart, Fallback, and Mesh Networking  
- Time synchronisation with Chrony and system validation tests  

📄 **Reference:** see `/docs/Walkie_Talkie_Pi_Zero_Final.pdf` (Diploma Thesis)  
This document contains the full procedural guide, configuration screenshots, and complete testing documentation complementing this README.

---

### 0. Prerequisites (workstation & tools)

- A computer with a **microSD card reader** (or adapter)
- **Raspberry Pi Imager** installed on the workstation  
  - Download from the official site or your OS package manager  
- (Recommended) **RealVNC Viewer** on the workstation for GUI access to the Pi after first boot
- A stable power source for the Pi
- Optional: your Wi-Fi SSID/Passphrase for development (for the Management WLAN)

---

### 1. Prepare the microSD (Raspberry Pi Imager)

1. Insert the microSD into your workstation and start **Raspberry Pi Imager**.  
2. Select:
   - **Device:** Raspberry Pi Zero 2 W
   - **OS:** *Raspberry Pi OS (32-bit with Desktop)*
   - **Storage:** your microSD (up to 256 GB)
3. Click **Next** → **OS customisation**:
   - Set **hostname** (e.g. `pi-node-1`)
   - Create your **user & password**
   - Optionally preconfigure **Wi-Fi** (Management WLAN for development only)
   - **Enable SSH** (password auth is fine in a lab network)
   - Optional comfort settings (eject media after write, sound on completion)
4. Confirm the overwrite warning and start writing.

---

### 2. First boot & remote access

1. Insert the microSD into the **Raspberry Pi Zero 2 WH** and power on.  
   The very first boot may take a bit longer.
2. From your workstation:
   - **SSH**: `ssh <user>@pi-node-1.local`
   - **VNC** (optional, for GUI): enable via `raspi-config` or the Imager preset

> For a predictable lab: assign a **static IPv4** during development (NetworkManager). Use the approach described in the thesis.

---

### 3. System update

Keep the base OS current:

```bash
sudo apt update && sudo apt upgrade -y
```

If prompted to replace default config files by the maintainer versions, choose the maintainer defaults unless you know you changed those files intentionally.

---

### 4. Enable the WM8960 Audio HAT

1. **Power off** the Pi before mounting the HAT. Attach the speakers to the HAT terminals.  
2. Boot the Pi.
3. Enable the device-tree overlay and I²C/I²S, with editing the config.txt file.
4. Reboot the Pi

> Edit `/boot/firmware/config.txt`:  
```bash
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=audio=off
dtoverlay=wm8960-soundcard
```
> After reboot, verify devices: `aplay -l`, `arecord -l`; adjust levels in `alsamixer`.

**Useful checks**
- `dmesg | grep -i wm8960` — driver messages  
- `cat /proc/asound/cards` — card listing should show the WM8960

---

### 5. Install core software

Install the software stack (mesh tools, VoIP, audio utils, time sync, Python runtime). Package names follow Raspberry Pi OS Bookworm repositories.
```bash
sudo apt install -y batctl mumble mumble-server alsa-utils pulseaudio chrony python3
```

---

### 6. Push-to-Talk (PTT)

PTT keeps the microphone **muted by default** and only enables capture while the hardware button is pressed.

- Environment sample (GPIO & mixer control): **`/config/ptt.env`** → copy to `/etc/walkietalkie/ptt.env`
- Controller script: **`/scripts/ptt.py`** → copy to `/usr/local/bin/ptt.py`
- Service unit: **`/systemd/ptt.service`** → copy to `/etc/systemd/system/ptt.service`

> The controller toggles ALSA capture via PulseAudio. If you use a different GPIO or control name, set them in the env file.
> Do not forget to enable the ptt.service with:```bash sudo systemctl enable --now ptt.service```

---

### 7. Mumble (VoIP): server, client and autostart, fallback

- Install **server + client**. Run the **Audio Wizard** once via VNC.  
- Optional server settings (welcome text, user limit): **`/config/mumble-server.ini`**  
- **Autostart (optional helper)**: **`/scripts/mumble-autostart.sh`**  
- **Fallback controller** (keeps client on the first reachable server): **`/scripts/mumble_fallback.py`**  
- **Service unit**: **`/systemd/mumble-client.service`**

> The fallback script expects a server list (prefer mesh IPs on `bat0`). On first connect to a new IP, accept the certificate warning once via VNC.

---

### 8. Mesh networking (batman-adv)

The mesh runs on a **dedicated Wi-Fi adapter** (e.g. `wlan1`) in **Ad-Hoc** mode and is bridged into **batman-adv** (Layer 2) as `bat0`. Each node gets a **static IP on `bat0`** (e.g. `10.30.5.10/24`, `10.30.5.20/24`, `10.30.5.30/24`).

#### Steps

1. **Unmanage `wlan1`** in NetworkManager so scripts can control it.  
   (Create a small NM keyfile override as described in `disable-wlan1.conf`.)
2. Use the provided **bring-up script** and **systemd unit** to initialise the mesh:
   - Script: **`/scripts/mesh-setup.sh`**  
   - Unit: **`/systemd/mesh.service`**
3. Optionally maintain readable mesh hostnames:  
   - Sample: **`/config/bat-hosts`** → copy to `/etc/bat-hosts`

> The script takes care of setting the mode, ESSID, channel, loading `batman-adv`, and assigning the IP to `bat0`. Adjust per node IPs before enabling the unit.

**Diagnostics**
- Neighbors: `sudo batctl n`  
- Mesh ping: `sudo batctl ping <bat0-IP>`  
- Path: `sudo batctl tr <bat0-IP>`


---

### 9. Local time sync (Chrony)

- Make **`pi-node-1`** the local mesh time source (stratum 10).  
- Point the other nodes to it.

Use the samples:
- **Server**: `/config/chrony/chrony.server.conf` on `pi-node-1`  
- **Client**: `/config/chrony/chrony.client.conf` on the other nodes

Verify with `chronyc tracking` and `chronyc sources -v`.

---

### 10. Enable the services

Reload units and enable the core services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mesh.service
sudo systemctl enable --now ptt.service
systemctl --user enable --now mumble-client.service
```

If you also run a local server on each node, ensure `mumble-server.service` is enabled.

---

### 11. Sanity checks

- **Mesh**  
  `sudo batctl n` — neighbors present  
  `sudo batctl ping 10.30.5.20` — ping a peer over the mesh  
  `sudo batctl tr 10.30.5.30` — see the path to another node
- **Audio**  
  `arecord -l`, `aplay -l` — devices visible  
  `alsamixer` — PCM and capture not muted; adjust levels as required
- **PTT**  
  Press the button and watch capture toggle; e.g.  
  `watch -n 0.3 "amixer sget Capture | grep -E '\[(on|off)\]'"`  
- **Services**  
  `systemctl status mesh.service ptt.service mumble-client.service`  
- **Time**  
  `chronyc tracking` — consistent across nodes

---

### 12. Replicate for all nodes

Repeat the steps for **`pi-node-2`** and **`pi-node-3`**:
- Unique hostnames and **node-specific `bat0` IPs**
- Accept certificates once per new server IP if prompted
- Keep Management WLAN disabled in field mode; operate on mesh only

---

## Operating the System

1. Power on the Pi.  
2. Mesh initializes automatically, then VoIP client connects to primary server.  
3. Press the PTT button to transmit voice (only active while pressed).  
4. If the primary server goes down, the client switches to a backup node.  
5. When the primary returns, it reconnects automatically.

---

## Troubleshooting & Diagnostics

| Area | Command | Purpose |
|-------|----------|----------|
| Mesh | `sudo batctl n` | Show neighbors |
| Mesh | `sudo batctl ping <IP>` | Ping over mesh |
| Audio | `arecord -l`, `aplay -l` | List devices |
| Audio | `alsamixer` | Adjust levels |
| Services | `systemctl status <service>` | Check service health |
| Time | `chronyc tracking` | Verify sync |

---

## Known Issues

- Limited WLAN range (~60 m line of sight).  
- Slight latency when reconnecting after fallback.  
- Not optimized for high traffic or more than 5 nodes.  
- Powerbank auto-shutdown must be disabled.

---

## Future Improvements

- Add LoRa or other long-range modules.  
- Integrate status display (OLED / TFT).  
- Design mechanical enclosure for field use.  
- Expand mesh to > 10 nodes for stress testing.  
- Harden system for outdoor operation.

---

## License

This project is licensed under the **MIT License**

---

## Acknowledgments

Special thanks to  
**TEKO Zürich / Swiss Technical College**, mentors, and everyone who supported the project during development.
