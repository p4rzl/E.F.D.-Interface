from PyPDF2 import PdfWriter, PdfReader
import os
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
import geopandas as gpd


# Definizione percorsi
pdf_dir = os.path.join(os.getcwd(), "pdf")
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)


file_path = os.path.join(pdf_dir, "esempio.pdf")
output_path = os.path.join(pdf_dir, "output.pdf")


def create_initial_pdf():
    """Create initial PDF with header and gradient"""
    c = canvas.Canvas(file_path, pagesize=letter)
   
    # Page dimensions
    page_width, page_height = letter
    rect_height = page_height * 0.30
    rect_y = page_height - rect_height + 20


    # Create gradient
    d = Drawing(page_width, page_height)
    create_gradient(d, page_width, rect_height, rect_y)
    renderPDF.draw(d, c, 0, 0)


    # Add title
    add_title(c, "Ocean currents data", page_width, rect_y, rect_height)
   
    # Add other text
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    c.drawString(30, rect_y - 70, "Luca Albanese - itis")
   
    c.save()
    return c


def create_gradient(drawing, width, height, y_pos):
    """Create gradient effect"""
    num_steps = 50
    for i in range(num_steps):
        segment_height = height / num_steps
        segment_y = y_pos + (i * segment_height)
        intensity = 0.5 - (i / (num_steps * 2))
        r = Drawing()
        r.add(Rect(
            0, segment_y, width, segment_height,
            fillColor=colors.Color(0.1, 0.2, 0.5 + intensity),
            strokeColor=None
        ))
        drawing.add(r)


def add_title(canvas, text, page_width, rect_y, rect_height):
    """Add centered title to PDF"""
    title_font_size = 36
    canvas.setFont("Helvetica", title_font_size)
    title_width = canvas.stringWidth(text, "Helvetica", title_font_size)
    title_x = (page_width - title_width) / 2
    title_y = rect_y + (rect_height/2) - 10
    canvas.setFillColor(colors.white)
    canvas.drawString(title_x, title_y, text)


def process_geojson_files():
    """Process GeoJSON files and add to PDF"""
    geojson_paths = [
        os.path.join('data', 'results_analysis', '01_Linea_orilla_2100', 'A01', 'A01-001', 'l_orilla_ini_A01-001_01.geojson'),
        os.path.join('data', 'results_analysis', '01_Linea_orilla_2100', 'A01', 'A01-001', 'l_orilla_ini_A01-001_02.geojson')
    ]


    c = canvas.Canvas(output_path, pagesize=letter)
    y_position = 750


    for i, geojson_path in enumerate(geojson_paths, 1):
        print(f"Reading GeoJSON file from: {geojson_path}")
        gdf = gpd.read_file(geojson_path)
       
        y_position = add_geojson_data(c, gdf, i, y_position)
       
        if i < len(geojson_paths):
            c.showPage()
            y_position = 750
   
    c.save()
    print(f"GeoJSON data saved to PDF: {output_path}")


def add_geojson_data(canvas, gdf, file_num, y_position):
    """Add GeoJSON data to PDF"""
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(50, y_position, f"GeoJSON Data - Linea Orilla {file_num}")
    y_position -= 30
   
    canvas.setFont("Helvetica", 12)
    canvas.drawString(50, y_position, f"Coordinate Points File {file_num}:")
    y_position -= 20
   
    coordinates = gdf.geometry.iloc[0].coords
    for j, coord in enumerate(coordinates, 1):
        if y_position < 50:
            canvas.showPage()
            y_position = 750
            canvas.setFont("Helvetica", 12)
       
        coord_text = f"Point {j}: Longitude={coord[0]:.6f}, Latitude={coord[1]:.6f}"
        canvas.drawString(70, y_position, coord_text)
        y_position -= 15
   
    return y_position


if __name__ == "__main__":
    if not os.path.exists(file_path):
        print(f"Creating new PDF: {file_path}")
        create_initial_pdf()
   
    process_geojson_files()


