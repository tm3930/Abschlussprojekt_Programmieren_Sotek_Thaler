'''
Hauptprogramm zur Ausführung und Steuerung der E-Bike-Fahrsimulation.
Weiters werden verschiedene Grafiken erstellt und abgespeichert.
'''

#generelle Imports
import logging
import sys
import webbrowser
from pathlib import Path
import matplotlib.pyplot as plt

#Imports von anderen selbstgeschriebenen Dateien
from battery import LiPoBattery
from gps_data import GPSData
from ebike_simulation import EBikeSimulation
from ebike_config import EbikeConfig
from motor import Motor
from ebike_dynamics import EbikeDynamics
from route_map import RouteMap
from plotting_utils import (
    plot_speed_power_soc,
    plot_elevation_profile,
    plot_colored_elevation_profile,
    plot_thermal_electrical_load,
    plot_resistance_forces,
    plot_energy_balance,
    plot_speed_vs_incline,
    plot_motor_operating_points
)
from data_from_csv import get_data_from_csv
from ebike_reporting import generate_report_reportlab



def main() -> None:
    '''
    Hauptfunktion zur Steuerung des gesamten Simulations- und Auswerteprozesses.
    '''
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

    #__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
    logger = logging.getLogger(__name__)
    logger.info("Starte Hauptprogramm für die E-Bike Simulation...")

    try:
        #Daten aus der CSV-Datei importieren
        raw_data = get_data_from_csv("final_project_input_data.csv")

        #Zentrale Konfiguration laden
        config = EbikeConfig()

        #Start-Umgebungstemperatur auslesen
        start_temp = raw_data["temperature"].iloc[0]

        #LiPoBattery laden
        battery = LiPoBattery(config = config, initial_temp = start_temp)

        #GPSData laden
        gps_obj = GPSData(data = raw_data)

        #EBikeDynamik laden
        dynamics = EbikeDynamics(config = config)

        #Motor laden
        motor = Motor(config = config)

        #Simulation mit derselben Config und Komponenten starten
        simulation = EBikeSimulation(
            battery=battery,
            gps_data=gps_obj,
            motor=motor,
            ebike_dynamics=dynamics,
            config=config
        )

        #Simulation ausführen und Ergebnisse aggregieren
        processed_data = simulation.run()

        #Summery_Stats berechnen
        summary_stats = simulation.summary(processed_data)


        #CSV Datei erstellen und diese in den richtigen Ordner speichern
        simulation.export_results(processed_data, filename="simulation_results.csv")
        logger.info("Ergebnisse wurden erfolgreich exportiert.")

        #Ergebnisse formatiert in der Konsole ausgeben
        print("\n=== SIMULATIONS-ZUSAMMENFASSUNG ===")
        print(f"Fahrzeit:                  {summary_stats['total_time_s']/60:.1f} min "
              f"({summary_stats['total_time_s']:.0f} s)")
        print(f"Zurückgelegte Strecke:     {summary_stats['total_distance_km']:.2f} km")
        print(f"Ø Geschwindigkeit:         {summary_stats['avg_velocity_kmh']:.1f} km/h")
        print(f"Max. Geschwindigkeit:      {summary_stats['max_velocity_kmh']:.1f} km/h")
        print(f"Bergauf:                   {summary_stats['elevation_gain_m']:.1f} hm")
        print(f"Bergab:                    {summary_stats['elevation_loss_m']:.1f} hm")
        print(f"Maximalleistung:           {summary_stats['max_power_w']:.1f} W")
        print(f"Ø Leistung:                {summary_stats['avg_power_w']:.1f} W")
        print(f"Erbrachte mech. Energie:   {summary_stats['mechanical_energy_wh']:.1f} Wh")
        print(f"Rekuperierte Energie:      {summary_stats['recuperated_energy_wh']:.1f} Wh")
        print(f"Verlustenergie (Wärme):    {summary_stats['dissipated_energy_wh']:.1f} Wh")
        print("------")
        print(f"Akku-Ladestand zu Beginn:  {summary_stats['start_soc_percent']:.1f} %")
        print(f"Akku-Ladestand am Ende:    {summary_stats['end_soc_percent']:.1f} %")
        print(f"Verbrauchter SoC:          {summary_stats['consumed_soc_percent']:.1f} %")
        print("=== SIMULATIONS-ZUSAMMENFASSUNG ===\n")

        #Diagramme generieren und als PNG-Dateien exportieren
        logger.info("Generiere Diagramme...")

        #Projekt-Stammverzeichnis ermitteln (analog zur restlichen Projektstruktur)
        base_dir = Path(__file__).resolve().parent.parent
        results_dir = base_dir / "results"

        #Kontrollieren, ob der Ordner existiert, falls nicht -> erstellen
        results_dir.mkdir(parents=True, exist_ok=True)

        #Farbiges Höhenprofil
        fig_elevation_c = plot_colored_elevation_profile(processed_data)
        fig_elevation_c.savefig(results_dir / "hoehenprofil_farbig_plot.png",
                              dpi=300, bbox_inches='tight')

        #Höhenprofil
        fig_elevation = plot_elevation_profile(processed_data)
        fig_elevation.savefig(results_dir / "hoehenprofil_plot.png",
                                      dpi=300, bbox_inches='tight')

        #Thermische und elektrische Akku-Belastung
        fig_therm = plot_thermal_electrical_load(processed_data)
        fig_therm.savefig(results_dir / "thermische_elektrische_last.png", dpi=150)

        #Geschwindigkeit, Leistung, Akkuladung
        fig_metrics = plot_speed_power_soc(processed_data)
        fig_metrics.savefig(results_dir / "simulations_plot.png",
                            dpi=300, bbox_inches='tight')

        #Aufschlüsselung der Fahrwiderstände
        fig_res = plot_resistance_forces(processed_data)
        fig_res.savefig(results_dir / "fahrwiderstaende.png", dpi=150)

        #Steigung vs. Geschwindigkeit
        fig_inc = plot_speed_vs_incline(processed_data)
        fig_inc.savefig(results_dir / "steigung_vs_geschwindigkeit.png", dpi=150)

        #Motor-Arbeitspunkte
        fig_motor = plot_motor_operating_points(processed_data)
        fig_motor.savefig(results_dir / "motor_arbeitspunkte.png", dpi=150)

        #Energiebilanz (braucht das Summary-Dictionary!)
        fig_energy = plot_energy_balance(summary_stats)
        fig_energy.savefig(results_dir / "energiebilanz.png", dpi=150)

        #HTML der route_map erstellen
        route_map = RouteMap(processed_data)
        route = route_map.create_map()
        output_path = Path(results_dir / "route_map.html").resolve()
        route.save(str(output_path))

        #HTML der route_map im Browser öffnen
        webbrowser.open(output_path.as_uri())

        logger.info("Diagramme wurden erfolgreich als PNG gespeichert.")

        #Liste der gespeicherten Bilder erstellen
        plot_pfade = [
            results_dir / "hoehenprofil_farbig_plot.png",
            results_dir / "simulations_plot.png",
            results_dir / "thermische_elektrische_last.png",
            results_dir / "fahrwiderstaende.png",
            results_dir / "steigung_vs_geschwindigkeit.png",
            results_dir / "motor_arbeitspunkte.png",
            results_dir / "energiebilanz.png",
        ]

        #Zielpfad für das PDF
        pdf_ausgabe = base_dir / "results" / "ebike_simulation_analyse.pdf"

        #Generator mit den ermittelten summary_stats und Plots aufrufen
        generate_report_reportlab(summary_stats, plot_pfade, str(pdf_ausgabe))
        logger.info("Abschlussbericht wurde als PDF gespeichert.")

        #Interaktive matplotlib Benutzeroberfläche öffnen
        logger.info("Öffne interaktives Diagrammfenster...")
        plt.show()

    except (ValueError, FileNotFoundError, RuntimeError) as e:
        logger.error("Ein kritischer Fehler ist während der Ausführung aufgetreten: %s", e)


if __name__ == "__main__":
    main()
