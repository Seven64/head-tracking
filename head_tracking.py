"""KI-Kopfverfolgung mit virtueller Kamera - Automatische Gesichtserkennung.

Dieses Modul nutzt Gesichtserkennung zur Steuerung einer virtuellen Kamera
mit dynamischem Zoom und Pan-Funktionalität. Das System folgt dem Kopf des
Benutzers und passt den Zoom automatisch an, um den optimalen Bildausschnitt
zu zeigen.

Hauptfunktionen:
- Echtzeit-Gesichtserkennung mit Haar-Kaskade
- Dynamischer Zoom basierend auf erkannter Gesichtsgröße
- Glatte Pan- und Zoom-Bewegungen durch Exponential Smoothing
- Virtuelle Kamera-Ausgabe für Video-Calls und Streaming

Verwendung:
    python head_tracking.py

Tastatursteuerung:
    V - Visualisierung der erkannten Gesichter umschalten
    Q - Programm beenden
"""

import cv2
import numpy as np
import pyvirtualcam

# ============================================================================
# KONFIGURATIONSKONSTANTEN - Verhalten des Systems steuern
# ============================================================================

# Wie groß soll das Gesicht im finalen Bild sein? (Anteil an der Bildbreite)
# Ein kleinerer Wert bedeutet mehr "Headroom" (Kamera zoomt raus)
# Ein größerer Wert bedeutet näher heran (Kamera zoomt rein)
# Typischer Bereich: 0.15 - 0.35
IDEAL_FACE_WIDTH_RATIO = 0.25  # 25% der Bildbreite

# Zoom-Grenzen - Verhindert extremes Verhalten und Pixelung
# MIN_ZOOM: Nicht weiter als das Originalbild herauszoomen
# MAX_ZOOM: Maximal erlaubter Zoom (höher = pixeliger)
MIN_ZOOM = 1.0  # Minimaler Zoom
MAX_ZOOM = 2.5  # Maximaler Zoom (3× ist oft zu pixelig)

# Glättungsfaktoren für sanfte, natürliche Bewegungen
# Kleinere Werte = langsamere, weichere Bewegung (träger)
# Größere Werte = schnellere Reaktion (ruckeliger)
# Bereich: 0.01 - 0.3 (empfohlen: 0.05 - 0.15)
SMOOTHING_FACTOR_PAN = 0.1   # Für Kopfbewegung (links/rechts/oben/unten)
SMOOTHING_FACTOR_ZOOM = 0.05  # Für Zoom-Bewegung (rein/raus)

# ============================================================================
# INITIALISIERUNG - Kamera und KI-Modell laden
# ============================================================================

# Lade das Haar-Kaskade-Klassifizierer-Modell für Gesichtserkennung
# Dieses Modell wurde von OpenCV bereitgestellt und auf Millionen von
# Gesichtern trainiert. Es erkennt frontale Gesichter sehr zuverlässig.
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Öffne die Standard-Webcam (Index 0)
# Bei mehreren Kameras: cv2.VideoCapture(1) für zweite Kamera, etc.
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Webcam konnte nicht geöffnet werden")

# Lese Kamera-Eigenschaften aus
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Berechne die ideale Gesichtsbreite in Pixeln basierend auf dem Verhältnis
# Beispiel: Bei 1920px Breite und 0.25 Ratio = 480px ideale Gesichtsbreite
ideal_face_width = width * IDEAL_FACE_WIDTH_RATIO

# Flag für Visualisierung der Gesichtserkennung
show_visualization = True


