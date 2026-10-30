"""
Генератор музыки и звуков для игры «ЛИЛУ».
Запусти один раз:  python make_music.py
Он создаст файлы в assets/music/ и assets/sfx/ (WAV, без внешних библиотек).
Хочешь другую мелодию — поменяй seed или аккорды в TRACKS.
"""
import math
import os
import random
import struct
import wave

SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(HERE, "assets", "music")
SFX_DIR = os.path.join(HERE, "assets", "sfx")


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def add_note(buf, start, dur, midi, kind="square", vol=0.2, attack=0.005,
             decay_k=3.0, duty=0.5, release=0.05):
    """Складывает ноту в буфер. Хвосты уходят в начало — так петля звучит без щелчков."""
    N = len(buf)
    f = mtof(midi)
    s0 = int(start * SR)
    total = int((dur + release) * SR)
    for j in range(total):
        t = j / SR
        if t < attack:
            env = t / attack
        else:
            env = 1.0
        if decay_k:
            env *= math.exp(-decay_k * t)
        if t > dur:
            env *= max(0.0, 1 - (t - dur) / release)
        x = f * t
        fr = x - math.floor(x)
        if kind == "sine":
            v = math.sin(2 * math.pi * x)
        elif kind == "square":
            v = 1.0 if fr < duty else -1.0
        elif kind == "tri":
            v = 4 * abs(fr - 0.5) - 1
        else:  # saw
            v = 2 * fr - 1
        buf[(s0 + j) % N] += v * env * vol


def add_kick(buf, start, vol=0.6):
    N = len(buf)
    s0 = int(start * SR)
    phase = 0.0
    for j in range(int(0.25 * SR)):
        t = j / SR
        f = 45 + 105 * math.exp(-t * 30)
        phase += f / SR
        buf[(s0 + j) % N] += math.sin(2 * math.pi * phase) * math.exp(-t * 12) * vol


def add_snare(buf, start, vol=0.3):
    N = len(buf)
    s0 = int(start * SR)
    for j in range(int(0.2 * SR)):
        t = j / SR
        noise = random.uniform(-1, 1) * math.exp(-t * 25)
        tone = math.sin(2 * math.pi * 180 * t) * math.exp(-t * 30)
        buf[(s0 + j) % N] += (noise * 0.6 + tone * 0.4) * vol


def add_hat(buf, start, vol=0.08):
    N = len(buf)
    s0 = int(start * SR)
    for j in range(int(0.05 * SR)):
        t = j / SR
        buf[(s0 + j) % N] += random.uniform(-1, 1) * math.exp(-t * 110) * vol


def normalize(buf, peak=0.85):
    m = max(abs(v) for v in buf) or 1.0
    k = peak / m
    return [int(max(-1.0, min(1.0, v * k)) * 32767) for v in buf]


