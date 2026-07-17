from data_from_csv import get_data_from_csv
from motor import Motor
from ebike_config import EbikeConfig
from gps_data import GPSData
from ebike_dynamics import EbikeDynamics
import logging
import sys

#Logging einrichten:
logging.basicConfig(
    level=logging.INFO, #bedeutet, dass Info, Warning, Error und Critical mitgeschrieben wird
    format="%(asctime)s [%(levelname)s] %(message)s",   #schreibt Zeit [Info / ...] und dann die Nachricht
    handlers=[
        logging.StreamHandler(sys.stdout),  #Ausgabe im Terminal
        logging.FileHandler("app.log", mode="a", encoding="utf-8")  #Ausgabe in eigener Logging Datei
    ]
)



#Daten importieren aus csv-File aus dem Ordner data / raw



#Zugriff der Motor-Klasse auf die Daten der EbikeConfig-Klasse
motor  = Motor(EbikeConfig())