#!/usr/bin/env python3
"""Generates every Little Weather texture (needs Pillow + numpy). Run from the project root:
    python3 tools/generate_textures.py
v2 art is rendered with soft lighting at higher resolution than vanilla (64px jar contents, 64px glass)."""
import json, math, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "assets", "littleweather")
TEX = os.path.join(ROOT, "textures")
for d in ("item", "block", "particle"):
    os.makedirs(os.path.join(TEX, d), exist_ok=True)
os.makedirs(os.path.join(ROOT, "particles"), exist_ok=True)

SW, SH = 32, 36      # side-face region of a 64x64 content frame (model uv [0,0,8,9])
TW = 32              # top/bottom region (model uv [8,0,16,8]) at x=32..64, y=0..32
N = 16               # frames per animation

# ------------------------------------------------------------------ helpers
def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)

def grid(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x + 0.5, y + 0.5

def vgrad(w, h, stops):
    _, Y = grid(w, h)
    v = Y / h
    out = np.zeros((h, w, 3), np.float32)
    ps = [s[0] for s in stops]
    for c in range(3):
        out[..., c] = np.interp(v, ps, [s[1][c] for s in stops])
    return out

def gradient_map(v, stops):
    out = np.zeros(v.shape + (3,), np.float32)
    ps = [s[0] for s in stops]
    for c in range(3):
        out[..., c] = np.interp(v, ps, [s[1][c] for s in stops])
    return out

def add_glow(img, cx, cy, r, color, k=1.0):
    h, w = img.shape[:2]
    X, Y = grid(w, h)
    g = np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * (r / 2.0) ** 2)) * k
    img += g[..., None] * np.array(color, np.float32)

def seg_dist(X, Y, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy + 1e-9
    t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L, 0, 1)
    return np.hypot(X - (x0 + t * dx), Y - (y0 + t * dy)), t

def blend(img, alpha, color):
    img[:] = img * (1 - alpha[..., None]) + alpha[..., None] * np.array(color, np.float32)

def vignette(img):
    h, w = img.shape[:2]
    X, Y = grid(w, h)
    e = np.minimum(np.minimum(X, w - X), np.minimum(Y, h - Y))
    img *= (0.72 + 0.28 * ss(0, 5, e))[..., None]

def to_u8(img):
    return np.clip(img, 0, 255).astype(np.uint8)

def compose_frame(side, top):
    fr = np.zeros((64, 64, 3), np.float32)
    fr[:] = side.mean(axis=(0, 1))
    fr[0:SH, 0:SW] = side
    fr[0:TW, 32:64] = top
    rgba = np.dstack([to_u8(fr), np.full((64, 64), 255, np.uint8)])
    return Image.fromarray(rgba, "RGBA")

def save_anim(frames, name, frametime, interpolate=True):
    sheet = Image.new("RGBA", (64, 64 * len(frames)))
    for i, f in enumerate(frames):
        sheet.paste(f, (0, 64 * i))
    sheet.save(os.path.join(TEX, f"block/{name}.png"))
    meta = {"animation": {"frametime": frametime}}
    if interpolate:
        meta["animation"]["interpolate"] = True
    with open(os.path.join(TEX, f"block/{name}.png.mcmeta"), "w") as fh:
        json.dump(meta, fh, indent=2)

def cloud_layer(w, h, circles, t, light, shadow, drift=1.2, extra=None):
    """Soft lit cloud: returns (density, colour) arrays."""
    X, Y = grid(w, h)
    dens = np.zeros((h, w), np.float32)
    col = np.zeros((h, w, 3), np.float32)
    wsum = np.zeros((h, w), np.float32)
    for i, (cx, cy, r) in enumerate(circles):
        cx = cx + drift * math.sin(2 * math.pi * t + i * 1.7)
        cy = cy + 0.5 * math.sin(2 * math.pi * t * 2 + i)
        d = np.hypot(X - cx, (Y - cy) * 1.1)
        m = ss(r, r - 2.2, d)
        lit = np.clip(0.55 + 0.6 * (cy - Y) / r - 0.15 * (X - cx) / r, 0, 1)
        c = np.array(shadow, np.float32) + (np.array(light, np.float32) - np.array(shadow, np.float32)) * lit[..., None]
        col += c * m[..., None]
        wsum += m
        dens = np.maximum(dens, m)
    col = col / np.maximum(wsum, 1e-4)[..., None]
    return dens, col

