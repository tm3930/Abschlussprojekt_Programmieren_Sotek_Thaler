from abc import ABC, abstractmethod
import logging
 
logger = logging.getLogger(__name__)
 

class Battery(ABC):
    """
    Abstrakte Basisklasse für den Akku-Pack.
    """
 
    #Definition des Datentyps für die OCV-Tabelle
    ocv_table: list[tuple[float, float]] = []
 
    @abstractmethod
    def __init__(
        self,
        capacity_Ah: float,
        internal_resistance: float,
        cells_series: int = 10,
        initial_soc: float = 1.0,
        v_min: float = 32.0, #3.2V*10, weil 10 Zellen in Serie
        v_max: float = 42.0 #4.2V*10, weil 10 Zellen in Serie
        ) -> None:
        '''
        Konstruktor zur Initialisierung des Akkus und Validierung der Parameter

        Eingabe:
            capacity_Ah: Kapazität in Amperestunden
            internal_resistance: Innenwiderstand in Ohm
            cells_series: Anzahl der Zellen in Serie
            initial_soc: Anfänglicher Ladezustand
            v_min: Minimale erlaubte Spannung
            v_max: Maximale erlaubte Spannung
        
        '''

        logger.info("Initialisiere Battery-Objekt.")

        self.capacity_Ah = capacity_Ah
        self._capacity_As = capacity_Ah * 3600.0
        self.internal_resistance = internal_resistance
        self.cells_series = cells_series
        self.v_min = v_min
        self.v_max = v_max

        #Fehlermeldungen bei unzulässigen Werten
        if capacity_Ah <= 0:
            raise ValueError(f"Kapazität (capacity_Ah) muss größer als 0 sein, aktueller Wert: {capacity_Ah}")
        
        if internal_resistance < 0:
            raise ValueError(f"Innerer Widerstand (internal_resistance_ohm) darf nicht negativ sein, aktueller Wert: {internal_resistance}")
        
        if cells_series <= 0:
            raise ValueError(f"Anzahl der Batteriezellen muss größer als 0 sein, aktueller Wert: {cells_series}")
        
        if v_min > v_max:
            raise ValueError(f"Minimale Spannung v_min ({v_min}) muss kleiner sein als maximale Spannung vmax ({v_max})")

        #Log-Warnung und Fehlerbehandlung, falls Anfangs-SoC außerhalb des 0.0 - 1.0 Bereiches liegt
        if not (0.0 <= initial_soc <= 1.0):
            logger.warning("Anfangs-SoC (initial_soc) von %s liegt ausserhalb [0.0, 1.0]. Wert wird begrenzt.", initial_soc)
        self.soc = max(0.0, min(initial_soc, 1.0))

        #Logging über aktuellen Zustand des Akkus
        logger.debug("%s: Kapazität = %.1f Ah, SoC = %.1f%%", type(self).__name__, capacity_Ah, self.soc * 100)
 
    @abstractmethod
    def open_circuit_voltage(self) -> float:
        '''
        Funktion zur Ausgabe der Leerlaufspannung (OCV) bei aktuellem SoC in V.
        
        Da dieser Wert in den Unterklassen (LiPo & NMC) ausgeführt wird und nicht in dieser Oberklasse,
        gibt die Funktion hier nur eine Fehlermeldung aus.

        Ausgabe:
            Leerlaufspannung       
        '''

        raise NotImplementedError
 
    def interpolate_ocv(self, soc: float) -> float:
        '''
        Funktion zur Interpolation der OCV-Kennlinie.

        Werte außerhalb der vorgegebenen OCV-Tabelle werden auf deren Ränder begrenzt.

        Eingabe:
            soc: Aktueller Ladezustand

        Ausgabe:
            interpolierte OCV-Spannung 

        '''

        logger.debug("Interpolierte OCV-Kennlinie basierend auf dem SoC")

        table = self.ocv_table

        if soc <= table[0][0]:
            return table[0][1]
        if soc >= table[-1][0]:
            return table[-1][1]

        for (s0, v0), (s1, v1) in zip(table, table[1:]):
            if s0 <= soc <= s1:
                return v0 + (v1 - v0) * (soc - s0) / (s1 - s0)
 
    def terminal_voltage(self, current: float = 0.0) -> float:
        '''
        Funktion zur Ausgabe der Spannung unter Last in V

        Eingabe:
            current: Stromstärke (positiv = Entladen, negativ = Laden)

        Ausgabe:
            Spannung unter Last
        '''
        
        logger.debug("Berechne Klemmspannung unter Last")

        voltage = self.open_circuit_voltage() - self.internal_resistance * current

        #Log-Warnung, falls aktuelle Spannung unter Minimalspannung liegt
        if voltage < self.v_min:
            logger.warning(
                "Aktuelle Spannung von %.2f V bei vorgegebener Minimalspannung von %.2f V "
                "(Strom = %.2f A, SoC = %.1f%%).",
                voltage,
                self.v_min,
                current,
                self.soc * 100
            )
        return voltage

    def apply_current(self, current: float, duration: float) -> None:
        '''
        Funktion zur Stromzufuhr über eine gewisse Zeitspanne und Aktualisierung des SoC

        Eingabe:
            current: Stromstärke
            duration: Zeitspanne
        '''

        logger.debug("Wende Stromzufuhr auf den Akku an und aktualisiere SoC.")        
        
        if duration < 0:
            raise ValueError(f"Zeitspanne (duration) darf nicht negativ sein, war {duration}")
 
        new_soc = self.soc - (current * duration) / self._capacity_As
 
        #Log-Warnung und Fehlerbehandlung, falls Akku ent- bzw. überladen ist (SoC außerhalb der 0.0 - 1.0 Grenze)
        if new_soc < 0.0:
            logger.warning("Akku während Strumzufuhr (apply_current) vollständig entladen. SoC auf 0.0 gesetzt.")
            self.soc = 0.0
        elif new_soc > 1.0:
            logger.warning("Akku während Strumzufuhr (apply_current) überladen. SoC auf 1.0 begrenzt.")
            self.soc = 1.0
        else:
            self.soc = new_soc

        #Logging über aktuellen SoC-Stand bei Stromzufuhr über gewisse Zeitspanne
        logger.debug(
            "Strom von %.2f A für %.1f s angewendet. Neuer SoC: %.1f%%",
            current,
            duration,
            self.soc * 100
        )
 
    def is_empty(self) -> bool:
        '''
        Funktion zur Überprüfung, falls der Akku leer ist.
        
        Ausgabe:
            True wenn leer, sonst False
        '''

        logger.debug("Überprüfe ob Akku leer ist")
        return self.soc <= 1e-9
 
    def is_full(self) -> bool:
        '''
        Funktion zur Überprüfung, ob der Akku voll ist

        Ausgabe:
            True wenn voll, sonst False
        '''

        logger.debug("Überprüfe ob Akku voll ist")
        return self.soc >= 1.0 - 1e-9
    
    def __str__(self) -> str:
        '''
        Funktion zur sinnvollen Ausgabe der Werte als String

        Ausgabe:
            Formatierter String mit Akku-Informationen
        '''
        return f"{type(self).__name__} (SoC = {self.soc*100:.1f}%, U = {self.terminal_voltage():.2f} V)"
 
 
