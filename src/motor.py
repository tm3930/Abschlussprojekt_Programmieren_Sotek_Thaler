import logging

logger = logging.getLogger(__name__)

class Motor:
    """Klasse für den Ebike-Motor"""

    def __init__(
            self,
            motor_constant: float, #Motorkonstante (Formelzeichen: Km)
            radius: float #Radius des Rades
            ) -> None:

        self.motor_constant = motor_constant
        self.radius = radius

        #Fehlermeldungen
        if motor_constant <= 0:
            raise ValueError(f"Motorkonstante muss größer als 0 sein, aktuell: {motor_constant}")
        if radius <= 0:
            raise ValueError(f"Radradius muss größer als 0 sein, aktuell: {radius}")
        
        #Logging über aktuelle Werte des Motors/Rads
        logger.info(f"Motorwerte: Motorkonstante = {motor_constant} Nm/A, Radius des Rads = {radius:.2f} m")

    def torque(self, F: float) -> float:
        """Funktion zur ausgabe des Drehmomentes des Rads nach der Formel T = F*r."""

        return F * self.radius

    def current(self, torque: float) -> float:
        """Funktion zur Ausgabe des Motorstroms nach der Formel I = T/Km."""

        current = torque / self.motor_constant
        logger.debug (f"Strom von {current:.2f} A bei einem Drehmoment von: {torque:.2f} Nm")
        return current

    def __str__(self) -> str:
        """Funktion zur sinnvollen Ausgabe der Werte bei Überprüfung mit "print(motor)".
        
        Gibt beim Selbsttest lesbare Information über den Motor aus."""

        return (f"Ebike-Motor: (Km = {self.motor_constant} Nm/A, r = {self.radius:.2f} m)")


if __name__ == "__main__":
    #Logging-Konfiguration
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(asctime)s - %(message)s")

    #Kennwerte (laut Angbe)
    diameter = 27 * 0.0254 #Umrechnung des Zoll-Wertes auf Meter
    motor = Motor(motor_constant = 1.5, radius = diameter / 2)

    #Selbsttest der Klasse
    F = 100.0
    T = motor.torque(F)
    I = motor.current(T)
    print(motor)
    print(f"Kraft F = {F:.0f} N - Drehmoment T = {T:.2f} Nm - Motorstrom I = {I:.2f} A")