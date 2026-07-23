'''
Modul zur Koordination, Durchführung und Auswertung der E-Bike-Fahrsimulation.

Dieses Modul enthält die Klasse `EBikeSimulation`, die als zentraler Integrationspunkt 
dient. Sie kombiniert GPS-Fahrdaten (`GPSData`), fahrzeugdynamische Gleichungen (`EbikeDynamics`), 
Motorkennwerte (`Motor`) und das elektro-thermische Batteriemodell (`Battery`), um den 
Gesamtzustand des E-Bikes entlang eines Streckenprofils zeitschrittbasiert zu simulieren.
'''

#generelle Imports
from pathlib import Path
from typing import NamedTuple
import logging
import numpy as np
import pandas as pd
from numba import njit

#Imports von anderen selbstgeschriebenen Dateien
from battery import Battery, LiPoBattery
from motor import Motor
from ebike_dynamics import EbikeDynamics
from gps_data import GPSData
from ebike_config import EbikeConfig
from constants import MPS_TO_KMH

#__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
logger = logging.getLogger(__name__)

class SimParams(NamedTuple):
    '''
    Container für Parameter welche dann an _run_simulation übergeben werden können
    '''
    initial_soc: float
    initial_temp: float
    capacity_ampere_s: float
    internal_resistance: float
    temp_coeff_resistance: float
    thermal_mass: float
    cooling_coeff: float
    efficiency: float
    max_charge_current: float
    max_discharge_current: float

