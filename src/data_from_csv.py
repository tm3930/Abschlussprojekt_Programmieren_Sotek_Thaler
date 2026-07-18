from pathlib import Path
import logging
import sys
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def get_data_from_csv(csv_name: str) -> pd.DataFrame:
    '''
    Funktion zum Laden und Auslesen von GPS-Daten aus einer CSV-Datei. Außerdem wird durch die Funktion validate() kontrolliert ob die Daten vollständig sind

    Eingabe:
        csv_name: Name der CSV-Datei
    
    Ausgabe:
        DataFrame: welches kontrolliert wurde ob alle Daten vollständig sind und weitere Berechnungen damit gemacht werden können
    '''

    #Pfad zur CSV-Datei:
    base_dir = Path(__file__).resolve().parent.parent
    path_to_csv = base_dir / "data" / "raw" / csv_name
    data = pd.read_csv(
        path_to_csv, 
        sep=";",                    #Semikolon als Trennzeichen
        parse_dates=["time"]        #parse_dates = Zeit direkt als datetime einlesen
    )

    #Zeit umrechnen, sodass Sekunden von 0 bis zum Ende gemessen werden (0, 1, 5, 125, ...) - von jeder Zeile wird der allererste Zeitstempel (.iloc[0]) abgezogen
    data["time"] = (data["time"] - data["time"].iloc[0]).dt.total_seconds()

    #Daten auf Korrektheit überprüfen:
    if not validate(data):
        #Wenn validate() einen Fehler erkennt wird das Programm abgebrochen und Details in die app.log Datei hineingeschrieben
        logger.error("Programm abgebrochen aufgrund fehlerhafter Daten.")
        raise ValueError("Die hochgeladenen CSV-Daten sind ungültig. Siehe 'app.log' für Details.")
    #Wenn kein Fehler erkannt wird, dann wird dies notiert und der Code wird weiter ausgeführt
    logger.info("Daten erfolgreich verifiziert und bereit zur Verarbeitung.")
    
    return data


def validate(df: pd.DataFrame) -> bool:
    """Funktion zur Überprüfung der GPS- und Temperaturdaten auf Fehler und Plausibilität.

    Eingabe:
        df: Das Pandas DataFrame mit den Spalten 'lat', 'lon', 'ele', 'temperature' und 'time'

    Ausgabe:
        True, wenn alle Tests bestanden wurden, sonst False
    """
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
        logger.error("Validierungsfehler: Ungültige Longitude-Werte außerhalb von -180 bis 180 Grad.")
        return False

    #Kontrolle ob sich alle Höhendaten zwischen -10 Metern und +3000 Metern über dem Meeresspiegel befinden
    if not df["ele"].between(-10, 3000).all():
        logger.error("Validierungsfehler: Unplausible Höhenwerte fürs Radfahren (außerhalb von -10m bis 3000m).")
        return False

    #Kontrolle ob es unrealistische Höhen-Sprünge (GPS-Ausreißer) gibt (mehr als 20 Meter Veränderung von einem zum nächsten Punkt)
    delta_ele = np.abs(np.diff(df["ele"].to_numpy()))
    if np.any(delta_ele > 20):
        anzahl_fehler = np.sum(delta_ele > 20)
        logger.warning(
            "Validierungswarnung: Es wurden %d extreme Höhen-Sprünge (>20m) festgestellt. Das deutet auf temporäre GPS-Messfehler hin.",
            anzahl_fehler
        )

    #Kontrolle ob für die Temperatur realistische Werte vorhanden sind zwischen -20 und +45 Grad
    if not df["temperature"].between(-20, 45).all():
        logger.error("Validierungsfehler: Unplausible Temperaturwerte (außerhalb von -20°C bis 45°C).")
        return False

    #Kontrolle ob die Zeiten immer aufsteigend sind
    delta_time = np.diff(df["time"].to_numpy())
    
    #Kontrolle ob sie still steht
    if np.any(delta_time == 0):
        logger.error("Validierungsfehler: Es gibt identische Zeitstempel (Zeitabschnitt ist 0s).")
        return False

    #Kontrolle ob sie rückwerts läuft
    if np.any(delta_time < 0):
        logger.error("Validierungsfehler: Die Zeitliste ist nicht chronologisch aufsteigend.")
        return False

    #Wenn alle Daten korrekt sind
    logger.info("Alle Validierungstests erfolgreich bestanden.")
    return True



#Wird nur ausgeführt wenn direkt die Datei ausgeführt wird.
if __name__ == "__main__":
    
    #Logging einrichten:
    logging.basicConfig(
        level=logging.INFO, #bedeutet, dass Info, Warning, Error und Critical mitgeschrieben wird
        format="%(asctime)s [%(levelname)s] %(message)s",   #schreibt Zeit [Info / ...] und dann die Nachricht
        handlers=[
            logging.StreamHandler(sys.stdout),  #Ausgabe im Terminal
            logging.FileHandler("app.log", mode="a", encoding="utf-8")  #Ausgabe in eigener Logging Datei
        ]
    )
    
    logger.info("Starte data_from_csv Datei...")
    
    try:
        #Daten laden
        gps = get_data_from_csv("final_project_input_data.csv")

        #Kurze Vorschau der Daten im Terminal anzeigen
        print("\n--- Daten-Vorschau (erste 5 Zeilen) ---")
        print(gps.head())
        print("---------------------------------------\n")
        
    except ValueError as e:
        logger.error("Ausführung gestoppt: %s", e)