class LiPoBattery(Battery):
    '''
    Unterklasse der LiPo-Batterie mit spezifischen Eigenschaften und Kennwerten
    '''    
    #LiPo-Batteriezellen Kennwerte (laut Angabe)
    RESISTANCE = 8e-3
    CELLS_SERIES = 10
    V_MIN: float = 32.0
    V_MAX: float = 42.0
    
    #OCV-Kennlinie (laut Angabe)
    ocv_table = [
        (0.00, 32.00), (0.04, 35.87), (0.09, 36.85), (0.13, 37.56),
        (0.17, 37.87), (0.21, 38.28), (0.26, 38.81), (0.30, 39.05),
        (0.40, 39.55), (0.52, 40.27), (0.64, 40.70), (0.76, 41.16),
        (0.88, 41.65), (1.00, 42.00),
    ]
 
    def __init__(
            self,
            capacity_Ah: float,
            cells_parallel: int = 1,
            initial_soc: float = 1.0
            ) -> None:
        '''
        Konstruktor zur Initialisierung der LiPo-Batterie

        Eingabe:
            capacity_Ah: Kapazität in Amperestunden
            cells_parallel: Anzahl der parallel geschalteten Zellen
            initial_soc: Anfänglicher Ladezustand
        '''

        logging.info("Initialisierung der LiPo Battery Klasse")
        
        #Fehlermeldung, falls Anzahl der Zellen nicht größer 0 ist
        if cells_parallel <= 0:
            raise ValueError(f"Anzahl der Batteriezellen (cells_parallel) muss größer als 0 sein, aktuell: {cells_parallel}")

        internal_resistance = self.RESISTANCE * self.CELLS_SERIES / cells_parallel
        self.cells_parallel = cells_parallel
        
        #Initialisierung der Werte für die Oberklasse "Battery"
        super().__init__(
            capacity_Ah = capacity_Ah,
            internal_resistance = internal_resistance,
            cells_series = self.CELLS_SERIES,
            initial_soc = initial_soc,
            v_min = self.V_MIN,
            v_max = self.V_MAX,
        )

    
    #Aktuelle interpolte (auf Randwerte begrenzte) Leerlaufspannung (OCV)
    def open_circuit_voltage(self) -> float:
        '''
        Funktion zur Berechnung der aktuellen Leerlaufspannung (OCV) per Interpolation

        Ausgabe:
            Leerlaufspannung
        '''

        return self.interpolate_ocv(self.soc)
 
 
