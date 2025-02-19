from netCDF4 import Dataset
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np

def plot_ocean_currents(input_file, output_file):
    # Carica il file netCDF
    dataset = Dataset(input_file, 'r')
    # Aggiungi questo dopo aver caricato il dataset per controllare le dimensioni
    print("Dimensioni del Dataset:")
    for var in dataset.variables:
        print(f"{var}: {dataset.variables[var].shape}")
    
    # Estrai le variabili senza presumere una struttura 3D
    u = dataset.variables['u'][:]  # Velocità longitudinale
    v = dataset.variables['v'][:]  # Velocità latitudinale
    lon = dataset.variables['lon'][:]
    lat = dataset.variables['lat'][:]

    # Modifica queste righe per gestire dati 2D
    u_current = u  # Rimuovi l'indicizzazione temporale poiché i dati sono 2D
    v_current = v  # Rimuovi l'indicizzazione temporale poiché i dati sono 2D
    
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
    from create_html_page import create_html_page
    create_html_page('currents_plot.png', 'currents_page.html')

# Modifica l'esecuzione
if __name__ == "__main__":  # Corretto da "currents_page.html" a "__main__"
    main()
