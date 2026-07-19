import logging
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

def plot_speed_power_soc(data: pd.DataFrame):
    '''
    Funktion zum plotten von Geschwindigkeit, Leistung und Ladezustand über den Fahrtverlauf (Zeit)
    '''

    #Fehlermeldung, falls einer der Werte in "data" fehlt
    for x in ("time", "velocity", "power", "soc"):
        if x not in data:
            raise KeyError(f"In den Daten fehlt der Wert von '{x}'.")

    #Zuweisung der Daten als NumPy-Array
    time = np.asarray(data["time"])
    velocity = np.asarray(data["velocity"])
    power = np.asarray(data["power"])
    soc = np.asarray(data["soc"])

    #Fehlermeldung, falls Listen sich in Länge unterscheiden
    if not (len(time) == len(velocity) == len(power) == len(soc)):
        raise ValueError("Die Datenlisten (time, velocity, power, soc) müssen gleich lang sein!")

    #Erstellung der drei Datendiagramme mit einer Zeitachse durch "sharex"
    fig, (ax_v, ax_p, ax_s) = plt.subplots(3, 1, figsize = (9, 7), sharex = True)

    ax_v.plot(time, velocity * 3.6, "b-") #m/s auf km/h umrechnen
    ax_v.set_ylabel("Geschwindigkeit / km/h")
    ax_v.grid(True)

    ax_p.plot(time, power, "r-")
    ax_p.axhline(0, color="grey", linewidth=0.8) #Nulllinie
    ax_p.set_ylabel("Leistung / W")
    ax_p.grid(True)

    ax_s.plot(time, soc * 100, "g-") #SoC (0.0 bis 1.0 auf Prozent umrechnen)
    ax_s.set_ylabel("Ladestand (SoC) / %")
    ax_s.set_xlabel("Zeit / s")
    ax_s.set_ylim(0, 100)
    ax_s.grid(True)

    fig.suptitle("Geschwindigkeit, Leistung und Ladestand über die Fahrtzeit")

    logger.info("Graph von Geschwindigkeit, Leistung und Ladestand über die Zeit erstellt.")

    return fig


def plot_elevation_profile(gps):
    """Eine Funktion zum plotten des Höhenprofils anhand der vorgegebenen GPS-Daten"""

    #Strecke und Höhe aus der GPS-Klasse holen
    distance = gps.get_distance()
    elevation = gps.data_elevation

    #Fehlermeldung, falls Listen sich in Länge unterscheiden
    if len(distance) != len(elevation):
        raise ValueError("Die Listen distance und elevation müssen gleich lang sein.")

    distance_km = distance / 1000.0 #m auf km umtrechnen

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(distance_km, elevation, "k-")

    ax.set_xlabel("Strecke / km")
    ax.set_ylabel("Höhe / m")
    ax.set_title("Höhenprofil der Ebike-Strecke")
    ax.grid(True)

    logger.info("Graph des Höhenprofils erstellt.")

    return fig

def plot_colored_elevation_profile(gps):
    '''
    Erweiterung: eine Funktion zum plotten eines farbigen Höhenprofils.
    
    (steigende Abschnitte rot, ebene Abschnitte gelb, fallende Abschnitte grün).
    '''

    #Strecke, Höhe und Steigung aus GPS-Klasse holen
    distance = gps.get_distance()
    elevation = gps.data_elevation
    incline = gps.get_incline(distance)

    #Fehlermeldung, falls Listen sich in Länge unterscheiden
    if not (len(distance) == len(elevation) == len(incline)):
        raise ValueError("Die Listen distance, elevation und incline müssen gleich lang sein.")

    distance_km = distance / 1000.0 #m auf km umrechnen
    incline_deg = np.degrees(incline) #Steigung von Radiant in Grad umrechnen

    #Farbskala RdYlGn (rot, gelb, grün) aus mathplot, mit "-r" invertiert
    color_scale = plt.get_cmap("RdYlGn_r")

    #Grenze festlegen, damit gelb/eben in der Mitte ist
    grenze = np.max(np.absolute(incline_deg))
    norm = plt.Normalize(vmin = -grenze, vmax = grenze)

    fig, ax = plt.subplots(figsize=(9, 4))

    #Einfärben der Streckenabschnitte nach Steitung
    for i in range(len(distance_km) - 1):
        ax.fill_between(
            distance_km[i:i + 1], #x-Werte des Streckenabschnitt
            elevation[i:i + 1], #Höhe des Streckenabschnitts
            np.min(elevation), #untere Grenze
            color = color_scale(norm(incline_deg[i + 1])) #Farbe nach Steigung des Streckenabschnitts
        )

    #Zusätzlich schwarze Linie der Höhenlinie
    ax.plot(distance_km, elevation, "k-", linewidth = 0.8)

    ax.set_xlabel("Strecke / km")
    ax.set_ylabel("Höhe / m")
    ax.set_title("Farbiges Höhenprofil der Ebike-Strecke")
    ax.grid(True)

    logger.info("Graph des farbigen Höhenprofils erstellt.")

    return fig


if __name__ == "__main__":
    #Logging-Konfiguration
    logging.basicConfig(level = logging.INFO, format="%(levelname)s - %(asctime)s - %(message)s")

    from data_from_csv import get_data_from_csv
    from gps_data import GPSData

    #Selbsttest: Höhenprofil mit GPS-Daten aus der csv plotten
    gps = GPSData(get_data_from_csv("final_project_input_data.csv"))
    fig_ele = plot_elevation_profile(gps)
    fig_ele.savefig("hoehenprofil.png")

    #Selbsttest: farbiges Höhenprofil mit GPS-Daten aus der csv plotten
    gps = GPSData(get_data_from_csv("final_project_input_data.csv"))
    fig_ele_col = plot_colored_elevation_profile(gps)
    fig_ele_col.savefig("farbiges_hoehenprofil.png")
    
    plt.show()