def rain_streaks(w, h, t, drops, y_top, length=4.0, slant=0.25, color=(196, 226, 255), strength=0.9):
    X, Y = grid(w, h)
    a = np.zeros((h, w), np.float32)
    span = h - y_top
    for (x0, y0, k) in drops:
        yy = y_top + ((y0 + k * span * t) % span)
        xx = x0 + slant * (yy - y_top) * 0.2
        d, tt = seg_dist(X, Y, xx - slant * length, yy - length, xx, yy)
        s = np.clip(1 - d / 0.85, 0, 1) * (0.25 + 0.75 * tt) * ss(y_top, y_top + 4, yy)
        a = np.maximum(a, s)
        if yy < y_top + length:   # wrap-around copy so streaks leave the bottom smoothly
            pass
        yy2 = yy - span
        d2, tt2 = seg_dist(X, Y, xx - slant * length, yy2 - length, xx, yy2)
        a = np.maximum(a, np.clip(1 - d2 / 0.85, 0, 1) * (0.25 + 0.75 * tt2))
    return a * strength

# ------------------------------------------------------------------ star
def star_scene(t):
    rng = np.random.RandomState(11)
    img = vgrad(SW, SH, [(0.0, (7, 8, 36)), (0.55, (20, 17, 66)), (1.0, (58, 36, 112))])
    X, Y = grid(SW, SH)
    neb = 0.5 + 0.5 * np.sin(X * 0.28 + Y * 0.17 + 2 * math.pi * t)
    img += neb[..., None] * np.array([16, 6, 26], np.float32) * ss(8, 36, Y)[..., None]
    for i in range(16):
        sx, sy = rng.uniform(2, SW - 2), rng.uniform(2, SH - 3)
        if (sx - 9) ** 2 + (sy - 9) ** 2 < 70:
            continue
        ph, k = rng.uniform(0, 1), rng.choice([1, 2])
        b = 0.55 + 0.45 * math.sin(2 * math.pi * (t * k + ph))
        warm = rng.rand() > 0.35
        col = (255, 238, 190) if warm else (200, 220, 255)
        big = i % 4 == 0
        add_glow(img, sx, sy, 3.0 if big else 1.7, col, (0.7 if big else 0.5) * b)
        add_glow(img, sx, sy, 1.0, (255, 255, 255), 0.9 * b)
        if big and b > 0.7:
            for (dx, dy) in ((1, 0), (0, 1)):
                d, tt = seg_dist(X, Y, sx - 4 * dx, sy - 4 * dy, sx + 4 * dx, sy + 4 * dy)
                img += (np.clip(1 - d / 0.6, 0, 1) * (1 - np.abs(tt - 0.5) * 2) * 0.8 * b)[..., None] * np.array(col, np.float32)
    # crescent moon
    mc = (9.0, 9.5)
    disc = ss(5.2, 4.2, np.hypot(X - mc[0], Y - mc[1]))
    cut = ss(4.0, 5.0, np.hypot(X - (mc[0] + 2.3), Y - (mc[1] - 1.2)))
    moon = disc * cut
    add_glow(img, mc[0], mc[1], 13, (255, 226, 150), 0.30)
    blend(img, moon, (255, 238, 176))
    # shooting star
    if 11 <= int(t * N) <= 13:
        p = (t * N - 11) / 3.0
        hx, hy = 27 - 10 * p, 4 + 7 * p
        d, tt = seg_dist(X, Y, hx, hy, hx + 7, hy - 4.7, ) if False else seg_dist(X, Y, hx + 6, hy - 4, hx, hy)
        a = np.clip(1 - d / 0.8, 0, 1) * tt * (1 - abs(p - 0.5) * 1.2)
        blend(img, a, (255, 248, 220))
    vignette(img)
    return img

def star_top(t):
    rng = np.random.RandomState(5)
    img = vgrad(TW, TW, [(0, (14, 13, 56)), (1, (30, 24, 86))])
    for i in range(9):
        sx, sy = rng.uniform(2, TW - 2), rng.uniform(2, TW - 2)
        b = 0.5 + 0.5 * math.sin(2 * math.pi * (t * rng.choice([1, 2]) + rng.rand()))
        add_glow(img, sx, sy, 3.0, (255, 240, 200), 0.8 * b)
    vignette(img)
    return img