def process_frame(frame, face_cascade, width, height, ideal_face_width,
                  show_visualization):
    """Verarbeite einen Frame zur Gesichtserkennung.

    Diese Funktion:
    1. Konvertiert das Farbbild zu Graustufen (schneller für Erkennung)
    2. Führt Gesichtserkennung durch Haar-Kaskade durch
    3. Berechnet den optimalen Zoom basierend auf erkannter Gesichtsgröße
    4. Gibt die erkannte Kopfposition und Zoom-Parameter zurück

    Der Haar-Kaskade-Algorithmus arbeitet durch Skalierung des Bildes
    in mehrere Größen und Scans nach Gesichtsmustern. Dies ermöglicht
    Erkennung von Gesichtern in verschiedenen Größen.

    Args:
        frame: Eingabe-Videoframe (BGR-Format von OpenCV).
        face_cascade: Vortrainiertes Haar-Kaskade-Modell.
        width: Frame-Breite in Pixeln.
        height: Frame-Höhe in Pixeln.
        ideal_face_width: Ideale Gesichtsbreite in Pixeln.
        show_visualization: Ob Erkennungen visualisiert werden sollen.

    Returns:
        tuple: (face_center, target_zoom, preview_frame)
            - face_center: numpy-Array [x, y] der Kopfmitte
            - target_zoom: Berechneter Zoom-Faktor (float)
            - preview_frame: Annotierter Frame zur Anzeige
    """
    # Erstelle eine Kopie für die Vorschau (ohne Original zu ändern)
    preview_frame = frame.copy()

    # Konvertiere zu Graustufen
    # Grund: Gesichtserkennung braucht nur Helligkeit, nicht Farbe
    # Effekt: 3× schneller als Farbverarbeitung
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Führe Gesichtserkennung durch
    # Parameter:
    # - gray: Eingabe-Graustufen-Bild
    # - 1.1: Skalierungsfaktor (kleiner = präziser, aber langsamer)
    # - 5: Minimale Nachbarn (höher = strengere Erkennung, weniger Fehlalarme)
    # Rückgabe: Liste von Rechtecken [x, y, breite, höhe]
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    # Prüfe, ob ein Gesicht erkannt wurde
    if len(faces) > 0:
        # Wähle das größte erkannte Gesicht aus (nach Fläche)
        # Grund: Das größte Gesicht ist wahrscheinlich die Hauptperson
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face

        # Berechne die Mittelpunkt-Koordinaten des Gesichts
        # Dies wird später für Pan (Verschiebung) verwendet
        face_center = np.array([x + w / 2, y + h / 2])

        # ====================================================================
        # DYNAMISCHE ZOOM-LOGIK
        # ====================================================================
        # Berechne den Ziel-Zoom basierend auf der aktuellen Gesichtsbreite
        # Formel: target_zoom = ideal_breite / aktuelle_breite
        #
        # Beispiele:
        # - Ideal 480px, aktuell 240px → target = 480/240 = 2.0 (2× rein)
        # - Ideal 480px, aktuell 600px → target = 480/600 = 0.8 (20% raus)
        #
        # Ein target_zoom > 1.0 bedeutet Vergrößerung (rein)
        # Ein target_zoom < 1.0 bedeutet Verkleinerung (raus)
        target_zoom = ideal_face_width / w

        # Begrenze den Zoom auf den definierten Min/Max-Bereich
        # Dies verhindert:
        # - Zu viel Rauszoomen (würde alles verstecken)
        # - Zu viel Reinzoomen (würde pixelig werden)
        target_zoom = np.clip(target_zoom, MIN_ZOOM, MAX_ZOOM)

        # Visualisiere das erkannte Gesicht mit einem grünen Rechteck
        if show_visualization:
            cv2.rectangle(preview_frame, (x, y), (x + w, y + h),
                          (0, 255, 0), 2)

    else:
        # Kein Gesicht erkannt → Verwende Standardwerte
        # Die Kopfposition wird außerhalb dieser Funktion gepuffert,
        # sodass die Kamera nicht überraschend springt
        face_center = np.array([width / 2, height / 2])
        # Ziehe langsam auf eine neutrale Zoomstellung zurück
        target_zoom = 1.5

    return face_center, target_zoom, preview_frame