class NMCBattery(Battery):
    '''
    Unterklasse der NMC-Batterie mit spezifischen Eigenschaften und Kennwerten
    '''

    #NMC-Batteriezellen Kennwerte (laut Angabe)
    RESISTANCE = 7e-3
    CELLS_SERIES = 10
    V_MIN: float = 32.0
    V_MAX: float = 42.0
    
    #OCV-Kennlinie (laut Angabe)
    ocv_table = [
        (0.00, 32.00), (0.04, 32.61), (0.09, 33.17), (0.13, 33.85),
        (0.17, 34.24), (0.21, 34.66), (0.26, 35.39), (0.30, 35.65),
        (0.40, 36.65), (0.52, 37.64), (0.64, 38.91), (0.76, 40.14),
        (0.88, 41.08), (1.00, 42.00),
    ]
 
    def __init__(
            self,
            capacity_Ah: float,
            cells_parallel: int = 1,
            initial_soc: float = 1.0
            ) -> None:
        
        '''
        Konstruktor zur Initialisierung der NMC-Batterie

        Eingabe:
            capacity_Ah: Kapazität in Amperestunden
            cells_parallel: Anzahl der parallel geschalteten Zellen
            initial_soc: Anfänglicher Ladezustand
        '''

        logging.info("Initialisierung der NMC Battery Klasse")

        #Fehlermeldung, falls Anzahl der Zellen nicht größer 0 ist
        if cells_parallel <= 0:
            raise ValueError(f"Anzahl der Batteriezellen (cells_parallel) muss größer als 0 sein, aktuell: {cells_parallel}")
        
        internal_resistance = self.RESISTANCE * self.CELLS_SERIES / cells_parallel
        self.cells_parallel = cells_parallel

        #Initialisierung der Werte für die Oberklasse "Battery"
        super().__init__(
            capacity_Ah = capacity_Ah,
            internal_resistance = internal_resistance,
            cells_series = self.CELLS_SERIES,
            initial_soc = initial_soc,
            v_min = self.V_MIN,
            v_max = self.V_MAX,
        )
    
    #Aktuelle interpolierte (auf Randwerte begrenzte) Leerlaufspannung (OCV)
    def open_circuit_voltage(self) -> float:
        '''
        Funktion zur Berechnung der aktuellen Leerlaufspannung (OCV) per Interpolation

        Ausgabe:
            Leerlaufspannung
        '''
        
        return self.interpolate_ocv(self.soc)
 
 
if __name__ == "__main__":
    import sys
    
    # Logging einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte battery Datei...")

    #Selbsttest: Ermittlung von Leerlaufspannung (OCV) bei bestimmtem SoC & Batterie-Werte bei 10 A über 20 min entladen
    for battery in (LiPoBattery(capacity_Ah = 15.0, initial_soc = 1.0), NMCBattery(capacity_Ah = 15.0, initial_soc = 1.0)):
        print(battery)
        print(f"  OCV bei SoC = 0.5: {battery.interpolate_ocv(0.5):.2f} V")
        battery.apply_current(current = 10.0, duration = 1200.0)
        print(f"  Wert nach 10 A / 20 min -> {battery}")
        print(f"  Akku leer? {battery.is_empty()}")
        print(f"  Akku voll? {battery.is_full()}")
        print()