# ------------------------------------------------------------------ rain / storm
def rain_scene(t):
    img = vgrad(SW, SH, [(0, (28, 32, 78)), (0.5, (50, 58, 120)), (1, (84, 98, 168))])
    circles = [(8, 6, 5.2), (14, 5, 6.5), (21, 6, 5.6), (26, 8, 4.2), (11, 9, 4.6), (18, 9.5, 5.2), (23, 10.5, 3.6)]
    dens, col = cloud_layer(SW, SH, circles, t, (226, 232, 255), (112, 124, 196))
    drops = [(5, 0, 1), (9, 8, 2), (13, 3, 1), (17, 14, 2), (21, 6, 1), (25, 11, 2), (28, 1, 1), (7, 17, 1), (19, 20, 1), (24, 2, 2)]
    a = rain_streaks(SW, SH, t, drops, 12)
    blend(img, a, (186, 222, 255))
    img = img * (1 - dens[..., None]) + col * dens[..., None]
    add_glow(img, 16, SH - 1, 14, (150, 190, 255), 0.18)           # wet mist at the bottom
    vignette(img)
    return img

def cloud_top(t, light, shadow, base):
    img = np.zeros((TW, TW, 3), np.float32) + np.array(base, np.float32)
    circles = [(6, 7, 6), (15, 5, 7), (25, 8, 6), (9, 17, 7), (20, 16, 7), (28, 22, 5), (6, 27, 6), (16, 27, 7), (25, 28, 6)]
    dens, col = cloud_layer(TW, TW, circles, t, light, shadow, drift=1.0)
    img = img * (1 - dens[..., None]) + col * dens[..., None]
    vignette(img)
    return img

def storm_scene(t):
    f = int(round(t * N)) % N
    flash = {6: 1.0, 7: 0.55, 8: 0.2, 12: 0.45, 13: 0.15}.get(f, 0.0)
    img = vgrad(SW, SH, [(0, (14, 14, 40)), (0.5, (30, 30, 70)), (1, (46, 48, 98))])
    circles = [(7, 6, 6), (13, 5, 7), (20, 6, 7), (27, 8, 5), (10, 10, 5.5), (17, 10, 6), (24, 11, 4.6)]
    light = tuple(np.array((120, 112, 170)) + flash * np.array((120, 120, 80)))
    shadow = tuple(np.array((52, 48, 96)) + flash * np.array((90, 90, 70)))
    dens, col = cloud_layer(SW, SH, circles, t, light, shadow)
    drops = [(4, 0, 2), (8, 5, 2), (12, 10, 1), (15, 2, 2), (19, 13, 2), (22, 7, 1), (26, 4, 2), (29, 16, 2), (6, 19, 1), (17, 21, 2), (24, 15, 1)]
    a = rain_streaks(SW, SH, t, drops, 13, length=5, slant=0.45, color=(170, 205, 255), strength=0.8)
    blend(img, a, (170, 205, 255))
    img = img * (1 - dens[..., None]) + col * dens[..., None]
    if flash > 0:
        X, Y = grid(SW, SH)
        pts = [(15.5, 12), (13.5, 17), (16.5, 21), (13, 27), (15, 31), (12, 35)]
        bolt = np.zeros((SH, SW), np.float32)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            d, _ = seg_dist(X, Y, x0, y0, x1, y1)
            bolt = np.maximum(bolt, np.clip(1 - d / 0.9, 0, 1))
        d, _ = seg_dist(X, Y, 16.5, 21, 21, 27)
        bolt = np.maximum(bolt, np.clip(1 - d / 0.7, 0, 1) * 0.7)
        add_glow(img, 15, 20, 12, (150, 170, 255), 0.5 * flash)
        blend(img, np.clip(bolt * flash, 0, 1), (255, 252, 235))
    vignette(img)
    return img