def apply_zoom_and_pan(frame, face_center, current_zoom, width, height):
    """Wende Zoom und Bildverschiebung auf das Frame an.

    Dieser Prozess funktioniert wie ein Fenster, das über das Bild geschoben wird:
    1. Berechne die Größe des sichtbaren Fensters basierend auf Zoom
    2. Zentriere das Fenster auf die erkannte Kopfposition
    3. Schneide das Bild zu (crop)
    4. Skaliere das zugeschnittene Bild zurück auf Originalgröße

    Mathematik:
    - Bei Zoom 1.0: Fenster = Gesamtbild (100%)
    - Bei Zoom 2.0: Fenster = Hälfte des Bildes (50%, aber 2× vergrößert)

    Args:
        frame: Eingabe-Frame (BGR).
        face_center: Mittelpunkt [x, y] für Zoom/Pan.
        current_zoom: Aktueller Zoom-Faktor (float).
        width: Frame-Breite in Pixeln.
        height: Frame-Höhe in Pixeln.

    Returns:
        numpy.ndarray: Verarbeitetes Frame mit Zoom und Pan.
    """
    # Berechne die Größe des sichtbaren Fensters in Pixel
    # Bei Zoom 2.0: Fenster ist halb so groß
    # Bei Zoom 1.0: Fenster ist gleich groß wie das ganze Bild
    zoom_width = width / current_zoom
    zoom_height = height / current_zoom

    # Berechne die obere-linke Ecke der ROI (Region of Interest)
    # Zentriere das Fenster auf face_center, aber gehe nicht über Bildgrenzen
    #
    # np.clip(wert, minimum, maximum) stellt sicher, dass der Wert im Bereich liegt
    # Beispiel: np.clip(2100, 0, 1920) = 1920 (zu groß, daher auf Max gekürzt)
    roi_x1 = int(np.clip(face_center[0] - zoom_width / 2, 0,
                         width - zoom_width))
    roi_y1 = int(np.clip(face_center[1] - zoom_height / 2, 0,
                         height - zoom_height))

    # Berechne die untere-rechte Ecke der ROI
    roi_x2 = int(roi_x1 + zoom_width)
    roi_y2 = int(roi_y1 + zoom_height)

    # Schneide das Bild zu (crop) - extrahiere nur den ROI-Bereich
    # Frame[y1:y2, x1:x2] ist die NumPy-Syntax (Zeile:Spalte)
    cropped_frame = frame[roi_y1:roi_y2, roi_x1:roi_x2]

    # Skaliere das zugeschnittene Bild zurück auf die Originalgröße
    # Dies erzeugt den Zoom-Effekt: Ein kleines Fenster wird vergrößert
    output_frame = cv2.resize(cropped_frame, (width, height))

    return output_frame


def smooth_parameter(current_value, target_value, smoothing_factor):
    """Glätte die Transition zwischen aktuellem und Zielwert.

    Dies implementiert Exponential Moving Average (EMA), einen häufig
    verwendeten Algorithmus für sanfte Übergänge in Echtzeit-Systemen.

    Formel:
        new_value = (1 - α) × old_value + α × target_value

    Wobei α (smoothing_factor) zwischen 0 und 1 liegt:
    - α = 0.0: Kein Smoothing (bleibt bei altem Wert)
    - α = 0.5: 50% zu Ziel, 50% zum alten Wert
    - α = 1.0: Sofort zum Zielwert (kein Smoothing)

    Intuitiv:
    - Kleinere α: Sanftere, träge Bewegung
    - Größere α: Schnellere, reaktivere Bewegung

    Args:
        current_value: Aktueller Wert (Kopfposition oder Zoom).
        target_value: Zielwert (wohin soll es gehen).
        smoothing_factor: Glättungsstärke (0.0 - 1.0).

    Returns:
        float: Geglätteter Wert zwischen aktuell und Ziel.
    """
    # Wende die Exponential Moving Average Formel an
    return ((1 - smoothing_factor) * current_value +
            smoothing_factor * target_value)


# ============================================================================
# HAUPTSCHLEIFE - Verarbeite Video-Frames
# ============================================================================

