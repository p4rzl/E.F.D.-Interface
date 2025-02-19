import pdfkit

# HTML come stringa
html_content = """
<html>
  <head><title>Test PDF</title></head>
  <body>
    <h1>Hello, this is a test PDF generated from HTML!</h1>
    <p>This is an example of HTML to PDF conversion using pdfkit.</p>
  </body>
</html>
"""

# Converti l'HTML in PDF
pdfkit.from_string(html_content, 'output.pdf')