def write_wav(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(struct.pack("<%dh" % len(samples), *samples))


def build_track(bpm, bars, chords, seed, spec):
    """Собирает петлю из аккордов. spec — что звучит: bass, arp, pad, lead, drums."""
    rng = random.Random(seed)
    random.seed(seed)
    beat = 60.0 / bpm
    bar = 4 * beat
    N = int(bars * bar * SR)
    buf = [0.0] * N
    for b in range(bars):
        chord = chords[b % len(chords)]
        t0 = b * bar
        root = chord[0]

        if spec.get("pad"):
            for n in chord:
                add_note(buf, t0, bar, n + 12, "sine", vol=0.06, attack=0.5,
                         decay_k=0, release=0.6)

        if spec.get("bass"):
            for k in range(8):
                add_note(buf, t0 + k * beat / 2, beat / 2 * 0.9, root - 12, spec["bass"],
                         vol=0.22, attack=0.005, decay_k=2.5)

        if spec.get("arp"):
            step = bar / 16
            for k in range(16):
                i = k % (len(chord) * 2)
                m = chord[i % len(chord)] + 12 * (i // len(chord))
                add_note(buf, t0 + k * step, step * 0.9, m + 12, spec["arp"],
                         vol=0.07, attack=0.002, decay_k=8)

        if spec.get("lead"):
            pool = [c + 12 for c in chord] + [chord[0] + 24, chord[1] + 24]
            for k in range(8):
                if rng.random() < 0.65:
                    m = rng.choice(pool)
                    add_note(buf, t0 + k * beat / 2, beat / 2 * 0.95, m, spec["lead"],
                             vol=spec.get("lead_vol", 0.12), attack=0.005, decay_k=3.5, duty=0.3)

        if spec.get("kick"):
            for i in range(4):
                if i in spec.get("kick_beats", (0, 2)):
                    add_kick(buf, t0 + i * beat, vol=0.6)
        if spec.get("snare"):
            for i in (1, 3):
                add_snare(buf, t0 + i * beat, vol=0.28)
        if spec.get("hat"):
            for k in range(8):
                add_hat(buf, t0 + k * beat / 2, vol=0.07)

    return normalize(buf)


TRACKS = {
    # Меню: спокойный чиптюн
    "menu": dict(bpm=92, bars=16, seed=11,
                 chords=[[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]],
                 spec=dict(bass="tri", arp="tri", lead="square", lead_vol=0.10, kick=True, hat=True)),
    # Лаборатория, квартира, город, Земля: бодро
    "early": dict(bpm=124, bars=16, seed=22,
                  chords=[[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]],
                  spec=dict(bass="saw", arp="square", lead="square", lead_vol=0.09,
                            kick=True, snare=True, hat=True)),
    # Космос (Солнечная система, галактика): мягкий эмбиент
    "space": dict(bpm=72, bars=16, seed=33,
                  chords=[[50, 53, 57], [58, 62, 65], [53, 57, 60], [48, 52, 55]],
                  spec=dict(pad=True, arp="tri", lead="sine", lead_vol=0.07, hat=False)),
    # Космические хрени и финал мира: напряжённо и эпично
    "cosmic": dict(bpm=150, bars=16, seed=44,
                   chords=[[52, 55, 59], [48, 52, 55], [50, 54, 57], [57, 60, 64]],
                   spec=dict(bass="saw", arp="square", lead="saw", lead_vol=0.08,
                             kick=True, kick_beats=(0, 1, 2, 3), snare=True, hat=True)),
    # Титры: светлая мелодия
    "ending": dict(bpm=84, bars=16, seed=55,
                   chords=[[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]],
                   spec=dict(pad=True, arp="sine", lead="tri", lead_vol=0.12, bass="tri")),
}


def make_sfx():
    out = {}

    # «ням» — короткий поп при поедании
    N = int(0.12 * SR)
    buf = [0.0] * N
    phase = 0.0
    for j in range(N):
        t = j / SR
        f = 500 + 900 * (t / 0.12)
        phase += f / SR
        buf[j] = math.sin(2 * math.pi * phase) * math.exp(-t * 28) * 0.9
    out["eat"] = normalize(buf, 0.7)

    # «БАМ» — взрыв в начале катсцены
    N = int(1.2 * SR)
    buf = [0.0] * N
    phase = 0.0
    for j in range(N):
        t = j / SR
        f = 120 * math.exp(-t * 2.5) + 25
        phase += f / SR
        noise = random.uniform(-1, 1) * math.exp(-t * 4)
        buf[j] = (math.sin(2 * math.pi * phase) * math.exp(-t * 3) * 0.9 + noise * 0.5)
    out["boom"] = normalize(buf, 0.9)

    # «бум» — удар о большой объект
    N = int(0.3 * SR)
    buf = [0.0] * N
    phase = 0.0
    for j in range(N):
        t = j / SR
        f = 220 * math.exp(-t * 12) + 60
        phase += f / SR
        buf[j] = math.sin(2 * math.pi * phase) * math.exp(-t * 10)
    out["bump"] = normalize(buf, 0.7)

    # клик кнопки
    N = int(0.05 * SR)
    buf = [math.sin(2 * math.pi * 1400 * (j / SR)) * math.exp(-(j / SR) * 80) for j in range(N)]
    out["click"] = normalize(buf, 0.5)
    return out


def main():
    for name, cfg in TRACKS.items():
        print("делаю музыку:", name, "...", flush=True)
        samples = build_track(cfg["bpm"], cfg["bars"], cfg["chords"], cfg["seed"], cfg["spec"])
        write_wav(os.path.join(MUSIC_DIR, name + ".wav"), samples)
    for name, samples in make_sfx().items():
        write_wav(os.path.join(SFX_DIR, name + ".wav"), samples)
    print("готово: музыка в assets/music, звуки в assets/sfx")


if __name__ == "__main__":
    main()
