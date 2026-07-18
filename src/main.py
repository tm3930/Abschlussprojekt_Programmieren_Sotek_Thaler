import logging
import sys

import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt
from ebike_config import EbikeConfig
from battery import LiPoBattery
#from battery import NMCBattery
from gps_data import GPSData
from ebike_simulation import EBikeSimulation
from plotting_utils import plot_speed_power_soc  
from data_from_csv import get_data_from_csv

def main():
    #Logging einrichten
    #Gemeinsames Textformat festlegen
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

    #Terminal-Ausgabe: Zeigt INFO, WARNING, ERROR, CRITICAL (kein DEBUG)
    terminal_output = logging.StreamHandler(sys.stdout)
    terminal_output.setLevel(logging.INFO)
    terminal_output.setFormatter(log_format)

    # 3. Datei-Ausgabe: Schreibt ALLES mit (inklusive DEBUG)
    file_output = logging.FileHandler("app.log", mode="a", encoding="utf-8")
    file_output.setLevel(logging.DEBUG)
    file_output.setFormatter(log_format)

    # 4. Globales System aktivieren (Muss auf DEBUG stehen, um die Datei zu füttern)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[terminal_output, file_output]
    )

    logger = logging.getLogger(__name__)
    logger.info("Starte Hauptprogramm für die E-Bike Simulation...")

    try:
        
        raw_data = get_data_from_csv("final_project_input_data.csv")

        config = EbikeConfig()
        battery = LiPoBattery(capacity_Ah=30.0, cells_parallel=1, initial_soc=1.0)
        #battery = NMCBattery(capacity_Ah=30.0, cells_parallel=1, initial_soc=1.0)
        
        simulation = EBikeSimulation(
            battery=battery,
            gps_data = GPSData(raw_data)
        )
        
        # 1. Simulation ausführen und die prozessierten Daten abfangen
        processed_data = simulation.run()

        summary_stats = simulation.summary(processed_data)
        
        print("\n================ SIMULATIONS-ZUSAMMENFASSUNG ================")
        print(f"Fahrzeit:                  {summary_stats['total_time_s']/60:.1f} min ({summary_stats['total_time_s']:.0f} s)")
        print(f"Zurückgelegte Strecke:     {summary_stats['total_distance_km']:.2f} km")
        print(f"Ø Geschwindigkeit:         {summary_stats['avg_velocity_kmh']:.1f} km/h")
        print(f"Max. Geschwindigkeit:      {summary_stats['max_velocity_kmh']:.1f} km/h")
        print(f"Kumulierte Höhenmeter:     {summary_stats['elevation_gain_m']:.1f} hm")
        print(f"Erbrachte mech. Energie:   {summary_stats['mechanical_energy_wh']:.1f} Wh")
        print("-------------------------------------------------------------")
        print(f"Akku-Ladestand zu Beginn:  {summary_stats['start_soc_percent']:.1f} %")
        print(f"Akku-Ladestand am Ende:    {summary_stats['end_soc_percent']:.1f} %")
        print(f"Verbrauchter SoC:          {summary_stats['consumed_soc_percent']:.1f} %")
        print("=============================================================\n")
        
        # 2. NEU: Die Figur erst hier in der main.py erstellen
        logger.info("Generiere Diagramme...")
        fig = plot_speed_power_soc(processed_data)
        
        # 3. Diagramm als Bild sichern (als Fallback)
        fig.savefig("simulations_plot.png", dpi=300, bbox_inches='tight')
        logger.info("Diagramm wurde erfolgreich als 'simulations_plot.png' gespeichert.")
        
        # 4. Diagrammfenster anzeigen
        logger.info("Öffne interaktives Diagrammfenster...")
        plt.show()

    except (ValueError, FileNotFoundError, RuntimeError) as e:
        logger.error("Ein kritischer Fehler ist während der Ausführung aufgetreten: %s", e)

if __name__ == "__main__":
    main()
