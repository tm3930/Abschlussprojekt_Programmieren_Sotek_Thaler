'''
Modul zur automatisierten Erstellung eines technischen PDF-Auswertungsberichts 
für die E-Bike-Fahrsimulation.
'''

import logging
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

logger = logging.getLogger(__name__)


def generate_report_reportlab(
    ergebnisse: dict[str, Any],
    plot_paths: list[Path],
    output_filename: str = "ebike_simulation_analyse.pdf"
) -> None:
    '''
    Funktion zur automatisierten Erstellung eines technischen PDF-Auswertungsberichts.
    
    Diese Funktion generiert ein PDF-Dokument mit ReportLab, das die aggregierten
    Simulationsergebnisse tabellarisch darstellt und die generierten Matplotlib-Diagramme einbettet.
    
    Eingabe:
        ergebnisse: Ein Dictionary mit den aggregierten Kennzahlen der Simulation 
                    (z. B. aus der summary-Methode der EBikeSimulation).
        plot_paths: Eine Liste von Dateipfaden (pathlib.Path) zu den zuvor 
                    gespeicherten PNG-Diagrammen.
        output_filename: Der Zieldateiname oder Zielpfad für das PDF 
                         (Standard: "ebike_simulation_analyse.pdf").
        
    Ausgabe:
        Keine (Die PDF-Datei wird direkt im Dateisystem gespeichert).
    '''
    logger.info("Starte Generierung des PDF-Berichts...")

    # 1. Dokumentenstruktur initialisieren
    # A4-Format definieren und Ränder auf 56 Punkte (ca. 20 mm) setzen
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=56,
        leftMargin=56,
        topMargin=56,
        bottomMargin=56
    )

    story: list[Any] = []
    styles = getSampleStyleSheet()

    # 2. Eigene Text-Styles für Überschriften und Fließtext definieren
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=6
    )

    normal_style = styles['Normal']
    normal_style.textColor = colors.HexColor('#2c3e50')
    normal_style.fontSize = 10
    normal_style.leading = 14

    # 3. Titel und Kopfzeile hinzufügen
    story.append(Paragraph("E-Bike Simulations- und Analysebericht", title_style))
    story.append(Paragraph(
        "Automatisiertes technisches Auswertungsdokument &bull; g = 9.81 m/s²",
        normal_style
    ))
    story.append(Spacer(1, 15))

    # 4. Abschnitt: Zusammenfassung der Kennzahlen
    story.append(Paragraph("<b>1. Zusammenfassung der Kennzahlen</b>", styles['Heading2']))

    # Daten für die Tabelle aus dem ergebnisse-Dictionary sicher abrufen
    data: list[list[str]] = [
        ['Fahrzeit', f"{ergebnisse.get('total_time_s', 0) / 60:.1f} min"],
        ['Zurückgelegte Strecke', f"{ergebnisse.get('total_distance_km', 0):.2f} km"],
        ['Ø Geschwindigkeit', f"{ergebnisse.get('avg_velocity_kmh', 0):.1f} km/h"],
        ['Max. Geschwindigkeit', f"{ergebnisse.get('max_velocity_kmh', 0):.1f} km/h"],
        ['Kumulierte Höhenmeter (+)', f"{ergebnisse.get('elevation_gain_m', 0):.1f} hm"],
        ['Kumulierte Höhenmeter (-)', f"{ergebnisse.get('elevation_loss_m', 0):.1f} hm"],
        ['Maximalleistung', f"{ergebnisse.get('max_power_w', 0):.1f} W"],
        ['Erbrachte mech. Energie', f"{ergebnisse.get('mechanical_energy_wh', 0):.1f} Wh"],
        ['Rekuperierte Energie', f"{ergebnisse.get('recuperated_energy_wh', 0):.1f} Wh"],
        ['Dissipierte Energie', f"{ergebnisse.get('dissipated_energy_wh', 0):.1f} Wh"],
        ['Akku-Ladestand (Start -> Ende)', f"{ergebnisse.get(
            'start_soc_percent', 0):.1f}% -> {ergebnisse.get('end_soc_percent', 0):.1f}%"],
        ['Verbrauchter SoC', f"{ergebnisse.get('consumed_soc_percent', 0):.1f}%"]
    ]

    # Tabellen-Objekt instanziieren und optisches Styling anwenden
    t = Table(data, colWidths=[200, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f4f6f8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d1d8e0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d8e0')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#2c3e50')),
    ]))

    story.append(t)
    story.append(Spacer(1, 20))

    # 5. Abschnitt: Physikalische Modellierung & Hinweise
    story.append(Paragraph(
        "<b>2. Physikalische Modellierung & Performance</b>", styles['Heading2']
    ))
    story.append(Paragraph(
        "Die Simulation wurde über vektorisierte Operationen und Numba-Kernel optimiert, "
        "um eine performante Ausführung der differentiellen Akkupaket- " \
        "und Dynamikgleichungen zu gewährleisten.",
        normal_style
    ))
    story.append(Spacer(1, 20))

    # 6. Abschnitt: Grafische Auswertung und Einbettung der Diagramme
    logger.debug("Bette Diagramme in das PDF-Dokument ein.")
    story.append(Paragraph("<b>3. Grafische Auswertung</b>", styles['Heading2']))

    for path in plot_paths:
        if path.exists():
            img = Image(str(path))

            # Seitenverhältnis berechnen, Bildbreite auf 15 cm fixieren
            aspect_ratio: float = img.imageHeight / float(img.imageWidth)
            img.drawWidth = 15 * cm
            img.drawHeight = 15 * cm * aspect_ratio

            story.append(img)
            story.append(Spacer(1, 15))
        else:
            logger.warning(
                "Diagramm '%s' konnte nicht gefunden werden und wird übersprungen.",
                path
            )

    # 7. PDF erstellen und im Dateisystem speichern
    try:
        doc.build(story)
        logger.info("PDF erfolgreich erstellt und unter '%s' gespeichert.", output_filename)
    except Exception as e:
        logger.error("Fehler beim Erstellen der PDF-Datei '%s': %s", output_filename, e)
        raise IOError(f"Die PDF-Datei konnte nicht erstellt werden: {e}") from e