def storm_top(t):
    f = int(round(t * N)) % N
    flash = {6: 1.0, 7: 0.55, 8: 0.2, 12: 0.45, 13: 0.15}.get(f, 0.0)
    return cloud_top(t, tuple(np.array((100, 94, 150)) + flash * 90), tuple(np.array((44, 42, 84)) + flash * 60), (24, 24, 56))

# ------------------------------------------------------------------ sunset
SUN_STOPS = [(0.0, (46, 36, 118)), (0.22, (126, 88, 196)), (0.45, (255, 108, 150)), (0.68, (255, 142, 64)), (0.88, (255, 204, 100)), (1.0, (255, 232, 150))]

def sunset_scene(t):
    X, Y = grid(SW, SH)
    v = Y / SH + 0.05 * np.sin(2 * math.pi * (X / 16 + t)) + 0.03 * np.sin(2 * math.pi * (X / 9 - 2 * t)) + 0.035 * math.sin(2 * math.pi * t)
    img = gradient_map(v, SUN_STOPS)
    # sun low on the horizon
    sy = 29.0
    d = np.hypot(X - 16, Y - sy)
    r = 5.6 + 0.5 * math.sin(2 * math.pi * t)
    add_glow(img, 16, sy, 26, (255, 170, 80), 0.55)
    blend(img, ss(r, r - 1.4, d), (255, 246, 208))
    # drifting clouds, lit from below
    for i, (cy, ln, ht) in enumerate([(10, 9, 1.6), (16, 11, 1.9), (22, 8, 1.5)]):
        cx0 = (i * 11.0 + 32 * t * (1 if i % 2 == 0 else -1)) % 32
        for wrap in (-32, 0, 32):
            dd = np.hypot((X - (cx0 + wrap)) / ln, (Y - cy) / ht)
            m = ss(1.0, 0.45, dd) * 0.85
            lit = np.clip((Y - cy) / ht * 0.5 + 0.5, 0, 1)
            col = np.array((150, 100, 190), np.float32) + (np.array((255, 160, 120), np.float32) - np.array((150, 100, 190), np.float32)) * lit[..., None]
            img = img * (1 - m[..., None]) + col * m[..., None]
    # silhouetted hills
    hill = 32.6 + 1.6 * np.sin(X * 0.33 + 1.0) + 0.9 * np.sin(X * 0.8)
    ground = ss(hill - 0.6, hill + 0.6, Y)
    rim = ss(hill - 1.4, hill, Y) * (1 - ground)
    img = img * (1 - ground[..., None]) + np.array((40, 24, 78), np.float32) * ground[..., None]
    img += rim[..., None] * np.array((60, 30, 10), np.float32)
    vignette(img)
    return img

def sunset_top(t):
    X, Y = grid(TW, TW)
    d = np.hypot(X - 16, Y - 16) / 20.0
    v = 1.0 - d + 0.06 * np.sin(2 * math.pi * (X / 16 + t))
    img = gradient_map(v * 0.8 + 0.15, SUN_STOPS)
    vignette(img)
    return img

# ------------------------------------------------------------------ snow
def snow_scene(t):
    rng = np.random.RandomState(21)
    X, Y = grid(SW, SH)
    img = vgrad(SW, SH, [(0, (36, 44, 100)), (0.55, (84, 98, 166)), (1, (160, 176, 226))])
    circles = [(9, 5, 5.5), (16, 4.5, 6.5), (23, 5.5, 5.5), (12, 8.5, 4.5), (20, 8.5, 4.5)]
    dens, col = cloud_layer(SW, SH, circles, t, (240, 244, 255), (150, 162, 220), drift=0.8)
    img = img * (1 - dens[..., None] * 0.9) + col * (dens[..., None] * 0.9)
    for i in range(14):
        x0, y0 = rng.uniform(2, SW - 2), rng.uniform(0, 30)
        k = rng.choice([1, 2]); sz = rng.uniform(0.8, 1.5); ph = rng.rand()
        yy = 8 + ((y0 + k * 28 * t) % 28)
        xx = x0 + 1.6 * math.sin(2 * math.pi * (t + ph))
        add_glow(img, xx, yy, 1.3 * sz + 0.4, (222, 232, 255), 0.32)
        d = np.hypot(X - xx, Y - yy)
        blend(img, ss(sz * 0.5, sz * 0.1, d), (255, 255, 255))
    pile = 31.5 + 1.4 * np.sin(X * 0.3 + 0.6) + 0.6 * np.sin(X * 0.9)
    g = ss(pile - 0.7, pile + 0.7, Y)
    snowc = vgrad(SW, SH, [(0.0, (246, 248, 255)), (1.0, (196, 208, 242))])
    img = img * (1 - g[..., None]) + snowc * g[..., None]
    for (sx, sy) in ((7, 33), (15, 34), (24, 33), (28, 34)):
        b = max(0.0, math.sin(2 * math.pi * (t + sx / 30.0)))
        add_glow(img, sx, sy, 2.2, (255, 255, 255), 0.7 * b)
    vignette(img)
    return img

