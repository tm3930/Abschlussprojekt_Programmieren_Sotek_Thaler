from dataclasses import dataclass

@dataclass
class EbikeConfig:
    """Datenklasse der Ebike- und Fahrerparameter aus der Angabe"""

    rider_mass: float = 70.0

    bike_mass: float = 10.0

    cw_and_area: float = 0.5625 #Produkt von cw-Wert und Stirnfläche (m^2)

    diameter: float = 27 * 0.0254 #27 Zoll Rad in m,

    radius: float = diameter / 2

    motor_constant: float = 1.5 #Motorkonstante (Formelzeichem Km)
    

if __name__ == "__main__":
    config = EbikeConfig()
    
    print(config)
    print(f"Gesamtmasse: {config.rider_mass + config.bike_mass} kg")
    print(f"Masse von: Fahrer -> {config.rider_mass} kg, Ebike -> {config.bike_mass} kg")
    print(f"Raddurchmesser: {config.diameter} m")
