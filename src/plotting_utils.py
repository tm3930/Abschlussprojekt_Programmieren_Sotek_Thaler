'''
Modul zur grafischen Darstellung und Visualisierung von E-Bike-Simulationsdaten.

Dieses Modul stellt spezialisierte Plot-Funktionen auf Basis von Matplotlib bereit.
Es ermöglicht die Generierung von kombinierten Zeit-Profilen (Geschwindigkeit, Leistung, 
Ladezustand) sowie die Erstellung von topografischen Höhenprofilen inklusive einer 
farblichen Kodierung nach dem lokalen Steigungsgrad.
'''

#generelle Imports
import logging
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.collections import PolyCollection

#Imports von anderen selbstgeschriebenen Dateien
from constants import HOURS_TO_SECONDS, MPS_TO_KMH, KM_TO_M

#__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
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
    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("time", "velocity", "power", "soc"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    #Zuweisung der Daten als NumPy-Arrays für performante Verarbeitung
    time_sec = np.asarray(data["time"])
    velocity = np.asarray(data["velocity"])
    power = np.asarray(data["power"])
    soc = np.asarray(data["soc"])

    #Validierung der Array-Längen auf Konsistenz
    if not len(time_sec) == len(velocity) == len(power) == len(soc):
        raise ValueError(
            "Die Datenvektoren (time, velocity, power, soc) müssen die gleiche Länge aufweisen."
        )

    #Zeit in Stunden umrechnen
    time = time_sec / HOURS_TO_SECONDS

    #Erstellung der drei Teildiagramme mit verknüpfter x-Achse
    fig, (ax_v, ax_p, ax_s) = plt.subplots(3, 1, figsize=(9, 7), sharex=True)

    #1. Subplot: Geschwindigkeit (Umrechnung von m/s in km/h)
    ax_v.plot(time, velocity * MPS_TO_KMH, "b-")
    ax_v.set_ylabel("Geschwindigkeit / km/h")
    ax_v.grid(True)

    #2. Subplot: Mechanische/Elektrische Leistung
    ax_p.plot(time, power, "r-")
    ax_p.axhline(0, color="grey", linewidth=0.8)  # Physikalische Nulllinie (Laden vs. Entladen)
    ax_p.set_ylabel("Leistung / W")
    ax_p.grid(True)

    #3. Subplot: Ladezustand (Umrechnung von 0.0-1.0 in Prozent)
    ax_s.plot(time, soc * 100, "g-")
    ax_s.set_ylabel("Ladestand (SoC) / %")
    ax_s.set_xlabel("Zeit / h")
    ax_s.set_ylim(0, 100)
    ax_s.grid(True)

    fig.suptitle("Geschwindigkeit, Leistung und Ladestand über die Fahrtzeit")
    fig.tight_layout()

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

    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("distance", "ele"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    #Zuweisung der Daten als NumPy-Arrays
    distance = np.asarray(data["distance"])
    elevation = np.asarray(data["ele"])

    #Validierung der Array-Längen
    if len(distance) != len(elevation):
        raise ValueError(
            "Die Vektoren 'distance' und 'elevation' müssen die gleiche Länge aufweisen."
        )

    #Umrechnung der Streckenachse von Metern in Kilometer
    distance_km = distance / KM_TO_M

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

    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("distance", "ele", "incline"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    #Zuweisung der Daten als NumPy-Arrays
    distance = np.asarray(data["distance"])
    elevation = np.asarray(data["ele"])

    incline = np.asarray(data["incline"])

    #Validierung der Array-Längen
    if not len(distance) == len(elevation) == len(incline):
        raise ValueError(
            "Die Vektoren 'distance', 'elevation' und 'incline' müssen die gleiche Länge aufweisen."
        )

    #Umrechnung: Meter in Kilometer & Steigung von Radiant in Grad
    distance_km = distance / KM_TO_M
    incline_deg = np.degrees(incline)

    #Farbpalette aus matplotlib laden (RdYlGn = Red-Yellow-Green, mit '_r' für die Invertierung)
    color_scale = plt.get_cmap("RdYlGn_r")

    #Symmetrische Normalisierung um 0.0 herum definieren
    grenze = np.max(np.absolute(incline_deg))
    if grenze == 0.0:
        grenze = 1.0  #Schutz vor Division durch Null bei absolut flachen Strecken
    norm = plt.Normalize(vmin=-grenze, vmax=grenze)

    fig, ax = plt.subplots(figsize=(9, 4))

    base_y = np.min(elevation) - 5

    # Polygone und Farben in je einer kompakten Zeile zusammenbauen
    verts = [
        [(distance_km[i], base_y), (distance_km[i], elevation[i]),
         (distance_km[i+1], elevation[i+1]), (distance_km[i+1], base_y)]
        for i in range(len(distance_km) - 1)
    ]
    face_colors = [color_scale(norm(incline_deg[i + 1])) for i in range(len(distance_km) - 1)]

    # Einmalig gebündelt zeichnen
    collection = PolyCollection(verts, facecolors=face_colors, edgecolors='face')
    ax.add_collection(collection)

    ax.set_xlim(distance_km[0], distance_km[-1])
    ax.set_ylim(base_y, np.max(elevation) + 5)

    #Zusätzliche prägnante schwarze Konturlinie auf dem Höhenprofil
    ax.plot(distance_km, elevation, "k-", linewidth=1.0)

    ax.set_xlabel("Strecke / km")
    ax.set_ylabel("Höhe / m")
    ax.set_title("Farbiges Höhenprofil der E-Bike-Strecke (nach Steigungsgrad)")
    ax.grid(True)

    logger.info("Farbig kodiertes Höhenprofil erfolgreich generiert.")
    return fig


def plot_thermal_electrical_load(data: pd.DataFrame) -> Figure:
    '''
    Plottet den zeitlichen Verlauf von Motorstrom und Akkutemperatur 

    Die linke Achse zeigt den Motorstrom in Ampere,
    während die rechte Achse die thermische Entwicklung des Akkus in Grad Celsius darstellt.

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'time', 
                'motor_current' und 'battery_temp' enthalten muss

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''

    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("time", "motor_current", "battery_temp"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")


    #Zuweisung der Daten als NumPy-Arrays für performante Verarbeitung
    time_sec = np.asarray(data["time"])
    motor_current = np.asarray(data["motor_current"])
    battery_temp = np.asarray(data["battery_temp"])


    #Validierung der Array-Längen auf Konsistenz
    if not len(time_sec) == len(motor_current) == len(battery_temp):
        raise ValueError(
            "Die Datenvektoren (time,motor_current,battery_temp) müssen die gleiche Länge aufweisen"
        )


    #Zeit in Stunden umrechnen
    time = time_sec / HOURS_TO_SECONDS

    fig, ax1 = plt.subplots(figsize=(9, 4.5))

    #1. Y-Achse (links): Motorstrom
    color1 = "tab:blue"
    ax1.set_xlabel("Zeit / h")
    ax1.set_ylabel("Motorstrom / A", color=color1)
    ax1.fill_between(time, motor_current, alpha=0.3, color=color1)
    ax1.plot(time, motor_current, color=color1, label="Strom")
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.grid(True, linestyle="--", alpha=0.6)

    #2. Y-Achse (rechts): Akkutemperatur
    ax2 = ax1.twinx()
    color2 = "tab:red"
    ax2.set_ylabel("Akkutemperatur / °C", color=color2)
    ax2.plot(time, battery_temp, color=color2, linewidth=1.5, label="Temperatur")
    ax2.tick_params(axis="y", labelcolor=color2)

    fig.suptitle("Thermische und elektrische Akku-Belastung über die Fahrzeit")
    fig.tight_layout()

    logger.info("Diagramm für thermische und elektrische Akku-Belastung erfolgreich generiert.")
    return fig


def plot_resistance_forces(data: pd.DataFrame) -> Figure:
    '''
    Plottet den zeitlichen oder streckenbasierten Verlauf der verschiedenen Fahrwiderstände.

    Die Einzelkräfte (Luftwiderstand, Rollwiderstand und Hangabtriebskraft) werden 
    als gestapeltes Flächendiagramm dargestellt, um deren prozentualen Anteil 
    an der Gesamt-Vorwärtskraft zu veranschaulichen.

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'time', 'drag_force', 
              'rolling_resistance' und 'incline_force' enthalten muss.

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''

    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("time", "drag_force", "rolling_resistance", "incline_force"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    #Zuweisung der Daten als NumPy-Arrays für performante Verarbeitung
    time_sec = np.asarray(data["time"])
    drag_force = np.asarray(data["drag_force"])
    rolling_resistance = np.asarray(data["rolling_resistance"])
    incline_force = np.asarray(data["incline_force"])

    #Validierung der Array-Längen auf Konsistenz
    if not len(time_sec) == len(drag_force) == len(rolling_resistance) == len(incline_force):
        raise ValueError(
            "Die Datenvektoren (time, drag_force, rolling_resistance, incline_force) " \
            "müssen die gleiche Länge aufweisen."
        )

    #Zeit in Stunden umrechnen
    time = time_sec / HOURS_TO_SECONDS

    fig, ax = plt.subplots(figsize=(9, 4.5))

    #Gestapeltes Flächendiagramm (stackplot) der Widerstandskräfte
    ax.stackplot(
        time,
        drag_force,
        rolling_resistance,
        incline_force,
        labels=["Luftwiderstand", "Rollwiderstand", "Hangabtriebskraft"],
        alpha=0.8
    )

    ax.set_xlabel("Zeit / h")
    ax.set_ylabel("Widerstandskraft / N")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.suptitle("Aufschlüsselung der Fahrwiderstände über die Fahrzeit")
    fig.tight_layout()

    logger.info("Diagramm zur Aufschlüsselung der Fahrwiderstände erfolgreich generiert.")
    return fig


def plot_energy_balance(summary_data: dict) -> Figure:
    '''
    Plottet die Energiebilanz der E-Bike-Fahrt als übersichtliches Balkendiagramm.

    Visualisiert den theoretischen Energiegehalt, thermische Verluste, 
    rekuperierte Energie und die tatsächlich genutzte mechanische Antriebsenergie.

    Eingabe:
        summary_data: Dictionary mit den aggregierten Energiewerten 
                      (erfordert 'discharged_energy_wh', 'dissipated_energy_wh', 
                       'recuperated_energy_wh', 'mechanical_energy_wh')

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''
    #Validierung: Fehlermeldung, falls erforderliche Schlüssel im Dictionary fehlen
    required_keys = (
        "discharged_energy_wh",
        "dissipated_energy_wh",
        "recuperated_energy_wh",
        "mechanical_energy_wh",
    )

    for key in required_keys:
        if key not in summary_data:
            raise KeyError(f"In den Zusammenfassungsdaten fehlt der erforderliche Schlüssel: "
                           f"'{key}'")

    #Extrahieren der Energiewerte in Wattstunden (Wh)
    categories = [
        "Entnommene Energie",
        "Therm. Verluste",
        "Rekuperation",
        "Mechanische Arbeit",
    ]
    values = [
        summary_data["discharged_energy_wh"],
        summary_data["dissipated_energy_wh"],
        summary_data["recuperated_energy_wh"],
        summary_data["mechanical_energy_wh"],
    ]

    fig, ax = plt.subplots(figsize=(9, 4.5))

    #Farbdefinition für die Bilanzelemente (Verluste rot, Energie grün/blau)
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:purple"]

    bars = ax.bar(categories, values, color=colors, alpha=0.85, width=0.5)

    #Werte als Text direkt über die Balken schreiben für bessere Lesbarkeit
    for rect in bars:
        height = rect.get_height()
        ax.annotate(
            f"{height:.1f} Wh",
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, 3),  # 3 Punkte vertikaler Abstand
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_ylabel("Energie / Wh")
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)

    fig.suptitle("Energiebilanz und Antriebsstrang-Komponenten")
    fig.tight_layout()

    logger.info("Diagramm zur Energiebilanz erfolgreich generiert.")
    return fig


def plot_speed_vs_incline(data: pd.DataFrame) -> Figure:
    '''
    Plottet die Geschwindigkeit in Abhängigkeit vom lokalen Steigungsgrad.

    Die einzelnen Datenpunkte werden farblich nach der aktuell abgegebenen 
    Motorleistung gewichtet, um zu verdeutlichen, bei welchen Steigungen 
    die maximale Unterstützung greift.

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'incline', 'velocity' und 'power' enthalten muss.

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''

    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("incline", "velocity", "power"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    #Zuweisung der Daten als NumPy-Arrays für performante Verarbeitung
    incline = np.asarray(data["incline"])
    velocity = np.asarray(data["velocity"])
    power = np.asarray(data["power"])

    #Validierung der Array-Längen auf Konsistenz
    if not len(incline) == len(velocity) == len(power):
        raise ValueError(
            "Die Datenvektoren (incline, velocity, power) müssen die gleiche Länge aufweisen."
        )

    #Steigung in Grad umrechnen für eine intuitivere Achsenbeschriftung
    incline_deg = np.degrees(incline)

    fig, ax = plt.subplots(figsize=(9, 4.5))

    #Scatter-Plot mit Farbskala für die Leistung
    sc = ax.scatter(
        incline_deg,
        velocity * MPS_TO_KMH,
        c=power,
        cmap="plasma",
        alpha=0.7,
        s=15,
    )

    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Motorleistung / W")

    ax.set_xlabel("Steigungsgrad / °")
    ax.set_ylabel("Geschwindigkeit / km/h")
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.suptitle("Geschwindigkeit in Abhängigkeit von Steigung und Leistung")
    fig.tight_layout()

    logger.info("Diagramm zur Steigungs-Geschwindigkeits-Korrelation erfolgreich generiert.")

    return fig


def plot_motor_operating_points(data: pd.DataFrame) -> Figure:
    '''
    Plottet die dynamischen Arbeitspunkte des Motors über der Zeit oder als Verlauf.

    Visualisiert das Zusammenspiel von Drehmoment und Drehzahl im Antriebsstrang.

    Eingabe:
        data: Pandas DataFrame, das die Spalten 'time', 'motor_torque' und motor_rpm enthalten muss

    Ausgabe:
        matplotlib.figure.Figure: Das generierte Matplotlib-Figure-Objekt.
    '''

    #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
    for col in ("time", "motor_torque", "motor_rpm"):
        if col not in data:
            raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

    #Zuweisung der Daten als NumPy-Arrays für performante Verarbeitung
    time_sec = np.asarray(data["time"])
    torque = np.asarray(data["motor_torque"])
    rpm = np.asarray(data["motor_rpm"])

    #Validierung der Array-Längen auf Konsistenz
    if not len(time_sec) == len(torque) == len(rpm):
        raise ValueError(
            "Die Datenvektoren (time, motor_torque, motor_rpm) müssen die gleiche Länge aufweisen."
        )

    time = time_sec / HOURS_TO_SECONDS

    fig, ax1 = plt.subplots(figsize=(9, 4.5))

    #Linke Achse: Motordrehmoment
    color1 = "tab:cyan"
    ax1.set_xlabel("Zeit / h")
    ax1.set_ylabel("Motordrehmoment / Nm", color=color1)
    ax1.plot(time, torque, color=color1, label="Drehmoment")
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.grid(True, linestyle="--", alpha=0.6)

    #Rechte Achse: Motordrehzahl
    ax2 = ax1.twinx()
    color2 = "tab:olive"
    ax2.set_ylabel("Motordrehzahl / rpm", color=color2)
    ax2.plot(time, rpm, color=color2, linewidth=1.2, label="Drehzahl")
    ax2.tick_params(axis="y", labelcolor=color2)

    fig.suptitle("Motordynamik: Drehmoment und Drehzahl im Fahrverlauf")
    fig.tight_layout()

    logger.info("Diagramm für Motor-Arbeitspunkte erfolgreich generiert.")
    return fig


if __name__ == "__main__":

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

    logger.info("Starte plotting_utils Datei...")

    try:
        from pathlib import Path


        #Pfad zur CSV-Datei:
        base_dir = Path(__file__).resolve().parent.parent
        path_to_csv = base_dir / "data" / "processed" / "simulation_results.csv"
        plot_data = pd.read_csv(
            path_to_csv,
            sep=";",                    #Semikolon als Trennzeichen
        )

        #Standard-Höhenprofil
        if all(col in plot_data for col in ("distance", "ele")):
            fig_ele = plot_elevation_profile(plot_data)
            fig_ele.savefig("hoehenprofil.png", dpi=150)
            logger.info("Grafik exportiert: hoehenprofil.png")

        #Farbig kodiertes Höhenprofil
        if all(col in plot_data for col in ("distance", "ele", "incline")):
            fig_ele_col = plot_colored_elevation_profile(plot_data)
            fig_ele_col.savefig("farbiges_hoehenprofil.png", dpi=150)
            logger.info("Grafik exportiert: farbiges_hoehenprofil.png")

        #Geschwindigkeit, Leistung und SoC
        if all(col in plot_data for col in ("time", "velocity", "power", "soc")):
            fig_sps = plot_speed_power_soc(plot_data)
            fig_sps.savefig("geschwindigkeit_leistung_soc.png", dpi=150)
            logger.info("Grafik exportiert: geschwindigkeit_leistung_soc.png")

        #Thermische und elektrische Akku-Belastung
        if all(col in plot_data for col in ("time", "motor_current", "battery_temp")):
            fig_therm = plot_thermal_electrical_load(plot_data)
            fig_therm.savefig("thermische_elektrische_last.png", dpi=150)
            logger.info("Grafik exportiert: thermische_elektrische_last.png")

        #Aufschlüsselung der Fahrwiderstände
        if all(col in plot_data for col in (
            "time", "drag_force", "rolling_resistance", "incline_force"
        )):
            fig_res = plot_resistance_forces(plot_data)
            fig_res.savefig("fahrwiderstaende.png", dpi=150)
            logger.info("Grafik exportiert: fahrwiderstaende.png")

        #Steigung vs. Geschwindigkeit
        if all(col in plot_data for col in ("incline", "velocity", "power")):
            fig_inc = plot_speed_vs_incline(plot_data)
            fig_inc.savefig("steigung_vs_geschwindigkeit.png", dpi=150)
            logger.info("Grafik exportiert: steigung_vs_geschwindigkeit.png")

        #Motor-Arbeitspunkte
        if all(col in plot_data for col in ("time", "motor_torque", "motor_rpm")):
            fig_motor = plot_motor_operating_points(plot_data)
            fig_motor.savefig("motor_arbeitspunkte.png", dpi=150)
            logger.info("Grafik exportiert: motor_arbeitspunkte.png")

        #Energiebilanz (Beispiel-Dictionary)
        summary_test = {
            "discharged_energy_wh": 150.0,
            "dissipated_energy_wh": 25.0,
            "recuperated_energy_wh": 10.0,
            "mechanical_energy_wh": 135.0,
        }
        fig_energy = plot_energy_balance(summary_test)
        fig_energy.savefig("energiebilanz.png", dpi=150)
        logger.info("Grafik exportiert: energiebilanz.png")

        #Alle generierten Plots gesammelt anzeigen
        plt.show()

    except ImportError:
        logger.warning(
            "Das Modul 'data_from_csv' ist nicht im Pfad. Selbsttest übersprungen."
        )
    except FileNotFoundError:
        logger.error("Die Datei 'processed_data.csv' wurde nicht gefunden.")