def snow_top(t):
    img = vgrad(TW, TW, [(0, (226, 234, 252)), (1, (198, 210, 244))])
    rng = np.random.RandomState(8)
    for i in range(10):
        b = max(0.0, math.sin(2 * math.pi * (t + rng.rand())))
        add_glow(img, rng.uniform(2, TW - 2), rng.uniform(2, TW - 2), 2.0, (255, 255, 255), 0.7 * b)
    return img

def rain_top(t):
    return cloud_top(t, (214, 222, 255), (116, 128, 200), (60, 68, 138))

# ------------------------------------------------------------------ glass, cork, ribbon, twine
def glass():
    S = 64
    im = np.zeros((S, S, 4), np.float32)
    # body region: pixels 0..40 x 0..40 (uv [0,0,10,10])
    B = 40
    X, Y = grid(B, B)
    x, y = X / B, Y / B
    edge = np.maximum(np.abs(x - 0.5), np.abs(y - 0.5)) * 2
    a = np.full((B, B), 20.0)
    a += 105 * ss(0.78, 1.0, edge)
    a += 55 * ss(0.84, 1.0, y)
    col = np.zeros((B, B, 3), np.float32)
    col[:] = (196, 186, 255)
    deep = np.array((120, 104, 214), np.float32)
    col = col + (deep - col) * ss(0.7, 1.0, edge)[..., None]
    col = col + (np.array((150, 200, 230), np.float32) - col) * (ss(0.84, 1.0, y) * 0.6)[..., None]
    streak = ss(0.12, 0.15, x) * ss(0.25, 0.20, x) * ss(0.04, 0.16, y) * ss(0.78, 0.55, y)
    streak2 = ss(0.28, 0.30, x) * ss(0.33, 0.30, x) * ss(0.10, 0.2, y) * ss(0.6, 0.45, y)
    glare = ss(0.76, 0.80, x) * ss(0.88, 0.84, x) * ss(0.16, 0.26, y) * ss(0.52, 0.38, y)
    a += 190 * streak + 80 * streak2 + 70 * glare
    for k, v in ((streak, 1.0), (streak2, 0.9), (glare, 0.7)):
        col = col + (np.array((255, 255, 255), np.float32) - col) * (np.clip(k, 0, 1) * v)[..., None]
    for (bx, by, br) in ((0.62, 0.78, 0.022), (0.7, 0.7, 0.014), (0.38, 0.86, 0.016)):
        d = np.hypot(x - bx, y - by)
        ring = ss(br + 0.012, br, d) * ss(br - 0.012, br - 0.004, d)
        a += 70 * ring
        col = col + (np.array((255, 255, 255), np.float32) - col) * ring[..., None]
    sheen = 16 * (1 - (x + y) / 2)
    a += sheen
    im[0:B, 0:B, :3] = col
    im[0:B, 0:B, 3] = np.clip(a, 0, 255)
    # neck/shoulder region: x 40..64, y 0..24 (uv [10,0,16,6])
    W2, H2 = 24, 24
    X2, Y2 = grid(W2, H2)
    x2 = X2 / W2
    a2 = 36 + 110 * ss(0.8, 1.0, np.abs(x2 - 0.5) * 2) + 150 * ss(0.14, 0.2, x2) * ss(0.30, 0.22, x2)
    c2 = np.zeros((H2, W2, 3), np.float32); c2[:] = (200, 190, 255)
    c2 = c2 + (np.array((255, 255, 255), np.float32) - c2) * (ss(0.14, 0.2, x2) * ss(0.30, 0.22, x2) * 0.9)[..., None]
    im[0:H2, 40:64, :3] = c2
    im[0:H2, 40:64, 3] = np.clip(a2, 0, 255)
    Image.fromarray(to_u8(im), "RGBA").save(os.path.join(TEX, "block/jar_glass.png"))

