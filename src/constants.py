'''
Zentrale physikalische und mathematische Konstanten.
'''

GRAVITY: float = 9.81              #Erdbeschleunigung in m/s^2
STD_PRESSURE: float = 101325.0     #Standard-Luftdruck auf Meereshöhe in Pa
STD_TEMP_KELVIN: float = 273.15    #Standard-Temperatur (0°C) in Kelvin
SEA_LEVEL_TEMP: float = 288.15     #Standardtemperatur auf Meereshöhe (15 °C) in K
TEMP_LAPSE_RATE: float = 0.0065    #Temperaturabnahme mit der Höhe in K/m
GAS_CONSTANT_AIR: float = 287.05   #Spezifische Gaskonstante für Luft in J/(kg*K)
EARTH_RADIUS_METERS: float = 6371000.0  #Mittlerer Erdradius in m

MPS_TO_KMH: float = 3.6                 #Umrechnungsfaktor m/s in km/h
INCH_TO_M: float = 0.0254               #Umrechnungsfaktor Zoll in m
HOURS_TO_SECONDS: int = 3600            #Umrechnungsfaktor h in s
KM_TO_M: int = 1000                     #Umrechnunsfaktor km in m
