"""
Modulo dedicato alla generazione di PDF con diverse strategie di fallback
Supporta multiple librerie: xhtml2pdf, WeasyPrint, e ReportLab come ultima risorsa
"""

import os
import logging
import traceback
from datetime import datetime
import jinja2
import base64
from io import BytesIO
from flask import current_app
from translations import get_translations
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pdf_generator')

# Verifica quali librerie PDF sono disponibili
PDF_LIBS = []
try:
    from xhtml2pdf import pisa
    PDF_LIBS.append('xhtml2pdf')
    logger.info("xhtml2pdf disponibile")
except ImportError:
    logger.warning("xhtml2pdf non disponibile")

try:
    from weasyprint import HTML
    PDF_LIBS.append('weasyprint')
    logger.info("WeasyPrint disponibile")
except ImportError:
    logger.warning("WeasyPrint non disponibile")

try:
    import reportlab
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    PDF_LIBS.append('reportlab')
    logger.info("ReportLab disponibile")
except ImportError:
    logger.warning("ReportLab non disponibile")

if not PDF_LIBS:
    logger.error("ATTENZIONE: Nessuna libreria PDF disponibile!")

def generate_pdf_report(report_type, beach_data, username, language='it'):
    """
    Genera un report PDF utilizzando varie strategie
    
    Args:
        report_type: 'risk' o 'hazard'
        beach_data: dizionario con i dati della spiaggia
        username: nome utente
        language: codice lingua per le traduzioni
    
    Returns:
        str: percorso relativo al file PDF generato
    """
    # Prepara un nome file univoco
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_report_{timestamp}.pdf"
    
    # Assicurati che la directory esista
    output_dir = os.path.join(current_app.static_folder, 'reports')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    # Sanitizza i dati della spiaggia
    clean_beach_data = sanitize_data(beach_data)
    
    # Ottieni traduzioni
    translations = get_translations(language)
    
    # Dati per il contesto del template
    context_data = {
        'beach': clean_beach_data,
        'username': username,
        'date': datetime.now().strftime('%d/%m/%Y'),
        'time': datetime.now().strftime('%H:%M'),
        't': translations
    }
    
    # Tenta diverse strategie in ordine
    for strategy in ['xhtml2pdf', 'simplified-xhtml2pdf', 'weasyprint', 'reportlab']:
        if strategy.startswith('xhtml2pdf') and 'xhtml2pdf' in PDF_LIBS:
            template_name = 'simple_' + report_type + '_report.html' if 'simplified' in strategy else report_type + '_report_template.html'
            template_path = os.path.join(current_app.root_path, 'templates', 'pdf_templates', template_name)
            
            if not os.path.exists(template_path):
                logger.warning(f"Template {template_path} non trovato, salto")
                continue
                
            success = generate_with_xhtml2pdf(template_path, output_path, context_data)
            if success:
                logger.info(f"PDF generato con successo usando {strategy}")
                break
                
        elif strategy == 'weasyprint' and 'weasyprint' in PDF_LIBS:
            template_name = report_type + '_report_template.html'
            template_path = os.path.join(current_app.root_path, 'templates', 'pdf_templates', template_name)
            
            if not os.path.exists(template_path):
                logger.warning(f"Template {template_path} non trovato, salto")
                continue
                
            success = generate_with_weasyprint(template_path, output_path, context_data)
            if success:
                logger.info("PDF generato con successo usando WeasyPrint")
                break
                
        elif strategy == 'reportlab' and 'reportlab' in PDF_LIBS:
            success = generate_with_reportlab(report_type, output_path, clean_beach_data, username, translations)
            if success:
                logger.info("PDF generato con successo usando ReportLab")
                break
    else:
        error_msg = "Tutte le strategie di generazione PDF hanno fallito"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Restituisci il percorso relativo
    return os.path.join('static', 'reports', filename)

def sanitize_data(beach_data):
    """Sanitizza i dati della spiaggia eliminando valori problematici"""
    if hasattr(beach_data, 'to_dict'):
        beach_data = beach_data.to_dict()
    
    # Copia i dati per non modificare l'originale
    cleaned = {}
    
    # Controlla e pulisci ogni campo
    for key, value in beach_data.items():
        if isinstance(value, (int, float)):
            if pd.isna(value):  # controlla NaN
                cleaned[key] = None
            else:
                cleaned[key] = value
        else:
            # Converti in stringa se non è None
            cleaned[key] = str(value) if value is not None else None
    
    return cleaned

