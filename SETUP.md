# 🔧 Installationsanleitung

Detaillierte Schritte zum Einrichten des Kopfverfolgungssystems auf verschiedenen Systemen.

## Windows

### Voraussetzungen
- Windows 10 oder neuer
- Python 3.8+ ([Download](https://www.python.org))

### Schritt-für-Schritt

#### 1. Python installieren

1. Gehe zu [python.org](https://www.python.org/downloads/)
2. Lade **Python 3.11** herunter
3. Starte den Installer
4. ✅ **WICHTIG**: Aktiviere "Add Python to PATH"
5. Klicke "Install Now"

**Überprüfung:**
```cmd
python --version
pip --version
```

#### 2. Repository klonen

```cmd
git clone https://github.com/dein-repo/head-tracking.git
cd head-tracking
```

Oder: Manuell ZIP herunterladen und entpacken.

#### 3. Virtual Environment erstellen

```cmd
python -m venv venv
venv\Scripts\activate
```

Du solltest jetzt `(venv)` am Anfang sehen:
```cmd
(venv) C:\Users\YourName\head-tracking>
```

#### 4. Abhängigkeiten installieren

```cmd
pip install -r requirements.txt
```

Dies installiert:
- `opencv-python` - Bildverarbeitung
- `numpy` - Numerische Berechnungen
- `pyvirtualcam` - Virtuelle Kamera

**Überprüfung:**
```cmd
python -c "import cv2, numpy, pyvirtualcam; print('OK')"
```

#### 5. Virtuelle Kamera installieren

Für Windows benötigst du **OBS Virtual Camera**:

1. Lade [OBS Studio](https://obsproject.com/) herunter
2. Starte den Installer
3. Wähle "Full Installation"
4. Nach Installation: Starte OBS
5. Tools → Start Virtual Camera

Alternativ: **VirtualCam** oder **ManyCam**

#### 6. Programm starten

```cmd
python head_tracking.py
```

---

## macOS

### Voraussetzungen
- macOS 10.14+
- Xcode Command Line Tools
- Python 3.8+ (über Homebrew)

### Installation

#### 1. Homebrew installieren (falls nicht vorhanden)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Python und Dependencies

```bash
brew install python3
brew install opencv
```

#### 3. Repository klonen

```bash
git clone https://github.com/dein-repo/head-tracking.git
cd head-tracking
```

#### 4. Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 5. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

#### 6. Virtuelle Kamera

macOS braucht kein externes Tool. `pyvirtualcam` erstellt die Kamera automatisch.

**Überprüfung:**
```bash
system_profiler SPCameraDataType
```

#### 7. Starten

```bash
python head_tracking.py
```

---

## Linux (Ubuntu/Debian)

### Voraussetzungen
- Ubuntu 18.04+
- Python 3.8+

### Installation

#### 1. System aktualisieren

```bash
sudo apt update
sudo apt upgrade
```

#### 2. Dependencies installieren

```bash
sudo apt install python3-pip python3-venv
sudo apt install libopencv-dev python3-opencv
sudo apt install libsm6 libxext6  # Für OpenCV GUI
```

#### 3. Repository klonen

```bash
git clone https://github.com/dein-repo/head-tracking.git
cd head-tracking
```

#### 4. Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 5. Abhängigkeiten

```bash
pip install -r requirements.txt
```

#### 6. Virtuelle Kamera (v4l2loopback)

```bash
# v4l2loopback installieren
sudo apt install v4l2loopback-dkms v4l2loopback-utils

# Laden
sudo modprobe v4l2loopback devices=1 video_nr=99

# Automatisch beim Booten laden
echo "v4l2loopback devices=1 video_nr=99" | sudo tee /etc/modprobe.d/v4l2loopback.conf
```

#### 7. Kamera-Berechtigungen

```bash
# Aktuelle Benutzer zur video-Gruppe hinzufügen
sudo usermod -aG video $USER

# Terminal neustarten oder:
newgrp video
```

#### 8. Starten

```bash
python3 head_tracking.py
```

---

## Docker (Optional)

Falls du Docker installed hast:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    libopencv-dev python3-opencv \
    libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY head_tracking.py .

CMD ["python", "head_tracking.py"]
```

Starten:
```bash
docker build -t head-tracking .
docker run --device /dev/video0 head-tracking
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'cv2'"

```bash
# Virtual Environment aktiviert?
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Neu installieren
pip install --upgrade opencv-python
```

### "Cannot open camera"

```bash
# Linux: Kamera-Berechtigungen überprüfen
ls -la /dev/video*

# Windows: Kamera in Einstellungen aktivieren
# Einstellungen → Datenschutz → Kamera → Zugriff erlauben

# macOS: Terminal-Zugriff auf Kamera in Sicherheit erlauben
```

### "pyvirtualcam: No camera device found"

**Linux:**
```bash
# v4l2loopback prüfen
modprobe -l | grep v4l2loopback
lsmod | grep v4l2

# Neu laden:
sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback devices=1
```

**Windows/macOS:**
Siehe Abschnitte oben für OBS Virtual Camera Setup.

### Performance-Probleme

```bash
# CPU-Last checken
top      # Linux/macOS
taskmgr  # Windows

# Auflösung in Code reduzieren:
width = 1280   # statt 1920
height = 720   # statt 1080
```

---

## Nächste Schritte

✅ Installiert? Dann:

1. Lese die [README.md](README.md)
2. Führe das Programm aus
3. Drücke 'v' um Erkennungen zu sehen
4. Lese [DOKUMENTATION.md](DOKUMENTATION.md) für technische Details

🎉 Viel Spaß!