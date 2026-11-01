#!/usr/bin/env python3
"""Generates every Little Weather pixel-art texture (needs Pillow). Run from the project root:
    python3 tools/generate_textures.py
Palette follows the banner: midnight blue, twilight purple, sunset orange/pink, pale yellow, rain-cloud blue."""
import json, math, os, random
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "assets", "littleweather")
TEX = os.path.join(ROOT, "textures")
for d in ("item", "block", "particle"):
    os.makedirs(os.path.join(TEX, d), exist_ok=True)
os.makedirs(os.path.join(ROOT, "particles"), exist_ok=True)

def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))

def gradient(stops, v):
    v = max(stops[0][0], min(stops[-1][0], v))
    for i in range(len(stops) - 1):
        (p0, c0), (p1, c1) = stops[i], stops[i + 1]
        if v <= p1:
            return lerp(c0, c1, 0 if p1 == p0 else (v - p0) / (p1 - p0))
    return stops[-1][1]

def px(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        c = tuple(int(round(max(0, min(255, v)))) for v in c)
        img.putpixel((x, y), c if len(c) == 4 else c + (255,))

def save(img, rel):
    img.save(os.path.join(TEX, rel))

# ---------------------------------------------------------------- empty jar (item, 16x16)
def empty_jar():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    edge, hi, lo, fill = (160, 140, 235), (232, 222, 255), (96, 76, 176), (176, 160, 240, 70)
    cork, cork_d, cork_l = (138, 90, 43), (107, 66, 32), (168, 116, 66)
    for y in range(1, 4):                       # cork
        for x in range(5, 11):
            px(im, x, y, cork_l if y == 1 else cork_d if y == 3 else cork)
    for x in range(4, 12):                      # glass rim
        px(im, x, 4, hi if x < 8 else edge)
    for y in range(5, 15):                      # body
        for x in range(3, 13):
            wall = x in (3, 12) or y in (5, 14)
            if wall:
                px(im, x, y, lo if (y == 14 or x == 12) else edge)
            else:
                px(im, x, y, fill)
    for y in range(6, 11):                      # glass highlight
        px(im, 4, y, hi + (200,))
    px(im, 5, 6, hi + (200,))
    px(im, 8, 9, (255, 244, 192)); px(im, 9, 9, (255, 244, 192, 120)); px(im, 7, 9, (255, 244, 192, 120)); px(im, 8, 8, (255, 244, 192, 120)); px(im, 8, 10, (255, 244, 192, 120))
    px(im, 6, 12, (200, 170, 255)); px(im, 10, 7, (200, 170, 255))
    save(im, "item/empty_weather_jar.png")

# ---------------------------------------------------------------- jar shell + cork (block, 16x16)
def glass():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    edge, hi, lo, fill = (170, 150, 240, 150), (240, 232, 255, 190), (100, 80, 180, 170), (190, 175, 255, 38)
    for y in range(11):
        for x in range(10):
            if x in (0, 9) or y in (0, 10):
                px(im, x, y, lo if (y == 10 or x == 9) else edge)
            else:
                px(im, x, y, fill)
    for y in range(2, 7):
        px(im, 2, y, hi)
    px(im, 3, 2, hi); px(im, 3, 1, hi[:3] + (120,))
    px(im, 7, 8, hi[:3] + (110,))
    save(im, "block/jar_glass.png")

def cork():
    rnd = random.Random(7)
    im = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            px(im, x, y, (168, 116, 66) if r > 0.82 else (107, 66, 32) if r < 0.22 else (138, 90, 43))
    save(im, "block/jar_cork.png")

# ---------------------------------------------------------------- animated contents (16 wide, 16 per frame)
def finish_anim(frames, name, frametime, interpolate=False):
    sheet = Image.new("RGBA", (16, 16 * len(frames)))
    for i, f in enumerate(frames):
        sheet.paste(f, (0, 16 * i))
    save(sheet, f"block/{name}.png")
    meta = {"animation": {"frametime": frametime}}
    if interpolate:
        meta["animation"]["interpolate"] = True
    with open(os.path.join(TEX, f"block/{name}.png.mcmeta"), "w") as fh:
        json.dump(meta, fh, indent=2)

SIDE_W, SIDE_H = 8, 9      # side faces use uv [0,0,8,9]
TOP = (8, 0)               # top/bottom faces use uv [8,0,16,8]

def star_frames():
    sky = [(0.0, (14, 13, 52)), (1.0, (38, 30, 100))]
    LEVEL = [0, 0, 1, 2, 2, 1, 0, 0]
    stars = [(5, 1, 0), (6, 4, 3), (4, 6, 5), (1, 7, 2), (7, 7, 6)]
    frames = []
    for f in range(8):
        im = Image.new("RGBA", (16, 16), (14, 13, 52, 255))
        for y in range(SIDE_H):
            for x in range(SIDE_W):
                px(im, x, y, gradient(sky, y / (SIDE_H - 1)))
        for (x, y) in [(2, 1), (3, 1), (1, 2), (1, 3), (2, 4), (3, 4)]:      # crescent moon
            px(im, x, y, (255, 236, 160))
        px(im, 1, 2, (240, 200, 110)); px(im, 1, 3, (240, 200, 110))
        for (sx, sy, ph) in stars:
            lv = LEVEL[(f + ph) % 8]
            col = [(120, 108, 200), (255, 233, 160), (255, 250, 220)][lv]
            px(im, sx, sy, col)
            if lv == 2:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = sx + dx, sy + dy
                    if 0 <= nx < SIDE_W and 0 <= ny < SIDE_H and (nx, ny) not in [(1, 2), (1, 3)]:
                        px(im, nx, ny, (255, 233, 160, 255))
        rnd = random.Random(3)
        for y in range(8):                                                     # top / bottom view of the sky
            for x in range(8):
                base = gradient(sky, 0.4)
                px(im, TOP[0] + x, TOP[1] + y, base)
        for k, (x, y) in enumerate([(1, 1), (5, 2), (3, 5), (6, 6)]):
            px(im, TOP[0] + x, TOP[1] + y, [(120, 108, 200), (255, 233, 160), (255, 250, 220)][LEVEL[(f + 2 * k) % 8]])
        frames.append(im)
    return frames

def rain_frames():
    sky = [(0.0, (40, 44, 108)), (1.0, (62, 68, 146))]
    drops = [(1, 0), (3, 3), (4, 5), (6, 1)]
    cloud_rows = {0: [1, 2, 5, 6], 1: range(1, 7), 2: range(0, 8), 3: range(1, 7)}
    frames = []
    for f in range(8):
        im = Image.new("RGBA", (16, 16), (40, 44, 108, 255))
        for y in range(SIDE_H):
            for x in range(SIDE_W):
                px(im, x, y, gradient(sky, y / (SIDE_H - 1)))
        for y, xs in cloud_rows.items():
            for x in xs:
                col = (196, 206, 255) if y == 0 else (150, 164, 228) if y < 3 else (112, 124, 200)
                px(im, x, y, col)
        px(im, 2 + 2 * (f // 4), 0, (226, 232, 255))
        px(im, 3, 1, (210, 218, 255))
        for (dx, off) in drops:
            y = 4 + ((f + off) % 8)
            if y <= 8:
                px(im, dx, y, (190, 226, 255))
                if y - 1 >= 4:
                    px(im, dx, y - 1, (120, 184, 255))
                if y - 2 >= 4:
                    px(im, dx, y - 2, (80, 130, 225))
        for y in range(8):
            for x in range(8):
                px(im, TOP[0] + x, TOP[1] + y, (150, 164, 228) if (x + y + f // 4) % 5 else (196, 206, 255))
        frames.append(im)
    return frames

def sunset_frames(n=16):
    stops = [(-0.3, (96, 72, 176)), (0.0, (122, 95, 208)), (0.28, (255, 127, 168)), (0.55, (255, 138, 61)),
             (0.8, (255, 200, 87)), (1.3, (255, 226, 140))]
    frames = []
    for f in range(n):
        t = f / n
        im = Image.new("RGBA", (16, 16), (255, 138, 61, 255))
        for y in range(SIDE_H):
            for x in range(SIDE_W):
                v = (y / (SIDE_H - 1)) + 0.12 * math.sin(2 * math.pi * (x / 8 + t)) \
                    + 0.08 * math.sin(2 * math.pi * ((x + y) / 10 - t)) + 0.07 * math.sin(2 * math.pi * t)
                c = gradient(stops, v)
                d = math.hypot(x - 3.5, y - 7.5)                                  # low sun glow
                r = 2.6 + 0.5 * math.sin(2 * math.pi * t)
                if d < r:
                    c = lerp(c, (255, 240, 180), 0.75 * (1 - d / r))
                px(im, x, y, c)
        for y in range(8):
            for x in range(8):
                d = math.hypot(x - 3.5, y - 3.5)
                v = 0.25 + 0.5 * (1 - d / 5.5) + 0.1 * math.sin(2 * math.pi * (t + x / 8))
                px(im, TOP[0] + x, TOP[1] + y, gradient(stops, v))
        frames.append(im)
    return frames

# ---------------------------------------------------------------- particles (8x8)
# Minecraft's end-rod particle tints by (242,235,201): pre-compensate so the colours land where we want them.
TINT = (242 / 255, 235 / 255, 201 / 255)
def comp(c):
    return tuple(min(255, int(round(c[i] / TINT[i]))) for i in range(3))

def particle(name, pixels):
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    for (x, y, col, a) in pixels:
        px(im, x, y, comp(col) + (a,))
    save(im, f"particle/{name}.png")

def particles():
    warm, white = (255, 236, 170), (255, 250, 225)
    particle("star_twinkle_0", [(3, 3, warm, 160), (4, 3, warm, 160), (3, 4, warm, 160), (4, 4, warm, 160)])
    particle("star_twinkle_1", [(3, 3, white, 255), (4, 3, white, 255), (3, 4, white, 255), (4, 4, white, 255),
                                (3, 2, warm, 150), (4, 2, warm, 150), (3, 5, warm, 150), (4, 5, warm, 150),
                                (2, 3, warm, 150), (2, 4, warm, 150), (5, 3, warm, 150), (5, 4, warm, 150)])
    cross = [(3, 3, white, 255), (4, 3, white, 255), (3, 4, white, 255), (4, 4, white, 255)]
    for k in (1, 2):
        cross += [(3, 3 - k, warm, 220), (4, 3 - k, warm, 220), (3, 4 + k, warm, 220), (4, 4 + k, warm, 220),
                  (3 - k, 3, warm, 220), (3 - k, 4, warm, 220), (4 + k, 3, warm, 220), (4 + k, 4, warm, 220)]
    particle("star_twinkle_2", cross)
    particle("star_twinkle_3", [(3, 3, warm, 200), (4, 3, warm, 200), (3, 4, warm, 200), (4, 4, warm, 200),
                                (3, 2, warm, 110), (3, 5, warm, 110), (2, 3, warm, 110), (5, 4, warm, 110)])
    blue, pale = (110, 178, 255), (200, 230, 255)
    particle("rain_drop_0", [(3, 2, blue, 200), (3, 3, pale, 255), (3, 4, blue, 255), (3, 5, blue, 200)])
    particle("rain_drop_1", [(3, 2, blue, 150), (3, 3, blue, 230), (3, 4, pale, 255), (3, 5, blue, 230)])
    for i, col in enumerate([(255, 168, 90), (255, 140, 168), (255, 208, 110)]):
        particle(f"sunset_mote_{i}", [(3, 3, col, 255), (4, 3, col, 255), (3, 4, col, 255), (4, 4, col, 255),
                                      (2, 3, col, 110), (2, 4, col, 110), (5, 3, col, 110), (5, 4, col, 110),
                                      (3, 2, col, 110), (4, 2, col, 110), (3, 5, col, 110), (4, 5, col, 110)])
    def pj(name, frames):
        with open(os.path.join(ROOT, "particles", f"{name}.json"), "w") as fh:
            json.dump({"textures": [f"littleweather:{n}" for n in frames]}, fh, indent=2)
    pj("star_twinkle", [f"star_twinkle_{i}" for i in range(4)] + ["star_twinkle_3"])
    pj("rain_drop", ["rain_drop_0", "rain_drop_1"])
    pj("sunset_mote", [f"sunset_mote_{i}" for i in range(3)])

if __name__ == "__main__":
    empty_jar(); glass(); cork()
    finish_anim(star_frames(), "star_content", 5)
    finish_anim(rain_frames(), "rain_content", 2)
    finish_anim(sunset_frames(), "sunset_content", 10, interpolate=True)
    particles()
    print("textures written to", os.path.normpath(TEX))
