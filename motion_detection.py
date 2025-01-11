import cv2
import os
import time
import threading
import requests
import yaml
import logging
from datetime import datetime, timedelta
import psutil  # Für Systemressourcen-Überwachung

# Logging einrichten
logging.basicConfig(
    filename='motion_detection.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Funktion zum Senden einer Telegram-Nachricht
def send_telegram_message(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                logging.info("Telegram-Nachricht gesendet.")
            else:
                logging.error(f"Fehler beim Senden der Telegram-Nachricht: {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"Fehler beim Senden der Telegram-Nachricht: {e}")
    else:
        logging.warning("Telegram-Bot-Token oder Chat-ID fehlt. Benachrichtigungen über Telegram werden nicht gesendet.")

# Konfiguration laden und validieren
def load_config(config_path='config.yaml'):
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        validate_config(config)
        return config
    except yaml.YAMLError as e:
        logging.error(f"Fehler beim Laden der YAML-Konfiguration: {e}")
        send_telegram_message(f"❌ Fehler beim Laden der YAML-Konfiguration: {e}")
        raise
    except Exception as e:
        logging.error(f"Allgemeiner Fehler beim Laden der Konfiguration: {e}")
        send_telegram_message(f"❌ Allgemeiner Fehler beim Laden der Konfiguration: {e}")
        raise

def validate_config(config):
    required_keys = ['rtsp_url', 'video_output_dir', 'motion_sensitivity', 'max_storage_gb',
                     'koofr_username', 'koofr_password', 'motion_end_delay']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        error_message = f"Fehlende Konfigurationsparameter: {', '.join(missing_keys)}"
        logging.error(error_message)
        send_telegram_message(f"❌ {error_message}")
        raise ValueError(error_message)
    # Hier können zusätzliche Validierungen hinzugefügt werden, z.B. URL-Format prüfen

config = load_config()

RTSP_URL = config['rtsp_url']
VIDEO_OUTPUT_DIR = config['video_output_dir']
MOTION_SENSITIVITY = config['motion_sensitivity']
MAX_STORAGE_GB = config['max_storage_gb']
KOOFR_USERNAME = config['koofr_username']
KOOFR_PASSWORD = config['koofr_password']
MOTION_END_DELAY = config['motion_end_delay']
TELEGRAM_BOT_TOKEN = config.get('telegram_bot_token')
TELEGRAM_CHAT_ID = config.get('telegram_chat_id')

# Optionale Konfigurationsparameter für Videoaufnahme
VIDEO_FRAME_RATE = config.get('video_frame_rate', 15)
VIDEO_RESOLUTION_WIDTH = config.get('video_resolution_width')
VIDEO_RESOLUTION_HEIGHT = config.get('video_resolution_height')

# Systemressourcen-Schwellenwerte
CPU_USAGE_THRESHOLD = config.get('cpu_usage_threshold', 90)  # in Prozent
MEMORY_USAGE_THRESHOLD = config.get('memory_usage_threshold', 90)  # in Prozent

# Überprüfen, ob das Ausgabe-Verzeichnis existiert
if not os.path.exists(VIDEO_OUTPUT_DIR):
    os.makedirs(VIDEO_OUTPUT_DIR)

# Funktion zum Überwachen des Speicherlimits
def monitor_storage():
    while True:
        try:
            total_size = 0
            file_list = []
            for dirpath, dirnames, filenames in os.walk(VIDEO_OUTPUT_DIR):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        size = os.path.getsize(fp)
                    except OSError as e:
                        logging.error(f"Fehler beim Zugriff auf Datei {fp}: {e}")
                        continue
                    total_size += size
                    file_list.append((fp, os.path.getctime(fp)))
            total_size_gb = total_size / (1024 * 1024 * 1024)
            if total_size_gb > MAX_STORAGE_GB:
                # Dateien nach Alter sortieren
                file_list.sort(key=lambda x: x[1])
                while total_size_gb > MAX_STORAGE_GB and file_list:
                    oldest_file = file_list.pop(0)[0]
                    try:
                        os.remove(oldest_file)
                        logging.info(f"Gelöschte Datei aufgrund von Speicherlimit: {oldest_file}")
                        total_size -= os.path.getsize(oldest_file)
                        total_size_gb = total_size / (1024 * 1024 * 1024)
                    except Exception as e:
                        logging.error(f"Fehler beim Löschen der Datei {oldest_file}: {e}")
        except Exception as e:
            logging.error(f"Fehler in der Speicherüberwachung: {e}")
        time.sleep(60)  # Überprüfung alle 60 Sekunden

# Funktion zum Hochladen von Dateien zu Koofr über WebDAV
def upload_to_koofr(file_path):
    try:
        # WebDAV-URL und Anmeldedaten
        webdav_url = 'https://app.koofr.net/dav/Koofr'
        username = KOOFR_USERNAME
        password = KOOFR_PASSWORD
        # Zielpfad in Koofr
        koofr_path = f'/Videos/{os.path.basename(file_path)}'
        # Datei hochladen via WebDAV
        with open(file_path, 'rb') as f:
            response = requests.put(f'{webdav_url}{koofr_path}', auth=(username, password), data=f)
        if response.status_code in [200, 201, 204]:
            logging.info(f"Datei erfolgreich hochgeladen: {file_path}")
        else:
            logging.error(f"Fehler beim Hochladen der Datei {file_path}: {response.status_code} - {response.text}")
            send_telegram_message(f"⚠️ Fehler beim Hochladen der Datei {file_path}: {response.status_code}")
    except Exception as e:
        logging.error(f"Fehler beim Hochladen der Datei {file_path}: {e}")
        send_telegram_message(f"⚠️ Fehler beim Hochladen der Datei {file_path}: {e}")

# Funktion zum Senden täglicher Statusberichte
def daily_status():
    while True:
        try:
            send_telegram_message("🔔 Täglicher Statusbericht: Alles läuft einwandfrei.")
            logging.info("Täglicher Statusbericht gesendet.")
        except Exception as e:
            logging.error(f"Fehler beim Senden des täglichen Statusberichts: {e}")
        # Nächster Statusbericht in 24 Stunden
        time.sleep(86400)

# Funktion zur Überwachung der Systemressourcen
def monitor_system_resources():
    check_interval = 60  # Sekunden
    while True:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            if cpu_usage > CPU_USAGE_THRESHOLD:
                message = f"⚠️ Hohe CPU-Auslastung: {cpu_usage}%"
                logging.warning(message)
                send_telegram_message(message)
            if memory_usage > MEMORY_USAGE_THRESHOLD:
                message = f"⚠️ Hohe RAM-Auslastung: {memory_usage}%"
                logging.warning(message)
                send_telegram_message(message)
        except Exception as e:
            logging.error(f"Fehler bei der Systemressourcen-Überwachung: {e}")
        time.sleep(check_interval)

# Thread für die Speicherüberwachung starten
storage_thread = threading.Thread(target=monitor_storage, daemon=True)
storage_thread.start()

# Thread für tägliche Statusberichte starten
status_thread = threading.Thread(target=daily_status, daemon=True)
status_thread.start()

# Thread für Systemressourcen-Überwachung starten
system_monitor_thread = threading.Thread(target=monitor_system_resources, daemon=True)
system_monitor_thread.start()

def main():
    retry_delay = 5  # Startverzögerung in Sekunden
    max_retry_delay = 300  # Maximale Verzögerung von 5 Minuten
    consecutive_failures = 0
    max_consecutive_failures = 5  # Nach 5 aufeinanderfolgenden Fehlern die Verzögerung erhöhen
    alert_failure_threshold = 720  # Nach 720 Fehlversuchen (ca. 1 Stunde bei 5 Sekunden Delay) Benachrichtigung senden
    alert_sent = False  # Flag, um zu verfolgen, ob eine Benachrichtigung gesendet wurde

    while True:
        try:
            cap = cv2.VideoCapture(RTSP_URL)
            if not cap.isOpened():
                raise ConnectionError("RTSP-Stream konnte nicht geöffnet werden.")
            logging.info("RTSP-Stream erfolgreich geöffnet.")
            consecutive_failures = 0  # Erfolgreiche Verbindung, Fehlerzähler zurücksetzen
            alert_sent = False  # Benachrichtigungs-Flag zurücksetzen

            ret, frame1 = cap.read()
            ret, frame2 = cap.read()

            if not ret:
                raise ValueError("Erste Frames konnten nicht gelesen werden.")

            recording = False
            out = None
            last_motion_time = None
            filename = ""

            while cap.isOpened():
                try:
                    ret, frame = cap.read()
                    if not ret:
                        logging.warning("Frame konnte nicht gelesen werden.")
                        raise Exception("Frame konnte nicht gelesen werden.")

                    diff = cv2.absdiff(frame1, frame)
                    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                    blur = cv2.GaussianBlur(gray, (5,5), 0)
                    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
                    dilated = cv2.dilate(thresh, None, iterations=3)
                    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    movement = False
                    for contour in contours:
                        if cv2.contourArea(contour) < MOTION_SENSITIVITY:
                            continue
                        movement = True
                        last_motion_time = time.time()
                        if not recording:
                            # Starte Aufnahme
                            # Videoeinstellungen
                            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                            timestamp = time.strftime("%Y%m%d-%H%M%S")
                            filename = os.path.join(VIDEO_OUTPUT_DIR, f"motion_{timestamp}.mp4")

                            # Frame-Größe einstellen
                            frame_width = VIDEO_RESOLUTION_WIDTH if VIDEO_RESOLUTION_WIDTH else frame.shape[1]
                            frame_height = VIDEO_RESOLUTION_HEIGHT if VIDEO_RESOLUTION_HEIGHT else frame.shape[0]

                            out = cv2.VideoWriter(filename, fourcc, VIDEO_FRAME_RATE, (frame_width, frame_height))
                            recording = True
                            logging.info(f"Bewegung erkannt. Aufnahme gestartet: {filename}")
                            # Sende Telegram-Nachricht
                            send_telegram_message(f"🚨 Bewegung erkannt! Aufnahme gestartet: {filename}")
                        break

                    if recording:
                        # Frame skalieren, falls nötig
                        if frame.shape[1] != frame_width or frame.shape[0] != frame_height:
                            frame_resized = cv2.resize(frame, (frame_width, frame_height))
                        else:
                            frame_resized = frame
                        out.write(frame_resized)
                        # Überprüfen, ob die Aufnahme gestoppt werden sollte
                        if not movement:
                            if last_motion_time and (time.time() - last_motion_time) > MOTION_END_DELAY:
                                # Stoppe Aufnahme
                                out.release()
                                recording = False
                                logging.info(f"Aufnahme beendet: {filename}")
                                # Sende Telegram-Nachricht
                                send_telegram_message(f"✅ Aufnahme beendet: {filename}")
                                # Starte Upload in separatem Thread
                                upload_thread = threading.Thread(target=upload_to_koofr, args=(filename,))
                                upload_thread.start()

                    frame1 = frame
                except Exception as e:
                    logging.error(f"Fehler im Aufnahmeprozess: {e}")
                    if recording and out:
                        out.release()
                        recording = False
                        logging.info(f"Aufnahme aufgrund eines Fehlers beendet: {filename}")
                        send_telegram_message(f"⚠️ Aufnahme aufgrund eines Fehlers beendet: {filename}")
                        # Starte Upload in separatem Thread
                        upload_thread = threading.Thread(target=upload_to_koofr, args=(filename,))
                        upload_thread.start()
                    break  # Versuch der Wiederverbindung

            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            consecutive_failures += 1
            logging.error(f"Fehler beim Verbinden zum RTSP-Stream: {e}")

            # Anpassung der Verzögerung basierend auf den Fehlversuchen
            if consecutive_failures >= max_consecutive_failures:
                retry_delay = min(retry_delay * 2, max_retry_delay)
                logging.warning(f"Erhöhte Wartezeit auf {retry_delay} Sekunden nach {consecutive_failures} Fehlversuchen.")
            else:
                retry_delay = 5  # Zurücksetzen auf die Anfangsverzögerung

            if not alert_sent and consecutive_failures >= alert_failure_threshold:
                alert_message = f"🚨 Achtung! Es gab {consecutive_failures} aufeinanderfolgende Verbindungsfehler zum RTSP-Stream."
                logging.error(alert_message)
                send_telegram_message(alert_message)
                alert_sent = True

            logging.info(f"Neuer Verbindungsversuch in {retry_delay} Sekunden.")
            time.sleep(retry_delay)

if __name__ == "__main__":
    main()


