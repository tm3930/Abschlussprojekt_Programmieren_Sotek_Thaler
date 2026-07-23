'''
Modul zur Konfiguration und Speicherung der physikalischen Parameter des E-Bikes und Fahrers.

Dieses Modul stellt die Datenklasse `EbikeConfig` bereit, welche alle relevanten 
Konstanten und Vorgaben (wie Massen, aerodynamische Eigenschaften, Raddurchmesser 
und Motorkonstanten) für die Simulation zentralisiert verwaltet. Der Radradius und
die Gesamtmasse wird nach der Initialisierung automatisch aus dem Durchmesser berechnet.
'''
#generelle Imports
import logging
from dataclasses import dataclass, field

#Imports von anderen selbstgeschriebenen Dateien
from constants import INCH_TO_M

#__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
logger = logging.getLogger(__name__)

@dataclass
class EbikeConfig:
    '''
    Datenklasse für die E-Bike- und Fahrerparameter.
    '''

    #Angaben aus der Aufgabenstellung
    rider_mass: float = 70.0        #kg
    bike_mass: float = 10.0         #kg
    cw_and_area: float = 0.5625     #Produkt aus cw-Wert und Stirnfläche (m²)
    diameter_inch: float = 27       #27-Zoll-Rad (inch)
    motor_constant: float = 1.5     #Motorkonstante (Nm/A)

    #Äbschätzen (nur für Kontrolle ob Steigungswerte aus GPS Daten sinnvoll sind)
    max_slope_limit = 0.6           #60% Steigung oder Gefälle als Grenze

    #Angaben durch Recherche ermittelt:
    #EBike:
    c_r: float = 0.005          #Rollwiderstandskoeffizient für Asphalt (ca. 0.005)
    max_support_speed_kmh: float = 25.0       #Gesetzliches Limit für Ebikes (km/h)
    eco_assist_factor: float = 0.35           #Unterstützungsfaktor ECO

    #Wirkungsgrad & Stromgrenzen
    system_efficiency: float = 0.85           #Gesamtwirkungsgrad des Antriebs
    max_charge_current_a: float = 10.0        #Max. Rekuperationsstrom (A)
    max_discharge_current_a: float = 15.0     #Max. Entladestrom (A)

    #Thermische Akku-Eigenschaften
    battery_thermal_mass_j_k: float = 5000.0  #Thermische Kapazität des Akkus (J/K)
    cooling_coefficient: float = 0.005        #Wärmeübergang an Luft
    temp_coeff_resistance: float = 0.05       #Temperaturkoeffizient bei 25°C (1/°C)
    recuperation_fraction: float = 0.40       #Anteil der Bremskraft, die der Motor aufnimmt

    #Akku:
    cells_parallel: int = 1                   #parallel geschaltene Akkus
    capacity_ampere_h: float = 15.0           #Akkukapazität (Ah)
    initial_soc: float = 1.0                  #Start-Ladezustand (1.0 = 100%)

    #Filter-Fenstergrößen
    #die Eingabedaten sind GPS-Daten und daher manchmal ungenau
    #durch Ableiten in v und a entstehen daher unrealistische Spitzen.
    #diese Spitzen können durch Glätten wieder ausgebügelt werden.
    velocity_window_size: int = 10            #Fenster für Geschwindigkeitsglättung
    accel_window_size: int = 20               #Fenster für Beschleunigungsglättung
    incline_window_size: int = 20             #Fenster für Steigungsglättung
    #Schwellenwert zur Filterung von GPS-Höhenrauschen
    noise_filter_threshold: float = 0.2       #(m)

    #diese Werte werden nicht beim Erstellen übergeben, sondern in __post_init__ berechnet
    diameter: float = field(init=False)       #Raddurchmesser (m)
    radius: float = field(init=False)         #Radradius (m)
    total_mass: float = field(init=False)     #Gesamtmasse (Fahrer + Ebike) (kg)

    def __post_init__(self):
        '''
        Wird automatisch nach dem Erstellen des Objekts ausgeführt.
        Werte werden immer "just in time" berechnet, auch bei geänderten Eingaben
        '''

        #Berechnungen:
        self.diameter = self.diameter_inch * INCH_TO_M
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
            f"Akku: {self.capacity_ampere_h:.1f} Ah)"
        )


if __name__ == "__main__":
    import sys

    #Logging System einrichten:
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

    #Output im Terminal dort werden nur INFOs, WARNINGs, ... angezeigt
    terminal_output = logging.StreamHandler(sys.stdout)
    terminal_output.setLevel(logging.INFO)
    terminal_output.setFormatter(log_format)

    #Output im Document: app.log: Hier werden auch alle DEBUGs angezeigt
    #hier können Fehler schnell identifiziert werden und im Code gefunden werden
    file_output = logging.FileHandler("app.log", mode="a", encoding="utf-8")
    file_output.setLevel(logging.DEBUG)
    file_output.setFormatter(log_format)

    #Einrichtung Protokollierungssystem für Logging (alle DEBUGs werden aufgezeichnet)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[terminal_output, file_output]
    )

    logger.info("Starte ebike_config Datei...")

    #Werte hereinladen
    config = EbikeConfig()

    # Ausgabe der Werte im Terminal
    print("\n=== E-BIKE PARAMETER ===")
    print(f"Masse Fahrer:       {config.rider_mass:>6.1f} kg")
    print(f"Masse E-Bike:       {config.bike_mass:>6.1f} kg")
    print(f"Gesamtmasse:        {config.total_mass:>6.1f} kg")
    print("------")
    print(f"Raddurchmesser:     {config.diameter:>6.4f} m ({config.diameter_inch} Zoll)")
    print(f"Radradius:          {config.radius:>6.4f} m")
    print(f"Rollwiderstand (cr):{config.c_r:>6.3f}")
    print(f"cw * Fläche:        {config.cw_and_area:>6.4f} m²")
    print("------")
    print(f"Motorkonstante:     {config.motor_constant:>6.2f} Nm/A")
    print(f"Max. V (Gesetz):    {config.max_support_speed_kmh:>6.1f} km/h")
    print(f"ECO-Faktor:         {config.eco_assist_factor:>6.2f}")
    print(f"Wirkungsgrad:       {config.system_efficiency:>6.2f}")
    print("------")
    print(f"Akkukapazität:      {config.capacity_ampere_h:>6.1f} Ah")
    print(f"Start-SoC:          {config.initial_soc * 100:>6.1f} %")
    print(f"Max. Entladestrom:  {config.max_discharge_current_a:>6.1f} A")
    print(f"Max. Ladestrom:     {config.max_charge_current_a:>6.1f} A")
    print(f"Akku Thermische M.: {config.battery_thermal_mass_j_k:>6.1f} J/K")
    print("=== E-BIKE PARAMETER ===\n")

    logger.info("Überprüfung erfolgreich abgeschlossen.")
