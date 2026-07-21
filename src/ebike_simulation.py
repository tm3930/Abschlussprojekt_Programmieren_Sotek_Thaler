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
from numba import njit

from battery import Battery, LiPoBattery
from motor import Motor
from ebike_dynamics import EbikeDynamics
from gps_data import GPSData
from ebike_config import EbikeConfig

from constants import MPS_TO_KMH

logger = logging.getLogger(__name__)


# =============================================================================
# NUMBA KERNEL: Hochperformante, JIT-kompilierte Simulations-Engine
# =============================================================================
@njit
def _run_simulation_kernel(
    times: np.ndarray,
    env_temp: np.ndarray,
    motor_current_arr: np.ndarray,
    initial_soc: float,
    initial_temp: float,
    capacity_ampere_s: float,
    internal_resistance: float,
    thermal_mass: float,
    cooling_coeff: float,
    efficiency: float,
    max_charge_current: float,
    max_discharge_current: float,
    ocv_table: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

    n_points = len(times)
    soc_profile = np.zeros(n_points)
    temp_profile = np.zeros(n_points)
    dissipated_power_profile = np.zeros(n_points)

    soc_profile[0] = initial_soc
    temp_profile[0] = initial_temp

    curr_soc = initial_soc
    curr_temp = initial_temp

    for i in range(n_points - 1):
        dt = times[i+1] - times[i]
        motor_current = motor_current_arr[i+1]

        # 1. Bestimmung des effektiven Akku-Stroms
        if motor_current > 0.0:  # Entladen
            ideal_battery_current = motor_current / efficiency
            battery_current = min(ideal_battery_current, max_discharge_current)
            dissipated_power_profile[i+1] = 0.0

        elif motor_current < 0.0:  # Laden / Rekuperation
            ideal_charge_current = abs(motor_current) * efficiency
            is_full = curr_soc >= 1.0 - 1e-9

            # Strom begrenzen, falls Akku voll oder Max-Ladestrom überschritten
            if is_full:
                effective_charge = 0.0
            else:
                effective_charge = min(ideal_charge_current, max_charge_current)

            # battery_current ist negativ für den Ladefall
            battery_current = -effective_charge

            # OCV elegant via np.interp ermitteln (Numba-kompatibel)
            ocv = np.interp(curr_soc, ocv_table[:, 0], ocv_table[:, 1])

            # Effektiver Innenwiderstand & Klemmspannung
            temp_factor = 1.0 + 0.05 * max(0.0, 25.0 - curr_temp)
            effective_r = internal_resistance * temp_factor
            terminal_voltage = ocv - effective_r * battery_current

            # Nicht nutzbare Rekuperationsleistung (Clipping-Verluste) aufzeichnen
            uncapped_lost_current = ideal_charge_current - effective_charge
            dissipated_power_profile[i+1] = uncapped_lost_current * terminal_voltage

        else:
            battery_current = 0.0
            dissipated_power_profile[i+1] = 0.0

        # 2. Thermik-Update
        temp_factor = 1.0 + 0.05 * max(0.0, 25.0 - curr_temp)
        effective_r = internal_resistance * temp_factor

        curr_temp += (env_temp[i] - curr_temp) * cooling_coeff * dt
        curr_temp += (battery_current**2 * effective_r * dt) / thermal_mass

        # 3. Kapazitätsupdate (SoC)
        curr_soc -= (battery_current * dt) / capacity_ampere_s
        curr_soc = max(0.0, min(curr_soc, 1.0))

        soc_profile[i+1] = curr_soc
        temp_profile[i+1] = curr_temp

    return soc_profile, temp_profile, dissipated_power_profile


# =============================================================================
# CLASS DEFINITION
# =============================================================================
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
        logger.info("Starte E-Bike Simulation (mit Numba-Beschleunigung)...")

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

        # Vollständig vektorisierte Vorberechnung der Kräfte & Ströme
        v_kmh = velocity * MPS_TO_KMH
        f_motor = np.where(
            forward_force > 0,
            np.where(
                v_kmh >= self.config.max_support_speed_kmh,
                0.0,
                forward_force * self.config.eco_assist_factor
            ),
            forward_force
        )
        motor_current_arr = self.motor.current(self.motor.get_torque(f_motor))

        # OCV-Kennlinie als 2D-NumPy-Array für den Numba-Kernel aufbereiten
        ocv_array = np.array(self.battery.ocv_table, dtype=np.float64)

        # Aufruf des JIT-kompilierten Kernels (keine Python-Schleife)
        soc_profile, temp_profile, dissipated_power_profile = _run_simulation_kernel(
            times=times,
            env_temp=temperature,
            motor_current_arr=motor_current_arr,
            initial_soc=float(self.battery.soc),
            initial_temp=float(self.battery.temperature),
            capacity_ampere_s=float(self.battery.capacity_ampere_s),
            internal_resistance=float(self.battery.internal_resistance),
            thermal_mass=float(self.config.battery_thermal_mass_j_k),
            cooling_coeff=float(self.config.cooling_coefficient),
            efficiency=float(self.config.system_efficiency),
            max_charge_current=float(self.config.max_charge_current_a),
            max_discharge_current=float(self.config.max_discharge_current_a),
            ocv_table=ocv_array
        )

        # Zustand des Akkus nach der Simulation synchronisieren
        self.battery.soc = soc_profile[-1]
        self.battery.temperature = temp_profile[-1]

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
        '''
        logger.info("Erstelle Simulations-Zusammenfassung (Summary)...")

        total_time_s = data["time"].iloc[-1] - data["time"].iloc[0]
        total_distance_m = data["distance"].iloc[-1]
        avg_velocity_kmh = data["velocity"].mean() * 3.6
        max_velocity_kmh = data["velocity"].max() * 3.6

        delta_ele = np.diff(data["ele"].to_numpy())
        positive_elevation_gain = np.sum(delta_ele[delta_ele > 0])
        negative_elevation_loss = np.sum(np.abs(delta_ele[delta_ele < 0]))

        max_power_w = data["power"].max()

        times = data["time"].to_numpy()
        power = data["power"].to_numpy()

        # Positive Leistung = Vom System aufgebrachte mechanische Antriebsenergie
        positive_power = np.maximum(power, 0.0)
        mechanical_energy_joule = np.trapezoid(positive_power, times)
        mechanical_energy_wh = mechanical_energy_joule / 3600.0

        # Optional: Generierte Rekuperationsenergie (negativ) separat auswerten
        recuperated_power = np.minimum(power, 0.0)
        recuperated_energy_joule = np.abs(np.trapezoid(recuperated_power, times))
        recuperated_energy_wh = recuperated_energy_joule / 3600.0

        dissipated_energy_joule = np.trapezoid(data["dissipated_power"].to_numpy(), times)
        dissipated_energy_wh = dissipated_energy_joule / 3600.0

        start_soc = data["soc"].iloc[0] * 100.0
        end_soc = data["soc"].iloc[-1] * 100.0
        soc_consumed = start_soc - end_soc

        stats = {
            "total_time_s": float(total_time_s),
            "total_distance_km": float(total_distance_m / 1000.0),
            "avg_velocity_kmh": float(avg_velocity_kmh),
            "max_velocity_kmh": float(max_velocity_kmh),
            "elevation_gain_m": float(positive_elevation_gain),
            "elevation_loss_m": float(negative_elevation_loss),
            "max_power_w": float(max_power_w),
            "mechanical_energy_wh": float(mechanical_energy_wh),
            "recuperated_energy_wh": float(recuperated_energy_wh),
            "start_soc_percent": float(start_soc),
            "end_soc_percent": float(end_soc),
            "consumed_soc_percent": float(soc_consumed),
            "dissipated_energy_wh": float(dissipated_energy_wh)
        }

        logger.info("Summary erfolgreich berechnet.")
        return stats

    def export_results(self, data: pd.DataFrame, filename: str = "simulation_results.csv") -> Path:
        '''
        Exportiert das DataFrame mit den Simulationsergebnissen als CSV-Datei
        in das Verzeichnis 'data/processed'.

        Eingabe:
            data: Pandas DataFrame mit den Simulationsergebnissen.
            filename: Name der Ziel-CSV-Datei (Standard: "simulation_results.csv").

        Ausgabe:
            Path: Absoluter Pfad zur gespeicherten CSV-Datei.
        '''
        logger.info("Starte Export der Simulationsergebnisse...")

        if data.empty:
            logger.error("Export abgebrochen: Das übergebene DataFrame ist leer.")
            raise ValueError("Das DataFrame enthält keine Daten zum Exportieren.")

        # Projekt-Stammverzeichnis ermitteln (analog zu data_from_csv.py)
        base_dir = Path(__file__).resolve().parent.parent
        target_dir = base_dir / "data" / "processed"

        # Zielverzeichnis erstellen, falls es noch nicht existiert
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / filename

        try:
            # CSV-Export mit Semikolon als Trennzeichen (analog zum Einleseformat)
            data.to_csv(file_path, sep=";", index=False, float_format="%.6f")
            logger.info("Simulationsergebnisse erfolgreich unter '%s' gespeichert.", file_path)
        except Exception as e:
            logger.error("Fehler beim Speichern der CSV-Datei '%s': %s", file_path, e)
            raise IOError(f"Die Datei konnte nicht gespeichert werden: {e}") from e

        return file_path

    def __str__(self) -> str:
        '''
        Erzeugt eine kurze Übersicht über das geladene Simulations-Setup.
        '''
        return (
            f"EBikeSimulation ("
            f"Akku: {type(self.battery).__name__}, "
            f"Datenpunkte: {len(self.gps_data.data)}, "
            f"Gesamtmasse: {self.config.total_mass:.1f} kg)"
        )


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logger.info("Starte Selbsttest ebike_simulation...")

    try:
        from data_from_csv import get_data_from_csv

        # 1. Konfiguration & Daten laden
        cfg = EbikeConfig()
        raw_data = get_data_from_csv("final_project_input_data.csv")
        start_temp = raw_data["temperature"].iloc[0]

        # 2. Objekte mit cfg instanziieren
        bat = LiPoBattery(capacity_ampere_h=cfg.battery_capacity_ah, initial_temp=start_temp)
        gps = GPSData(raw_data)
        mot = Motor(cfg)
        dyn = EbikeDynamics(cfg)

        # 3. Simulation zusammenbauen
        sim = EBikeSimulation(
            battery=bat,
            gps_data=gps,
            motor=mot,
            ebike_dynamics=dyn,
            config=cfg
        )

        print(f"\n{sim}\n")

        # Ausführung & Zusammenfassung
        results = sim.run()
        sim_stats = sim.summary(results)  # Umbenannt von stats -> sim_stats

        print("=== TEST-ERGEBNIS ===")
        print(
            f"Strecke: {sim_stats['total_distance_km']:.2f} km | "
            f"Zeit: {sim_stats['total_time_s'] / 60.0:.1f} min"
        )
        print(
            f"Energie: {sim_stats['mechanical_energy_wh']:.1f} Wh | "
            f"SoC: {sim_stats['start_soc_percent']:.0f}% -> {sim_stats['end_soc_percent']:.0f}%\n"
        )

    except Exception as e:
        logger.error("Test fehlgeschlagen: %s", e)
        raise
