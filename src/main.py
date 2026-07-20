'''
Hauptprogramm zur Ausführung und Steuerung der E-Bike-Fahrsimulation.
'''
import logging
import sys
import matplotlib
import matplotlib.pyplot as plt

from battery import LiPoBattery
from gps_data import GPSData
from ebike_simulation import EBikeSimulation
from ebike_config import EbikeConfig
from motor import Motor
from ebike_dynamics import EbikeDynamics
from plotting_utils import (
    plot_speed_power_soc,
    plot_colored_elevation_profile,
    plot_elevation_profile
)
from data_from_csv import get_data_from_csv


# Setzt das interaktive Backend für die grafische Anzeige vor dem Import von pyplot
matplotlib.use('TkAgg')

def main() -> None:
    '''
    Hauptfunktion zur Steuerung des gesamten Simulations- und Auswerteprozesses.
    '''
    # --- GLOBALES LOGGING SYSTEM CONTEXT SETUP ---
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

    terminal_output = logging.StreamHandler(sys.stdout)
    terminal_output.setLevel(logging.INFO)
    terminal_output.setFormatter(log_format)

    file_output = logging.FileHandler("app.log", mode="a", encoding="utf-8")
    file_output.setLevel(logging.DEBUG)
    file_output.setFormatter(log_format)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[terminal_output, file_output]
    )

    logger = logging.getLogger(__name__)
    logger.info("Starte Hauptprogramm für die E-Bike Simulation...")

    try:
        # 1. Daten-Import aus der CSV-Datei
        raw_data = get_data_from_csv("final_project_input_data.csv")

        # 2. Zentrale Konfiguration EINMALIG instanziieren
        config = EbikeConfig()

        # 3. Start-Umgebungstemperatur auslesen
        start_temp = raw_data["temperature"].iloc[0]

        # 4. Systemkomponenten mit der ZENTRALEN Config initialisieren
        battery = LiPoBattery(
            capacity_ampere_h=getattr(config, "battery_capacity_ah", 15.0),
            initial_temp=start_temp,
            cells_parallel=1,
            initial_soc=getattr(config, "initial_soc", 1.0)
        )
        gps_obj = GPSData(raw_data)
        dynamics = EbikeDynamics(config=config)
        motor = Motor(config=config)

        # 5. Simulations-Orchestrator mit derselben Config und Komponenten starten
        simulation = EBikeSimulation(
            battery=battery,
            gps_data=gps_obj,
            motor=motor,
            ebike_dynamics=dynamics,
            config=config
        )

        # 6. Simulation ausführen und Ergebnisse aggregieren
        processed_data = simulation.run()

        # HIER WAR DER FEHLER: Die Berechnung der summary_stats fehlte!
        summary_stats = simulation.summary(processed_data)

        # 7. Ergebnisse formatiert in der Konsole ausgeben
        print("\n================ SIMULATIONS-ZUSAMMENFASSUNG ================")
        print(f"Fahrzeit:                  {summary_stats['total_time_s']/60:.1f} min "
              f"({summary_stats['total_time_s']:.0f} s)")
        print(f"Zurückgelegte Strecke:     {summary_stats['total_distance_km']:.2f} km")
        print(f"Ø Geschwindigkeit:         {summary_stats['avg_velocity_kmh']:.1f} km/h")
        print(f"Max. Geschwindigkeit:      {summary_stats['max_velocity_kmh']:.1f} km/h")
        print(f"Kumulierte Höhenmeter (+): {summary_stats['elevation_gain_m']:.1f} hm")
        print(f"Kumulierte Höhenmeter (-): {summary_stats['elevation_loss_m']:.1f} hm (NEU)")
        print(f"Maximalleistung:           {summary_stats['max_power_w']:.1f} W (NEU)")
        print(f"Erbrachte mech. Energie:   {summary_stats['mechanical_energy_wh']:.1f} Wh")
        print("-------------------------------------------------------------")
        print(f"Akku-Ladestand zu Beginn:  {summary_stats['start_soc_percent']:.1f} %")
        print(f"Akku-Ladestand am Ende:    {summary_stats['end_soc_percent']:.1f} %")
        print(f"Verbrauchter SoC:          {summary_stats['consumed_soc_percent']:.1f} %")
        print("=============================================================\n")

        # 8. Diagramme generieren und als hochauflösende PNG-Dateien exportieren
        logger.info("Generiere Diagramme...")

        fig_metrics = plot_speed_power_soc(processed_data)
        fig_metrics.savefig("simulations_plot.png", dpi=300, bbox_inches='tight')

        fig_elevation_1 = plot_elevation_profile(processed_data)
        fig_elevation_1.savefig("hoehenprofil_plot_1.png", dpi=300, bbox_inches='tight')

        fig_elevation = plot_colored_elevation_profile(processed_data)
        fig_elevation.savefig("hoehenprofil_plot.png", dpi=300, bbox_inches='tight')

        logger.info("Diagramme wurden erfolgreich als PNG gespeichert.")

        # 9. Interaktive matplotlib Benutzeroberfläche öffnen
        logger.info("Öffne interaktives Diagrammfenster...")
        plt.show()

    except (ValueError, FileNotFoundError, RuntimeError) as e:
        logger.error("Ein kritischer Fehler ist während der Ausführung aufgetreten: %s", e)


if __name__ == "__main__":
    main()
