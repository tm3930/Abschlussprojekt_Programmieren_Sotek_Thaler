import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class GPSData:
    '''
    Klasse zur Berechnung verschiedener Fahrdaten aus GPS-Messwerten
    '''

    def __init__(self, data: pd.DataFrame) -> None:
        '''
        Konstruktor zum Speichern der GPS-Daten als NumPy-Arrays

        Eingabe:
            data: Pandas DataFrame mit den Spalten 'lat', 'lon', 'ele', 'time' und 'temperature'
        '''

        logger.info("Initialisiere GPSData-Objekt.")

        self.data = data

        #Übernehmen der einzelnen Spalten in Numpy-Listen um später mit Ihnen arbeiten zu können
        self.data_latitude = self.data["lat"].to_numpy()
        self.data_longitude = self.data["lon"].to_numpy()
        self.data_elevation = self.data["ele"].to_numpy()
        self.data_time = self.data["time"].to_numpy()
        self.data_temperature = self.data["temperature"].to_numpy()

        logger.info("GPS-Daten erfolgreich übernommen.")

    def get_distance(self) -> np.ndarray:
        '''
        Funktion zur Berechnung der zurückgelegten Strecke aufgrund von Längen- & Breitengrade von GPS Daten
        Dies wird mithilfe der Haversine Formel gemacht
        
        Eingabe:
            Breitengrade
            Längengrade

        Ausgabe:
            zurückgelegte Strecke 
        '''

        logger.debug("Berechne zurückgelegte Strecke mithilfe der Haversine-Formel.")

        #Umwandlung von Grad in Radiant
        latitude_rad = np.radians(self.data_latitude)
        longitude_rad = np.radians(self.data_longitude)

        #Berechnung der Differenz zwischen 2 Punkten
        delta_latitude = np.diff(latitude_rad)
        delta_longitude = np.diff(longitude_rad)

        #Haversine Formel berechnen
        a = np.sin(delta_latitude / 2.0)**2 + np.cos(latitude_rad[:-1]) * np.cos(latitude_rad[1:]) * np.sin(delta_longitude / 2.0)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distances = c * 6371000  # 6371000 Meter ist der Erdradius

        #Aufsummieren, der einzelnen Ergebnisse um die zurückgelegte Strecke zu erhalten
        distance_travelled = np.concatenate(([0.0], np.cumsum(distances)))
        
        logger.debug("Streckenberechnung abgeschlossen.")

        return distance_travelled
    

    def get_velocity(self, distance: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Bestimmung der Geschwindigkeit = Zurückgelegte Strecke über der Zeit
        
        Eingabe:
            Zeit
            Strecke
        
        Ausgabe:
            Geschwindigkeit
        '''
        
        logger.debug("Berechne Geschwindigkeit.")

        #Berechnung der Differenz zwischen 2 Punkten
        delta_time = np.diff(self.data_time)
        delta_distance = np.diff(distance)

        #Berechnung der Geschwindigkeit aus Strecke / Zeit
        velocity = delta_distance / delta_time

        logger.debug("Geschwindigkeit erfolgreich berechnet.")

        return np.insert(velocity, 0, 0.0) #Anfangswert auf 0.0 gesetzt, damit die Listen wieder die gleiche Länge haben


    def get_acceleration(self, velocity: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Bestimmung der Beschleunigung = Änderung der Geschwindigkeit über der Zeit
        
        Eingabe:
            Zeit
            Geschwindigkeit
        
        Ausgabe:
            Beschleunigung
        '''
        
        logger.debug("Berechne Beschleunigung.")

        #Berechnung der Differenz zwischen 2 Punkten
        delta_time = np.diff(self.data_time)
        delta_velocity = np.diff(velocity)

        #Berechnung der Geschwindigkeit aus Strecke / Zeit
        acceleration = delta_velocity / delta_time

        logger.debug("Beschleunigung erfolgreich berechnet.")

        return np.insert(acceleration, 0, 0.0) #Anfangswert auf 0.0 gesetzt, damit die Listen wieder die gleiche Länge haben

    def get_incline(self, distance: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Bestimmung der Steigung = ArcusSinus von Änderung der Höhe zu Änderung der Strecke
        
        Eingabe: 
            Strecke
            Höhe über dem Meeresspiegel
            
        Ausgabe:
            Steigung
        '''

        logger.debug("Berechne Steigung der Strecke.")

        #Berechnung der Differenz zwischen 2 Punkten
        delta_distance = np.diff(distance)
        delta_elevation = np.diff(self.data_elevation)

        #Verhältnis zwischen beiden Werten ausrechnen
        #np.clip verhindert dass Werte größer oder kleiner als 1 werden, weil dies durch GPS manchmal passieren kann jedoch nicht realistisch ist
        ratio = np.clip(delta_elevation / delta_distance, -1, 1)

        #Steigung in Radiant ausrechnen
        incline = np.arcsin(ratio)

        logger.debug("Steigungsberechnung abgeschlossen.")

        return np.insert(incline, 0, 0.0)
    

if __name__ == "__main__":
    import sys

    #Logging einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte gps_data Datei...")
    #Künstliche Testdaten erstellen (3 Wegpunkte auf dem Fahrrad)
    #Zeit in Sekunden, Höhen in Metern, Temperatur in °C
    test_data = pd.DataFrame(
        {
            "time": [0.0, 5.0, 10.0],
            "lat": [47.2682, 47.2685, 47.2689],
            "lon": [11.3923, 11.3932, 11.3941],
            "ele": [574.0, 575.5, 578.0],
            "temperature": [21.0, 21.5, 22.0],
        }
    )

    gps_calculator = GPSData(test_data)

    
    #Strecke berechnen
    strecke = gps_calculator.get_distance()

    #Geschwindigkeit berechnen
    geschwindigkeit = gps_calculator.get_velocity(strecke)

    #Beschleunigung berechnen
    beschleunigung = gps_calculator.get_acceleration(geschwindigkeit)

    #Steigung berechnen
    steigung = gps_calculator.get_incline(strecke)

    #Ergebnisse übersichtlich zusammenführen und anzeigen
    ergebnisse = pd.DataFrame(
        {
            "Zeit [s]": test_data["time"],
            "Gesamtstrecke [m]": np.round(strecke, 1),
            "Geschw. [m/s]": np.round(geschwindigkeit, 2),
            "Beschl. [m/s²]": np.round(beschleunigung, 2),
            "Steigung [rad]": np.round(steigung, 3),
        }
    )

    print("\n================ BERECHNETE FAHRDATEN ================")
    print(ergebnisse.to_string(index=False))
    print("======================================================\n")
