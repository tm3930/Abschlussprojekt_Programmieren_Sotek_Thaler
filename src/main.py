'''
Hauptprogramm zur Ausführung und Steuerung der E-Bike-Fahrsimulation.

Dieses Skript bildet den zentralen Einstiegspunkt (Entry Point) des Projekts. 
Es initialisiert das globale Logging-System (aufgeteilt in Terminal- und Datei-Ausgabe), 
lädt die externen GPS-Rohdaten aus einer CSV-Datei, instanziiert das gewünschte 
Batteriemodell und startet die zeitschrittbasierte Simulation. Im Anschluss werden 
die statistischen Kennzahlen ausgegeben und die resultierenden Diagramme generiert, 
gespeichert sowie interaktiv angezeigt.
'''
import logging
import sys
import matplotlib
import matplotlib.pyplot as plt

from battery import LiPoBattery
from gps_data import GPSData
from ebike_simulation import EBikeSimulation
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
    
    Übernimmt das Logging-Setup, den Daten-Pipeline-Fluss sowie das Exception-Handling 
    bei Fehlern während der Dateiverarbeitung oder der physikalischen Berechnung.
    '''
    # --- GLOBALES LOGGING SYSTEM CONTEXT SETUP ---
    # Gemeinsames Textformat für alle Logger-Ausgaben festlegen
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

    # Terminal-Ausgabe: Zeigt INFO, WARNING, ERROR, CRITICAL (unterdrückt DEBUG-Meldungen)
    terminal_output = logging.StreamHandler(sys.stdout)
    terminal_output.setLevel(logging.INFO)
    terminal_output.setFormatter(log_format)

    # Datei-Ausgabe: Schreibt jede Aktivität detailliert mit (inklusive DEBUG)
    file_output = logging.FileHandler("app.log", mode="a", encoding="utf-8")
    file_output.setLevel(logging.DEBUG)
    file_output.setFormatter(log_format)

    # Globales Logging-System aktivieren (Wurzel-Level muss auf DEBUG stehen)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[terminal_output, file_output]
    )

    logger = logging.getLogger(__name__)
    logger.info("Starte Hauptprogramm für die E-Bike Simulation...")

    try:
        # 1. Daten-Import aus der CSV-Datei
        raw_data = get_data_from_csv("final_project_input_data.csv")

        # 2. Start-Umgebungstemperatur für die thermische Akku-Simulation auslesen
        start_temp = raw_data["temperature"].iloc[0]

        # 3. Systemkomponenten instanziieren
        battery = LiPoBattery(
            capacity_ampere_h=15.0,
            initial_temp=start_temp,
            cells_parallel=1,
            initial_soc=1.0
        )
        gps_obj = GPSData(raw_data)

        # 4. Simulations-Orchestrator aufsetzen
        simulation = EBikeSimulation(battery=battery, gps_data=gps_obj)

        # 5. Simulation ausführen und Ergebnisse aggregieren
        processed_data = simulation.run()
        summary_stats = simulation.summary(processed_data)

        # 6. Ergebnisse formatiert in der Konsole ausgeben
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

        # 7. Diagramme generieren und als hochauflösende PNG-Dateien exportieren
        logger.info("Generiere Diagramme...")

        # Zeitverlauf-Profil (Geschwindigkeit, Leistung, SoC)
        fig_metrics = plot_speed_power_soc(processed_data)
        fig_metrics.savefig("simulations_plot.png", dpi=300, bbox_inches='tight')

        # Standard-Höhenprofil
        fig_elevation_1 = plot_elevation_profile(processed_data)
        fig_elevation_1.savefig("hoehenprofil_plot_1.png", dpi=300, bbox_inches='tight')

        # Farbcodiertes Höhenprofil nach Steigungsgrad
        fig_elevation = plot_colored_elevation_profile(processed_data)
        fig_elevation.savefig("hoehenprofil_plot.png", dpi=300, bbox_inches='tight')

        logger.info("Diagramme wurden erfolgreich als PNG gespeichert.")

        # 8. Interaktive matplotlib Benutzeroberfläche öffnen
        logger.info("Öffne interaktives Diagrammfenster...")
        plt.show()

    except (ValueError, FileNotFoundError, RuntimeError) as e:
        logger.error("Ein kritischer Fehler ist während der Ausführung aufgetreten: %s", e)


if __name__ == "__main__":
    main()
