from data_from_csv import get_data_from_csv
from motor import Motor
from ebike_config import EbikeConfig
from gps_data import GPSData
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
gps = GPSData( get_data_from_csv("final_project_input_data.csv") )

distance = gps.get_distance()
velocity = gps.get_velocity(distance)
acceleration = gps.get_acceleration(velocity)
incline = gps.get_incline(distance)


#Zugriff der Motor-Klasse auf die Daten der EbikeConfig-Klasse
config = EbikeConfig()
motor  = Motor(motor_constant = config.motor_constant, radius = config.radius)
