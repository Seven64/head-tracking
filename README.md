# 🎥 KI-Kopfverfolgung mit virtueller Kamera

Ein intelligentes Kopfverfolgungssystem, das Ihr Gesicht erkennt und eine virtuelle Kamera automatisch zoomt und ausrichtet. Perfekt für Video-Calls, Streaming und kreative Anwendungen!

## 🎬 Demo-Video / Showdown

<video width="560" height="315" controls>
  <source src="videos/VCbhYCzgBF.mp4" type="video/mp4">
  Dein Browser unterstützt keine Video-Wiedergabe.
</video>


## ✨ Features

- **🎯 Automatische Gesichtserkennung** - Erkennt Ihr Gesicht in Echtzeit
- **🔍 Dynamischer Zoom** - Passt automatisch den Zoomfaktor an
- **📐 Intelligente Ausrichtung (Pan)** - Folgt dem Kopf sanft und ruckelfrei
- **🎬 Virtuelle Kamera** - Funktioniert mit Zoom, Teams, OBS und mehr
- **⚙️ Konfigurierbar** - Alle Parameter leicht anpassbar
- **✅ PEP 8 konform** - Sauberer, professioneller Code

## 🖥️ Systemanforderungen

- **Python**: 3.8+
- **Betriebssystem**: Windows, macOS, Linux
- **Hardware**: 
  - Webcam / integrierte Kamera
  - Mindestens 4 GB RAM
  - Multi-Core Prozessor empfohlen

## 📦 Installation

### Schritt 1: Python und pip installieren

Stelle sicher, dass Python 3.8+ installiert ist:
```bash
python --version
```

### Schritt 2: Repository klonen oder Dateien herunterladen

```bash
git clone https://github.com/dein-repo/head-tracking.git
cd head-tracking
```

### Schritt 3: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

**Benötigte Pakete:**
- `opencv-python` - Gesichtserkennung und Bildverarbeitung
- `numpy` - Numerische Berechnungen
- `pyvirtualcam` - Virtuelle Kamera

### Schritt 4: Programm ausführen

```bash
python head_tracking.py
```

## 🚀 Verwendung

### Grundlegende Bedienung

Das Programm startet automatisch mit Ihrer Standard-Webcam:

| Taste | Funktion |
|-------|----------|
| **V** | Visualisierung umschalten (zeigt erkannte Gesichter) |
| **Q** | Programm beenden |

### Beispiel-Session

```
$ python head_tracking.py
Virtual camera: OBS Camera
Press 'v' to toggle visualization
Press 'q' to quit
```

Das Programm wird nun:
1. ✅ Ihr Gesicht erkennen
2. ✅ Automatisch zoomen und ausrichten
3. ✅ Die virtuelle Kamera mit dem Output füttern

## ⚙️ Konfiguration

Öffne `head_tracking.py` und passe diese Konstanten an:

```python
# Wie groß soll das Gesicht im Bild sein? (25% der Bildbreite)
IDEAL_FACE_WIDTH_RATIO = 0.25

# Zoom-Grenzen (verhindert zu extremes Verhalten)
MIN_ZOOM = 1.0    # Minimaler Zoom (kein Rauszoomen)
MAX_ZOOM = 2.5    # Maximaler Zoom (Pixelierung vermeiden)

# Glättungsfaktoren (kleinere = weichere Bewegung)
SMOOTHING_FACTOR_PAN = 0.1    # Kopfbewegung
SMOOTHING_FACTOR_ZOOM = 0.05  # Zoom-Bewegung
```

### Parameter erklären

| Parameter | Bereich | Effekt |
|-----------|---------|--------|
| `IDEAL_FACE_WIDTH_RATIO` | 0.1 - 0.5 | Kleinere Werte = weiter raus, mehr "Headroom" |
| `MAX_ZOOM` | 1.0 - 5.0 | Höhere Werte = näher heran, aber pixeliger |
| `SMOOTHING_FACTOR_PAN` | 0.01 - 0.3 | Kleinere = langsamere, glattere Kopfbewegung |
| `SMOOTHING_FACTOR_ZOOM` | 0.01 - 0.2 | Kleinere = sanfteres Zoomen |

## 🔍 Wie es funktioniert

### Die Kopfverfolgung im Detail

```
1. GESICHTSERKENNUNG (Cascade Classifier)
   ↓
   Eingabebild → Konvertierung zu Graustufen
   ↓
   Haar-Kaskade scannt nach Gesichtsmuster
   ↓
   Größtes erkanntes Gesicht wird ausgewählt

2. ZOOM-BERECHNUNG
   ↓
   Aktuelle Gesichtsbreite gemessen
   ↓
   Zoomfaktor = Ideal-Breite / Aktuelle-Breite
   ↓
   Zoom begrenzt auf MIN_ZOOM bis MAX_ZOOM

3. GLÄTTUNG (Smoothing)
   ↓
   Aktuelle Position + Ziel-Position blended
   ↓
   Formeln: new = old × (1 - factor) + target × factor
   ↓
   Ergebnis: ruckelfrei statt abrupt

4. BILDTRANSFORMATION
   ↓
   Rechteckiger Ausschnitt berechnet
   ↓
   Bild zuschneiden und hochskalieren
   ↓
   An virtuelle Kamera senden
```

