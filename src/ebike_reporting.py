'''
Modul zur automatisierten Erstellung eines technischen PDF-Auswertungsberichts 
für die E-Bike-Fahrsimulation.
'''

#generelle Imports
import logging
from pathlib import Path
from typing import Any

#Imports von anderen selbstgeschriebenen Dateien
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus.flowables import KeepTogether

#__name__ zeigt sofort an, in welcher Datei der Code gerade ausgeführt wird.
logger = logging.getLogger(__name__)


def generate_report_reportlab(
    ergebnisse: dict[str, Any],
    plot_paths: list[Path],
    output_filename: str = "ebike_simulation_analyse.pdf",
    map_html_path: Path = None
) -> None:
    '''
    Funktion zur automatisierten Erstellung eines technischen PDF-Auswertungsberichts.
    
    Generiert ein strukturiertes Dokument mit Tabellen, Begleittexten und Diagrammbeschreibungen.
    '''

    logger.info("Starte Generierung des PDF-Berichts...")

    #Dokumentenstruktur initialisieren (A4)
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=56, leftMargin=56,
        topMargin=56, bottomMargin=56
    )

    story: list[Any] = []
    styles = getSampleStyleSheet()

    #Text-Styles definieren
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor("#0f19d0"),
        spaceAfter=12,
        fontName="Helvetica-Bold"
    )

    heading2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#1b3045"),
        spaceBefore=15,
        spaceAfter=8,
        fontName="Helvetica-Bold"
    )

    heading3_style = ParagraphStyle(
        'Heading3Style',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor("#333333"),
        spaceBefore=10,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        textColor=colors.HexColor("#222222"),
        fontSize=10,
        leading=15,
        alignment=4
    )

    #Titel und Einleitung
    story.append(Paragraph("E-Bike Fahrsimulation: Technischer Auswertungsbericht", title_style))
    story.append(Paragraph(
        "Dieser automatisierte Bericht fasst die dynamischen, kinematischen und elektrothermischen "
        "Ergebnisse der Fahrsimulation zusammen. Die Berechnungen basieren auf vektorisierten "
        "Operationen, um eine gute Lösung der Akkupaket- und Dynamikgleichungen zu gewährleisten.",
        normal_style
    ))
    story.append(Spacer(1, 20))

    #Zusammenfassung der Kennzahlen
    story.append(Paragraph("1. Numerische Zusammenfassung der Simulation", heading2_style))
    story.append(Paragraph(
        "Die nachfolgende Tabelle zeigt die wichtigsten physikalischen Kennzahlen der " \
        "gefahrenen Strecke. Hierzu zählen kinematische Parameter, der Gesamtwirkungsgrad " \
        "sowie die thermischen und elektrischen Verluste des Akkupacks.",
        normal_style
    ))
    story.append(Spacer(1, 10))

    data: list[list[str]] = [
        ['Fahrzeit', f"{ergebnisse.get('total_time_s', 0) / 60:.1f} min"],
        ['Zurückgelegte Strecke', f"{ergebnisse.get('total_distance_km', 0):.2f} km"],
        ['Ø Geschwindigkeit / Max.', f"{ergebnisse.get('avg_velocity_kmh', 0):.1f} km/h  |  "
         f"{ergebnisse.get('max_velocity_kmh', 0):.1f} km/h"],
        ['Höhenmeter (Auf / Ab)', f"+{ergebnisse.get('elevation_gain_m', 0):.0f} hm  |  "
         f"-{ergebnisse.get('elevation_loss_m', 0):.0f} hm"],
        ['Erbrachte mech. Energie', f"{ergebnisse.get('mechanical_energy_wh', 0):.1f} Wh"],
        ['Rekuperierte Energie', f"{ergebnisse.get('recuperated_energy_wh', 0):.1f} Wh"],
        ['Dissipierte Verlustenergie', f"{ergebnisse.get('dissipated_energy_wh', 0):.1f} Wh"],
        ['Ladezustand SoC (Start -> Ende)', f"{ergebnisse.get('start_soc_percent', 0):.1f}% -> "
         f"{ergebnisse.get('end_soc_percent', 0):.1f}%"],
    ]

    t = Table(data, colWidths=[220, 230])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#555555")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), # Erste Spalte fett
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1b3045")),
    ]))
    story.append(t)
    story.append(Spacer(1, 25))

    #Streckenkarte Maps
    story.append(Paragraph("2. Streckenverlauf", heading2_style))

    # Prüfe ob ein Bild der Karte existiert (z.B. route_map.png).
    # Wenn nicht, setze einen Link auf die HTML-Datei, falls vorhanden.
    map_img_path = Path("results/route_map.png")
    map_html_default = Path("results/route_map.html")

    if map_img_path.exists():
        img = Image(str(map_img_path))
        img.drawWidth = 15 * cm
        img.drawHeight = 15 * cm * (img.imageHeight / float(img.imageWidth))
        story.append(img)
    elif (map_html_path and map_html_path.exists()) or map_html_default.exists():
        html_target = map_html_path if map_html_path else map_html_default
        link = f'<link href="file://{html_target.resolve()}" color="blue">Klicken Sie hier, um die interaktive Streckenkarte (HTML) im Browser zu öffnen.</link>'
        story.append(Paragraph(
            f"Die GPS-Koordinaten wurden über Folium kartografiert. "
            f"Da interaktive Karten nicht direkt in PDFs gerendert werden können, "
            f"liegt diese extern vor: {link}",
            normal_style
        ))
    else:
        story.append(Paragraph("Für diesen Lauf wurde keine Streckenkarte erzeugt.", normal_style))

    story.append(Spacer(1, 20))
    story.append(PageBreak())

    #Grafische Auswertung
    story.append(Paragraph("3. Detaillierte grafische Auswertung", heading2_style))
    story.append(Paragraph(
        "Die folgenden Matplotlib-Plots visualisieren die systemischen Abhängigkeiten zwischen Streckenprofil, "
        "Fahrwiderständen und der Batteriedynamik.",
        normal_style
    ))
    story.append(Spacer(1, 15))

    # Wörterbuch zur automatischen Zuweisung von Titeln und Texten basierend auf dem Dateinamen
    diagramm_metadaten = {
        "hoehenprofil_farbig_plot": {
            "titel": "Topografisches Höhenprofil & Steigungsgrad",
            "text": "Das Höhenprofil zeigt den Streckenverlauf. Die Einfärbung der Linie verdeutlicht die lokale Steigung, welche direkt in die Berechnung der Hangabtriebskraft einfließt."
        },
        "simulations_plot": {
            "titel": "Kinematik, Leistung und Ladezustand (SoC)",
            "text": "Dieser Plot stellt die Momentangeschwindigkeit und die resultierende mechanische Systemleistung dar. Im untersten Graphen ist der synchrone Abfall des Batterie-Ladezustands (SoC) über die Zeit abgebildet."
        },
        "thermische_elektrische_last": {
            "titel": "Thermische und elektrische Batteriebelastung",
            "text": "Die Temperatur des Akkupacks wird dynamisch berechnet. Die Verlustleistung erwärmt die Zellen, während Fahrtwind kühlend wirkt. Stromspitzen (Entladen/Rekuperieren) sind dem Temperaturverlauf gegenübergestellt."
        },
        "fahrwiderstaende": {
            "titel": "Fahrwiderstände im Zeitverlauf",
            "text": "Aufschlüsselung der einwirkenden Kräfte: Der Luftwiderstand wächst quadratisch zur Geschwindigkeit, während Rollwiderstand und Hangabtriebskraft stark von Streckenbeschaffenheit und Topografie abhängen."
        },
        "steigung_vs_geschwindigkeit": {
            "titel": "Korrelation: Steigung vs. Geschwindigkeit",
            "text": "Dieses Scatter-Plot veranschaulicht das Fahrverhalten: In starken Steigungen sinkt die Geschwindigkeit ab, bei Gefälle (negative Steigung) werden höhere Geschwindigkeiten erreicht."
        },
        "motor_arbeitspunkte": {
            "titel": "Arbeitspunkte des Elektromotors",
            "text": "Darstellung der mechanischen Anforderung an den Motor. Gezeigt wird das angeforderte Drehmoment aufgetragen über die Motordrehzahl (RPM)."
        },
        "energiebilanz": {
            "titel": "Gesamte Energiebilanz",
            "text": "Gegenüberstellung der insgesamt erbrachten mechanischen Antriebsenergie, der durch Rekuperation zurückgewonnenen Energie und der im Akku durch Innenwiderstand generierten thermischen Verluste."
        }
    }

    #Diagramme iterieren, Text zuordnen und einfügen
    for path in plot_paths:
        if path.exists():
            stem = path.stem
            meta = diagramm_metadaten.get(stem, {
                "titel": f"Diagramm: {path.name}",
                "text": "Ergänzende grafische Auswertung der Simulationsdaten."
            })

            # KeepTogether sorgt dafür, dass Titel, Text und Bild nicht durch einen Seitenumbruch getrennt werden
            block = []
            block.append(Paragraph(meta["titel"], heading3_style))
            block.append(Paragraph(meta["text"], normal_style))
            block.append(Spacer(1, 10))

            img = Image(str(path))
            aspect_ratio: float = img.imageHeight / float(img.imageWidth)
            img.drawWidth = 14.5 * cm
            img.drawHeight = 14.5 * cm * aspect_ratio
            block.append(img)
            block.append(Spacer(1, 20))

            story.append(KeepTogether(block))
        else:
            logger.warning("Diagramm '%s' konnte nicht gefunden werden und wird übersprungen.", path)

    #PDF generieren
    try:
        doc.build(story)
        logger.info("PDF erfolgreich erstellt und unter '%s' gespeichert.", output_filename)
    except Exception as e:
        logger.error("Fehler beim Erstellen der PDF-Datei '%s': %s", output_filename, e)
        raise IOError(f"Die PDF-Datei konnte nicht erstellt werden: {e}") from e

