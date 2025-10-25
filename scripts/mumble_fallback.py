#!/usr/bin/env python3
import os
import shutil
import socket
import subprocess
import time
import signal
import sys

# --- Konfiguration -----------------------------------------------------------
USERNAME = "user01"   # Mumble-Benutzername anpassen
PASSWORD = ""         # optional, sonst "" lassen
SERVERS = [           # Reihenfolge = Prioritaet (oben = bevorzugt)
    ("10.30.5.10", 64738),  # pi-node-1
    ("10.30.5.20", 64738),  # pi-node-2
    ("10.30.5.30", 64738),  # pi-node-3
]
CHECK_TIMEOUT = 1.0   # Sek. fuer Portcheck
RETRY_DOWN    = 3.0   # Sek. warten, wenn kein Server erreichbar
RECHECK_PRI   = 15.0  # Sek. Intervall, wenn auf Sekundaer, um Primary zu pruefen
RUN_ON_DESKTOP = True # setzt DISPLAY/XDG/DBUS fuer GUI-Client
MUMBLE_BIN = shutil.which("mumble") or "/usr/bin/mumble"
# -----------------------------------------------------------------------------

def log(msg: str):
    print(msg, flush=True)

def is_up(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=CHECK_TIMEOUT):
            return True
    except OSError:
        return False

def pick_server():
    for host, port in SERVERS:
        if is_up(host, port):
            return host, port
    return None, None

def build_url(user: str, host: str, port: int, pw: str = "") -> str:
    # mumble://[user[:pass]@]host[:port]
    auth = user if not pw else f"{user}:{pw}"
    auth = (auth + "@") if auth else ""
    return f"mumble://{auth}{host}:{port}"

def launch_client(host: str, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    if RUN_ON_DESKTOP:
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["XDG_RUNTIME_DIR"] = env.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        env["DBUS_SESSION_BUS_ADDRESS"] = env.get(
            "DBUS_SESSION_BUS_ADDRESS",
            f"unix:path={env['XDG_RUNTIME_DIR']}/bus"
        )
    url = build_url(USERNAME, host, port, PASSWORD)
    log(f"Starte Mumble-Client: {url}")
    return subprocess.Popen([MUMBLE_BIN, url], env=env)

def stop_client(proc: subprocess.Popen | None):
    """Versuche den laufenden Mumble-Prozess sauber zu beenden, notfalls hart killen."""
    if proc is None:
        return
    try:
        if proc.poll() is None:
            log("Beende laufenden Mumble-Client (SIGTERM)...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log("Prozess reagiert nicht → hartes Kill (SIGKILL).")
                proc.kill()
                proc.wait(timeout=3)
    except Exception as e:
        log(f"Fehler beim Beenden: {e}")

def main():
    log("Mumble Fallback-Launcher gestartet.")
    preferred = SERVERS[0]
    current: tuple[str, int] | None = None
    proc: subprocess.Popen | None = None

    # Sanfte Startverzoegerung, damit Netzwerk/Audio bereit sind
    time.sleep(2)

    try:
        while True:
            # Falls kein Client laeuft (neu starten oder nach Absturz)
            if proc is None or proc.poll() is not None:
                stop_client(proc)  # sicherheitshalber
                host, port = pick_server()
                if not host:
                    log("Kein Server erreichbar. Warte...")
                    time.sleep(RETRY_DOWN)
                    continue
                log(f"Verbinde zu {host}:{port}")
                current = (host, port)
                proc = launch_client(host, port)
                # kleine Pause, damit GUI/Verbindung initialisieren kann
                time.sleep(2)

            # Rueckwechsel auf Primary, falls wir gerade auf Sekundaer sind
            if current != preferred and is_up(*preferred):
                log("Primary ist wieder online → Wechsel zurueck auf Primary.")
                stop_client(proc)
                proc = None
                current = None
                continue

            # Wenn aktueller Server weg ist, sofort umschalten
            if current and not is_up(*current):
                log(f"Aktueller Server {current[0]} nicht erreichbar → Umschalten.")
                stop_client(proc)
                proc = None
                current = None
                continue

            # Schlafintervall: schneller, wenn wir auf Primary sind; gemuetlicher auf Sekundaer
            time.sleep(3 if current == preferred else RECHECK_PRI)

    except KeyboardInterrupt:
        log("Beendet (KeyboardInterrupt).")
    finally:
        stop_client(proc)

if __name__ == "__main__":
    sys.exit(main() or 0)
