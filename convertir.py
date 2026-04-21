import os

# Rutas
carpeta_recursos = os.path.join("assets", "Recursos")
archivo_entrada = os.path.join(carpeta_recursos, "sonidoCasino.mp4")
archivo_salida = os.path.join(carpeta_recursos, "sonidoCasino.wav")

# Verificar que existe el archivo
if not os.path.exists(archivo_entrada):
    print(f"❌ Error: No encontré {archivo_entrada}")
    exit(1)

# Copiar como wav
with open(archivo_entrada, "rb") as src:
    with open(archivo_salida, "wb") as dst:
        dst.write(src.read())

print(f"✅ Convertido: {archivo_salida}")