def cork():
    S = 32
    rng = np.random.RandomState(4)
    base = np.zeros((S, S, 3), np.float32); base[:] = (176, 128, 78)
    noise = rng.rand(S, S)
    from_blur = (noise + np.roll(noise, 1, 0) + np.roll(noise, 1, 1)) / 3
    base += ((from_blur - 0.5) * 60)[..., None]
    pits = rng.rand(S, S) > 0.93
    base[pits] = (112, 74, 42)
    lights = rng.rand(S, S) > 0.95
    base[lights] = (214, 168, 112)
    Image.fromarray(np.dstack([to_u8(base), np.full((S, S), 255, np.uint8)]), "RGBA").save(os.path.join(TEX, "block/jar_cork.png"))

def ribbon():
    S = 32
    X, Y = grid(S, S)
    sheen = 0.5 + 0.5 * np.sin(Y * 0.55 + 1.0)
    img = np.zeros((S, S, 3), np.float32); img[:] = (120, 84, 200)
    img += (sheen * 70)[..., None] * np.array((0.8, 0.9, 0.6), np.float32)
    img *= (0.85 + 0.15 * ss(0, 3, np.minimum(Y, S - Y)))[..., None]
    Image.fromarray(np.dstack([to_u8(img), np.full((S, S), 255, np.uint8)]), "RGBA").save(os.path.join(TEX, "block/jar_ribbon.png"))

def twine():
    S = 32
    X, Y = grid(S, S)
    twist = 0.5 + 0.5 * np.sin((X + Y) * 0.9)
    img = np.zeros((S, S, 3), np.float32); img[:] = (176, 142, 92)
    img += ((twist - 0.5) * 70)[..., None]
    img *= (0.8 + 0.2 * ss(0, 2, np.minimum(Y, S - Y)))[..., None]
    Image.fromarray(np.dstack([to_u8(img), np.full((S, S), 255, np.uint8)]), "RGBA").save(os.path.join(TEX, "block/jar_twine.png"))

