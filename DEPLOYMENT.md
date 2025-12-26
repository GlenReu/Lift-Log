# Raspberry Pi + Tailscale Deployment Guide

Komplette Anleitung zum Deployment der Lift Log App auf Raspberry Pi mit Remote-Zugriff via Tailscale.

---

## 📋 Voraussetzungen

- Raspberry Pi (3B+ oder neuer empfohlen)
- MicroSD-Karte (min. 16GB)
- Stromversorgung für Pi
- WLAN/Ethernet-Verbindung
- iPhone mit Tailscale App

---

## 🔧 Phase 1: Raspberry Pi einrichten

### 1.1 Raspberry Pi OS installieren

1. **Raspberry Pi Imager** herunterladen:
   - https://www.raspberrypi.com/software/

2. **OS flashen:**
   - Imager öffnen
   - OS auswählen: "Raspberry Pi OS Lite (64-bit)" (ohne Desktop, spart Ressourcen)
   - SD-Karte auswählen
   - ⚙️ Einstellungen öffnen:
     - Hostname: `liftlog` (oder dein Wunschname)
     - SSH aktivieren (wichtig!)
     - Username: `pi`
     - Passwort: [dein sicheres Passwort]
     - WLAN konfigurieren (SSID + Passwort)
     - Zeitzone: Europe/Zurich
   - "Schreiben" klicken

3. **Pi starten:**
   - SD-Karte in Pi einlegen
   - Strom anschließen
   - 1-2 Minuten warten

### 1.2 Auf Pi verbinden (vom Mac)

```bash
# Pi IP-Adresse finden (eine von diesen sollte funktionieren)
ssh pi@liftlog.local
# ODER über IP (Router checken oder nmap verwenden)
ssh pi@192.168.1.XXX

# Passwort eingeben
```

**Falls "liftlog.local" nicht funktioniert:**
```bash
# Router-Interface öffnen (meist http://192.168.1.1)
# Nach "liftlog" oder "raspberrypi" suchen
# Oder IP-Scanner nutzen:
brew install nmap
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry"
```

### 1.3 Pi aktualisieren

```bash
# System updaten
sudo apt update && sudo apt upgrade -y

# Python und Tools installieren
sudo apt install -y python3-pip python3-venv git
```

---

## 🚀 Phase 2: Lift Log App deployen

### 2.1 Projekt übertragen

**Option A: Via Git (empfohlen wenn du Git nutzt)**
```bash
# Auf dem Pi
cd ~
git clone [DEINE-GIT-URL]
cd Tracker
```

**Option B: Via SCP (vom Mac aus)**
```bash
# Auf deinem Mac (im Tracker-Ordner)
cd /Users/glen/Documents/Python/Tracker

# Dateien zum Pi kopieren
scp -r . pi@liftlog.local:~/Tracker/

# Dann auf Pi einloggen
ssh pi@liftlog.local
cd ~/Tracker
```

### 2.2 Python-Umgebung einrichten

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Requirements installieren
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 App testen

```bash
# Streamlit starten (Test)
streamlit run app.py --server.port=8501 --server.address=0.0.0.0

# Im Browser auf deinem Mac öffnen:
# http://liftlog.local:8501
# oder http://[PI-IP]:8501
```

**Funktioniert? → Ctrl+C zum Beenden und weiter zu Phase 3**

---

## 🌐 Phase 3: Tailscale einrichten

### 3.1 Tailscale Account erstellen

1. Browser öffnen: https://tailscale.com
2. "Get Started" → Mit Google/GitHub/Email anmelden
3. Account erstellen (kostenlos)

### 3.2 Tailscale auf Raspberry Pi installieren

```bash
# Auf dem Pi
curl -fsSL https://tailscale.com/install.sh | sh

# Tailscale starten
sudo tailscale up

# Output zeigt einen Link, z.B.:
# To authenticate, visit: https://login.tailscale.com/a/abc123xyz
```

**Link im Browser öffnen und Gerät autorisieren**

### 3.3 Tailscale IP herausfinden

```bash
# Auf dem Pi
tailscale ip -4

# Gibt Tailscale-IP aus, z.B.: 100.64.1.2
# Diese IP notieren!
```

### 3.4 Tailscale auf iPhone installieren

1. App Store → "Tailscale" suchen und installieren
2. App öffnen → Mit gleichem Account anmelden
3. VPN-Profil erlauben
4. Pi sollte in der Geräteliste erscheinen ✅

---

## ⚙️ Phase 4: Streamlit als Service einrichten

Damit die App automatisch beim Boot startet und immer läuft:

### 4.1 Service-Datei erstellen

```bash
# Auf dem Pi
sudo nano /etc/systemd/system/liftlog.service
```

**Folgenden Inhalt einfügen:**
```ini
[Unit]
Description=Lift Log Streamlit App
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Tracker
Environment="PATH=/home/pi/Tracker/venv/bin"
ExecStart=/home/pi/Tracker/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Speichern:** Ctrl+O → Enter → Ctrl+X

### 4.2 Service aktivieren

```bash
# Service neu laden
sudo systemctl daemon-reload

# Service aktivieren (startet beim Boot)
sudo systemctl enable liftlog

