from pathlib import Path
import numpy as np
import logging
import pandas as pd

from battery import Battery
from motor import Motor
from ebike_dynamics import EbikeDynamics
from gps_data import GPSData

logger = logging.getLogger(__name__)


class EBikeSimulation:
    '''
    Klasse zur Durchführung, Auswertung und zum Export der gesamten E-Bike Simulation.
    '''

    def __init__(self, battery: Battery, gps_data: GPSData, motor: Motor = Motor(), ebike_dynamics: EbikeDynamics = EbikeDynamics()) -> None:
        self.battery = battery
        self.gps_data = gps_data
        self.motor = motor
        self.ebike_dynamics = ebike_dynamics
        
    def run(self) -> pd.DataFrame:
        logger.info("Starte E-Bike Simulation...")
        
        #GPS-Fahrdaten berechnen
        data = self.gps_data.data.copy()
        distance = self.gps_data.get_distance()
        velocity = self.gps_data.get_velocity(distance)
        acceleration = self.gps_data.get_acceleration(velocity)
        incline = self.gps_data.get_incline(distance)

        #Physikalische Kräfte & mechanische Leistung berechnen
        drag_force = self.ebike_dynamics.get_drag_force(velocity)
        incline_force = self.ebike_dynamics.get_incline_force(incline)
        forward_force = self.ebike_dynamics.get_total_force(acceleration, incline_force, drag_force)
        power = self.ebike_dynamics.get_power(forward_force, velocity)

        #Akku-Simulation (SoC-Verlauf berechnen)
        # Da apply_current Zeitschritte benötigt, iterieren wir über die Zeilen
        soc_profile = [self.battery.soc] 
        times = data["time"].to_numpy()

        for i in range(len(times) - 1):
            duration = times[i+1] - times[i]
            
            #Stromstärke für den aktuellen Punkt berechnen
            f_drive = forward_force[i]
            torque = self.motor.get_torque(f_drive)
            motor_current = self.motor.current(torque)
            
            # Akku entladen/laden und neuen SoC erfassen
            self.battery.apply_current(motor_current, duration)
            soc_profile.append(self.battery.soc)

        #Alle berechneten Werte in das DataFrame schreiben
        data["distance"] = distance
        data["velocity"] = velocity
        data["acceleration"] = acceleration
        data["incline"] = incline
        data["forward_force"] = forward_force
        data["power"] = power
        data["soc"] = soc_profile

        logger.info("EBike Simulation beendet")

        return data
    
    def summary(self, data: pd.DataFrame) -> dict:
        '''
        Erstellt eine zusammenfassende Statistik über die durchgeführte E-Bike-Simulation.

        Eingabe:
            data: Das von run() zurückgegebene DataFrame mit allen Simulationswerten.

        Ausgabe:
            dict: Ein Dictionary mit den wichtigsten Kennzahlen der Fahrt.
        '''
        
        logger.info("Erstelle Simulations-Zusammenfassung (Summary)...")

        # 1. Zeitberechnung
        total_time_s = data["time"].iloc[-1] - data["time"].iloc[0]
        
        # 2. Strecken- und Geschwindigkeitsberechnung
        total_distance_m = data["distance"].iloc[-1]
        avg_velocity_kmh = data["velocity"].mean() * 3.6
        max_velocity_kmh = data["velocity"].max() * 3.6

        # 3. Höhenprofil-Statistik (kumulierte Höhenmeter)
        delta_ele = np.diff(data["ele"].to_numpy())
        positive_elevation_gain = np.sum(delta_ele[delta_ele > 0])

        # 4. Leistungs- und Energieberechnung
        # Mechanische Arbeit (Joule = Watt * Sekunde) über numerische Integration (Trapezregel)
        # Da Leistung auch negativ sein kann (Rekuperation/Bergab), betrachten wir die verbrauchte Energie
        times = data["time"].to_numpy()
        power = data["power"].to_numpy()
        
        # Integration der mechanischen Leistung über die Zeit
        mechanical_energy_joule = np.trapezoid(power, times)
        mechanical_energy_wh = mechanical_energy_joule / 3600.0

        # 5. Akku-Statistik
        start_soc = data["soc"].iloc[0] * 100.0
        end_soc = data["soc"].iloc[-1] * 100.0
        soc_consumed = start_soc - end_soc

        # 6. Ergebnisse in Dictionary strukturieren
        stats = {
            "total_time_s": float(total_time_s),
            "total_distance_km": float(total_distance_m / 1000.0),
            "avg_velocity_kmh": float(avg_velocity_kmh),
            "max_velocity_kmh": float(max_velocity_kmh),
            "elevation_gain_m": float(positive_elevation_gain),
            "mechanical_energy_wh": float(mechanical_energy_wh),
            "start_soc_percent": float(start_soc),
            "end_soc_percent": float(end_soc),
            "consumed_soc_percent": float(soc_consumed)
        }

        logger.info("Summary erfolgreich berechnet.")
        return stats
    

    def export_results(self, data: pd.DataFrame) -> None:
        '''
        Exportiert die prozessierten Simulationsdaten in eine CSV-Datei.
        Legt den Zielordner automatisch an, falls er nicht existiert.

        Eingabe:
            data: Das Pandas DataFrame mit den berechneten Simulationsergebnissen.
        '''
        logger.info("Starte Export der Simulationsdaten...")

        # 1. Pfad zur CSV-Datei dynamisch ermitteln (data/processed/simulated_ebike_data.csv)
        base_dir = Path(__file__).resolve().parent.parent
        output_dir = base_dir / "data" / "processed"
        output_path = output_dir / "simulated_ebike_data.csv"
        
        try:
            # 2. Falls die Ordnerstruktur 'data/processed/' noch nicht existiert, erstellen wir sie
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Abspeichern (mit Semikolon getrennt, passend zur Input-Datei, ohne den Pandas-Index)
            data.to_csv(output_path, sep=";", index=False)
            logger.info("Simulationsdaten erfolgreich exportiert nach: %s", output_path)
            
        except OSError as e:
            logger.error("Fehler beim Erstellen des Export-Verzeichnisses oder beim Schreiben der Datei: %s", e)
            raise RuntimeError(f"Export fehlgeschlagen: {e}")