# ------------------------------------------------------------------ empty jar item (32x32, drawn at 4x and downsampled)
def empty_jar():
    S = 128
    X, Y = grid(S, S)
    def rrect(x0, y0, x1, y1, r):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        qx, qy = np.abs(X - cx) - ((x1 - x0) / 2 - r), np.abs(Y - cy) - ((y1 - y0) / 2 - r)
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
        return ss(1.2, -1.2, d), d
    img = np.zeros((S, S, 4), np.float32)
    def paint(mask, color, alpha=1.0):
        a = mask * alpha
        for c in range(3):
            img[..., c] = img[..., c] * (1 - a) + color[c] * a if not hasattr(color[c], 'shape') else img[..., c] * (1 - a) + color[c] * a
        img[..., 3] = np.clip(img[..., 3] + a * (1 - img[..., 3]) * 255 * 1.0, 0, 255) if False else np.maximum(img[..., 3], a * 255)
    body, bd = rrect(22, 44, 106, 120, 20)
    neck, _ = rrect(38, 30, 90, 56, 6)
    lip, _ = rrect(34, 24, 94, 38, 5)
    cork_m, _ = rrect(42, 6, 86, 30, 5)
    # glass body
    glass_col = np.zeros((S, S, 3), np.float32); glass_col[:] = (196, 186, 255)
    inner = ss(-1, -9, bd)
    rimv = 1 - inner
    glass_a = body * (30 + 120 * rimv)
    rgb = glass_col * (1 - rimv[..., None] * 0.35) + np.array((120, 104, 214), np.float32) * (rimv[..., None] * 0.35)
    img[..., :3] = rgb * (body[..., None] > 0)
    img[..., 3] = glass_a
    for m, col, al in ((neck, (200, 190, 255), 90), (lip, (222, 214, 255), 190)):
        a = m * al
        img[..., :3] = np.where(m[..., None] > 0.01, np.array(col, np.float32), img[..., :3])
        img[..., 3] = np.maximum(img[..., 3], a)
    # specular streak and glare
    st = ss(31, 34, X) * ss(41, 37, X) * ss(52, 62, Y) * ss(104, 82, Y) * body
    img[..., :3] = img[..., :3] * (1 - st[..., None]) + 255 * st[..., None]
    img[..., 3] = np.maximum(img[..., 3], st * 215)
    gl = ss(90, 94, X) * ss(98, 94, X) * ss(60, 70, Y) * ss(84, 76, Y) * body
    img[..., :3] = img[..., :3] * (1 - gl[..., None] * 0.7) + 255 * gl[..., None] * 0.7
    img[..., 3] = np.maximum(img[..., 3], gl * 120)
    # ribbon around the neck and a small bow
    rb, _ = rrect(36, 50, 92, 58, 2)
    img[..., :3] = np.where(rb[..., None] > 0.01, np.array((130, 92, 214), np.float32), img[..., :3]); img[..., 3] = np.maximum(img[..., 3], rb * 255)
    for (x0, x1) in ((46, 62), (66, 82)):
        lp, _ = rrect(x0, 56, x1, 70, 5)
        img[..., :3] = np.where(lp[..., None] > 0.01, np.array((150, 112, 230), np.float32), img[..., :3]); img[..., 3] = np.maximum(img[..., 3], lp * 255)
    kn, _ = rrect(58, 54, 70, 66, 4)
    img[..., :3] = np.where(kn[..., None] > 0.01, np.array((106, 72, 190), np.float32), img[..., :3]); img[..., 3] = np.maximum(img[..., 3], kn * 255)
    # cork
    cgrad = np.clip((Y - 6) / 24, 0, 1)
    ck = np.zeros((S, S, 3), np.float32); ck[:] = (192, 142, 88)
    ck = ck * (1 - 0.25 * cgrad[..., None])
    rng = np.random.RandomState(2)
    ck += ((rng.rand(S, S) - 0.5) * 36)[..., None]
    img[..., :3] = np.where(cork_m[..., None] > 0.01, ck, img[..., :3]); img[..., 3] = np.maximum(img[..., 3], cork_m * 255)
    # amethyst shard in the jar
    def poly(pts, color, al=255):
        from PIL import ImageDraw
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        mm = np.array(m, np.float32) / 255.0
        img[..., :3] = np.where(mm[..., None] > 0.5, np.array(color, np.float32), img[..., :3]); img[..., 3] = np.maximum(img[..., 3], mm * al)
    poly([(62, 112), (54, 94), (60, 78), (68, 94), (72, 112)], (150, 96, 220))
    poly([(62, 112), (54, 94), (60, 78)], (190, 140, 255))
    poly([(72, 112), (68, 94), (60, 78)], (110, 64, 180))
    poly([(78, 112), (74, 100), (80, 90), (86, 102), (88, 112)], (136, 84, 206))
    poly([(78, 112), (74, 100), (80, 90)], (176, 126, 244))
    # glints
    for (gx, gy, gr) in ((60, 86, 5), (84, 98, 3), (48, 74, 3)):
        d = np.hypot(X - gx, Y - gy)
        g = ss(gr * 2.2, 0, d)
        img[..., :3] = img[..., :3] * (1 - g[..., None]) + np.array((255, 246, 214), np.float32) * g[..., None]
        img[..., 3] = np.maximum(img[..., 3], g * 255)
    out = Image.fromarray(to_u8(img), "RGBA").resize((32, 32), Image.LANCZOS)
    out.save(os.path.join(TEX, "item/empty_weather_jar.png"))

# ------------------------------------------------------------------ particles (16x16, pre-compensated for the end-rod tint)
TINT = (242 / 255, 235 / 255, 201 / 255)
def save_particle(name, rgb, alpha):
    S = alpha.shape[0]
    img = np.zeros((S, S, 4), np.float32)
    for c in range(3):
        img[..., c] = np.minimum(255, rgb[..., c] / TINT[c]) if isinstance(rgb, np.ndarray) else min(255, rgb[c] / TINT[c])
    img[..., 3] = alpha * 255
    Image.fromarray(to_u8(img), "RGBA").save(os.path.join(TEX, f"particle/{name}.png"))

