'''
Modul zur grafischen Darstellung und Visualisierung von E-Bike-Simulationsdaten.

Dieses Modul stellt spezialisierte Plot-Funktionen auf Basis von Matplotlib bereit.
Es ermöglicht die Generierung von kombinierten Zeit-Profilen (Geschwindigkeit, Leistung, 
Ladezustand) sowie die Erstellung von topografischen Höhenprofilen inklusive einer 
farblichen Kodierung nach dem lokalen Steigungsgrad.
'''

import logging
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


def plot_speed_power_soc(data: pd.DataFrame) -> Figure:
    '''
    Plottet den zeitlichen Verlauf von Geschwindigkeit, Motorleistung und Ladezustand (SoC).

    Die drei Diagramme werden untereinander dargestellt und teilen sich eine 
    gemeinsame Zeitachse (x-Achse), um die dynamischen Abhängigkeiten direkt zu veranschaulichen.

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'time', 'velocity', 'power' und 'soc' enthalten muss

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''
    # Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("time", "velocity", "power", "soc"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    # Zuweisung der Daten als NumPy-Arrays für performante Verarbeitung
    time = np.asarray(data["time"])
    velocity = np.asarray(data["velocity"])
    power = np.asarray(data["power"])
    soc = np.asarray(data["soc"])

    # Validierung der Array-Längen auf Konsistenz
    if not len(time) == len(velocity) == len(power) == len(soc):
        raise ValueError(
            "Die Datenvektoren (time, velocity, power, soc) müssen die gleiche Länge aufweisen."
        )

    # Erstellung der drei Teildiagramme mit verknüpfter x-Achse
    fig, (ax_v, ax_p, ax_s) = plt.subplots(3, 1, figsize=(9, 7), sharex=True)

    # 1. Subplot: Geschwindigkeit (Umrechnung von m/s in km/h)
    ax_v.plot(time, velocity * 3.6, "b-")
    ax_v.set_ylabel("Geschwindigkeit / km/h")
    ax_v.grid(True)

    # 2. Subplot: Mechanische/Elektrische Leistung
    ax_p.plot(time, power, "r-")
    ax_p.axhline(0, color="grey", linewidth=0.8)  # Physikalische Nulllinie (Laden vs. Entladen)
    ax_p.set_ylabel("Leistung / W")
    ax_p.grid(True)

    # 3. Subplot: Ladezustand (Umrechnung von 0.0-1.0 in Prozent)
    ax_s.plot(time, soc * 100, "g-")
    ax_s.set_ylabel("Ladestand (SoC) / %")
    ax_s.set_xlabel("Zeit / s")
    ax_s.set_ylim(0, 100)
    ax_s.grid(True)

    fig.suptitle("Geschwindigkeit, Leistung und Ladestand über die Fahrtzeit")

    logger.info("Diagramm für Geschwindigkeit, Leistung und SoC erfolgreich generiert.")
    return fig


def plot_elevation_profile(data: pd.DataFrame) -> Figure:
    '''
    Plottet das topografische Höhenprofil der Fahrstrecke über die Distanz.

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'distance' und 'ele' enthalten muss.

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''
    for col in ("distance", "ele"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    # Zuweisung der Daten als NumPy-Arrays
    distance = np.asarray(data["distance"])
    elevation = np.asarray(data["ele"])

    # Validierung der Array-Längen
    if len(distance) != len(elevation):
        raise ValueError(
            "Die Vektoren 'distance' und 'elevation' müssen die gleiche Länge aufweisen."
        )

    # Umrechnung der Streckenachse von Metern in Kilometer
    distance_km = distance / 1000.0

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(distance_km, elevation, "k-", linewidth=1.2)

    ax.set_xlabel("Strecke / km")
    ax.set_ylabel("Höhe / m")
    ax.set_title("Höhenprofil der E-Bike-Strecke")
    ax.grid(True)

    logger.info("Standard-Höhenprofil erfolgreich generiert.")
    return fig


def plot_colored_elevation_profile(data: pd.DataFrame) -> Figure:
    '''
    Erstellt ein erweitertes, farblich kodiertes Höhenprofil der E-Bike-Strecke.
    
    Die Fläche unterhalb des Profils wird basierend auf dem lokalen Steigungsgrad 
    eingefärbt (steile Anstiege = rot, ebene Abschnitte = gelb, Gefälle = grün).

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'distance', 'ele' und 'incline' enthalten muss.

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''
    for col in ("distance", "ele", "incline"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    # Zuweisung der Daten als NumPy-Arrays
    distance = np.asarray(data["distance"])
    elevation = np.asarray(data["ele"])
    incline = np.asarray(data["incline"])

    # Validierung der Array-Längen
    if not len(distance) == len(elevation) == len(incline):
        raise ValueError(
            "Die Vektoren 'distance', 'elevation' und 'incline' müssen die gleiche Länge aufweisen."
        )

    # Umrechnung: Meter in Kilometer & Steigung von Radiant in Grad
    distance_km = distance / 1000.0
    incline_deg = np.degrees(incline)

    # Farbpalette aus matplotlib laden (RdYlGn = Red-Yellow-Green, mit '_r' für die Invertierung)
    color_scale = plt.get_cmap("RdYlGn_r")

    # Symmetrische Normalisierung um 0.0 herum definieren
    grenze = np.max(np.absolute(incline_deg))
    if grenze == 0.0:
        grenze = 1.0  # Schutz vor Division durch Null bei absolut flachen Strecken
    norm = plt.Normalize(vmin=-grenze, vmax=grenze)

    fig, ax = plt.subplots(figsize=(9, 4))

    # Iterative polygonale Einfärbung der Streckenabschnitte nach lokaler Steigung
    for i in range(len(distance_km) - 1):
        ax.fill_between(
            distance_km[i:i + 2],          # x-Werte des aktuellen Segments
            elevation[i:i + 2],             # Höhenprofil-Oberkante
            np.min(elevation) - 5,          # Untere Grenze (mit leichtem Offset für die Optik)
            color=color_scale(norm(incline_deg[i + 1]))  # Farbwert ermittelt aus Steigung
        )

    # Zusätzliche prägnante schwarze Konturlinie auf dem Höhenprofil
    ax.plot(distance_km, elevation, "k-", linewidth=1.0)

    ax.set_xlabel("Strecke / km")
    ax.set_ylabel("Höhe / m")
    ax.set_title("Farbiges Höhenprofil der E-Bike-Strecke (nach Steigungsgrad)")
    ax.grid(True)

    logger.info("Farbig kodiertes Höhenprofil erfolgreich generiert.")
    return fig

if __name__ == "__main__":
    # Lokale Logging-Konfiguration für den Modultest
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger.info("Starte lokalen Selbsttest der Visualisierungs-Funktionen...")

    # Sichere Einbindung der Datenkomponenten für den Testlauf
    try:
        from data_from_csv import get_data_from_csv
        from gps_data import GPSData

        # 1. Daten laden und Vorverarbeitung über das GPS-Modul anstoßen
        raw_data = get_data_from_csv("final_project_input_data.csv")
        gps = GPSData(raw_data)

        # Für die Diagramme benötigte Spalten temporär berechnen, sofern im Test-GPS verfügbar
        plot_data = gps.data.copy()
        plot_data["distance"] = gps.get_distance()
        plot_data["incline"] = gps.get_incline(plot_data["distance"])

        # 2. Test und Export des Standard-Höhenprofils
        fig_ele = plot_elevation_profile(plot_data)
        fig_ele.savefig("hoehenprofil.png", dpi=150)
        logger.info("Grafik exportiert: hoehenprofil.png")

        # 3. Test und Export des farbkodierten Profils
        fig_ele_col = plot_colored_elevation_profile(plot_data)
        fig_ele_col.savefig("farbiges_hoehenprofil.png", dpi=150)
        logger.info("Grafik exportiert: farbiges_hoehenprofil.png")

        # Zeige die Plots an, falls ein UI-Backend aktiv ist
        plt.show()

    except ImportError:
        logger.warning(
            "Abhängige Module (data_from_csv oder gps_data) nicht im Pfad. Selbsttest übersprungen."
        )
    except FileNotFoundError:
        logger.error("Die Testdatei 'final_project_input_data.csv' wurde nicht gefunden.")
