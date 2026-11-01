#!/usr/bin/env python3
"""Static resource check: every model/texture/blockstate/item/loot/recipe/lang reference must resolve. Exit 1 on error."""
import json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources")
A, D, NS = os.path.join(ROOT, "assets", "littleweather"), os.path.join(ROOT, "data", "littleweather"), "littleweather"
errors = []
def need(path, why):
    if not os.path.exists(path):
        errors.append(f"missing {os.path.relpath(path, ROOT)} ({why})")
def ref(r):  # "littleweather:block/x" -> "block/x"
    ns, _, p = r.partition(":") if ":" in r else ("minecraft", "", r)
    return ns, p
blocks = ["star_jar", "rain_jar", "sunset_jar"]
items = blocks + ["empty_weather_jar"]
lang = json.load(open(os.path.join(A, "lang", "en_us.json")))
for n in items:
    need(os.path.join(A, "items", n + ".json"), "item definition")
    need(os.path.join(A, "models", "item", n + ".json"), "item model")
    for k in (f"item.{NS}.{n}",):
        if k not in lang: errors.append(f"lang key missing: {k}")
for n in blocks:
    need(os.path.join(A, "blockstates", n + ".json"), "blockstate")
    need(os.path.join(A, "models", "block", n + ".json"), "block model")
    need(os.path.join(D, "loot_table", "blocks", n + ".json"), "loot table")
    if f"block.{NS}.{n}" not in lang: errors.append(f"lang key missing: block.{NS}.{n}")
need(os.path.join(D, "recipe", "empty_weather_jar.json"), "recipe")
for root, _, files in os.walk(A):
    for f in files:
        if not f.endswith(".json") or "lang" in root or "particles" in root: continue
        data = json.load(open(os.path.join(root, f)))
        text = json.dumps(data)
        for m in re.findall(r'"(littleweather:[a-z0-9_/]+)"', text):
            ns, p = ref(m)
            if root.endswith("blockstates") or "models" in root and p.startswith(("block/", "item/")) and "textures" not in text.split(m)[0][-40:]:
                pass
        for tex in (data.get("textures") or {}).values():
            if tex.startswith("#"): continue
            ns, p = ref(tex)
            if ns == NS: need(os.path.join(A, "textures", p + ".png"), f"texture used by {f}")
        if "model" in data and isinstance(data["model"], dict):
            ns, p = ref(data["model"]["model"]); need(os.path.join(A, "models", p + ".json"), f"model used by {f}")
        if "variants" in data:
            for v in data["variants"].values():
                ns, p = ref(v["model"]); need(os.path.join(A, "models", p + ".json"), f"model used by {f}")
        if "parent" in data and data["parent"].startswith(NS + ":"):
            ns, p = ref(data["parent"]); need(os.path.join(A, "models", p + ".json"), f"parent of {f}")
for f in os.listdir(os.path.join(A, "particles")):
    for t in json.load(open(os.path.join(A, "particles", f)))["textures"]:
        ns, p = ref(t); need(os.path.join(A, "textures", "particle", p + ".png"), f"particle sprite for {f}")
need(os.path.join(A, "icon.png"), "mod icon")
mod = json.load(open(os.path.join(ROOT, "fabric.mod.json")))
need(os.path.join(ROOT, mod["icon"]), "fabric.mod.json icon")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("resource check OK")
