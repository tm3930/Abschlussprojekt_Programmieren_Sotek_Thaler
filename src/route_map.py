'''
Modul zum Einzeichnen der gefahrenen Route auf einer GPS-Landkarte.

Dieses Modul übernimmt die Koordinaten aus dem GPSData-Modul.
Aus diesen erstellt es eine Route auf einer GPS-Landkarte mit "folium".
'''

#generelle Imports
from pathlib import Path
import webbrowser
import logging
import pandas as pd
import numpy as np
import folium

#Imports von anderen selbstgeschriebenen Dateien
from gps_data import GPSData

#__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
logger = logging.getLogger(__name__)

class RouteMap:
    '''
    Klasse zum visualisieren der Route auf einer Karte
    '''

    def __init__(self, data: pd.DataFrame) -> None:
        '''
        Konstruktor zum Übernehmen der GPS-Koordinaten aus dem GPSData-Objekt.

        Eingabe:
            gps: GPSData-Klasse mit den Attributen data_latitude und data_longitude
        '''

        logger.info("Initialisiere RouteMap-Objekt.")
        self.data = data

        #Validierung: Fehlermeldung, falls erforderliche Spalten im DataFrame fehlen
        for col in ("lat", "lon"):
            if col not in data:
                raise KeyError(f"In den Simulationsdaten fehlt die erforderliche Spalte: '{col}'")

        #Übernehmen der benötigten Koordinaten aus GPSData
        self.data_latitude = self.data["lat"].to_numpy()
        self.data_longitude = self.data["lon"].to_numpy()

        #Fehlermeldung, falls keine Koordinaten zum vorhanden sind
        if len(self.data_latitude) == 0:
            raise ValueError("GPS-Daten fehlen -> Zeichnen der Route fehlgeschlagen")

        #Fehlermeldung, falls Breiten- und Längengrad unterschiedlich lang sind
        if len(self.data_latitude) != len(self.data_longitude):
            raise ValueError("Breiten- und Längengrad müssen gleich lang sein.")

        logger.info("GPS-Koordinaten erfolgreich übernommen.")

    def create_map(self) -> folium.Map:
        '''
        Funktion zum Erstellen der Karte mit eingezeichneter Route als blaue Linie.

        Ausgabe:
            karte: folium-Karte, die als html gespeichert und ausgeführt wird
        '''

        logger.debug("Karte mit Ebike-Route wird erstellt")

        #Route als Liste von [Breitengrad, Längengrad]-Paaren nach folium-Vorgabe
        route = [[lat, lon] for lat, lon in zip(self.data_latitude, self.data_longitude)]

        #Kartenmittelpunkt = Mittelwert aller Koordinaten
        center = [float(np.mean(self.data_latitude)), float(np.mean(self.data_longitude))]

        #Karte mit OpenStreetMap-Hintergrund erstellen
        maps = folium.Map(location=center, zoom_start = 13, tiles="OpenStreetMap")

        #Route als blaue Linie einzeichnen
        folium.PolyLine(route, color="blue", weight = 4, opacity = 0.8).add_to(maps)

        #Start- und Zielpunkt
        folium.Marker(
            route[0],
            popup = ("Start/Ziel"),
            icon = folium.Icon(color="red"),
        ).add_to(maps)

        #Zoom auf Route anoassen
        maps.fit_bounds([
            [float(np.min(self.data_latitude)), float(np.min(self.data_longitude))],
            [float(np.max(self.data_latitude)), float(np.max(self.data_longitude))],
        ])

        logger.info("Route wurde auf der Karte eingezeichnet")

        return maps


if __name__ == "__main__":
    import sys

    #Logging einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte route_map...")

    from data_from_csv import get_data_from_csv

    #GPS-Daten aus der csv einlesen und Route auf der Karte zeichnen
    gps = GPSData(get_data_from_csv("final_project_input_data.csv"))
    route_map = RouteMap(gps)
    karte = route_map.create_map()

    #Karte als html speichern und im Browser öffnen
    output_path = Path("route_map.html").resolve()
    karte.save(str(output_path))
    webbrowser.open(output_path.as_uri())

    print("Karte gespeichert: route_map.html")
