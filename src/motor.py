import logging
import sys
import numpy as np
from ebike_config import EbikeConfig

logger = logging.getLogger(__name__)

class Motor:
    '''
    Klasse für den Ebike-Motor
    '''

    def __init__(
            self,
            config: EbikeConfig = EbikeConfig()
            ) -> None:

        '''
        Konstruktor zur Initialisierung des Ebike-Motors
        
        Eingabe:
            Konfigurations-Objekt
        '''
        
        logger.info("Initialisiere Motor-Objekt.")
        
        self.config = config

        #Fehlermeldungen
        if self.config.motor_constant <= 0:
            raise ValueError(f"Motorkonstante muss größer als 0 sein, aktuell: {self.config.motor_constant}")
        if self.config.radius <= 0:
            raise ValueError(f"Radradius muss größer als 0 sein, aktuell: {self.config.radius}")
        
        #Logging über aktuelle Werte des Motors/Rads
        logger.debug(
            "Motorwerte: Motorkonstante = %s Nm/A, Radius des Rads = %.2f m", 
            self.config.motor_constant, 
            self.config.radius
        )

    def get_torque(self, force: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung des Drehmoments am Rad.

        Eingabe:
            force: NumPy-Array mit den Kräften in Newton
            
        Ausgabe:
            np.ndarray: Array mit dem resultierenden Drehmoment in Newtonmetern (Nm)
        '''
        
        logger.debug("Berechne Drehmoment am Rad.")
        
        return force * self.config.radius

    def current(self, torque: float) -> float:
        '''
        Funktion zur Berechnung des Motorstroms nach der Formel I = T / Km
        
        Eingabe:
            Drehmoment
            
        Ausgabe:
            Motorstrom
        '''

        logger.debug("Berechne Motorstrom.")

        current = torque / self.config.motor_constant
        
        logger.debug("Strom von %.2f A bei einem Drehmoment von: %.2f Nm", current, torque)
        
        return current

    def __str__(self) -> str:
        '''
        Funktion zur sinnvollen Ausgabe der Werte bei Überprüfung mit "print(motor)"
        
        Ausgabe:
            Lesbare Information über den Motor
        '''

        return (f"Ebike-Motor: (Km = {self.config.motor_constant} Nm/A, r = {self.config.radius:.2f} m)")


if __name__ == "__main__":
    
    # Logging einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )
    
    logger.info("Starte Motor Datei... ")

    motor = Motor()

    #Selbsttest der Klasse
    F = 100.0
    T = motor.get_torque(F)
    I = motor.current(T)
    
    print("\n================ BERECHNETE MOTORDATEN ================")
    print(motor)
    print(f"Kraft F          = {F:.0f} N")
    print(f"Drehmoment T     = {T:.2f} Nm")
    print(f"Motorstrom I     = {I:.2f} A")

    #Selbsttest mit der Battery-Klasse - 20min fahren
    try:
        from battery import LiPoBattery

        battery = LiPoBattery(capacity_Ah=15.0, initial_soc=1.0)
        battery.apply_current(current=I, duration=1200.0)
        print("-------------------------------------------------------")
        print(battery)
    except ImportError:
        logger.warning("Battery-Klasse konnte für den Selbsttest nicht geladen werden.")
        
    print("======================================================\n")