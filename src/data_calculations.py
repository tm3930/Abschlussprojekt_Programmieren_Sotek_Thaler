import numpy as np

def get_distance(latitude, longitude):
    '''
    Funktion zur Berechnung der zurückgelegten Streck aufgrund von Längen- & Breitengrade von GPS Daten
    Dies wird mithilfe der Haversine Formel gemacht
    
    Eingabe:
        Breitengrade
        Längengrade

    Ausgabe:
        zurückgelegte Strecke 
    '''

    #Umwandlung von Grad in Radiant
    latitude_rad = np.radians(latitude)
    longitude_rad = np.radians(longitude)

    #Berechnung der Differenz zwischen 2 Punkten
    delta_latitude = np.diff(latitude_rad)
    delta_longitude = np.diff(longitude_rad)

    #Haversine Formel berechnen
    a = np.sin(delta_latitude / 2.0)**2 + np.cos(latitude_rad[:-1]) * np.cos(latitude_rad[1:]) * np.sin(delta_longitude / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distances = c * 6371000  # 6371000 Meter ist der Erdradius

    #Aufsummieren, der einzelnen Ergebnisse um die zurückgelegte Strecke zu erhalten
    distance_travelled = np.concatenate(([0.0], np.cumsum(distances)))
    
    return distance_travelled


def get_velocity(distance, time):
    '''
    Funktion zur Bestimmung der Geschwindigkeit = Zurückgelegte Strecke über der Zeit
    
    Eingabe:
        Zeit
        Strecke
    
    Ausgabe:
        Geschwindigkeit
    '''
    
    #Berechnung der Differenz zwischen 2 Punkten
    delta_time = np.diff(time)
    delta_distance = np.diff(distance)

    #Berechnung der Geschwindigkeit aus Strecke / Zeit
    velocity = delta_distance / delta_time


    return np.insert(velocity, 0, 0.0) #Anfangswert auf 0.0 gesetzt, damit die Listen wieder die gleiche Länge haben


def get_acceleration(velocity, time):
    '''
    Funktion zur Bestimmung der Beschleunigung = Änderung der Geschwindigkeit über der Zeit
    
    Eingabe:
        Zeit
        Geschwindigkeit
    
    Ausgabe:
        Beschleunigung
    '''
    
    #Berechnung der Differenz zwischen 2 Punkten
    delta_time = np.diff(time)
    delta_velocity = np.diff(velocity)

    #Berechnung der Geschwindigkeit aus Strecke / Zeit
    acceleration = delta_velocity / delta_time


    return np.insert(acceleration, 0, 0.0) #Anfangswert auf 0.0 gesetzt, damit die Listen wieder die gleiche Länge haben
