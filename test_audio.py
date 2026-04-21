import os
import pygame

pygame.mixer.init()

ruta = os.path.join("assets", "Recursos", "sonidoCasino.wav")

print(f"Buscando: {ruta}")
print(f"¿Existe?: {os.path.exists(ruta)}")

if os.path.exists(ruta):
    try:
        sound = pygame.mixer.Sound(ruta)
        print(f"✅ Archivo válido. Duración: {sound.get_length()} segundos")
        print("Reproduciendo...")
        sound.play()
        import time
        time.sleep(sound.get_length() + 1)
        print("✅ Reproducción completada")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No encontré el archivo")