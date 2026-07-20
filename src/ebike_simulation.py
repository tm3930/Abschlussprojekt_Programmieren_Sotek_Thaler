'''
Modul zur Koordination, Durchführung und Auswertung der E-Bike-Fahrsimulation.

Dieses Modul enthält die Klasse `EBikeSimulation`, die als zentraler Integrationspunkt 
dient. Sie kombiniert GPS-Fahrdaten (`GPSData`), fahrzeugdynamische Gleichungen (`EbikeDynamics`), 
Motorkennwerte (`Motor`) und das elektro-thermische Batteriemodell (`Battery`), um den 
Gesamtzustand des E-Bikes entlang eines Streckenprofils zeitschrittbasiert zu simulieren.
'''

from pathlib import Path
import logging
import numpy as np
import pandas as pd

from battery import Battery
from motor import Motor
from ebike_dynamics import EbikeDynamics
from gps_data import GPSData
from ebike_config import EbikeConfig

from constants import MPS_TO_KMH

logger = logging.getLogger(__name__)


class EBikeSimulation:
    '''
    Klasse zur Durchführung, Auswertung und zum Export der gesamten E-Bike Simulation.
    '''

    def __init__(
        self,
        battery: Battery,
        gps_data: GPSData,
        motor: Motor = Motor(),
        ebike_dynamics: EbikeDynamics = EbikeDynamics(),
        config: EbikeConfig = EbikeConfig()
    ) -> None:
        '''
        Initialisiert den Simulations-Orchestrator mit den erforderlichen Subsystemen.

        Eingabe:
            battery: Instanz eines Batteriesystems (z.B. LiPoBattery oder NMCBattery).
            gps_data: Instanz mit den geladenen und vorverarbeiteten GPS-Rohdaten.
            motor: Instanz des Motormodells zur Drehmoment- und Stromberechnung.
            ebike_dynamics: Instanz des Dynamikmodells für die physikalische Kraftberechnung.
        '''
        self.battery = battery
        self.gps_data = gps_data
        self.motor = motor
        self.ebike_dynamics = ebike_dynamics
        self.config = config

    def run(self) -> pd.DataFrame:
        """
        Führt die zeitschrittbasierte Fahrsimulation aus.
        """
        logger.info("Starte E-Bike Simulation...")

        # GPS-Fahrdaten extrahieren
        data = self.gps_data.data.copy()
        elevation = data["ele"].to_numpy()
        temperature = data["temperature"].to_numpy()
        distance = self.gps_data.get_distance()

        # 1. Glättung mit Parametern aus EbikeConfig
        velocity_raw = self.gps_data.get_velocity(distance)
        velocity = (
            pd.Series(velocity_raw)
            .rolling(window=self.config.velocity_window_size, min_periods=1, center=True)
            .mean().to_numpy()
        )

        accel_raw = self.gps_data.get_acceleration(velocity)
        acceleration = (
            pd.Series(accel_raw)
            .rolling(window=self.config.accel_window_size, min_periods=1, center=True)
            .mean().to_numpy()
        )

        incline_raw = self.gps_data.get_incline(distance)
        incline = (
            pd.Series(incline_raw)
            .rolling(window=self.config.incline_window_size, min_periods=1, center=True)
            .mean().to_numpy()
        )

        # Physikalische Kräfte & mechanische Leistung berechnen
        drag_force = self.ebike_dynamics.get_drag_force(velocity, elevation, temperature)
        rolling_resistance = self.ebike_dynamics.get_rolling_resistance(incline)
        incline_force = self.ebike_dynamics.get_incline_force(incline)
        forward_force = (
            self.ebike_dynamics
            .get_total_force(acceleration, incline_force, drag_force, rolling_resistance)
        )
        power = self.ebike_dynamics.get_power(forward_force, velocity)

        times = data["time"].to_numpy()
        n_points = len(times)

        soc_profile = np.zeros(n_points)
        soc_profile[0] = self.battery.soc

        temp_profile = np.zeros(n_points)
        temp_profile[0] = self.battery.temperature

        dissipated_power_profile = np.zeros(n_points)

        # Zeitschrittbasierte Simulationsschleife
        for i in range(n_points - 1):
            duration = times[i+1] - times[i]

            f_roll = self.ebike_dynamics.get_rolling_resistance(incline[i+1])
            f_drive = (
                self.ebike_dynamics
                .get_total_force(acceleration[i+1], incline_force[i+1], drag_force[i+1], f_roll)
            )

            v_kmh = velocity[i+1] * MPS_TO_KMH

            # --- Gesetzliche Begrenzung auf 25 km/h ---
            if f_drive > 0:
                if v_kmh >= self.config.max_support_speed_kmh:
                    f_motor = 0.0
                else:
                    f_motor = f_drive * self.config.eco_assist_factor
            else:
                f_motor = f_drive

            motor_current = self.motor.current(self.motor.get_torque(f_motor))

            # --- Wirkungsgrad und Leistungsgrenzen aus ZENTRALER Config ---
            efficiency = self.config.system_efficiency
            max_charge_current = self.config.max_charge_current_a
            max_discharge_current = self.config.max_discharge_current_a

            if motor_current > 0:  # Motorbetrieb (Entladen)
                ideal_battery_current = motor_current / efficiency
                battery_current = min(ideal_battery_current, max_discharge_current)

            elif motor_current < 0:  # Generatorbetrieb (Laden)
                ideal_charge_current = abs(motor_current) * efficiency

                if self.battery.is_full() or ideal_charge_current > max_charge_current:
                    effective_charge = min(ideal_charge_current, max_charge_current)
                    battery_current = -effective_charge
                    dissipated_power_profile[i+1] = (
                        (ideal_charge_current - effective_charge) * self.battery.terminal_voltage()
                    )
                else:
                    battery_current = -ideal_charge_current
            else:
                battery_current = 0.0

            # --- Thermik-Update mit ZENTRALEN Parametern ---
            self.battery.temperature += (
                (data["temperature"].iloc[i] - self.battery.temperature)
                * self.config.cooling_coefficient
                * duration
            )
            self.battery.temperature += (
                (battery_current**2 * self.battery.get_effective_resistance() * duration)
                / self.config.battery_thermal_mass_j_k
            )

            # Akku-Kapazitätsupdate durchführen
            self.battery.apply_current(battery_current, duration)
            soc_profile[i+1] = self.battery.soc
            temp_profile[i+1] = self.battery.temperature

        # Vektoren ins DataFrame schreiben
        data["distance"] = distance
        data["velocity"] = velocity
        data["acceleration"] = acceleration
        data["incline"] = incline
        data["forward_force"] = forward_force
        data["power"] = power
        data["soc"] = soc_profile
        data["battery_temp"] = temp_profile
        data["dissipated_power"] = dissipated_power_profile

        logger.info("EBike Simulation beendet.")
        return data

    def summary(self, data: pd.DataFrame) -> dict:
        '''
        Erstellt eine zusammenfassende Statistik über die durchgeführte E-Bike-Simulation.

        Eingabe:
            data: Das von run() zurückgegebene DataFrame mit allen Simulationswerten.

        Ausgabe:
            dict: Ein Dictionary mit den wichtigsten aggregierten Kennzahlen der Fahrt.
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
        negative_elevation_loss = np.sum(np.abs(delta_ele[delta_ele < 0]))

        # 4. Leistungs- und Energieberechnung
        max_power_w = data["power"].max()

        times = data["time"].to_numpy()
        power = data["power"].to_numpy()

        # Numerische Integration der mechanischen und dissipierten Leistung über die Zeit
        mechanical_energy_joule = np.trapezoid(power, times)
        mechanical_energy_wh = mechanical_energy_joule / 3600.0
        dissipated_energy_joule = np.trapezoid(data["dissipated_power"].to_numpy(), times)
        dissipated_energy_wh = dissipated_energy_joule / 3600.0

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
            "elevation_loss_m": float(negative_elevation_loss),
            "max_power_w": float(max_power_w),
            "mechanical_energy_wh": float(mechanical_energy_wh),
            "start_soc_percent": float(start_soc),
            "end_soc_percent": float(end_soc),
            "consumed_soc_percent": float(soc_consumed),
            "dissipated_energy_wh": float(dissipated_energy_wh)
        }

        logger.info("Summary erfolgreich berechnet.")
        return stats

    def export_results(self, data: pd.DataFrame) -> None:
        '''
        Exportiert die prozessierten Simulationsdaten in eine CSV-Datei.
        Legt den Zielordner automatisch an, falls er noch nicht existiert.

        Eingabe:
            data: Das Pandas DataFrame mit den berechneten Simulationsergebnissen.
        '''
        logger.info("Starte Export der Simulationsdaten...")

        # Pfad zur CSV-Datei dynamisch ermitteln (data/processed/simulated_ebike_data.csv)
        base_dir = Path(__file__).resolve().parent.parent
        output_dir = base_dir / "data" / "processed"
        output_path = output_dir / "simulated_ebike_data.csv"

        try:
            # Falls die Ordnerstruktur 'data/processed/' noch nicht existiert, erstellen
            output_dir.mkdir(parents=True, exist_ok=True)

            # Abspeichern (mit Semikolon getrennt, ohne den Pandas-Index)
            data.to_csv(output_path, sep=";", index=False)
            logger.info("Simulationsdaten erfolgreich exportiert nach: %s", output_path)

        except OSError as e:
            logger.error(
                "Fehler beim Erstellen des Export-Verzeichnisses oder beim Schreiben der Datei: %s",
                e
            )
            raise RuntimeError(f"Export fehlgeschlagen: {e}") from e
