'''
Modul zur mathematischen Modellierung und Simulation von E-Bike-Akkupacks.

Dieses Modul stellt die abstrakte Basisklasse `Battery` sowie die spezifischen 
Unterklassen `LiPoBattery` und `NMCBattery` zur Verfügung. Es erlaubt die Simulation 
des Ladezustands (SoC), der temperaturabhängigen Innenwiderstände, der linearen 
Interpolation der Leerlaufspannung (OCV) über Kennlinien-Tabellen sowie der 
Klemmspannung unter Last.
'''

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class Battery(ABC):
    '''
    Abstrakte Basisklasse für das E-Bike-Batteriesystem.
    '''

    # Definition des Datentyps für die OCV-Tabelle (wird in den Unterklassen überschrieben)
    ocv_table: list[tuple[float, float]] = []

    @abstractmethod
    def __init__(
        self,
        capacity_ampere_h: float,
        internal_resistance: float,
        initial_temp: float = 20.0,
        cells_series: int = 10,
        initial_soc: float = 1.0,
        v_min: float = 32.0,
        v_max: float = 42.0
    ) -> None:
        '''
        Konstruktor zur Initialisierung des Akkus und Validierung der Parameter.

        Eingabe:
            capacity_Ah: Kapazität in Amperestunden (Ah)
            internal_resistance: Innenwiderstand in Ohm (Ω)
            initial_temp: Anfangstemperatur des Akkus in °C (Standard: 20.0 °C)
            cells_series: Anzahl der Zellen in Serie (Standard: 10)
            initial_soc: Anfänglicher Ladezustand zwischen 0.0 und 1.0 (Standard: 1.0)
            v_min: Minimale erlaubte Pack-Spannung in Volt (V)
            v_max: Maximale erlaubte Pack-Spannung in Volt (V)
        '''

        logger.info("Initialisiere Battery-Objekt.")

        self.capacity_ampere_h = capacity_ampere_h
        self._capacity_ampere_s = capacity_ampere_h * 3600.0
        self.temperature = initial_temp
        self.internal_resistance = internal_resistance
        self.cells_series = cells_series
        self.v_min = v_min
        self.v_max = v_max

        # Validierung und Fehlermeldungen bei unzulässigen Werten
        if capacity_ampere_h <= 0:
            raise ValueError(
                f"Kapazität muss größer als 0 sein, aktueller Wert: {capacity_ampere_h}"
            )

        if internal_resistance < 0:
            raise ValueError(
                f"Innerer Widerstand darf nicht negativ sein, aktueller Wert: {internal_resistance}"
            )

        if cells_series <= 0:
            raise ValueError(
                f"Anzahl der Batteriezellen muss größer als 0 sein, aktueller Wert: {cells_series}"
            )

        if v_min > v_max:
            raise ValueError(
                f"Minimale Spannung ({v_min}) muss kleiner sein als maximale Spannung ({v_max})"
            )

        #Log-Warnung und Fehlerbehandlung, falls Anfangs-SoC außerhalb des 0.0 - 1.0 Bereiches liegt
        if not 0.0 <= initial_soc <= 1.0:
            logger.warning(
                "Anfangs-SoC von %s liegt außerhalb [0.0, 1.0]. Wert wird begrenzt.",
                initial_soc
            )
        self.soc = max(0.0, min(initial_soc, 1.0))

        # Logging über den aktuellen Zustand des Akkus
        logger.debug(
            "%s: Kapazität = %.1f Ah, SoC = %.1f%%",
            type(self).__name__,
            capacity_ampere_h,
            self.soc * 100
        )

    @abstractmethod
    def open_circuit_voltage(self) -> float:
        '''
        Abstrakte Methode zur Ausgabe der Leerlaufspannung (OCV) beim aktuellen SoC in Volt.
        Muss in den spezifischen Unterklassen implementiert werden.

        Ausgabe:
            float: Die aktuelle Leerlaufspannung in Volt.
        '''
        raise NotImplementedError
    def get_effective_resistance(self) -> float:
        '''
        Berechnet den temperaturabhängigen, effektiven Innenwiderstand des Akkus.
        Bei Temperaturen unter 25 °C steigt der Widerstand um 5% pro Grad Celsius Abweichung.

        Ausgabe:
            float: Der effektive Innenwiderstand in Ohm.
        '''
        temp_factor = 1.0 + 0.05 * max(0, (25.0 - self.temperature))
        return self.internal_resistance * temp_factor

    def interpolate_ocv(self, soc: float) -> float:
        '''
        Hilfsfunktion zur linearen Interpolation der OCV-Kennlinie basierend auf dem SoC.
        Werte außerhalb der vorgegebenen OCV-Tabelle werden auf deren Ränder begrenzt.

        Eingabe:
            soc: Der zu interpolierende Ladezustand (0.0 bis 1.0)

        Ausgabe:
            float: Die interpolierte OCV-Spannung in Volt.
        '''

        logger.debug("Interpolierte OCV-Kennlinie basierend auf dem SoC.")

        table = self.ocv_table

        if soc <= table[0][0]:
            return table[0][1]
        if soc >= table[-1][0]:
            return table[-1][1]

        for (s0, v0), (s1, v1) in zip(table, table[1:]):
            if s0 <= soc <= s1:
                return v0 + (v1 - v0) * (soc - s0) / (s1 - s0)

        return table[0][1]

    def terminal_voltage(self, current: float = 0.0) -> float:
        '''
        Funktion zur Berechnung der Klemmspannung unter Last in Volt.

        Eingabe:
            current: Stromstärke in Ampere (positiv = Entladen, negativ = Laden)

        Ausgabe:
            float: Die resultierende Klemmspannung unter Last in Volt.
        '''

        logger.debug("Berechne Klemmspannung unter Last.")

        effective_r = self.get_effective_resistance()
        voltage = self.open_circuit_voltage() - effective_r * current

        # Log-Warnung, falls aktuelle Spannung unter der zulässigen Minimalspannung liegt
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
        Simuliert die Stromzufuhr oder Stromentnahme über eine Zeitspanne und aktualisiert den SoC.

        Eingabe:
            current: Stromstärke in Ampere (positiv = Entladen, negativ = Laden)
            duration: Zeitspanne des Stromflusses in Sekunden
        '''

        logger.debug("Wende Stromzufuhr auf den Akku an und aktualisiere SoC.")

        if duration < 0:
            raise ValueError(f"Zeitspanne (duration) darf nicht negativ sein, war {duration}")

        new_soc = self.soc - (current * duration) / self._capacity_ampere_s

        # Log-Warnung und Fehlerbehandlung, falls Akku vollständig entladen oder überladen wird
        if new_soc < 0.0:
            logger.warning(
                "Akku während Stromzufuhr vollständig entladen. SoC auf 0.0 gesetzt."
            )
            self.soc = 0.0
        elif new_soc > 1.0:
            logger.warning(
                "Akku während Stromzufuhr (apply_current) überladen. SoC auf 1.0 begrenzt."
            )
            self.soc = 1.0
        else:
            self.soc = new_soc

        # Logging über aktuellen SoC-Stand
        logger.debug(
            "Strom von %.2f A für %.1f s angewendet. Neuer SoC: %.1f%%",
            current,
            duration,
            self.soc * 100
        )

    def is_empty(self) -> bool:
        '''
        Überprüft, ob der Akku leer ist.
        
        Ausgabe:
            bool: True wenn leer (SoC nahe 0), sonst False
        '''
        logger.debug("Überprüfe ob Akku leer ist.")
        return self.soc <= 1e-9

    def is_full(self) -> bool:
        '''
        Überprüft, ob der Akku vollständig geladen ist.

        Ausgabe:
            bool: True wenn voll (SoC nahe 1.0), sonst False
        '''
        logger.debug("Überprüfe ob Akku voll ist.")
        return self.soc >= 1.0 - 1e-9

    def __str__(self) -> str:
        '''
        Erzeugt eine lesbare String-Repräsentation des aktuellen Akku-Zustands.

        Ausgabe:
            str: Formatierter String mit Typ, SoC und aktueller Leerlauf-/Klemmspannung.
        '''
        name = type(self).__name__
        u = self.terminal_voltage()

        return f"{name} (SoC = {self.soc:.1%}, U = {u:.2f} V)"


class LiPoBattery(Battery):
    '''
    Unterklasse für ein Lithium-Polymer (LiPo) Akkupack mit spezifischer OCV-Kennlinie.
    '''
    # LiPo-Batteriezellen Kennwerte
    RESISTANCE = 8e-3
    CELLS_SERIES = 10
    V_MIN: float = 32.0
    V_MAX: float = 42.0

    # OCV-Kennlinie (SoC vs. Pack-Spannung)
    ocv_table = [
        (0.00, 32.00), (0.04, 35.87), (0.09, 36.85), (0.13, 37.56),
        (0.17, 37.87), (0.21, 38.28), (0.26, 38.81), (0.30, 39.05),
        (0.40, 39.55), (0.52, 40.27), (0.64, 40.70), (0.76, 41.16),
        (0.88, 41.65), (1.00, 42.00),
    ]

    def __init__(
        self,
        capacity_ampere_h: float,
        cells_parallel: int = 1,
        initial_soc: float = 1.0,
        initial_temp: float = 20.0
    ) -> None:
        '''
        Konstruktor zur Initialisierung der LiPo-Batterie.

        Eingabe:
            capacity_Ah: Gesamtkapazität in Amperestunden
            cells_parallel: Anzahl der parallel geschalteten Zellenketten
            initial_soc: Anfänglicher Ladezustand (0.0 bis 1.0)
            initial_temp: Anfangstemperatur des Akkus in °C
        '''
        logger.info("Initialisierung der LiPo Battery Klasse.")

        if cells_parallel <= 0:
            raise ValueError(
                f"Anzahl der Batteriezellen muss größer als 0 sein, aktuell: {cells_parallel}"
            )

        # Der Gesamtwiderstand sinkt mit der Anzahl paralleler Zellenketten
        internal_resistance = self.RESISTANCE * self.CELLS_SERIES / cells_parallel
        self.cells_parallel = cells_parallel

        # Initialisierung über die Basisklasse
        super().__init__(
            capacity_ampere_h = capacity_ampere_h,
            internal_resistance = internal_resistance,
            cells_series = self.CELLS_SERIES,
            initial_soc = initial_soc,
            v_min = self.V_MIN,
            v_max = self.V_MAX,
            initial_temp = initial_temp
        )

    def open_circuit_voltage(self) -> float:
        '''
        Berechnet die aktuelle Leerlaufspannung (OCV) per Kennlinien-Interpolation.

        Ausgabe:
            float: Die interpolierte Leerlaufspannung des LiPo-Packs in Volt.
        '''
        return self.interpolate_ocv(self.soc)


class NMCBattery(Battery):
    '''
    Unterklasse für ein Lithium-Nickel-Mangan-Cobalt (NMC) Akkupack mit spezifischer OCV-Kennlinie.
    '''

    # NMC-Batteriezellen Kennwerte
    RESISTANCE = 7e-3
    CELLS_SERIES = 10
    V_MIN: float = 32.0
    V_MAX: float = 42.0

    # OCV-Kennlinie (SoC vs. Pack-Spannung)
    ocv_table = [
        (0.00, 32.00), (0.04, 32.61), (0.09, 33.17), (0.13, 33.85),
        (0.17, 34.24), (0.21, 34.66), (0.26, 35.39), (0.30, 35.65),
        (0.40, 36.65), (0.52, 37.64), (0.64, 38.91), (0.76, 40.14),
        (0.88, 41.08), (1.00, 42.00),
    ]

    def __init__(
        self,
        capacity_ampere_h: float,
        cells_parallel: int = 1,
        initial_soc: float = 1.0,
        initial_temp: float = 20.0
    ) -> None:
        '''
        Konstruktor zur Initialisierung der NMC-Batterie.

        Eingabe:
            capacity_Ah: Gesamtkapazität in Amperestunden
            cells_parallel: Anzahl der parallel geschalteten Zellenketten
            initial_soc: Anfänglicher Ladezustand (0.0 bis 1.0)
            initial_temp: Anfangstemperatur des Akkus in °C
        '''
        logger.info("Initialisierung der NMC Battery Klasse.")

        if cells_parallel <= 0:
            raise ValueError(
                f"Anzahl der Batteriezellen muss größer als 0 sein, aktuell: {cells_parallel}"
            )

        internal_resistance = self.RESISTANCE * self.CELLS_SERIES / cells_parallel
        self.cells_parallel = cells_parallel

        # Initialisierung über die Basisklasse
        super().__init__(
            capacity_ampere_h = capacity_ampere_h,
            internal_resistance = internal_resistance,
            cells_series = self.CELLS_SERIES,
            initial_soc = initial_soc,
            v_min = self.V_MIN,
            v_max = self.V_MAX,
            initial_temp = initial_temp
        )

    def open_circuit_voltage(self) -> float:
        '''
        Berechnet die aktuelle Leerlaufspannung (OCV) per Kennlinien-Interpolation.

        Ausgabe:
            float: Die interpolierte Leerlaufspannung des NMC-Packs in Volt.
        '''
        return self.interpolate_ocv(self.soc)


if __name__ == "__main__":
    import sys

    # Logging für den lokalen Funktionstest einrichten
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        ],
    )

    logger.info("Starte battery Datei...")

    # Vergleich der Entladungsdynamik zwischen LiPo und NMC bei 10 A Last über 20 Minuten
    for battery in (
        LiPoBattery(capacity_ampere_h = 15.0, initial_soc = 1.0),
        NMCBattery(capacity_ampere_h = 15.0, initial_soc = 1.0)
        ):
        print(battery)
        print(f"  OCV bei SoC = 0.5: {battery.interpolate_ocv(0.5):.2f} V")
        battery.apply_current(current = 10.0, duration = 1200.0)
        print(f"  Wert nach 10 A / 20 min -> {battery}")
        print(f"  Akku leer? {battery.is_empty()}")
        print(f"  Akku voll? {battery.is_full()}")
        print()