def orb(S, cx, cy, r_core, r_glow):
    X, Y = grid(S, S)
    d = np.hypot(X - cx, Y - cy)
    return np.clip(ss(r_core, 0, d) + 0.55 * ss(r_glow, r_core * 0.6, d), 0, 1)

def particles():
    S = 16
    X, Y = grid(S, S)
    warm = (255, 240, 190)
    # twinkle: 4 sparkle frames
    for i, (arm, core) in enumerate(((2.5, 1.2), (4.5, 1.8), (6.8, 2.2), (3.6, 1.5))):
        a = orb(S, 8, 8, core, core * 2.6) * 0.9
        for (dx, dy) in ((1, 0), (0, 1)):
            d, tt = seg_dist(X, Y, 8 - arm * dx, 8 - arm * dy, 8 + arm * dx, 8 + arm * dy)
            a = np.maximum(a, np.clip(1 - d / 0.8, 0, 1) * (1 - np.abs(tt - 0.5) * 2) ** 0.7)
        save_particle(f"star_twinkle_{i}", warm, np.clip(a, 0, 1))
    # raindrop
    for i, (tilt, ln) in enumerate(((0.0, 4.5), (0.0, 3.8))):
        d, tt = seg_dist(X, Y, 8, 3.5, 8, 3.5 + ln * 1.6)
        a = np.clip(1 - d / (0.9 + 0.8 * tt), 0, 1) * (0.35 + 0.65 * tt)
        save_particle(f"rain_drop_{i}", (140, 196, 255), a)
    # sunset motes
    for i, col in enumerate(((255, 168, 90), (255, 140, 168), (255, 208, 110))):
        save_particle(f"sunset_mote_{i}", col, orb(S, 8, 8, 2.2, 6.2))
    # snow flake
    for i, rot in enumerate((0.0, 0.5)):
        a = orb(S, 8, 8, 1.4, 4.0) * 0.8
        for k in range(3):
            ang = math.pi * k / 3 + rot
            d, tt = seg_dist(X, Y, 8 - 4.2 * math.cos(ang), 8 - 4.2 * math.sin(ang), 8 + 4.2 * math.cos(ang), 8 + 4.2 * math.sin(ang))
            a = np.maximum(a, np.clip(1 - d / 0.7, 0, 1) * 0.9)
        save_particle(f"snow_flake_{i}", (232, 240, 255), np.clip(a, 0, 1))
    # storm spark: tiny zig-zag
    for i, pts in enumerate(([(5, 2), (9, 6), (6, 8), (10, 13)], [(10, 2), (6, 6), (9, 8), (5, 13)])):
        a = np.zeros((S, S), np.float32)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            d, _ = seg_dist(X, Y, x0, y0, x1, y1)
            a = np.maximum(a, np.clip(1 - d / 0.8, 0, 1))
        a = np.maximum(a, 0.4 * ss(3.5, 0, np.hypot(X - 8, Y - 8)))
        save_particle(f"storm_spark_{i}", (232, 232, 255), a)
    def pj(name, frames):
        with open(os.path.join(ROOT, "particles", f"{name}.json"), "w") as fh:
            json.dump({"textures": [f"littleweather:{n}" for n in frames]}, fh, indent=2)
    pj("star_twinkle", [f"star_twinkle_{i}" for i in range(4)])
    pj("rain_drop", ["rain_drop_0", "rain_drop_1"])
    pj("sunset_mote", [f"sunset_mote_{i}" for i in range(3)])
    pj("snow_flake", ["snow_flake_0", "snow_flake_1"])
    pj("storm_spark", ["storm_spark_0", "storm_spark_1"])

if __name__ == "__main__":
    empty_jar(); glass(); cork(); ribbon(); twine()
    scenes = {
        "star": (star_scene, star_top, 4),
        "rain": (rain_scene, rain_top, 2),
        "sunset": (sunset_scene, sunset_top, 8),
        "snow": (snow_scene, snow_top, 5),
        "storm": (storm_scene, storm_top, 2),
    }
    for name, (side, top, ft) in scenes.items():
        save_anim([compose_frame(side(i / N), top(i / N)) for i in range(N)], f"{name}_content", ft)
    particles()
    print("textures written to", os.path.normpath(TEX))
