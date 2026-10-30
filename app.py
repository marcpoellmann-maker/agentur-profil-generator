import streamlit as st
import json
import pdfplumber
import io
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Seite konfigurieren
st.set_page_config(page_title="Profil Generator", page_icon="📄", layout="centered")

st.title("📄 Agentur Profil-Generator")
st.write("Lade das PDF der Partner-Agentur hoch. Die KI extrahiert die Daten und gießt sie automatisch in euer eigenes Corporate Design.")

# OpenAI API Key in der Seitenleiste eingeben (oder hart im Code/Umgebungsvariable hinterlegen)
with st.sidebar:
    st.header("Einstellungen")
    api_key = st.text_input("OpenAI API-Key", type="password", help="Trage hier deinen OpenAI API Key ein")

def lade_fremdes_pdf(pdf_file):
    """Liest den Text aus der hochgeladenen PDF-Datei aus."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extrahiere_profildaten(rohtext, client):
    """Nutzt GPT-4o-mini, um die Profildaten als strukturierte JSON auszulesen."""
    prompt = f"""
    Analysiere das Profil dieser Betreuungskraft und extrahiere die Daten als sauberes JSON mit folgenden Schlüsseln:
    - vorname (String)
    - nachname (String)
    - titel_untertitel (String, z.B. "ERFAHRENE BETREUUNGSKRAFT MIT GUTEN DEUTSCHKENNTNISSEN")
    - zitat (String, das persönliche Zitat)
    - geburtsdatum (String)
    - nationalitaet (String)
    - groesse (String)
    - gewicht (String)
    - geschlecht (String)
    - raucherin (String)
    - fuehrerschein (String)
    - sprachkenntnisse (String)
    - berufserfahrung_titel (String)
    - berufserfahrung_text (String)
    - einsatzbereiche (Liste von Strings)
    - verfuegbarkeit (Liste von Strings)
    - unterbringung (Liste von Strings)
    - staerken (Liste von Strings)

    Rohtext der Partneragentur:
    {rohtext}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def erstelle_agentur_pdf(json_daten_str):
    """Erstellt ein sauberes Agentur-PDF im Speicher (BytesIO)."""
    daten = json.loads(json_daten_str)
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    story = []
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#1b4332")  # Dunkelgrün
    accent_color = colors.HexColor("#f4f1ea")   # Beige/Sand
    text_color = colors.HexColor("#2b2b2b")     # Dunkelgrau
    
    name_style = ParagraphStyle('NameStyle', parent=styles['Heading1'], fontSize=22, leading=26, textColor=primary_color, fontName='Helvetica-Bold')
    titel_style = ParagraphStyle('TitelStyle', parent=styles['Normal'], fontSize=10, leading=13, textColor=primary_color, fontName='Helvetica-Bold', spaceAfter=8)
    zitat_style = ParagraphStyle('ZitatStyle', parent=styles['Normal'], fontSize=9, leading=13, textColor=text_color, fontName='Helvetica-Oblique')
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=11, leading=15, textColor=primary_color, fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=text_color, fontName='Helvetica')

    # Kopfbereich
    header_left = [
        Paragraph(f"<b>{daten.get('vorname', '')}</b><br/>{daten.get('nachname', '')}", name_style),
        Spacer(1, 4),
        Paragraph(daten.get('titel_untertitel', ''), titel_style)
    ]
    zitat_text = f"„{daten.get('zitat', '')}“" if daten.get('zitat') else ""
    header_right = [Paragraph(zitat_text, zitat_style)]
    
    header_table = Table([[header_left, header_right]], colWidths=[240, 295])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (1, 0), accent_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (1, 0), (1, 0), 8),
        ('TOPPADDING', (1, 0), (1, 0), 8),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Linke Spalte
    left_content = []
    left_content.append(Paragraph("PERSÖNLICHE DATEN", section_heading))
    pers_daten = [
        ("Geburtsdatum:", daten.get('geburtsdatum')),
        ("Nationalität:", daten.get('nationalitaet')),
        ("Größe:", daten.get('groesse')),
        ("Gewicht:", daten.get('gewicht')),
        ("Geschlecht:", daten.get('geschlecht')),
        ("Raucherin:", daten.get('raucherin')),
        ("Führerschein:", daten.get('fuehrerschein')),
        ("Sprachen:", daten.get('sprachkenntnisse'))
    ]
    for label, val in pers_daten:
        if val:
            left_content.append(Paragraph(f"<b>{label}</b> {val}", body_style))
            left_content.append(Spacer(1, 2))
            
    left_content.append(Spacer(1, 8))
    left_content.append(Paragraph("PERSÖNLICHKEIT & STÄRKEN", section_heading))
    for staerke in daten.get('staerken', []):
        left_content.append(Paragraph(f"• {staerke}", body_style))
        left_content.append(Spacer(1, 2))

    # Rechte Spalte
    right_content = []
    right_content.append(Paragraph("BERUFSERFAHRUNG", section_heading))
    right_content.append(Paragraph(daten.get('berufserfahrung_text', ''), body_style))
    right_content.append(Spacer(1, 8))
    
    right_content.append(Paragraph("EINSATZBEREICH", section_heading))
    for einwand in daten.get('einsatzbereiche', []):
        right_content.append(Paragraph(f"✓ {einwand}", body_style))
        right_content.append(Spacer(1, 2))
        
    right_content.append(Spacer(1, 8))
    right_content.append(Paragraph("VERFÜGBARKEIT", section_heading))
    for verf in daten.get('verfuegbarkeit', []):
        right_content.append(Paragraph(f"📅 {verf}", body_style))
        right_content.append(Spacer(1, 2))
        
    right_content.append(Spacer(1, 8))
    right_content.append(Paragraph("UNTERBRINGUNG", section_heading))
    for unt in daten.get('unterbringung', []):
        right_content.append(Paragraph(f"🏠 {unt}", body_style))
        right_content.append(Spacer(1, 2))

    main_table = Table([[left_content, right_content]], colWidths=[240, 295])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
    ]))
    
    story.append(main_table)
    doc.build(story)
    
    buffer.seek(0)
    return buffer

# File Uploader UI
uploaded_file = st.file_uploader("Fremdes Partner-PDF hier ablegen", type=["pdf"])

if uploaded_file is not None:
    if not api_key:
        st.error("Bitte gib zuerst links in der Seitenleiste deinen OpenAI API-Key ein!")
    else:
        if st.button("Profil jetzt konvertieren", type="primary"):
            try:
                with st.spinner("Lese PDF aus und analysiere Daten mit KI..."):
                    client = OpenAI(api_key=api_key)
                    rohtext = lade_fremdes_pdf(uploaded_file)
                    json_daten = extrahiere_profildaten(rohtext, client)
                    pdf_out = erstelle_agentur_pdf(json_daten)
                    
                    st.success("Profil erfolgreich im eigenen Design generiert!")
                    
                    # Download Button
                    st.download_button(
                        label="📥 Fertiges PDF herunterladen",
                        data=pdf_out,
                        file_name=f"Profil_Agentur_{uploaded_file.name}",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Fehler bei der Verarbeitung: {str(e)}")