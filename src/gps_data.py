import logging
import numpy as np
import pandas as pd


class GPSData:
    '''
    Klasse zur Berechnung verschiedener Fahrdaten aus GPS-Messwerten
    '''

    def __init__(self, data: pd.DataFrame):
        '''
        Konstruktor zum Speichern der GPS-Daten als NumPy-Arrays

        Eingabe:
            data: Pandas DataFrame mit den Spalten 'lat', 'lon', 'ele', 'time' und 'temperature'
        '''

        logging.info("Initialisiere GPSData-Objekt.")

        self.data = data

        #Übernehmen der einzelnen Spalten in Numpy-Listen um später mit Ihnen arbeiten zu können
        self.data_latitude = self.data["lat"].to_numpy()
        self.data_longitude = self.data["lon"].to_numpy()
        self.data_elevation = self.data["ele"].to_numpy()
        self.data_time = self.data["time"].to_numpy()
        self.data_temperature = self.data["temperature"].to_numpy()

        logging.info("GPS-Daten erfolgreich übernommen.")

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

        logging.info("Berechne zurückgelegte Strecke mithilfe der Haversine-Formel.")

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
        
        logging.info("Streckenberechnung abgeschlossen.")

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
        
        logging.info("Berechne Geschwindigkeit.")

        #Berechnung der Differenz zwischen 2 Punkten
        delta_time = np.diff(self.data_time)
        delta_distance = np.diff(distance)

        #Berechnung der Geschwindigkeit aus Strecke / Zeit
        velocity = delta_distance / delta_time

        logging.info("Geschwindigkeit erfolgreich berechnet.")

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
        
        logging.info("Berechne Beschleunigung.")

        #Berechnung der Differenz zwischen 2 Punkten
        delta_time = np.diff(self.data_time)
        delta_velocity = np.diff(velocity)

        #Berechnung der Geschwindigkeit aus Strecke / Zeit
        acceleration = delta_velocity / delta_time

        logging.info("Beschleunigung erfolgreich berechnet.")

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

        logging.info("Berechne Steigung der Strecke.")

        #Berechnung der Differenz zwischen 2 Punkten
        delta_distance = np.diff(distance)
        delta_elevation = np.diff(self.data_elevation)

        #Verhältnis zwischen beiden Werten ausrechnen
        #np.clip verhindert dass Werte größer oder kleiner als 1 werden, weil dies durch GPS manchmal passieren kann jedoch nicht realistisch ist
        ratio = np.clip(delta_elevation / delta_distance, -1, 1)

        #Steigung in Radiant ausrechnen
        incline = np.arcsin(ratio)

        logging.info("Steigungsberechnung abgeschlossen.")

        return np.insert(incline, 0, 0.0)