if __name__ == "__main__":
    # Test-Logik
    import sys
    import numpy as np
    import matplotlib.pyplot as plt

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    logger.info("Starte lokalen Testlauf für die Report-Generierung...")

    test_ergebnisse = {
        "total_time_s": 1500.0, "total_distance_km": 12.5, "avg_velocity_kmh": 22.5,
        "max_velocity_kmh": 45.2, "elevation_gain_m": 350.0, "elevation_loss_m": 120.0,
        "mechanical_energy_wh": 180.5, "recuperated_energy_wh": 25.0,
        "dissipated_energy_wh": 5.5, "start_soc_percent": 100.0, "end_soc_percent": 78.5,
    }

    test_plot_pfad = Path("simulations_plot.png")
    plt.figure(figsize=(8, 4))
    plt.plot(np.linspace(0, 10, 100), np.sin(np.linspace(0, 10, 100)) * 250 + 250)
    plt.title("Dummy-Daten")
    plt.savefig(test_plot_pfad, dpi=150)
    plt.close()

    try:
        generate_report_reportlab(
            ergebnisse=test_ergebnisse,
            plot_paths=[test_plot_pfad],
            output_filename="test_bericht_ausgabe.pdf"
        )
        logger.info("Testlauf erfolgreich. Bitte PDF überprüfen.")
    finally:
        if test_plot_pfad.exists():
            test_plot_pfad.unlink()