### Beispiel: Smoothing erklärt

Stellen Sie sich vor, der Zoomfaktor soll von 1.0 auf 2.0 gehen:

```python
# Ohne Smoothing (abrupt, ruckelig):
current_zoom = 2.0  # ← Sofort!

# Mit Smoothing (factor=0.05, weich):
current_zoom = 0.95 × 1.0 + 0.05 × 2.0 = 1.05  # Iteration 1
current_zoom = 0.95 × 1.05 + 0.05 × 2.0 = 1.0975  # Iteration 2
current_zoom = 0.95 × 1.0975 + 0.05 × 2.0 = 1.1426  # Iteration 3
# ... langsam sich annähernd ...
```

Deshalb wirkt die Bewegung flüssig und nicht ruckelig.

## 🐛 Häufige Probleme

### Problem: "Kamera kann nicht geöffnet werden"

**Ursache**: Kamera nicht vorhanden oder nicht verfügbar
```bash
# Lösung: Kamera-Index prüfen
# Ändere in head_tracking.py:
cap = cv2.VideoCapture(1)  # statt 0
```

### Problem: Gesicht wird nicht erkannt

**Ursachen**:
- ❌ Schlechte Beleuchtung → **Besseres Licht verwenden**
- ❌ Zu weit weg vom Bildschirm → **Näher herangehen**
- ❌ Gesicht teilweise verdeckt → **Behinderungen entfernen**

**Lösung**: Erkennung anpassen:
```python
# In process_frame():
faces = face_cascade.detectMultiScale(
    gray, 
    1.1,  # Scale factor (kleiner = präziser, langsamer)
    5     # Min neighbors (höher = strengere Erkennung)
)
```

### Problem: Bewegung ist zu ruckelig/zu träge

**Zu träge** (verzögertes Folgen):
- SMOOTHING_FACTOR erhöhen (z.B. 0.2)

**Zu ruckelig** (abrupte Sprünge):
- SMOOTHING_FACTOR senken (z.B. 0.02)

### Problem: Virtuelle Kamera wird nicht erkannt

**Windows**:
```bash
# OBS Virtual Camera installieren
# https://obsproject.com/
```

**macOS/Linux**:
```bash
pip install pyvirtualcam
# Die Virtualkamera sollte dann verfügbar sein
```

## 📁 Projektstruktur

```
head-tracking/
├── head_tracking.py
├── requirements.txt
├── README.md
├── DOKUMENTATION.md
├── SETUP.md
├── LICENSE
├── .gitignore
└── config/
    └── default_config.yaml
```

## 🎓 Technische Hintergründe

### Cascade Classifier (Haar-Kaskade)

Das Programm nutzt OpenCV's vortrainiertes Modell:
```python
haarcascade_frontalface_default.xml
```

Dies ist ein **Machine Learning Modell**, das Gesichtsmuster erkennt:
- ✅ Schnell (Echtzeit möglich)
- ✅ Zuverlässig unter guten Bedingungen
- ❌ Weniger genau bei extremen Winkeln
- ❌ Braucht gute Beleuchtung

### ROI (Region of Interest)

Nur ein kleiner Bereich des Bildes wird verarbeitet:
```python
roi_x1 = int(np.clip(face_center[0] - zoom_width / 2, 0, width - zoom_width))
roi_y1 = int(np.clip(face_center[1] - zoom_height / 2, 0, height - zoom_height))
```

Dies ist eine **Ausschneideoperation**, die:
- 🔺 CPU-Ressourcen spart
- 🔺 Bildqualität verbessert
- 🔺 Zoom-Effekt erzeugt

## 📋 Lizenz

Dieses Projekt ist Open Source und kann frei verwendet werden.

## 🤝 Beitragen

Dein Feedback und deine Verbesserungen sind willkommen!

### Pull Requests

1. Fork das Projekt
2. Feature-Branch erstellen: `git checkout -b feature/neue-funktion`
3. Änderungen committen: `git commit -m "Neue Funktion hinzugefügt"`
4. Push zum Branch: `git push origin feature/neue-funktion`
5. Pull Request öffnen

### Code-Standard

Dieses Projekt folgt **PEP 8**:
```bash
pip install flake8
flake8 head_tracking.py
```

## 📞 Support

Bei Fragen oder Problemen:
- 📧 Issues auf GitHub öffnen
- 💬 Diskussionen starten
- 📖 Dokumentation lesen

---

**Viel Spaß mit dem Kopfverfolgungssystem!** 🎬✨
