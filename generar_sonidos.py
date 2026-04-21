"""
Genera archivos de audio WAV para el juego Maka-i
"""
import wave
import struct
import math

def generar_tonos(frecuencias, duracion_ms, sample_rate=22050):
    """Genera onda de audio sinusoidal para frecuencias dadas."""
    num_samples = int(sample_rate * duracion_ms / 1000)
    frames = []
    
    for i in range(num_samples):
        sample = 0
        t = i / sample_rate
        for freq in frecuencias:
            sample += math.sin(2 * math.pi * freq * t)
        
        # Normalizar y convertir a int16
        if len(frecuencias) > 0:
            sample = int((sample / len(frecuencias)) * 30000)
        else:
            sample = 0  # Silencio
        frames.append(struct.pack('<h', sample))
    
    return b''.join(frames)

def guardar_wav(filename, audio_data, sample_rate=22050):
    """Guarda datos de audio en archivo WAV."""
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    print(f"✓ {filename}")

# Crear carpeta si no existe
import os
os.makedirs("assets/Recursos", exist_ok=True)

# 1. Música de fondo (loop suave, 8 segundos)
print("Generando música de fondo...")
notas = [261.63, 329.63, 392.00, 440.00]  # Do, Mi, Sol, La
bg_music = generar_tonos(notas, 1000)  # 1 seg
for _ in range(8):  # Repetir 8 veces para 8 segundos
    bg_music += generar_tonos(notas, 1000)
guardar_wav("assets/Recursos/background.wav", bg_music)

# 2. Sonido de aplauso (secuencia de "claps" sintéticos)
print("Generando sonido de aplauso...")
aplauso = b''
for _ in range(6):  # 6 aplausos rápidos
    aplauso += generar_tonos([200, 300, 400], 150)  # Ruido sintético
    aplauso += generar_tonos([], 100)  # Silencio
guardar_wav("assets/Recursos/applause.wav", aplauso)

print("\n✓ Sonidos generados en assets/Recursos/")
