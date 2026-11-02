#!/usr/bin/env python3
"""Generates block/item models, blockstates, item definitions and loot tables for every jar. Run from the project root."""
import json, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources")
A, D = os.path.join(R, "assets", "littleweather"), os.path.join(R, "data", "littleweather")
for d in ("models/block", "models/item", "blockstates", "items"):
    os.makedirs(os.path.join(A, d), exist_ok=True)
os.makedirs(os.path.join(D, "loot_table", "blocks"), exist_ok=True)
KINDS = ["star", "rain", "sunset", "snow", "storm"]

def w(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2); f.write("\n")

def faces(tex, side, cap, skip=()):
    out = {}
    for k in ("north", "south", "east", "west"):
        if k not in skip: out[k] = {"uv": side, "texture": tex}
    for k in ("up", "down"):
        out[k] = {"uv": cap, "texture": tex}
    return out

def elements():
    E = [
        {"name": "contents", "from": [4.5, 1, 4.5], "to": [11.5, 10.5, 11.5], "shade": False, "faces": faces("#content", [0, 0, 8, 9], [8, 0, 16, 8])},
        {"name": "glass_body", "from": [3.5, 0, 3.5], "to": [12.5, 11, 12.5], "faces": faces("#glass", [0, 0, 10, 10], [0, 0, 10, 10])},
        {"name": "shoulder", "from": [4.3, 11, 4.3], "to": [11.7, 12.2, 11.7], "faces": faces("#glass", [10, 0, 16, 1.5], [10, 0, 16, 6])},
        {"name": "neck", "from": [5, 12.2, 5], "to": [11, 13.5, 11], "faces": faces("#glass", [10, 0, 16, 1.5], [10, 0, 16, 6])},
        {"name": "lip", "from": [4.5, 13.2, 4.5], "to": [11.5, 14, 11.5], "faces": faces("#glass", [10, 0, 16, 1], [10, 0, 16, 6])},
        {"name": "cork", "from": [5.5, 13.6, 5.5], "to": [10.5, 15.8, 10.5], "faces": faces("#cork", [0, 0, 16, 8], [0, 0, 16, 16])},
        {"name": "ribbon", "from": [4.9, 12.3, 4.9], "to": [11.1, 13.0, 11.1], "faces": faces("#ribbon", [0, 0, 16, 3], [0, 0, 16, 16])},
        {"name": "bow_knot", "from": [7.2, 12.2, 11.1], "to": [8.8, 13.2, 11.6], "faces": faces("#ribbon", [0, 0, 4, 4], [0, 0, 4, 4], skip=("north",))},
        {"name": "bow_left", "from": [5.8, 12.3, 11.1], "to": [7.2, 13.0, 11.5], "faces": faces("#ribbon", [0, 0, 6, 4], [0, 0, 6, 4], skip=("north",))},
        {"name": "bow_right", "from": [8.8, 12.3, 11.1], "to": [10.2, 13.0, 11.5], "faces": faces("#ribbon", [0, 0, 6, 4], [0, 0, 6, 4], skip=("north",))},
    ]
    return E

def hanging_elements():
    s = 0.8
    def tx(v): return round(8 + (v - 8) * s, 3)
    def ty(v): return round(v * s, 3)
    out = []
    for e in elements():
        e = json.loads(json.dumps(e))
        f, t = e["from"], e["to"]
        e["from"] = [tx(f[0]), ty(f[1]), tx(f[2])]
        e["to"] = [tx(t[0]), ty(t[1]), tx(t[2])]
        out.append(e)
    out.append({"name": "rope", "from": [7.5, 12.4, 7.5], "to": [8.5, 15.2, 8.5], "faces": faces("#twine", [0, 0, 2, 8], [0, 0, 2, 2])})
    out.append({"name": "rope_knot", "from": [6.9, 15.2, 6.9], "to": [9.1, 16, 9.1], "faces": faces("#twine", [0, 0, 6, 2], [0, 0, 6, 6])})
    return out

for k in KINDS:
    tex = {"particle": f"littleweather:block/{k}_content", "content": f"littleweather:block/{k}_content",
           "glass": "littleweather:block/jar_glass", "cork": "littleweather:block/jar_cork",
           "ribbon": "littleweather:block/jar_ribbon", "twine": "littleweather:block/jar_twine"}
    w(f"{A}/models/block/{k}_jar.json", {"parent": "minecraft:block/block", "textures": tex, "elements": elements()})
    w(f"{A}/models/block/{k}_jar_hanging.json", {"parent": "minecraft:block/block", "textures": tex, "elements": hanging_elements()})
    w(f"{A}/models/item/{k}_jar.json", {"parent": f"littleweather:block/{k}_jar"})
    w(f"{A}/blockstates/{k}_jar.json", {"variants": {
        "hanging=false": {"model": f"littleweather:block/{k}_jar"},
        "hanging=true": {"model": f"littleweather:block/{k}_jar_hanging"}}})
    w(f"{A}/items/{k}_jar.json", {"model": {"type": "minecraft:model", "model": f"littleweather:item/{k}_jar"}})
    w(f"{D}/loot_table/blocks/{k}_jar.json", {
        "type": "minecraft:block",
        "pools": [{"rolls": 1.0, "bonus_rolls": 0.0,
                   "entries": [{"type": "minecraft:item", "name": f"littleweather:{k}_jar"}],
                   "conditions": [{"condition": "minecraft:survives_explosion"}]}],
        "random_sequence": f"littleweather:blocks/{k}_jar"})
w(f"{A}/models/item/empty_weather_jar.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "littleweather:item/empty_weather_jar"}})
w(f"{A}/items/empty_weather_jar.json", {"model": {"type": "minecraft:model", "model": "littleweather:item/empty_weather_jar"}})
print("models written")
