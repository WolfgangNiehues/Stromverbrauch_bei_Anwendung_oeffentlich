# Ziel:
# 	• ESP32 mit AHT10 verbinden
# 	• Temperatur und Feuchtigkeit alle 60 Sekunden per MQTT senden
# 	• Stromaufnahme im Dauerbetrieb messen und dokumentieren
# Anleitung:
# 	• Programmiere den ESP32 so, dass er sich mit dem WLAN verbindet, den AHT10 ausliest und die Daten an einen MQTT-Broker sendet.
# 	• Verwende eine präzise Strommessung (z.B. USB-Multimeter, Messwiderstand mit Oszilloskop/Multimeter).
# 	• Dokumentiere die durchschnittliche Stromaufnahme im Betrieb.
# Messung:
# 	• Ruhestrom ESP32 + Sensor während WLAN aktiv ist.


#------------------------------------------
#Importieren der benötigten Bibliotheken
from machine import SoftI2C, Pin
from umqtt.simple import MQTTClient
import ujson
import time
import network

#from aht10 import AHT10
from BH1750_Paul import BH1750 as bh

from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD
#-------------------------------------------


#Initialisierung der Variablen
# IP-Adresse des MQTT-Brokers
broker_ip = "192.168.1.177"

# I2C initialisieren
i2c = SoftI2C(scl=Pin(4), sda=Pin(5))

# Sensor initialisieren
#messwerte = AHT10(i2c)

# Lichtsensor BH1750 initialisieren
bh_i2c = bh(0x23, i2c)

# Initialisierung der Variablen für die Lichtmessung
lumi = 0


# Counter für OTA Updates
ota_counter = 0

#-------------------------------------------

# # Temperaturmessung
# def messung_temp():
#     temp = round(messwerte.temperature())
#     return temp

# # Feuchtigkeitsmessung
# def messung_humi():
#     feucht = round(messwerte.humidity())
#     return feucht
#-------------------------------------------
# Lichtmessung mit BH1750
def lum ():
    
    lumi = bh_i2c.measurement
    lumi = round(lumi)
    lums = f"{lumi} lumen"
    return lumi
#--------------------------------------------

# MQTT-Broker Konfiguration
def mqtt_broker():
    broker = broker_ip
    client_id = "Niehues_ESP32"
    port = 1883
    topic = "Stromverbrauch"
    try:
        client = MQTTClient(client_id, broker, port)
        client.connect()
        print("Mit MQTT-Broker verbunden.")
        return client, topic
    except Exception as e:
        print(f"Fehler beim Verbinden mit dem MQTT-Broker: {e}")
        return None, None
#-------------------------------------------

# Grundfunktionen aufrufen
mqtt_client, topic = mqtt_broker()

# WORKAROUND: Korrigiere die fehlerhafte URL-Zusammensetzung in der OTA-Klasse
import re

# Monkey-patch für die OTAUpdater URL-Korrektur
original_init = OTAUpdater.__init__

def patched_init(self, ssid, password, repo_url, filename):
    original_init(self, ssid, password, repo_url, filename)
    # Korrigiere die fehlerhaften URLs
    if "main/version.json" in self.version_url and "/main/" not in self.version_url:
        self.version_url = self.version_url.replace("main/version.json", "/main/version.json")
        print(f"URL korrigiert zu: {self.version_url}")
    if "main/" in self.firmware_url and "/main/" not in self.firmware_url:
        self.firmware_url = self.firmware_url.replace("main/", "/main/")
        print(f"Firmware URL korrigiert zu: {self.firmware_url}")

OTAUpdater.__init__ = patched_init

# OTA Updater initialisieren (nach WLAN-Verbindung)
ota_updater = OTAUpdater(SSID, PASSWORD, "https://github.com/WolfgangNiehues/Stromverbrauch_bei_Anwendung_oeffentlich", "Aufgabe_1.py")

#--------------------------------------------

# Hauptprogramm
while True:
    try:
        lumi = lum()
        print(f"Lichtstaerke: {lumi} lumen")
        daten = {
            "Lichtstaerke": lumi,
        }
        payload = ujson.dumps(daten)
        print("Sende JSON:", payload)
        if mqtt_client:
            mqtt_client.publish(topic, payload)
        time.sleep(6)  # 6 Sekunden warten
          # OTA Update prüfen (alle 10 Zyklen)
        ota_counter += 1
        
        if ota_counter % 10 == 0:  # Alle 10 Messungen prüfen
            try:
                print(f"OTA Check #{ota_counter//10}: Prüfe auf Updates...")
                if ota_updater.check_for_updates():
                    print("Update verfügbar! Lade herunter...")
                    ota_updater.download_and_install_update_if_available()
                else:
                    print("Keine Updates verfügbar.")
            except Exception as ota_error:
                print(f"OTA Fehler: {ota_error}")
                print("Programm läuft trotz OTA-Fehler weiter...")
                
    except KeyboardInterrupt:
        print("Programm wurde durch den Benutzer beendet.")
        break
    except Exception as e:
        print(f"Fehler im Hauptprogramm: {e}")
        time.sleep(10)  # Bei Fehlern länger warten

#--------------------------------------------