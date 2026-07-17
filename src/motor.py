import logging
import numpy as np
from ebike_config import EbikeConfig

logger = logging.getLogger(__name__)

class Motor:
    """Klasse für den Ebike-Motor"""

    def __init__(
            self,
            config: EbikeConfig
            ) -> None:

        self.config = config

        #Fehlermeldungen
        if self.config.motor_constant <= 0:
            raise ValueError(f"Motorkonstante muss größer als 0 sein, aktuell: {self.config.motor_constant}")
        if self.config.radius <= 0:
            raise ValueError(f"Radradius muss größer als 0 sein, aktuell: {self.config.radius}")
        
        #Logging über aktuelle Werte des Motors/Rads
        logger.info(f"Motorwerte: Motorkonstante = {self.config.motor_constant} Nm/A, Radius des Rads = {self.config.radius:.2f} m")

    def get_torque(self, force: np.ndarray) -> np.ndarray:
        '''
        Funktion zur Berechnung des Drehmoments am Rad.

        Eingabe:
            force: NumPy-Array mit den Kräften in Newton
            
        Ausgabe:
            np.ndarray: Array mit dem resultierenden Drehmoment in Newtonmetern (Nm)
        '''
        return force * self.config.radius

    def current(self, torque: float) -> float:
        """Funktion zur Ausgabe des Motorstroms nach der Formel I = T/Km."""

        current = torque / self.config.motor_constant
        logger.debug (f"Strom von {current:.2f} A bei einem Drehmoment von: {torque:.2f} Nm")
        return current

    def __str__(self) -> str:
        """Funktion zur sinnvollen Ausgabe der Werte bei Überprüfung mit "print(motor)".
        
        Gibt beim Selbsttest lesbare Information über den Motor aus."""

        return (f"Ebike-Motor: (Km = {self.config.motor_constant} Nm/A, r = {self.config.radius:.2f} m)")


if __name__ == "__main__":
    #Logging-Konfiguration
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(asctime)s - %(message)s")

    motor = Motor(config=EbikeConfig())

    #Selbsttest der Klasse
    F = 100.0
    T = motor.get_torque(F)
    I = motor.current(T)
    print(motor)
    print(f"Kraft F = {F:.0f} N - Drehmoment T = {T:.2f} Nm - Motorstrom I = {I:.2f} A")

    #Selbsttest mit der Battery-Klasse - 20min fahren
    from battery import LiPoBattery

    battery = LiPoBattery(capacity_Ah = 15.0, initial_soc = 1.0)
    battery.apply_current(current = I, duration = 1200.0)
    print(battery)