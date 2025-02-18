import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import netCDF4 as nc
import pdfkit

# Funzione per caricare e visualizzare le correnti oceaniche
def plot_ocean_currents(nc_file, output_image):
    # Carica i dati dal file NetCDF esistente
    dataset = nc.Dataset(nc_file, 'r')
    lon = dataset.variables['longitude'][:]  # Longitudine
    lat = dataset.variables['latitude'][:]   # Latitudine
    u = dataset.variables['u'][:]            # Componente longitudinale della corrente
    v = dataset.variables['v'][:]            # Componente latitudinale della corrente

    # Seleziona un'istantanea (ad esempio il primo timestep)
    u_current = u[0, :, :]  # Velocità longitudinale per il primo timestep
    v_current = v[0, :, :]  # Velocità latitudinale per il primo timestep

    # Crea la figura e l'asse con la proiezione geografica
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.coastlines()
    ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()])

    # Traccia le correnti oceaniche con un campo vettoriale (u, v)
    ax.quiver(lon, lat, u_current, v_current, transform=ccrs.PlateCarree(), scale=500)

    # Aggiungi titolo e etichette
    ax.set_title('Ocean Currents')

    # Salva l'immagine
    plt.savefig(output_image, dpi=300)
    plt.close()

    print(f"Grafico delle correnti salvato come {output_image}")

# Funzione per convertire l'HTML in PDF
def convert_html_to_pdf(input_html, output_pdf):
    # Configura pdfkit per utilizzare il percorso corretto dell'eseguibile wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')  # Modifica il percorso se necessario
    pdfkit.from_file(input_html, output_pdf, configuration=config)
    print(f"File PDF creato: {output_pdf}")

# Funzione principale per eseguire il flusso completo
def main():
    # Step 1: Genera il grafico delle correnti oceaniche
    plot_ocean_currents('ocean_currents.nc', 'currents_plot.png')

    # Step 2: Crea la pagina HTML con il grafico
    import create_html_page  # Importa il modulo per creare il file HTML
    create_html_page.create_html_page('currents_plot.png', 'currents_page.html')

    # Step 3: Converte l'HTML in PDF
    convert_html_to_pdf('currents_page.html', 'currents_visualization.pdf')

# Esegui il programma
if __name__ == "__main__":
    main()
