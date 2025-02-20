from PyPDF2 import PdfWriter, PdfReader
import os
from reportlab.pdfgen import canvas 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter 

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
    c.setFillColor(colors.white)  # Colore del testo (bianco)


    # Impostare il colore per il titolo (Blu scuro)
    c.setFont("Helvetica", 36)
    c.setFillColor(colors.white)  # Colore del testo (bianco)
    c.drawString(200, 800, titleText)


    c.setFillColorRGB(0.1, 0.2, 0.5)# Colore di sfondo dietro il titolo
    c.rect(0, 750, 612, 400, fill=True)  # Aggiungi un rettangolo come sfondo


    # Impostazione del font e del testo
    c.setFont("Helvetica", 20)
    # Posiziona il titolo al centro della pagina
    c.drawString(letter[0]/2 - 100, letter[1] - 50, titleText)
    
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.black)  # Colore del testo (nero)
    # Posiziona il testo del paragrafo
    c.drawString(30, letter[1] - 100, paraText)


    # Aggiungi altre informazioni (DATI)
    c.setFont("Helvetica", 12)
    c.drawString(50, 650, "DATA: Software Developer presso XYZ Inc.")
    c.drawString(50, 625, "Formazione: Laurea in Informatica presso Università ABC")



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
