import sys
from data_validation import validate
from data_from_csv import get_data_from_csv
from data_calculations import get_distance, get_velocity, get_acceleration
from motor import Motor
from ebike_config import EbikeConfig


#Daten importieren aus csv-File aus dem Ordner data / raw
data = get_data_from_csv("final_project_input_data.csv")

#ZEIT DIREKT UMRECHNEN: Sekunden ab dem ersten Punkt (0, 5, 10...)
#Wir ziehen einfach von jeder Zeile den allerersten Zeitstempel (.iloc[0]) ab
data["time"] = (data["time"] - data["time"].iloc[0]).dt.total_seconds()

#Daten auf Korrektheit überprüfen: 
if not validate(data):
    sys.exit("Programm abgebrochen aufgrund fehlerhafter Daten.")
#Idee: andere Abbruchsbedingung / Textnachricht hinzufügen

#einzelne Spalten übernehmen und als numpy Listen abspeichern
data_lat = data["lat"].to_numpy()
data_lon = data["lon"].to_numpy()
data_ele = data["ele"].to_numpy()
data_time = data["time"].to_numpy()
data_temperature = data["temperature"].to_numpy()

data_distance_travelled = get_distance(data_lat, data_lon)
data_velocity = get_velocity(data_distance_travelled, data_time)
data_acceleration = get_acceleration(data_velocity, data_time)

#Zugriff der Motor-Klasse auf die Daten der EbikeConfig-Klasse
config = EbikeConfig()
motor  = Motor(motor_constant = config.motor_constant, radius = config.radius)
