import os
import urllib.request

# URL de un sonido de victoria libre
url = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# Guardar en assets/Recursos/
carpeta = os.path.join("assets", "Recursos")
os.makedirs(carpeta, exist_ok=True)
archivo = os.path.join(carpeta, "victoria.mp3")

print("Descargando sonido de victoria...")
try:
    urllib.request.urlretrieve(url, archivo)
    print(f"✅ Descargado en: {archivo}")
except Exception as e:
    print(f"❌ Error: {e}")
