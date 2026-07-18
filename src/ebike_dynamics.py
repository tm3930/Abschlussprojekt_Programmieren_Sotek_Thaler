import logging
from ebike_config import EbikeConfig
import numpy as np

logger = logging.getLogger(__name__)

class EbikeDynamics():
    '''
    Klasse um die Dynamik des Ebikes besser zu beschreiben und verschiedene Berechnungen durchzuführen
    '''
    
    def __init__(self, config: EbikeConfig = EbikeConfig()):
        '''
        Initialisierung der Klasse
        Alle Argumente & Methoden von EbikeConfig werden übernommen
        '''
        
        logger.info("Initialisiere EbikeDynamics-Objekt.")
        
        self.config = config

    
    def get_drag_force(self, velocity: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der Luftwiderstandskraft des E-Bikes auf Basis der Geschwindigkeit

        Eingabe:
            velocity: NumPy-Array mit den Geschwindigkeitswerten in m/s
        
        Ausgabe:
            np.ndarray: Array mit den berechneten Luftwiderstandskräften in Newton
        '''
        logger.debug("Berechne Luftwiderstandskraft")

        rho = 1.2 #Rho ist die Luftdichte -> ca. 1,2 kg/m^3
        a: float = rho * self.config.cw_and_area / 2
        
        logger.debug("Luftwiderstandskraft Berechnung abgeschlossen")
        
        return (velocity ** 2) * a
    
    
    def get_incline_force(self, incline: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der Hangabtriebskraft bei Steigungen.

        Eingabe:
            incline: NumPy-Array mit den Steigungswinkeln in Bogenmaß (Rad)
        
        Ausgabe:
            np.ndarray: Array mit den wirkenden Kräften durch die Steigung in Newton
        '''
        
        logger.debug("Berechne Hangabtriebskraft")

        g = 9.81 #Gravitationskonstante: 9,81 m / s^2
        total_mass = self.config.bike_mass + self.config.rider_mass

        logger.debug("Hangabtriebskraft Berechnung abgeschlossen")

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
        
        logger.debug("Berechne gesamte benötigte Antriebskraft")
        
        total_mass = self.config.bike_mass + self.config.rider_mass
        
        logger.debug("gesamte benötigte Antriebskraft Berechnung abgeschlossen")

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

        logger.debug("Berechne Leistung")

        return np.multiply(force, velocity)
        
    

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

    logger.info("Starte ebike_dynamics Datei...")

    #Konfiguration aufsetzen
    config_test = EbikeConfig()
    config_test.bike_mass, config_test.rider_mass, config_test.cw_and_area = 20.0, 80.0, 0.6

    dynamics = EbikeDynamics()

    #Testdaten
    v = np.array([2.0, 5.0, 7.5])
    acc = np.array([0.5, 0.2, -0.1])
    inc = np.array([0.0, 0.04, 0.08])

    #Berechnungen kompakt ausführen
    f_drag = dynamics.get_drag_force(v)
    f_inc = dynamics.get_incline_force(inc)
    f_total = dynamics.get_total_force(acc, f_inc, f_drag)
    power = dynamics.get_power(f_total, v)

    #Ausgabe
    print("\n========== BERECHNETE KRÄFTE & LEISTUNGEN ===========")
    print("Luftwiderstand [N]:", np.round(f_drag, 1))
    print("Hangabtrieb [N]:   ", np.round(f_inc, 1))
    print("Gesamtkraft [N]:   ", np.round(f_total, 1))
    print("Leistung [Watt]:   ", np.round(power, 1))
    print("======================================================\n")