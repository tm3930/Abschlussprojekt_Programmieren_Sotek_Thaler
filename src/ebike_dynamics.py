'''
Modul zur Berechnung der Fahrdynamik und der mechanischen Kräfte eines E-Bikes.

Dieses Modul stellt die Klasse `EbikeDynamics` bereit. Sie berechnet auf 
Basis der Fahrspurdaten und Fahrzeugparameter alle relevanten physikalischen 
Kräfte (Luftwiderstand unter Berücksichtigung der barometrischen Höhenformel, 
Rollwiderstand und Hangabtriebskraft) sowie die daraus resultierende 
mechanische Gesamtleistung des Systems.
'''

import logging
import numpy as np
from ebike_config import EbikeConfig
from constants import (
    GRAVITY,
    STD_PRESSURE,
    STD_TEMP_KELVIN,
    SEA_LEVEL_TEMP,
    TEMP_LAPSE_RATE,
    GAS_CONSTANT_AIR,
)

logger = logging.getLogger(__name__)

class EbikeDynamics:
    '''
    Klasse zur mathematischen Beschreibung der E-Bike-Dynamik und Kraftberechnungen.
    '''

    def __init__(self, config: EbikeConfig = None):
        '''
        Initialisierung der Dynamik-Klasse.
        
        Eingabe:
            config: Optionale Instanz von EbikeConfig. Wenn keine übergeben wird, 
                    werden die Standardvorgaben geladen.
        '''

        logger.info("Initialisiere EbikeDynamics-Objekt.")

        # Falls keine Config übergeben wird, wird eine frische Standard-Config erstellt
        self.config = config if config is not None else EbikeConfig()

    def get_drag_force(
            self,
            velocity: np.ndarray,
            elevation: np.ndarray,
            temperature: np.ndarray
        ) -> np.ndarray:
        '''
        Funktion zur Berechnung der Luftwiderstandskraft des E-Bikes auf Basis der Geschwindigkeit,
        Höhe über dem Meeresspiegel und der Temperatur.

        Eingabe:
            velocity: NumPy-Array mit den Geschwindigkeitswerten in m/s
            elevation: NumPy-Array mit der Höhe in Metern
            temperature: NumPy-Array mit der Temperatur in °C
        
        Ausgabe:
            np.ndarray: Array mit den berechneten Luftwiderstandskräften in Newton
        '''
        logger.debug("Berechne Luftwiderstandskraft mit dynamischer Luftdichte")

        # Temperatur in Kelvin umrechnen
        t_kelvin = temperature + STD_TEMP_KELVIN

        # Luftdruck in Abhängigkeit der Höhe (barometrische Höhenformel)
        pressure_exponent = GRAVITY / (GAS_CONSTANT_AIR * TEMP_LAPSE_RATE)

        p = STD_PRESSURE * (
            1 - (TEMP_LAPSE_RATE * elevation) / SEA_LEVEL_TEMP
        ) ** pressure_exponent

        # 3. Luftdichte rho nach der idealen Gasgleichung berechnen
        # R_s = 287.05 J/(kg*K) ist die spezifische Gaskonstante für trockene Luft
        rho = p / (GAS_CONSTANT_AIR * t_kelvin)

        a = rho * self.config.cw_and_area / 2

        logger.debug("Luftwiderstandskraft Berechnung abgeschlossen")

        return (velocity ** 2) * a

    def get_rolling_resistance(self, incline: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der Rollwiderstandskraft auf Basis des Steigungswinkels.
        Formel: F_R = m * g * cos(alpha) * c_r

        Eingabe:
            incline: NumPy-Array mit den Steigungswinkeln in Bogenmaß (rad)

        Ausgabe:
            np.ndarray: Array mit den berechneten Rollwiderstandskräften in Newton
        '''

        return self.config.total_mass * GRAVITY * np.cos(incline) * self.config.c_r

    def get_incline_force(self, incline: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung der Hangabtriebskraft bei Steigungen.

        Eingabe:
            incline: NumPy-Array mit den Steigungswinkeln in Bogenmaß (rad)
        
        Ausgabe:
            np.ndarray: Array mit den wirkenden Kräften durch die Steigung in Newton
        '''

        logger.debug("Berechne Hangabtriebskraft")

        return self.config.total_mass * GRAVITY * np.sin(incline)

    def get_total_force(
            self,
            acceleration: np.ndarray,
            incline_force: np.ndarray,
            drag_force: np.ndarray,
            rolling_resistance: np.ndarray
        ) -> np.ndarray:
        '''
        Funktion zur Berechnung der gesamten benötigten Antriebskraft 
        (Massenbeschleunigung + alle Fahrwiderstände)

        Eingabe:
            acceleration: NumPy-Array mit den Beschleunigungswerten in m/s²
            incline_force: NumPy-Array mit den Steigungskräften in Newton
            drag_force: NumPy-Array mit den Luftwiderstandskräften in Newton
            rolling_resistance: NumPy-Array mit den Rollwiderstandskräften in Newton
        
        Ausgabe:
            np.ndarray: Array mit der gesamten erforderlichen Antriebskraft in Newton
        '''

        logger.debug("Berechne gesamte benötigte Antriebskraft")

        return (
            self.config.total_mass * acceleration
            + incline_force
            + drag_force
            + rolling_resistance
        )

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

    def __str__(self) -> str:
        '''
        Erzeugt eine kurze Repräsentation des Dynamik-Modells.
        '''
        return (
            f"EbikeDynamics (Gesamtmasse: {self.config.total_mass:.1f} kg, "
            f"cw*A: {self.config.cw_and_area:.4f} m²)"
        )


if __name__ == "__main__":
    import sys

    # Logging einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte ebike_dynamics Datei...")

    # Konfiguration mit spezifischen Testwerten aufsetzen
    config_test = EbikeConfig()
    config_test.bike_mass, config_test.rider_mass, config_test.cw_and_area = 20.0, 80.0, 0.6

    # Wichtig: Die modifizierte config_test hier an die Dynamik übergeben!
    dynamics = EbikeDynamics(config=config_test)

    # Testdaten (jeweils 3 Punkte)
    v = np.array([2.0, 5.0, 7.5])
    acc = np.array([0.5, 0.2, -0.1])
    inc = np.array([0.0, 0.04, 0.08])
    ele = np.array([500.0, 520.0, 550.0])
    temp = np.array([20.0, 19.5, 19.0])

    # Berechnungen fehlerfrei ausführen
    f_drag = dynamics.get_drag_force(v, ele, temp)
    f_roll = dynamics.get_rolling_resistance(inc)
    f_inc = dynamics.get_incline_force(inc)
    f_total = dynamics.get_total_force(acc, f_inc, f_drag, f_roll)
    power = dynamics.get_power(f_total, v)

    # Übersichtliche Text-Ausgabe im Terminal
    print("\n========== BERECHNETE KRÄFTE & LEISTUNGEN ===========")
    print("Luftwiderstand [N]: ", np.round(f_drag, 1))
    print("Rollwiderstand [N]: ", np.round(f_roll, 1))
    print("Hangabtrieb [N]:    ", np.round(f_inc, 1))
    print("Gesamtkraft [N]:    ", np.round(f_total, 1))
    print("Leistung [Watt]:    ", np.round(power, 1))
    print("======================================================\n")

    logger.info("Überprüfung erfolgreich abgeschlossen.")
