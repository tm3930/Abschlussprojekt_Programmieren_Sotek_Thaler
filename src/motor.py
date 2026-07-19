'''
Modul zur mathematischen Modellierung und Stromberechnung des E-Bike-Elektromotors.

Dieses Modul stellt die Klasse `Motor` bereit. Sie bildet die elektromechanische 
Schnittstelle des E-Bikes, indem sie die translatorische Vortriebskraft in ein 
rotatorisches Drehmoment am Rad übersetzt und daraus den korrespondierenden 
Motorstrom über die Motorkonstante (Km) berechnet.
'''

import logging
import sys
import numpy as np
from ebike_config import EbikeConfig

logger = logging.getLogger(__name__)


class Motor:
    '''
    Klasse zur Simulation der elektromechanischen Eigenschaften des E-Bike-Motors.
    '''

    def __init__(self, config: EbikeConfig = None) -> None:
        '''
        Konstruktor zur Initialisierung des E-Bike-Motors und Validierung der Parameter.

        Eingabe:
            config: Optionales Konfigurations-Objekt (EbikeConfig). Falls None,
                    wird automatisch die Standardkonfiguration geladen.
        '''
        logger.info("Initialisiere Motor-Objekt.")

        # Falls keine Konfiguration übergeben wurde, Standardwerte laden
        self.config = config if config is not None else EbikeConfig()

        # Validierung der physikalischen Parameter und Fehlerbehandlung
        if self.config.motor_constant <= 0:
            raise ValueError(
                f"Motorkonstante muss größer als 0 sein, aktuell: {self.config.motor_constant}"
            )
        if self.config.radius <= 0:
            raise ValueError(f"Radradius muss größer als 0 sein, aktuell: {self.config.radius}")

        # Logging über die erfolgreich gesetzten Motor- und Radparameter
        logger.debug(
            "Motorwerte: Motorkonstante = %s Nm/A, Radius des Rads = %.2f m", 
            self.config.motor_constant,
            self.config.radius
        )

    def get_torque(self, force: float | np.ndarray) -> float | np.ndarray:
        '''
        Berechnet das mechanische Drehmoment am Hinterrad basierend auf der Vortriebskraft.

        Eingabe:
            force: Die wirkende Kraft in Newton (N) als Skalar oder NumPy-Array.
            
        Ausgabe:
            float | np.ndarray: Das resultierende Drehmoment in Newtonmetern (Nm).
        '''
        logger.debug("Berechne Drehmoment am Rad.")
        return force * self.config.radius

    def current(self, torque: float | np.ndarray) -> float | np.ndarray:
        '''
        Berechnet den benötigten Motorstrom für ein gegebenes Drehmoment.
        Die Berechnung basiert auf der linearen Beziehung: I = T / Km

        Eingabe:
            torque: Das Drehmoment in Newtonmetern (Nm) als Skalar oder NumPy-Array.
            
        Ausgabe:
            float | np.ndarray: Der resultierende Motorstrom in Ampere (A).
        '''
        logger.debug("Berechne Motorstrom.")

        current_value = torque / self.config.motor_constant

        logger.debug(
            "Strom von %.2f A bei einem Drehmoment von: %.2f Nm",
            np.mean(current_value),
            np.mean(torque)
        )
        return current_value

    def __str__(self) -> str:
        '''
        Erzeugt eine lesbare String-Repräsentation der wichtigsten Motorkennwerte.
        
        Ausgabe:
            str: Formatierte Information über Motorkonstante und Radradius.
        '''
        return f"Ebike-Motor: (Km={self.config.motor_constant} Nm/A, r={self.config.radius:.2f} m)"


if __name__ == "__main__":
    # Logging für den lokalen Funktionstest konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte Motor Datei...")

    # Instanziierung des Test-Objekts
    motor = Motor()

    # Lokaler Funktionstest mit einer konstanten Kraft
    F_TEST = 100.0
    T_test = motor.get_torque(F_TEST)
    I_test = motor.current(F_TEST)

    print("\n================ BERECHNETE MOTORDATEN ================")
    print(motor)
    print(f"Kraft F          = {F_TEST:.0f} N")
    print(f"Drehmoment T     = {T_test:.2f} Nm")
    print(f"Motorstrom I     = {I_test:.2f} A")

    # Koppelungstest mit dem Batteriemodell (20 Minuten Fahrt simulieren)
    try:
        from battery import LiPoBattery

        battery_test = LiPoBattery(capacity_ampere_h=15.0, initial_soc=1.0)
        battery_test.apply_current(current=I_test, duration=1200.0)
        print("-------------------------------------------------------")
        print(battery_test)
    except ImportError:
        logger.warning("Battery-Klasse konnte für den Selbsttest nicht geladen werden.")

    print("======================================================\n")
