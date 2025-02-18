import os
from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter

# Nome del file PDF
file_path = "esempio.pdf"

# Se il file non esiste, crearlo
if not os.path.exists(file_path):
    print(f"Il file '{file_path}' non esiste. Creazione in corso...")

    # Creazione di un nuovo documento PDF
    pdf = FPDF()

    # Aggiunta di una nuova pagina
    pdf.add_page()

    # Aggiunta di testo alla pagina
    titleText = "Luca Cassano"
    paraText = "Luca Albanese"

    # Creazione del font e colore
    pdf.set_font("Helvetica", size=20)
    pdf.set_text_color(0, 0, 0)  # Colore nero

    # Disegna il testo sulla pagina
    pdf.cell(200, 10, txt=titleText, ln=True, align='C')
    pdf.set_font("Helvetica", size=14)
    pdf.cell(200, 10, txt=paraText, ln=True, align='C')

    # Salvataggio del file
    pdf.output(file_path)
    print(f"File '{file_path}' creato con successo.")

# Ora possiamo caricare e modificare il file PDF esistente
reader = PdfReader(file_path)
writer = PdfWriter()

# Copia tutte le pagine esistenti nel nuovo writer
for page in reader.pages:
    writer.add_page(page)

# Aggiunta di una nuova pagina vuota
writer.add_blank_page()

# Salvataggio del file modificato
with open("output.pdf", "wb") as output_pdf:
    writer.write(output_pdf)

print("PDF aggiornato e salvato come 'output.pdf'")