# Service jetzt starten
sudo systemctl start liftlog

# Status prüfen
sudo systemctl status liftlog

# Sollte "active (running)" zeigen ✅
```

### 4.3 Logs ansehen (bei Problemen)

```bash
# Live-Logs
sudo journalctl -u liftlog -f

# Letzte 50 Zeilen
sudo journalctl -u liftlog -n 50
```

---

## 📱 Phase 5: Vom iPhone zugreifen

### 5.1 Im WLAN (zu Hause)

```
http://liftlog.local:8501
oder
http://[PI-LOCAL-IP]:8501
```

### 5.2 Remote (im Gym)

1. **Tailscale auf iPhone aktivieren** (VPN-Toggle in der App)
2. **Browser öffnen:**
   ```
   http://100.64.1.2:8501
   ```
   (Deine notierte Tailscale-IP verwenden!)

3. **Lesezeichen speichern** für schnellen Zugriff

---

## 🔧 Nützliche Befehle

### Service-Management
```bash
# Service stoppen
sudo systemctl stop liftlog

# Service neu starten
sudo systemctl restart liftlog

# Service deaktivieren
sudo systemctl disable liftlog

# Logs ansehen
sudo journalctl -u liftlog -f
```

### App aktualisieren
```bash
# Auf dem Pi
cd ~/Tracker

# Git-Update (falls Git genutzt)
git pull

# Oder Dateien via SCP übertragen (vom Mac)
# scp app.py pi@liftlog.local:~/Tracker/

# Service neu starten
sudo systemctl restart liftlog
```

### Tailscale-Management
```bash
# Status
tailscale status

# IP-Adresse
tailscale ip -4

# Neu verbinden
sudo tailscale up

# Trennen
sudo tailscale down
```

---

## 🐛 Troubleshooting

### Problem: Pi nicht erreichbar via SSH

**Lösung 1:** IP direkt verwenden
```bash
# Router-Interface öffnen, Pi-IP finden
ssh pi@192.168.1.XXX
```

**Lösung 2:** mDNS installieren (auf Mac)
```bash
# Avahi auf Pi installieren
ssh pi@[IP]
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

### Problem: Streamlit startet nicht

```bash
# Logs prüfen
sudo journalctl -u liftlog -n 100

# Manuell testen
cd ~/Tracker
source venv/bin/activate
streamlit run app.py
```

Häufige Fehler:
- **ModuleNotFoundError:** `pip install -r requirements.txt` erneut ausführen
- **Permission denied:** Pfade in Service-Datei prüfen
- **Port already in use:** `sudo lsof -i :8501` und Prozess killen

### Problem: Tailscale funktioniert nicht

```bash
# Status prüfen
sudo tailscale status

# Neu authentifizieren
sudo tailscale up

# Logs prüfen
sudo journalctl -u tailscaled -n 50
```

### Problem: App lädt auf iPhone nicht

1. **Tailscale VPN aktiv?** (Toggle in App prüfen)
2. **Richtige IP?** `tailscale ip -4` auf Pi prüfen
3. **Service läuft?** `sudo systemctl status liftlog` auf Pi prüfen
4. **Browser-Cache leeren** auf iPhone

---

## 🔒 Sicherheit

### Empfohlene Maßnahmen

1. **Firewall aktivieren**
```bash
sudo apt install ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8501/tcp  # Streamlit (nur lokal nötig)
sudo ufw enable
```

2. **SSH-Key statt Passwort** (optional aber empfohlen)
```bash
# Auf dem Mac
ssh-keygen -t ed25519 -C "pi-liftlog"

# Public Key zum Pi kopieren
ssh-copy-id pi@liftlog.local

# Passwort-Login deaktivieren (auf Pi)
sudo nano /etc/ssh/sshd_config
# Zeile ändern: PasswordAuthentication no
sudo systemctl restart ssh
```

3. **Regelmäßige Updates**
```bash
# Auf dem Pi (monatlich)
sudo apt update && sudo apt upgrade -y
```

---

## 📊 Performance-Tipps

### Für ältere Pis (3B/3B+)

Falls die App langsam ist:

```bash
# Swap erhöhen
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=1024 (statt 100)
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Datenbank-Backups

```bash
# Backup-Script erstellen
nano ~/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/Tracker/training.db ~/backups/training_$DATE.db
# Alte Backups löschen (älter als 30 Tage)
find ~/backups -name "training_*.db" -mtime +30 -delete
```

```bash
chmod +x ~/backup.sh
mkdir ~/backups

# Cronjob (täglich um 3 Uhr)
crontab -e
# Zeile hinzufügen:
0 3 * * * /home/pi/backup.sh
```

---

## ✅ Fertig!

Deine App läuft jetzt:
- ✅ 24/7 auf dem Raspberry Pi
- ✅ Zugriff zu Hause via `http://liftlog.local:8501`
- ✅ Zugriff im Gym via Tailscale IP
- ✅ Startet automatisch nach Neustart
- ✅ Daten bleiben lokal bei dir

**Test:** Geh ins Gym, Tailscale aktivieren, App öffnen, trainieren! 💪

Bei Fragen oder Problemen: Logs prüfen mit `sudo journalctl -u liftlog -f`