def generate_with_xhtml2pdf(template_path, output_path, context_data):
    """Genera PDF usando xhtml2pdf"""
    try:
        # Carica e compila il template
        with open(template_path, 'r', encoding='utf-8') as file:
            template_string = file.read()
        
        # Configura Jinja2 con filtri sicuri
        env = jinja2.Environment(autoescape=True)
        
        # Aggiungi filtri sicuri per evitare errori
        env.filters['default'] = lambda value, default: default if value is None else value
        
        def safe_int(value):
            if value is None:
                return 0
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        
        def safe_format(format_string, value):
            if value is None:
                return 'N/A'
            try:
                return format_string % float(value)
            except (ValueError, TypeError):
                return 'N/A'
        
        # Registra i filtri
        env.filters['int'] = safe_int
        env.filters['format'] = safe_format
        
        # Compila il template
        template = env.from_string(template_string)
        html = template.render(**context_data)
        
        # Salva HTML per debug
        debug_path = output_path.replace('.pdf', '.debug.html')
        with open(debug_path, 'w', encoding='utf-8') as file:
            file.write(html)
        
        # Genera PDF
        with open(output_path, 'wb') as file:
            pdf = pisa.pisaDocument(
                BytesIO(html.encode('UTF-8')), 
                file,
                encoding='UTF-8',
                debug=0,
                path=os.path.dirname(template_path)
            )
        
        success = not pdf.err
        
        if not success:
            logger.error(f"xhtml2pdf error: {pdf.err}")
            for msg in getattr(pdf, 'log', []):
                if isinstance(msg, tuple) and len(msg) >= 2 and msg[0] == 'error':
                    logger.error(f"PDF Error: {msg[1]}")
        
        return success
    except Exception as e:
        logger.error(f"Errore in generate_with_xhtml2pdf: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def generate_with_weasyprint(template_path, output_path, context_data):
    """Genera PDF usando WeasyPrint"""
    try:
        # Carica e compila il template
        with open(template_path, 'r', encoding='utf-8') as file:
            template_string = file.read()
        
        env = jinja2.Environment(autoescape=True)
        template = env.from_string(template_string)
        html = template.render(**context_data)
        
        # Salva HTML per debug
        debug_path = output_path.replace('.pdf', '.weasy.html')
        with open(debug_path, 'w', encoding='utf-8') as file:
            file.write(html)
        
        # Genera PDF con WeasyPrint
        HTML(string=html).write_pdf(output_path)
        
        return os.path.exists(output_path)
    except Exception as e:
        logger.error(f"Errore in generate_with_weasyprint: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def generate_with_reportlab(report_type, output_path, beach_data, username, translations):
    """Genera un PDF molto semplice usando ReportLab (ultima risorsa)"""
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Titolo
        title = translations[f"{report_type}_report_title"]
        story.append(Paragraph(f"<h1>{title} - {beach_data.get('name', 'N/A')}</h1>", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Metadata
        story.append(Paragraph(f"<b>{translations['generated_by']}:</b> {username}", styles['Normal']))
        story.append(Paragraph(f"<b>{translations['date']}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Overview
        story.append(Paragraph(f"<h2>{translations['overview']}</h2>", styles['Heading2']))
        
        # Tabella dati principali
        data = [
            [translations['length'], f"{beach_data.get('length', 'N/A')} {translations['meters']}"],
            [translations['width'], f"{beach_data.get('width', 'N/A')} {translations['meters']}"],
            [translations['risk_index'], f"{beach_data.get('risk_index', 'N/A')}"],
            [translations['erosion_rate'], f"{beach_data.get('erosion_rate', 'N/A')} {translations['meters_per_year']}"]
        ]
        
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), '#f2f2f2'),
            ('TEXTCOLOR', (0, 0), (0, -1), '#333333'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, '#cccccc')
        ]))
        
        story.append(t)
        story.append(Spacer(1, 20))
        
        # Risk or Hazard details
        if report_type == 'risk':
            story.append(Paragraph(f"<h2>{translations['risk_details']}</h2>", styles['Heading2']))
            
            risk_data = [
                [translations['economic_risk'], calculate_risk(beach_data, 0.8)],
                [translations['social_risk'], calculate_risk(beach_data, 0.6)],
                [translations['environmental_risk'], calculate_risk(beach_data, 0.7)]
            ]
            
            risk_table = Table(risk_data)
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), '#f2f2f2'),
                ('TEXTCOLOR', (0, 0), (0, -1), '#333333'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, '#cccccc')
            ]))
            
            story.append(risk_table)
        else:  # hazard
            story.append(Paragraph(f"<h2>{translations['hazard_details']}</h2>", styles['Heading2']))
            
            hazard_data = [
                [translations['erosion_hazard'], beach_data.get('erosion_rate', 'N/A')],
                [translations['flooding_hazard'], calculate_risk(beach_data, 0.7)],
                [translations['storm_hazard'], calculate_risk(beach_data, 0.6)]
            ]
            
            hazard_table = Table(hazard_data)
            hazard_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), '#f2f2f2'),
                ('TEXTCOLOR', (0, 0), (0, -1), '#333333'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, '#cccccc')
            ]))
            
            story.append(hazard_table)
        
        # Recommendations
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<h2>{translations['recommendations']}</h2>", styles['Heading2']))
        
        if report_type == 'risk':
            story.append(Paragraph("• Implementare barriere artificiali per ridurre l'erosione costiera", styles['Normal']))
            story.append(Paragraph("• Ripristinare la vegetazione dunale per stabilizzare la costa", styles['Normal']))
            story.append(Paragraph("• Monitorare regolarmente le variazioni della linea di costa", styles['Normal']))
            story.append(Paragraph("• Informare la popolazione locale sui rischi e le misure di adattamento", styles['Normal']))
        else:
            story.append(Paragraph("• Implementare sistemi di monitoraggio delle condizioni meteorologiche estreme", styles['Normal']))
            story.append(Paragraph("• Sviluppare piani di evacuazione per eventi di inondazione", styles['Normal']))
            story.append(Paragraph("• Costruire difese costiere adeguate alle condizioni di pericolo", styles['Normal']))
            story.append(Paragraph("• Stabilire aree di buffer per proteggere le infrastrutture critiche", styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"{translations['coastal_monitoring_system']} © {datetime.now().year}"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Genera il PDF
        doc.build(story)
        return True
    except Exception as e:
        logger.error(f"Errore in generate_with_reportlab: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def calculate_risk(beach_data, factor=1.0):
    """Calcola un valore di rischio"""
    risk = beach_data.get('risk_index')
    if risk is None:
        return 'N/A'
        
    try:
        return f"{float(risk) * factor:.2f}"
    except (ValueError, TypeError):
        return 'N/A'
