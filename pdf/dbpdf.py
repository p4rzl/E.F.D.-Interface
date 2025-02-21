from flask import Flask, request, render_template, send_file
from netCDF4 import Dataset
from PyPDF2 import PdfWriter, PdfReader
import os
from reportlab.pdfgen import canvas 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "pdf"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nessun file caricato"
        file = request.files['file']
        if file.filename == '':
            return "Nessun file selezionato"
        
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        pdf_path = process_nc_file(filepath)
        return send_file(pdf_path, as_attachment=True)
    
    return render_template('upload.html')

def process_nc_file(nc_file):
    pdf_output = os.path.join(OUTPUT_FOLDER, "output.pdf")
    temp_pdf_path = os.path.join(OUTPUT_FOLDER, "temp_page.pdf")
    pdf_input = "pdf/esempio.pdf"
    
    with Dataset(nc_file, "r") as nc:
        lat = nc.variables["latitude"][:]
        lon = nc.variables["longitude"][:]
        temp = nc.variables["temperature"][:]

    c = canvas.Canvas(temp_pdf_path, pagesize=letter)
    page_width, page_height = letter
    rect_height = page_height * 0.30
    rect_y = page_height - rect_height + 20
    
    d = Drawing(page_width, page_height)
    num_steps = 50
    for i in range(num_steps):
        segment_height = rect_height / num_steps
        segment_y = rect_y + (i * segment_height)
        intensity = 0.5 - (i / (num_steps * 2))
        r = Drawing()
        r.add(Rect(0, segment_y, page_width, segment_height, fillColor=colors.Color(0.1, 0.2, 0.5 + intensity), strokeColor=None))
        d.add(r)
    renderPDF.draw(d, c, 0, 0)
    
    titleText = "Ocean currents data"
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 36)
    title_x = (page_width - c.stringWidth(titleText, "Helvetica", 36)) / 2
    title_y = rect_y + (rect_height/2) - 10
    c.drawString(title_x, title_y, titleText)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    c.drawString(30, rect_y - 70, "Dati estratti dal file NetCDF")

    c.setFont("Helvetica", 12)
    for i in range(min(5, len(lat))):
        text = f"Punto {i+1}: {lat[i]:.2f}°N, {lon[i]:.2f}°E, Temp: {temp[i]:.1f}°C"
        c.drawString(50, rect_y - 100 - (i * 20), text)
    
    c.save()

    reader = PdfReader(pdf_input)
    writer = PdfWriter()
    temp_reader = PdfReader(temp_pdf_path)
    
    page = reader.pages[0]
    temp_page = temp_reader.pages[0]
    page.merge_page(temp_page)
    writer.add_page(page)
    
    with open(pdf_output, "wb") as output_pdf:
        writer.write(output_pdf)
    
    os.remove(temp_pdf_path)
    return pdf_output

if __name__ == '__main__':
    app.run(debug=True)
