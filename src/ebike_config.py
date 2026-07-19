'''
Modul zur Konfiguration und Speicherung der physikalischen Parameter des E-Bikes und Fahrers.

Dieses Modul stellt die Datenklasse `EbikeConfig` bereit, welche alle relevanten 
Konstanten und Vorgaben (wie Massen, aerodynamische Eigenschaften, Raddurchmesser 
und Motorkonstanten) für die Simulation zentralisiert verwaltet. Der Radradius 
wird nach der Initialisierung automatisch aus dem Durchmesser berechnet.
'''

from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class EbikeConfig:
    '''
    Datenklasse für die E-Bike- und Fahrerparameter.
    '''

    rider_mass: float = 70.0

    bike_mass: float = 10.0

    cw_and_area: float = 0.5625  # Produkt aus cw-Wert und Stirnfläche (m²)

    diameter: float = 27 * 0.0254  # 27-Zoll-Rad umgerechnet in Meter

    motor_constant: float = 1.5  # Motorkonstante (Formelzeichen: Km)

    # Radius wird nicht beim Erstellen übergeben, sondern in __post_init__ berechnet
    radius: float = field(init=False)

    def __post_init__(self):
        '''
        Wird automatisch nach dem Erstellen des Objekts ausgeführt.
        '''

        # Berechnet den Radius immer passend zum (evtl. geänderten) Durchmesser
        self.radius = self.diameter / 2

        logger.info("Daten aus der E-Bike-Konfiguration erfolgreich erfasst.")


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

    logger.info("Starte ebike_config Datei...")

    # Werte hereinladen
    config = EbikeConfig()

    # Ausgabe der Werte im Terminal
    print("\n================= E-BIKE PARAMETER =================")
    print(f"Masse Fahrer:     {config.rider_mass:>6.1f} kg")
    print(f"Masse E-Bike:     {config.bike_mass:>6.1f} kg")
    print(f"Gesamtmasse:      {config.rider_mass + config.bike_mass:>6.1f} kg")
    print("----------------------------------------------------")
    print(f"Raddurchmesser:   {config.diameter:>6.4f} m")
    print(f"Radradius:        {config.radius:>6.4f} m")
    print("----------------------------------------------------")
    print(f"Motorkonstante:   {config.motor_constant:>6.2f} (Km)")
    print(f"cw-Wert * Fläche: {config.cw_and_area:>6.4f} m²")
    print("=====================================================\n")

    logger.info("Überprüfung erfolgreich abgeschlossen.")
