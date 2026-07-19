'''
Modul zur kinematischen Analyse und Berechnung von Fahrprofildaten aus GPS-Messwerten.

Dieses Modul stellt die Klasse `GPSData` zur Verfügung, welche geografische und 
zeitliche Rohdaten verarbeitet. Es berechnet essentielle physikalische Größen für 
die E-Bike-Simulation, wie die kumulierte Wegstrecke (via Haversine-Formel), 
die Momentangeschwindigkeit, die Beschleunigung sowie den lokalen Steigungswinkel.
'''

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class GPSData:
    '''
    Klasse zur Berechnung verschiedener Fahrdaten aus GPS-Messwerten.
    '''

    def __init__(self, data: pd.DataFrame) -> None:
        '''
        Konstruktor zum Speichern der GPS-Daten als NumPy-Arrays.

        Eingabe:
            data: Pandas DataFrame mit den Spalten 'lat', 'lon', 'ele', 'time' und 'temperature'
        '''

        logger.info("Initialisiere GPSData-Objekt.")

        self.data = data

        # Übernehmen der einzelnen Spalten in NumPy-Arrays, um später besser damit rechnen zu können
        self.data_latitude = self.data["lat"].to_numpy()
        self.data_longitude = self.data["lon"].to_numpy()
        self.data_elevation = self.data["ele"].to_numpy()
        self.data_time = self.data["time"].to_numpy()
        self.data_temperature = self.data["temperature"].to_numpy()

        logger.info("GPS-Daten erfolgreich übernommen.")

    def get_distance(self) -> np.ndarray:
        '''
        Funktion zur Berechnung der zurückgelegten Strecke anhand von Längen- und Breitengraden.
        Die Berechnung erfolgt mithilfe der Haversine-Formel.
        
        Ausgabe:
            np.ndarray: Ein Array mit der jeweils kumulierten zurückgelegten Strecke in Metern.
        '''

        logger.debug("Berechne zurückgelegte Strecke mithilfe der Haversine-Formel.")

        # Umwandlung von Grad in Radiant
        latitude_rad = np.radians(self.data_latitude)
        longitude_rad = np.radians(self.data_longitude)

        # Berechnung der Differenz zwischen zwei aufeinanderfolgenden Punkten
        delta_latitude = np.diff(latitude_rad)
        delta_longitude = np.diff(longitude_rad)

        # Haversine-Formel anwenden
        a_1 = np.sin(delta_latitude / 2.0)**2 + np.cos(latitude_rad[:-1])
        a_2 = np.cos(latitude_rad[1:]) * np.sin(delta_longitude / 2.0)**2
        c = 2 * np.arcsin(np.sqrt(a_1 * a_2))
        distances = c * 6371000  # 6.371.000 Meter entspricht dem mittleren Erdradius

        # Aufsummieren der einzelnen Intervalle, um die Gesamtwegstrecke zu erhalten
        distance_travelled = np.concatenate(([0.0], np.cumsum(distances)))

        logger.debug("Streckenberechnung abgeschlossen.")

        return distance_travelled

    def get_velocity(self, distance: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Bestimmung der Geschwindigkeit (Änderung der Strecke über der Zeit).
        
        Eingabe:
            distance: Array der bereits berechneten Wegstrecke in Metern.
        
        Ausgabe:
            np.ndarray: Die berechnete Momentangeschwindigkeit in m/s für jeden Zeitschritt.
        '''

        logger.debug("Berechne Geschwindigkeit.")

        # Berechnung der Differenzen zwischen zwei Punkten
        delta_time = np.diff(self.data_time)
        delta_distance = np.diff(distance)

        # Berechnung aus Strecke / Zeit (Division durch 0 wird durch np.where abgefangen)
        velocity_intervals = np.where(delta_time > 0, delta_distance / delta_time, 0.0)

        logger.debug("Geschwindigkeit erfolgreich berechnet.")

        return np.concatenate(([0.0], velocity_intervals))

    def get_acceleration(self, velocity: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Bestimmung der Beschleunigung (Änderung der Geschwindigkeit über der Zeit).
        
        Eingabe:
            velocity: Array der berechneten Momentangeschwindigkeiten in m/s.
        
        Ausgabe:
            np.ndarray: Die berechnete Beschleunigung in m/s² für jeden Zeitschritt.
        '''

        logger.debug("Berechne Beschleunigung.")

        # Berechnung der Differenzen zwischen zwei Punkten
        delta_time = np.diff(self.data_time)
        delta_velocity = np.diff(velocity)

        # Berechnung aus Geschwindigkeitsänderung / Zeit (Division durch 0 wird abgefangen)
        acceleration_intervals = np.where(delta_time > 0, delta_velocity / delta_time, 0.0)

        logger.debug("Beschleunigung erfolgreich berechnet.")

        return np.concatenate(([0.0], acceleration_intervals))

    def get_incline(self, distance: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Bestimmung der lokalen Steigung mittels Arcustangens 
        (Verhältnis von Höhenänderung zu Streckenänderung).
        
        Eingabe: 
            distance: Array der bereits berechneten Wegstrecke in Metern.
            
        Ausgabe:
            np.ndarray: Der lokale Steigungswinkel im Bogenmaß (rad) für jeden Zeitschritt.
        '''

        logger.debug("Berechne Steigung der Strecke.")

        # Berechnung der Differenzen zwischen zwei Punkten
        delta_distance = np.diff(distance)
        delta_elevation = np.diff(self.data_elevation)

        # Verhältnis zwischen Höhenänderung und Distanzänderung bestimmen
        # np.clip begrenzt das Verhältnis auf plausible Werte zwischen -100% und +100% Steigung
        ratio = np.zeros_like(delta_elevation)
        valid = delta_distance > 0
        ratio[valid] = np.clip(delta_elevation[valid] / delta_distance[valid], -1, 1)

        # Lokalen Steigungswinkel über den Arcustangens bestimmen
        incline_intervals = np.arctan(ratio)

        logger.debug("Steigungsberechnung abgeschlossen.")

        return np.concatenate(([0.0], incline_intervals))


if __name__ == "__main__":
    import sys

    # Logging für den lokalen Testlauf einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte gps_data Datei...")

    # Künstliche Testdaten erstellen (3 Wegpunkte auf dem Fahrrad)
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

    # Physikalische und kinematische Kennwerte berechnen
    strecke = gps_calculator.get_distance()
    geschwindigkeit = gps_calculator.get_velocity(strecke)
    beschleunigung = gps_calculator.get_acceleration(geschwindigkeit)
    steigung = gps_calculator.get_incline(strecke)

    # Ergebnisse übersichtlich zusammenführen und anzeigen
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