#NUMBA KERNEL: Hochperformante, JIT-kompilierte Simulations-Engine
@njit
def _run_simulation(
    times: np.ndarray,
    env_temp: np.ndarray,
    motor_current_arr: np.ndarray,
    ocv_table: np.ndarray,
    params: SimParams
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

    #Arrays laden & Anfangswerte vorbereiten
    n_points = len(times)
    soc_profile = np.zeros(n_points)
    temp_profile = np.zeros(n_points)
    dissipated_power_profile = np.zeros(n_points)

    soc_profile[0] = params.initial_soc
    temp_profile[0] = params.initial_temp

    curr_soc = params.initial_soc
    curr_temp = params.initial_temp

    for i in range(n_points - 1):
        dt = times[i+1] - times[i]
        motor_current = motor_current_arr[i+1]

        dumped_power: float = 0.0

        #Bestimmung des effektiven Akku-Stroms
        if motor_current > 0.0:  #Entladen
            ideal_battery_current = motor_current / params.efficiency
            battery_current = min(ideal_battery_current, params.max_discharge_current)

        elif motor_current < 0.0:  #Laden / Rekuperation
            ideal_charge_current = abs(motor_current) * params.efficiency
            is_full = curr_soc >= 1.0 - 1e-9

            #Strom begrenzen, falls Akku voll oder Max-Ladestrom überschritten
            if is_full:
                effective_charge = 0.0
            else:
                effective_charge = min(ideal_charge_current, params.max_charge_current)

            #battery_current ist negativ für den Ladefall
            battery_current = -effective_charge

            #OCV ermitteln
            ocv = np.interp(curr_soc, ocv_table[:, 0], ocv_table[:, 1])

            #Effektiver Innenwiderstand & Klemmspannung
            temp_factor_tmp = 1.0 + params.temp_coeff_resistance * max(0.0, 25.0 - curr_temp)
            eff_r_tmp = params.internal_resistance * temp_factor_tmp
            terminal_voltage = ocv - eff_r_tmp * battery_current

            #Weggeregelte Leistung (Verlust an Bremsen)
            uncapped_lost_current = ideal_charge_current - effective_charge
            dumped_power = uncapped_lost_current * terminal_voltage

        else:
            battery_current = 0.0

        #Thermik-Update
        temp_factor = 1.0 + params.temp_coeff_resistance * max(0.0, 25.0 - curr_temp)
        effective_r = params.internal_resistance * temp_factor

        battery_heat_power = battery_current ** 2 * effective_r

        dissipated_power_profile[i+1] = battery_heat_power + dumped_power

        curr_temp += (env_temp[i] - curr_temp) * params.cooling_coeff * dt
        curr_temp += (battery_current**2 * effective_r * dt) / params.thermal_mass

        #Kapazitätsupdate (SoC)
        curr_soc -= (battery_current * dt) / params.capacity_ampere_s
        curr_soc = max(0.0, min(curr_soc, 1.0))

        soc_profile[i+1] = curr_soc
        temp_profile[i+1] = curr_temp

    return soc_profile, temp_profile, dissipated_power_profile



class EBikeSimulation:
    '''
    Klasse zur Durchführung, Auswertung und zum Export der gesamten E-Bike Simulation.
    '''

    def __init__(
        self,
        gps_data: GPSData,
        battery: Battery = None,
        motor: Motor = None,
        ebike_dynamics: EbikeDynamics = None,
        config: EbikeConfig = None
    ) -> None:
        '''
        Initialisiert den Simulations-Orchestrator mit den erforderlichen Subsystemen.
        '''
        self.gps_data = gps_data
        self.battery = battery if battery is not None else LiPoBattery()
        self.motor = motor if motor is not None else Motor()
        self.ebike_dynamics = ebike_dynamics if ebike_dynamics is not None else EbikeDynamics()
        self.config = config if config is not None else EbikeConfig()

    def run(self) -> pd.DataFrame:
        '''
        Führt die zeitschrittbasierte Fahrsimulation aus.
        '''

        logger.info("Starte E-Bike Simulation...")

        #GPS-Fahrdaten extrahieren
        data = self.gps_data.data.copy()
        elevation = data["ele"].to_numpy()
        temperature = data["temperature"].to_numpy()
        distance = self.gps_data.get_distance()

        #Glättung der GPS Daten um extreme Werte zu unterbinden
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

        #Physikalische Kräfte & mechanische Leistung berechnen
        drag_force = self.ebike_dynamics.get_drag_force(velocity, elevation, temperature)
        rolling_resistance = self.ebike_dynamics.get_rolling_resistance(incline)
        incline_force = self.ebike_dynamics.get_incline_force(incline)
        forward_force = (
            self.ebike_dynamics
            .get_total_force(acceleration, incline_force, drag_force, rolling_resistance)
        )
        power = self.ebike_dynamics.get_power(forward_force, velocity)

        times = data["time"].to_numpy()

        #vektorisierte Vorberechnung der Kräfte & Ströme
        v_kmh = velocity * MPS_TO_KMH
        f_motor = np.where(
            forward_force > 0,
            np.where(
                v_kmh >= self.config.max_support_speed_kmh,
                0.0,
                forward_force * self.config.eco_assist_factor
            ),
            forward_force * self.config.recuperation_fraction
        )

        motor_torque = self.motor.get_torque(f_motor)
        motor_current_arr = self.motor.current(motor_torque)

        #OCV-Kennlinie als 2D-NumPy-Array für den Numba-Kernel aufbereiten
        ocv_array = np.array(self.battery.ocv_table, dtype=np.float64)

        #Parameter im Container bündeln
        sim_params = SimParams(
            initial_soc=float(self.battery.soc),
            initial_temp=float(self.battery.temperature),
            capacity_ampere_s=float(self.battery.capacity_ampere_s),
            internal_resistance=float(self.battery.internal_resistance),
            temp_coeff_resistance=float(self.config.temp_coeff_resistance),
            thermal_mass=float(self.config.battery_thermal_mass_j_k),
            cooling_coeff=float(self.config.cooling_coefficient),
            efficiency=float(self.config.system_efficiency),
            max_charge_current=float(self.config.max_charge_current_a),
            max_discharge_current=float(self.config.max_discharge_current_a)
        )

        #Aufruf des JIT-kompilierten Kernels
        soc_profile, temp_profile, dissipated_power_profile = _run_simulation(
            times=times,
            env_temp=temperature,
            motor_current_arr=motor_current_arr,
            ocv_table=ocv_array,
            params=sim_params
        )

        #Zustand des Akkus nach der Simulation synchronisieren
        self.battery.soc = soc_profile[-1]
        self.battery.temperature = temp_profile[-1]

        motor_rpm = (velocity * 60) / (2 * np.pi * self.config.radius)

        #Vektoren ins DataFrame schreiben
        data["distance"] = distance
        data["velocity"] = velocity
        data["acceleration"] = acceleration
        data["incline"] = incline
        data["forward_force"] = forward_force
        data["power"] = power
        data["soc"] = soc_profile
        data["battery_temp"] = temp_profile
        data["dissipated_power"] = dissipated_power_profile
        data["motor_current"] = motor_current_arr
        data["drag_force"] = drag_force
        data["rolling_resistance"] = rolling_resistance
        data["incline_force"] = incline_force
        data["motor_torque"] = motor_torque
        data["motor_rpm"] = motor_rpm

        logger.info("EBike Simulation beendet.")
        return data

    def summary(self, data: pd.DataFrame) -> dict:
        '''
        Erstellt eine zusammenfassende Statistik über die durchgeführte E-Bike-Simulation.
        '''

        logger.info("Erstelle Simulations-Zusammenfassung...")

        #Allgemeine Parameter zur Tour
        total_time_s = data["time"].iloc[-1] - data["time"].iloc[0]
        total_distance_m = data["distance"].iloc[-1]
        avg_velocity_kmh = data["velocity"].mean() * MPS_TO_KMH
        max_velocity_kmh = data["velocity"].max() * MPS_TO_KMH

        # Höhenmeter mit Schwellenwert gegen GPS-Rauschen gefiltert
        delta_ele = np.diff(data["ele"].to_numpy())
        positive_elevation_gain = np.sum(delta_ele[delta_ele > self.config.noise_filter_threshold])
        negative_elevation_loss = np.sum(
            np.abs(delta_ele[delta_ele < -self.config.noise_filter_threshold])
        )

        max_power_w = data["power"].max()

        times = data["time"].to_numpy()
        power = data["power"].to_numpy()

        #Positive Leistung = Vom System aufgebrachte mechanische Antriebsenergie
        positive_power = np.maximum(power, 0.0)
        mechanical_energy_joule = np.trapezoid(positive_power, times)
        mechanical_energy_wh = mechanical_energy_joule / 3600.0

        #Durchschnittliche Antriebsleistung (nur während aktiver Phasen > 0 W)
        active_power = positive_power[positive_power > 0]
        avg_power_w = float(np.mean(active_power)) if len(active_power) > 0 else 0.0

        #Generierte Rekuperationsenergie
        recuperated_power = np.minimum(power, 0.0)
        recuperated_energy_joule = np.abs(np.trapezoid(recuperated_power, times))
        recuperated_energy_wh = recuperated_energy_joule / 3600.0

        dissipated_energy_joule = np.trapezoid(data["dissipated_power"].to_numpy(), times)
        dissipated_energy_wh = dissipated_energy_joule / 3600.0

        start_soc = data["soc"].iloc[0] * 100.0
        end_soc = data["soc"].iloc[-1] * 100.0
        soc_consumed = start_soc - end_soc

        discharged_energy_wh = ((soc_consumed / 100.0)
            * self.battery.capacity_ampere_h
            * self.battery.open_circuit_voltage()
        )

        stats = {
            "total_time_s": float(total_time_s),
            "total_distance_km": float(total_distance_m / 1000.0),
            "avg_velocity_kmh": float(avg_velocity_kmh),
            "max_velocity_kmh": float(max_velocity_kmh),
            "elevation_gain_m": float(positive_elevation_gain),
            "elevation_loss_m": float(negative_elevation_loss),
            "max_power_w": float(max_power_w),
            "avg_power_w": float(avg_power_w),
            "mechanical_energy_wh": float(mechanical_energy_wh),
            "recuperated_energy_wh": float(recuperated_energy_wh),
            "dissipated_energy_wh": float(dissipated_energy_wh),
            "start_soc_percent": float(start_soc),
            "end_soc_percent": float(end_soc),
            "consumed_soc_percent": float(soc_consumed),
            'discharged_energy_wh': float(discharged_energy_wh)
        }

        logger.info("Summary erfolgreich berechnet.")
        return stats

    def export_results(self, data: pd.DataFrame, filename: str = "simulation_results.csv") -> None:
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

        #Projekt-Stammverzeichnis ermitteln
        base_dir = Path(__file__).resolve().parent.parent
        target_dir = base_dir / "data" / "processed"

        #Zielverzeichnis erstellen, falls es noch nicht existiert
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / filename

        try:
            #CSV-Export mit Semikolon als Trennzeichen
            data.to_csv(file_path, sep=";", index=False, float_format="%.6f")
            logger.info("Simulationsergebnisse erfolgreich unter '%s' gespeichert.", file_path)
        except Exception as e:
            logger.error("Fehler beim Speichern der CSV-Datei '%s': %s", file_path, e)
            raise IOError(f"Die Datei konnte nicht gespeichert werden: {e}") from e

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

        #Konfiguration & Daten laden
        raw_data = get_data_from_csv("final_project_input_data.csv")
        start_temp = raw_data["temperature"].iloc[0]

        #Objekte mit cfg instanziieren
        gps = GPSData(raw_data)

        #Simulation zusammenbauen
        sim = EBikeSimulation(gps_data=gps)

        print(f"\n{sim}\n")

        #Ausführung & Zusammenfassung
        results = sim.run()
        sim_stats = sim.summary(results)

        print("\n=== TEST-ERGEBNIS ===")
        print(
            f"Strecke: {sim_stats['total_distance_km']:.2f} km | "
            f"Zeit: {sim_stats['total_time_s'] / 60.0:.1f} min"
        )
        print(
            f"Energie: {sim_stats['mechanical_energy_wh']:.1f} Wh | "
            f"SoC: {sim_stats['start_soc_percent']:.0f}% -> {sim_stats['end_soc_percent']:.0f}%\n"
        )
        print("=== TEST-ERGEBNIS ===\n")

    except Exception as e:
        logger.error("Test fehlgeschlagen: %s", e)
        raise
