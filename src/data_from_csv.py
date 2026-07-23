'''
Modul zum Laden, Normalisieren und Validieren von GPS- und Umgebungsdaten.

Dieses Modul liest die rohen Fahrdaten aus einer CSV-Datei ein, konvertiert die 
Zeitstempel in relative Sekunden für die Simulation und führt umfangreiche 
Plausibilitätsprüfungen für Koordinaten, Höhenprofile und Temperaturen durch, 
um fehlerhafte Datensätze vorab herauszufiltern.
'''

#allgemeine Imports
from pathlib import Path
import logging
import sys
import numpy as np
import pandas as pd

#__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
logger = logging.getLogger(__name__)

def get_data_from_csv(csv_name: str) -> pd.DataFrame:
    '''
    Funktion zum Laden und Auslesen von GPS-Daten aus einer CSV-Datei. 
    Außerdem wird durch die Funktion validate() kontrolliert ob die Daten vollständig sind

    Eingabe:
        csv_name: Name der CSV-Datei
    
    Ausgabe:
        DataFrame: welches kontrolliert wurde ob alle Daten vollständig sind
    '''

    #Pfad zur CSV-Datei:
    base_dir = Path(__file__).resolve().parent.parent
    path_to_csv = base_dir / "data" / "raw" / csv_name
    data = pd.read_csv(
        path_to_csv,
        sep=";",                    #Semikolon als Trennzeichen
        parse_dates=["time"]        #parse_dates = Zeit direkt als datetime einlesen
    )

    #Daten auf Korrektheit überprüfen:
    if not validate(data):
        #Wenn validate() einen Fehler erkennt wird das Programm abgebrochen
        logger.error("Programm abgebrochen aufgrund fehlerhafter Daten.")
        raise ValueError("Die hochgeladenen CSV-Daten sind ungültig. Siehe 'app.log' für Details.")

    #Zeit umrechnen, sodass Sekunden von 0 bis zum Ende gemessen werden (0, 1, 5, 125, ...)
    #von jeder Zeile wird der allererste Zeitstempel (.iloc[0]) abgezogen
    data["time"] = (data["time"] - data["time"].iloc[0]).dt.total_seconds()

    #Wenn kein Fehler erkannt wird, dann wird dies notiert und der Code wird weiter ausgeführt
    logger.info("Daten erfolgreich verifiziert und bereit zur Verarbeitung.")

    return data


def validate(df: pd.DataFrame) -> bool:
    '''
    Funktion zur Überprüfung der GPS- und Temperaturdaten auf Fehler und Plausibilität.

    Eingabe:
        df: Das Pandas DataFrame mit den Spalten 'lat', 'lon', 'ele', 'temperature' und 'time'

    Ausgabe:
        True, wenn alle Tests bestanden wurden, sonst False
    '''

    logger.info("Starte Datenvalidierung...")

    #Kontrolle ob Daten vorhanden sind:
    if len(df) == 0:
        logger.error("Validierungsfehler: Das Dataset ist leer.")
        return False

    #Kontrolle ob irgendwelche Werte fehlen, im Datensatz Zellen ausgelassen wurden
    if df.isnull().any().any():
        logger.error("Validierungsfehler: Es sind fehlende Werte vorhanden.")
        return False

    #Kontrolle ob sich alle Breitengrade in +90 und -90 Grad befinden
    if not df["lat"].between(-90, 90).all():
        logger.error("Validierungsfehler: Ungültige Latitude-Werte außerhalb von -90 bis 90 Grad.")
        return False

    #Kontrolle ob sich alle Längengrade in +180 und -180 Grad befinden
    if not df["lon"].between(-180, 180).all():
        logger.error(
            "Validierungsfehler: Ungültige Longitude-Werte außerhalb von -180 bis 180 Grad."
        )
        return False

    #Kontrolle ob sich alle Höhendaten zwischen -10 Höhenmetern und +3000 Höhenmetern befinden
    if not df["ele"].between(-10, 3000).all():
        logger.error(
            "Validierungsfehler: Unplausible Höhenwerte fürs Radfahren außerhalb von -10 bis 3000hm"
        )
        return False

    #Kontrolle ob für die Temperatur realistische Werte vorhanden sind zwischen -20 und +45 Grad
    if not df["temperature"].between(-20, 45).all():
        logger.error(
            "Validierungsfehler: Unplausible Temperaturwerte (außerhalb von -20°C bis 45°C)."
        )
        return False

    #Zeitdifferenz berechnen für einfacheren Vergleich der Zeiten
    time_diff = df["time"].diff().dt.total_seconds().to_numpy()

    #Kontrolle ob die Zeit irgendwann still steht
    if np.any(time_diff == 0):
        logger.error("Validierungsfehler: Es gibt identische Zeitstempel (Zeitabschnitt ist 0s).")
        return False

    #Kontrolle ob die Zeit irgendwann rückwerts läuft
    if np.any(time_diff < 0):
        logger.error("Validierungsfehler: Die Zeitliste ist nicht chronologisch aufsteigend.")
        return False

    #Wenn alle Daten korrekt sind
    logger.info("Alle Validierungstests erfolgreich bestanden.")
    return True



#Wird nur ausgeführt wenn direkt die Datei ausgeführt wird.
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

    logger.info("Starte data_from_csv Datei...")

    try:
        #Daten laden
        gps_data = get_data_from_csv("final_project_input_data.csv")

        #Kurze Vorschau der Daten im Terminal anzeigen
        print("\n=== Data from CSV ===")
        print(gps_data.head())
        print("=== Data from CSV ===\n")

    except ValueError as e:
        logger.error("Ausführung gestoppt: %s", e)
