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
#lum auf 0
lumi = 0
lums = 0

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
    
    global lumi
    global lums
    
    lumi = bh_i2c.measurement
    lumi = round(lumi)
    lums = f"{lumi} lumen"
    return lumi
#--------------------------------------------
    
# WLAN-Verbindung Konfiguration
def wlan_verbinden(ssid, passwort):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, passwort)
    timeout = 10
    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            print("Verbindung zum WLAN fehlgeschlagen.")
            return False
        print("Verbinde...")
        time.sleep(1)
    print("WLAN verbunden:", wlan.ifconfig())
    return True
#-------------------------------------------

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
wlan_verbinden("SSID", "PASSWORD")
mqtt_client, topic = mqtt_broker()

#OTA Updater initialisieren (nach WLAN-Verbindung)
ota_updater = OTAUpdater("SSID", "PASSWORD", "https://github.com/your-repo/your-project", "Aufgabe_1.py")
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
        time.sleep(6)  # 60 Sekunden warten    except KeyboardInterrupt:
    except KeyboardInterrupt:
        print("Programm wurde durch den Benutzer beendet.")
        break    
    except Exception as e:
        print(f"Fehler im Hauptprogramm: {e}")
        time.sleep(10)  # Bei Fehlern länger warten

#--------------------------------------------