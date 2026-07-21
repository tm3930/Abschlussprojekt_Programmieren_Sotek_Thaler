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
    #Angaben aus der Aufgabenstellung
    rider_mass: float = 70.0
    bike_mass: float = 10.0
    cw_and_area: float = 0.5625  # Produkt aus cw-Wert und Stirnfläche (m²)
    diameter: float = 27 * 0.0254  # 27-Zoll-Rad umgerechnet in Meter
    motor_constant: float = 1.5  # Motorkonstante (Formelzeichen: Km)

    #Angaben durch Recherche ermittelt
    c_r: float = 0.005     # Rollwiderstandskoeffizient für Asphalt (ca. 0.005)
    max_support_speed_kmh: float = 25.0       # Gesetzliches Limit
    eco_assist_factor: float = 0.35           # Unterstützungsfaktor ECO

    #Wirkungsgrad & Stromgrenzen
    system_efficiency: float = 0.85           # Gesamtwirkungsgrad des Antriebs
    max_charge_current_a: float = 10.0        # Max. Rekuperationsstrom
    max_discharge_current_a: float = 15.0     # Max. Entladestrom

    #Thermische Akku-Eigenschaften
    battery_thermal_mass_j_k: float = 5000.0  # Thermische Kapazität des Akkus
    cooling_coefficient: float = 0.005        # Wärmeübergang an Luft

    battery_capacity_ah: float = 15.0         # Akkukapazität in Ah
    initial_soc: float = 1.0                   # Start-Ladezustand (1.0 = 100%)

    #Filter-Fenstergrößen
    velocity_window_size: int = 5             # Fenster für Geschwindigkeitsglättung
    accel_window_size: int = 10               # Fenster für Beschleunigungsglättung
    incline_window_size: int = 10             # Fenster für Steigungsglättung

    # Radius wird nicht beim Erstellen übergeben, sondern in __post_init__ berechnet
    radius: float = field(init=False)
    total_mass: float = field(init=False)

    def __post_init__(self):
        '''
        Wird automatisch nach dem Erstellen des Objekts ausgeführt.
        '''

        # Berechnet den Radius immer passend zum (evtl. geänderten) Durchmesser
        self.radius = self.diameter / 2
        self.total_mass = self.rider_mass + self.bike_mass

        logger.info("Daten aus der E-Bike-Konfiguration erfolgreich erfasst.")

    def __str__(self) -> str:
        '''
        Erzeugt eine übersichtliche Text-Repräsentation der wichtigsten Konfigurationsparameter.
        '''
        return (
            f"EbikeConfig ("
            f"Masse: {self.total_mass:.1f} kg"
            f"[Fahrer: {self.rider_mass:.1f} kg, Bike: {self.bike_mass:.1f} kg], "
            f"Km: {self.motor_constant:.2f} Nm/A, "
            f"Rad-Ø: {self.diameter:.3f} m, "
            f"Akku: {self.battery_capacity_ah:.1f} Ah)"
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
