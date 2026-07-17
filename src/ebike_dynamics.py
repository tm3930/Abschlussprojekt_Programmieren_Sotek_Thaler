import logging
from ebike_config import EbikeConfig
import numpy as np


class EbikeDynamics():
    '''
    Klasse um die Dynamik des Ebikes besser zu beschreiben und verschiedene Berechnungen durchzuführen
    '''
    
    def __init__(self, config: EbikeConfig):
        '''
        Initialisierung der Klasse
        Alle Argumente & Methoden von EbikeConfig werden übernommen
        '''
        self.config = config

    
    def get_drag_force(self, velocity: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der Luftwiderstandskraft des E-Bikes auf Basis der Geschwindigkeit

        Eingabe:
            velocity: NumPy-Array mit den Geschwindigkeitswerten in m/s
        
        Ausgabe:
            np.ndarray: Array mit den berechneten Luftwiderstandskräften in Newton
        '''
        rho = 1.2 #Rho ist die Luftdichte -> ca. 1,2 kg/m^3
        a: float = rho * self.config.cw_and_area / 2

        return (velocity ** 2) * a
    
    
    def get_incline_force(self, incline: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der Hangabtriebskraft bei Steigungen.

        Eingabe:
            incline: NumPy-Array mit den Steigungswinkeln in Bogenmaß (Rad)
        
        Ausgabe:
            np.ndarray: Array mit den wirkenden Kräften durch die Steigung in Newton
        '''
        g = 9.81 #Gravitationskonstante: 9,81 m / s^2
        total_mass = self.config.bike_mass + self.config.rider_mass

        return total_mass * g * np.sin(incline)


    def get_total_force(self, acceleration: np.ndarray, incline_force: np.ndarray, drag_force: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der gesamten benötigten Antriebskraft.

        Eingabe:
            acceleration: NumPy-Array mit den Beschleunigungswerten in m/s^2
            incline_force: NumPy-Array mit den Steigungskräften in Newton
            drag_force: NumPy-Array mit den Luftwiderstandskräften in Newton
        
        Ausgabe:
            np.ndarray: Array mit der gesamten erforderlichen Antriebskraft in Newton
        '''
        total_mass = self.config.bike_mass + self.config.rider_mass
        
        return total_mass * acceleration + incline_force + drag_force

    
    def get_power(self, force: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der mechanischen Leistung.

        Eingabe:
            force: NumPy-Array mit den Kräften in Newton
            velocity: NumPy-Array mit den Geschwindigkeiten in m/s
        
        Ausgabe:
            np.ndarray: Array mit der berechneten Leistung in Watt
        '''
        return np.multiply(force, velocity)