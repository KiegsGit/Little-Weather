#!/usr/bin/env python3
"""Synthesizes Little Weather's two sounds (numpy + ffmpeg with libvorbis). Run from the project root."""
import os, subprocess, wave, tempfile
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "assets", "littleweather", "sounds")
os.makedirs(OUT, exist_ok=True)
SR = 44100

def write_ogg(name, data):
    data = data / (np.max(np.abs(data)) + 1e-9) * 0.8
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:a", "libvorbis", "-q:a", "4", os.path.join(OUT, name + ".ogg")], check=True)
    os.remove(path)

def chime():
    """Soft glass chime: three bell notes in a quick rising arpeggio, each with shimmering overtones."""
    dur = 1.6
    t = np.arange(int(SR * dur)) / SR
    out = np.zeros_like(t)
    for start, f in ((0.00, 1318.5), (0.11, 1568.0), (0.23, 2093.0)):
        tt = np.clip(t - start, 0, None)
        env = (t >= start) * np.exp(-tt * 3.2) * np.minimum(1, tt * 400)
        tone = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6) + 0.18 * np.sin(2 * np.pi * f * 5.4 * tt) * np.exp(-tt * 10)
        tone *= 1 + 0.03 * np.sin(2 * np.pi * 5.5 * tt)
        out += env * tone
    return out

def cork_pop():
    dur = 0.18
    t = np.arange(int(SR * dur)) / SR
    rng = np.random.RandomState(3)
    sweep = np.sin(2 * np.pi * np.cumsum(520 * np.exp(-t * 28) + 140) / SR) * np.exp(-t * 30)
    noise = rng.randn(len(t)) * np.exp(-t * 80) * 0.25
    return sweep + noise

if __name__ == "__main__":
    write_ogg("capture_chime", chime())
    write_ogg("cork_pop", cork_pop())
    print("sounds written to", os.path.normpath(OUT))
