def create_html_page(image_path, output_html):
    html_content = f"""
    <html>
    <head>
        <title>Ocean Currents Visualization</title>
    </head>
    <body>
        <h1>Ocean Currents</h1>
        <img src="{image_path}" alt="Ocean Currents" style="width:80%;">
    </body>
    </html>
    """

    # Salva il contenuto HTML in un file
    with open(output_html, 'w') as file:
        file.write(html_content)

    print(f"File HTML creato: {output_html}")
