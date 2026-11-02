#!/usr/bin/env python3
"""Rough software preview of the jar models (south/east/up faces, orthographic, glass alpha-blended).
Not Minecraft's renderer - only a sanity check of proportions and textures. Usage: python3 tools/preview_jars.py out.png"""
import json, math, os, sys
import numpy as np
from PIL import Image
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "assets", "littleweather")
def tex(name, frame):
    im = Image.open(os.path.join(R, "textures", name + ".png")).convert("RGBA")
    if name.endswith("_content"):
        im = im.crop((0, 64 * frame, 64, 64 * frame + 64))
    return np.array(im, np.float32)
def render(model, frame, W=300, bg=(60, 52, 84)):
    m = json.load(open(os.path.join(R, "models", "block", model + ".json")))
    texs = {k: v.split(":")[1] for k, v in m["textures"].items() if k != "particle"}
    cache = {}
    def T(key):
        n = texs[key[1:]].replace("block/", "block/")
        if n not in cache: cache[n] = tex(n, frame)
        return cache[n]
    yaw, pitch = math.radians(-35), math.radians(30)
    d = np.array([-math.cos(pitch) * math.sin(yaw) * -1, -math.sin(pitch), -math.cos(pitch) * math.cos(yaw)])
    d = np.array([-0.55, -0.55, -0.62]); d /= np.linalg.norm(d)
    right = np.cross(d, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, d)
    ys, xs = np.mgrid[0:W, 0:W].astype(np.float32)
    sc = 22.0 / W * 1.0
    px = (xs - W / 2) * sc; py = -(ys - W / 2) * sc * 1.0
    origin = np.array([8, 8, 8], np.float32)[None, None] + px[..., None] * right + py[..., None] * up - d * 40
    layers = []
    for e in m["elements"]:
        lo, hi = np.array(e["from"], np.float32), np.array(e["to"], np.float32)
        with np.errstate(divide="ignore", invalid="ignore"):
            t1, t2 = (lo - origin) / d, (hi - origin) / d
        tn = np.minimum(t1, t2); tf = np.maximum(t1, t2)
        tnear = tn.max(axis=-1); tfar = tf.min(axis=-1)
        axis = tn.argmax(axis=-1)
        hit = (tnear <= tfar) & (tnear > 0)
        p = origin + d * tnear[..., None]
        rgba = np.zeros((W, W, 4), np.float32)
        for ax, name_pos, name_neg in ((0, "east", "west"), (1, "up", "down"), (2, "south", "north")):
            sel = hit & (axis == ax)
            face = name_neg if d[ax] > 0 else name_pos
            f = e["faces"].get(face)
            if f is None or not sel.any(): continue
            u0, v0, u1, v1 = f["uv"]
            if ax == 2:
                s = (p[..., 0] - lo[0]) / (hi[0] - lo[0]); s = s if face == "south" else 1 - s
                tt = 1 - (p[..., 1] - lo[1]) / (hi[1] - lo[1])
            elif ax == 0:
                s = (p[..., 2] - lo[2]) / (hi[2] - lo[2]); s = s if face == "east" else 1 - s
                tt = 1 - (p[..., 1] - lo[1]) / (hi[1] - lo[1])
            else:
                s = (p[..., 0] - lo[0]) / (hi[0] - lo[0]); tt = (p[..., 2] - lo[2]) / (hi[2] - lo[2])
            img = T(f["texture"]); S = img.shape[1]
            u = np.clip((u0 + (u1 - u0) * s) / 16 * S, 0, S - 1).astype(int)
            v = np.clip((v0 + (v1 - v0) * tt) / 16 * S, 0, S - 1).astype(int)
            c = img[v, u]
            shade = {"up": 1.0, "south": 0.85, "east": 0.7}.get(face, 0.8) if e.get("shade", True) else 1.0
            c = c.copy(); c[..., :3] *= shade
            rgba[sel] = c[sel]
        t = np.where(hit, tnear, np.inf)
        layers.append((t, rgba))
    ts = np.stack([l[0] for l in layers]); cs = np.stack([l[1] for l in layers])
    order = np.argsort(-np.where(np.isinf(ts), -1, ts), axis=0)   # far to near
    out = np.zeros((W, W, 3), np.float32); out[:] = bg
    for i in range(len(layers)):
        idx = order[i]
        t = np.take_along_axis(ts, idx[None], 0)[0]
        c = np.take_along_axis(cs, idx[None, ..., None].repeat(4, -1), 0)[0]
        a = (c[..., 3:4] / 255.0) * (~np.isinf(t))[..., None]
        out = out * (1 - a) + c[..., :3] * a
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
if __name__ == "__main__":
    kinds = ["star", "rain", "sunset", "snow", "storm"]
    W = 300
    sheet = Image.new("RGB", (W * 5, W * 2))
    frames = {"star": 3, "rain": 4, "sunset": 6, "snow": 6, "storm": 6}
    for i, k in enumerate(kinds):
        sheet.paste(render(f"{k}_jar", frames[k], W), (i * W, 0))
        sheet.paste(render(f"{k}_jar_hanging", frames[k], W), (i * W, W))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/jars.png")
    print("ok")