# Öffne virtuelle Kamera mit denselben Eigenschaften wie die echte Kamera
# Diese erscheint als "OBS Camera" oder ähnlich in Video-Anwendungen
with pyvirtualcam.Camera(width=width, height=height, fps=fps) as cam:
    print(f'Virtuelle Kamera: {cam.device}')
    print("Drücken Sie 'V' zum Umschalten der Visualisierung")
    print("Drücken Sie 'Q' zum Beenden")

    # Zustandsvariablen für Smoothing
    # Diese werden über mehrere Frames hinweg gepuffert, um Smoothing zu ermöglichen
    current_zoom = 1.0  # Aktueller Zoom (wird beim Start auf 1.0 gesetzt)
    last_face_center = np.array([width / 2, height / 2])  # Letzte bekannte Position

    # ========================================================================
    # VIDEO-VERARBEITUNGSSCHLEIFE
    # ========================================================================
    while True:
        # Lese einen Frame von der Webcam
        ret, frame = cap.read()
        if not ret:
            # Fehler beim Lesen (z.B. Kamera getrennt)
            break

        # Verarbeite Frame: Erkennung + Zoomberechnung
        # Gibt Kopfmitte, Zoom und Vorschau zurück
        face_center, target_zoom, preview_frame = process_frame(
            frame, face_cascade, width, height, ideal_face_width,
            show_visualization
        )

        # ====================================================================
        # GLÄTTUNG (SMOOTHING)
        # ====================================================================
        # Glätte Pan-Bewegung (Kopfposition)
        # Dies verhindert, dass die Kamera zwischen erkannten Positionen springt
        # Stattdessen bewegt sie sich sanft von A nach B
        last_face_center = smooth_parameter(
            last_face_center, face_center, SMOOTHING_FACTOR_PAN
        )

        # Glätte Zoom-Bewegung
        # Auch Zoom-Änderungen werden sanft übergeleitet, nicht abrupt
        current_zoom = smooth_parameter(
            current_zoom, target_zoom, SMOOTHING_FACTOR_ZOOM
        )

        # ====================================================================
        # BILDTRANSFORMATION UND AUSGABE
        # ====================================================================
        # Wende Zoom und Verschiebung auf das Original-Frame an
        output_frame = apply_zoom_and_pan(
            frame, last_face_center, current_zoom, width, height
        )

        # Konvertiere von BGR (OpenCV-Format) zu RGB (Kamera-Format)
        # Dies ist notwendig, da OpenCV BGR verwendet, aber virtuelle Kameras RGB
        output_frame_rgb = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)

        # Sende Frame an virtuelle Kamera
        cam.send(output_frame_rgb)

        # Warte bis zur nächsten Frame-Zeit (z.B. 33ms bei 30fps)
        # Dies hält die Bildrate konsistent
        cam.sleep_until_next_frame()

        # ====================================================================
        # VORSCHAUFENSTER UND BENUTZERINTERAKTION
        # ====================================================================
        # Schreibe Hilfetext auf das Vorschau-Frame
        cv2.putText(preview_frame, "Drücke 'V' zum Umschalten, 'Q' zum Beenden",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 2)

        # Zeige das Vorschau-Frame in einem Fenster an
        cv2.imshow('KI Kopfverfolgung Vorschau', preview_frame)

        # Lese Tastatureingabe (1ms Timeout)
        # & 0xFF extrahiert nur die unteren 8 Bits (um Fehler zu vermeiden)
        key = cv2.waitKey(1) & 0xFF

        # Prüfe auf Benutzereingaben
        if key == ord('q'):
            # 'Q' gedrückt → Hauptschleife beenden
            break
        if key == ord('v'):
            # 'V' gedrückt → Visualisierung umschalten
            show_visualization = not show_visualization

# ============================================================================
# AUFRÄUMEN - Ressourcen freigeben
# ============================================================================

# Schließe die Webcam-Verbindung
cap.release()

# Schließe alle OpenCV-Fenster
cv2.destroyAllWindows()

# Das Programm endet hier
# Die virtuelle Kamera wird automatisch durch den 'with' Block geschlossen