from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
import numpy as np

def create_ocean_currents_animation(output_file):
    try:
        # Genera dati di test
        lon = np.linspace(-180, 180, 72)
        lat = np.linspace(-90, 90, 36)
        lon_mesh, lat_mesh = np.meshgrid(lon, lat)
        
        # Crea campi di velocità sintetici
        u = np.sin(np.radians(lat_mesh)) * 20  # Velocità zonale
        v = np.cos(np.radians(lon_mesh)) * 20  # Velocità meridionale
        
        # Crea la figura
        fig, ax = plt.subplots(figsize=(16, 12),  
                              subplot_kw={'projection': ccrs.PlateCarree()})
        ax.coastlines()
        ax.gridlines()
        
        def update(frame):
            ax.clear()
            ax.coastlines()
            ax.gridlines()
            
            # Ruota i dati per l'animazione
            u_rot = np.roll(u, frame * 2, axis=1)
            v_rot = np.roll(v, frame * 2, axis=1)
            
            # Disegna le correnti
            q = ax.quiver(lon_mesh[::2, ::2], lat_mesh[::2, ::2], 
                         u_rot[::2, ::2], v_rot[::2, ::2],
                         transform=ccrs.PlateCarree(),
                         scale=1000, color='blue', alpha=0.6)
            return q,
        
        # Crea e salva l'animazione
        anim = animation.FuncAnimation(fig, update, frames=30, 
                                     interval=100, blit=True)
        anim.save(output_file, writer='pillow', fps=10)
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"Errore nella generazione dell'animazione: {str(e)}")
        return False