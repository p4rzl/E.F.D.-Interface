from PyPDF2 import PdfWriter, PdfReader
import os
from reportlab.pdfgen import canvas 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import *
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Rect

# Nome della cartella che contiene i dati
data_folder = os.path.join(os.getcwd(), "data")  # Percorso assoluto

# Funzione per leggere i dati dalla cartella e dalle sottocartelle
def read_data_from_folder(data_folder):
    data = {}
    try:
        # Verifica se la directory esiste
        if not os.path.exists(data_folder):
            print(f"La directory {data_folder} non esiste!")
            return data
            
        for subfolder in os.listdir(data_folder):
            subfolder_path = os.path.join(data_folder, subfolder)
            if os.path.isdir(subfolder_path):
                data[subfolder] = []
                print(f"Processando la cartella: {subfolder_path}")  # Debug
                for filename in os.listdir(subfolder_path):
                    if filename.endswith(".txt"):
                        file_path = os.path.join(subfolder_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                lines = file.readlines()
                                # Rimuovi spazi bianchi e linee vuote
                                cleaned_lines = [line.strip() for line in lines if line.strip()]
                                data[subfolder].extend(cleaned_lines)
                                print(f"Letti {len(cleaned_lines)} dati da {file_path}")
                        except Exception as e:
                            print(f"Errore nella lettura del file {file_path}: {str(e)}")
    except Exception as e:
        print(f"Errore nell'accesso alla directory {data_folder}: {str(e)}")
    
    return data

# Carica i dati dalla cartella 'data' e dalle sue sottocartelle
data = read_data_from_folder(data_folder)

# Dopo aver letto i dati
print("Dati letti:", data)  # Per verificare che i dati vengano effettivamente letti

# Nome del file PDF e directory
pdf_dir = os.path.join(os.getcwd(), "pdf")
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)

file_path = os.path.join(pdf_dir, "esempio.pdf")
temp_pdf_path = os.path.join(pdf_dir, "temp_page.pdf")
output_path = os.path.join(pdf_dir, "output.pdf")

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
    c.drawString(50, rect_y - 125, "Formazione: Laurea in Informatica presso Universita' ABC")  # abbassato

    # Salvataggio del file
    c.save()
    print(f"File '{file_path}' creato con successo.")

# Ora possiamo caricare e modificare il file PDF esistente
reader = PdfReader(file_path)
writer = PdfWriter()

# Crea un PDF temporaneo con i nuovi dati
c = canvas.Canvas(temp_pdf_path, pagesize=letter)

# Inizia da una posizione più alta nella pagina
y_position = 300

# Aggiungi il titolo della sezione dati
c.setFont("Helvetica-Bold", 16)
c.drawString(50, y_position, "Dati Aggiornati:")
y_position -= 40

# Aggiungi i dati letti dalla cartella 'data' e dalle sue sottocartelle
c.setFont("Helvetica-Bold", 14)
for category, category_data in data.items():
    if category_data:  # Verifica se ci sono dati nella categoria
        # Titolo della categoria
        c.drawString(50, y_position, f"{category.upper()}")
        y_position -= 25
        
        # Contenuto della categoria
        c.setFont("Helvetica", 12)
        for line in category_data:
            # Controlla se c'è abbastanza spazio nella pagina
            if y_position < 50:
                c.showPage()  # Crea una nuova pagina
                y_position = 300
            
            # Aggiungi il contenuto con un bullet point
            c.drawString(70, y_position, f"• {line}")
            y_position -= 20
        
        # Spazio tra categorie
        y_position -= 30
        c.setFont("Helvetica-Bold", 14)

# Salva il PDF temporaneo
c.save()

# Leggi la prima pagina del PDF esistente
page = reader.pages[0]

# Leggi la pagina temporanea con i nuovi dati
temp_reader = PdfReader(temp_pdf_path)
temp_page = temp_reader.pages[0]

# Unisci le pagine (sovrapponi i nuovi dati sulla pagina esistente)
page.merge_page(temp_page)

# Aggiungi la pagina modificata al nuovo PDF
writer.add_page(page)

# Salva il PDF modificato
with open(output_path, "wb") as output_pdf:
    writer.write(output_pdf)

# Rimuovi il file temporaneo
if os.path.exists(temp_pdf_path):
    os.remove(temp_pdf_path)

print(f"PDF aggiornato e salvato come '{output_path}'")