if __name__ == "__main__":
    import sys
    import numpy as np
    import matplotlib.pyplot as plt

    # Logging für den lokalen Testlauf einrichten (analog zu den anderen Modulen)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger.info("Starte lokalen Testlauf für die Report-Generierung...")

    # 1. Dummy-Ergebnisse erstellen (entspricht dem Output von EBikeSimulation.summary)
    test_ergebnisse = {
        "total_time_s": 1500.0,
        "total_distance_km": 12.5,
        "avg_velocity_kmh": 22.5,
        "max_velocity_kmh": 45.2,
        "elevation_gain_m": 350.0,
        "elevation_loss_m": 120.0,
        "max_power_w": 550.0,
        "mechanical_energy_wh": 180.5,
        "recuperated_energy_wh": 25.0,
        "dissipated_energy_wh": 5.5,
        "start_soc_percent": 100.0,
        "end_soc_percent": 78.5,
        "consumed_soc_percent": 21.5
    }

    # 2. Ein einfaches Test-Diagramm mit Matplotlib generieren, um das Einbetten zu testen
    test_plot_pfad = Path("test_diagramm_dummy.png")

    plt.figure(figsize=(8, 4))
    # Eine simple Sinuskurve, die E-Bike-Leistungsdaten simuliert
    plt.plot(
        np.linspace(0, 10, 100), np.sin(np.linspace(0, 10, 100)) * 250 + 250, label="Leistung (W)"
    )
    plt.title("Dummy-Leistungsdaten für Test-PDF")
    plt.xlabel("Zeit [s]")
    plt.ylabel("Leistung [W]")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(test_plot_pfad, dpi=150)
    plt.close()

    logger.info("Test-Diagramm unter '%s' erstellt.", test_plot_pfad)

    # 3. PDF-Generierung aufrufen
    AUSGABE_PDF = "test_bericht_ausgabe.pdf"

    try:
        generate_report_reportlab(
            ergebnisse=test_ergebnisse,
            plot_paths=[test_plot_pfad],
            output_filename=AUSGABE_PDF
        )
        logger.info("Testlauf erfolgreich beendet. Bitte die Datei '%s' überprüfen.", AUSGABE_PDF)
    except Exception as e:
        logger.error("Testlauf fehlgeschlagen: %s", e)
        raise
    finally:
        # Hinweis: Das Test-Bild bleibt auf der Festplatte,
        # damit du das Resultat nachvollziehen kannst.
        # Du kannst einkommentieren, um es automatisch löschen zu lassen:
        # if test_plot_pfad.exists():
        #     test_plot_pfad.unlink()
        pass
