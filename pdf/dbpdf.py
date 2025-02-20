from PyPDF2 import PdfWriter, PdfReader
import os
from reportlab.pdfgen import canvas 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import *
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Rect

# Nome del file PDF
file_path = "pdf/esempio.pdf"

# Se il file non esiste, crearlo
if not os.path.exists(file_path):
    print(f"Il file '{file_path}' non esiste. Creazione in corso...")

    # Creazione di un file PDF temporaneo con ReportLab
    c = canvas.Canvas(file_path, pagesize=letter)

    # Aggiunta di testo alla pagina
    titleText = "Ocean currents data"
    paraText = "Luca Albanese - itis"

    # Calcola le dimensioni del rettangolo 
    page_width = letter[0]    # larghezza pagina
    page_height = letter[1]   # altezza pagina
    rect_height = page_height * 0.30  # aumentato al 30% dell'altezza
    rect_y = page_height - rect_height + 20  # aggiustato per coprire tutto in alto

    # Creazione del gradiente
    d = Drawing(page_width, page_height)
    
    # Creiamo diversi rettangoli con opacità decrescente per simulare il gradiente
    num_steps = 50
    for i in range(num_steps):
        # Calcola l'altezza di ogni segmento
        segment_height = rect_height / num_steps
        # Calcola la posizione y di ogni segmento
        segment_y = rect_y + (i * segment_height)
        # Calcola il colore con intensità decrescente
        intensity = 0.5 - (i / (num_steps * 2))  # da 0.5 a 0
        r = Drawing()
        r.add(Rect(
            0,                          # x
            segment_y,                  # y
            page_width,                 # width
            segment_height,             # height
            fillColor=colors.Color(0.1, 0.2, 0.5 + intensity),  # colore blu con intensità variabile
            strokeColor=None
        ))
        d.add(r)
    
    # Renderizza il gradiente
    renderPDF.draw(d, c, 0, 0)

    # Calcolo della posizione centrale per il titolo
    title_font_size = 36
    c.setFont("Helvetica", title_font_size)
    title_width = c.stringWidth(titleText, "Helvetica", title_font_size)
    title_x = (page_width - title_width) / 2  # centro orizzontale
    title_y = rect_y + (rect_height/2) - 10   # centro verticale nel rettangolo

    # Disegna il testo del titolo in bianco
    c.setFillColor(colors.white)
    c.drawString(title_x, title_y, titleText)

    # Resto del testo in nero
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    c.drawString(30, rect_y - 70, paraText)  # aumentato lo spazio sotto il rettangolo

    # Aggiungi altre informazioni (DATI)
    c.setFont("Helvetica", 12)
    c.drawString(50, rect_y - 100, "DATA: Software Developer presso XYZ Inc.")  # abbassato
    c.drawString(50, rect_y - 125, "Formazione: Laurea in Informatica presso Università ABC")  # abbassato

    # Salvataggio del file
    c.save()
    print(f"File '{file_path}' creato con successo.")




# Ora possiamo caricare e modificare il file PDF esistente
reader = PdfReader(file_path)
writer = PdfWriter()

# Aggiungi tutte le pagine del PDF esistente al nuovo file PDF
for page_num in range(len(reader.pages)):
    page = reader.pages[page_num]
    writer.add_page(page)

# Aggiungi una nuova pagina al file PDF
writer.add_blank_page()

# Salvataggio del file modificato
output_path = "pdf/output.pdf"
with open(output_path, "wb") as output_pdf:
    writer.write(output_pdf)

print(f"PDF aggiornato e salvato come '{output_path}'")
