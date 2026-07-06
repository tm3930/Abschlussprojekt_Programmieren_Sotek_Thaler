import numpy as np

def validate(df):
    # 1. leere Daten
    if len(df) == 0:
        print("Validierungsfehler: Das Dataset ist leer.")
        return False

    # 2. fehlende Werte
    if df.isnull().any().any():
        print("Validierungsfehler: Es sind fehlende Werte (NaN) vorhanden.")
        return False

    # 3. GPS Bereich
    if not df["lat"].between(-90, 90).all():
        print("Validierungsfehler: Ungültige Latitude-Werte außerhalb von -90 bis 90 Grad.")
        return False

    if not df["lon"].between(-180, 180).all():
        print("Validierungsfehler: Ungültige Longitude-Werte außerhalb von -180 bis 180 Grad.")
        return False

    # 4. Temperatur grob plausibel
    if not df["temperature"].between(-30, 45).all():
        print("Validierungsfehler: Unplausible Temperaturwerte (außerhalb von -30°C bis 45°C).")
        return False

    # 5. NEU: Zeit-Validierung (Zeiten müssen strikt aufsteigend sein)
    # Wir berechnen die Differenzen der Zeit-Spalte
    time_diffs = np.diff(df["time"].to_numpy())

    # Wenn eine Differenz 0 ist, steht die Zeit still
    if np.any(time_diffs == 0):
        print("Validierungsfehler: Es gibt identische Zeitstempel (Zeitabschnitt ist 0s).")
        return False

    # Wenn eine Differenz kleiner als 0 ist, läuft die Zeit rückwärts
    if np.any(time_diffs < 0):
        print("Validierungsfehler: Die Zeitliste ist nicht chronologisch aufsteigend.")
        return False

    # Wenn alles glattgelaufen ist
    return True