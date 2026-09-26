#!/usr/bin/env python3
# Written for Rolehack by Lucas Ruiz, 2026-09-26.  See ROLEHACK-CHANGES.md.
"""Data for the Rolehack Dressing Room (2026-09-26).

Reads the real tile files and object table from RolehackDroid and writes one
JSON file the viewer embeds: the palette, every hero body with the anchors
RhDoll.java uses, every wearable item with its floor tile and the flags the
core would send (weapon family, dragon scales, dragon index, front garment,
cloak style), a few absurd things to hold, some map tiles for the scene, and
the starting kits from u_init.c.  Run: python3 export.py [OUT.json]
(default: data.json beside this script).
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = str(HERE.parents[1])            # tools/dressing-room -> the repository
OUT = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "data.json")

def tiles(path):
    txt = open(path).read()
    pal = {m.group(1): "#%02x%02x%02x" % tuple(int(v) for v in m.group(2, 3, 4))
           for m in re.finditer(r"^(\S) = \((\d+),\s*(\d+),\s*(\d+)\)", txt, re.M)}
    ts = [(m.group(1), "".join(r.strip() for r in m.group(2).split("\n")))
          for m in re.finditer(r"# tile \d+ \((.*?)\)\n(?:#[^\n]*\n)*\{\n(.*?)\n\}", txt, re.S)]
    return pal, ts

pal, MON = tiles(f"{ROOT}/win/share/monsters.txt")
_, OBJ = tiles(f"{ROOT}/win/share/objects.txt")
_, OTH = tiles(f"{ROOT}/win/share/other.txt")
MOND = dict(MON)
OTHD = dict(OTH)
assert len(pal) >= 28

# ---- objects.h, in order (the same parse as tools/paperdoll/census.py)
src = open(f"{ROOT}/include/objects.h").read().split("\n")
lines, skip = [], 0
for ln in src:
    s = ln.strip()
    if s.startswith("#if 0"):
        skip += 1; continue
    if skip and s.startswith("#if"):
        skip += 1; continue
    if skip and s.startswith("#endif"):
        skip -= 1; continue
    if not skip:
        lines.append(ln)
body = "\n".join(lines)
body = body[body.index("/* dummy object[0]"):]
MACROS = ("OBJECT GENERIC WEAPON PROJECTILE BOW ARMOR HELM CLOAK SHIELD GLOVES BOOTS DRGN_ARMR "
          "RING AMULET TOOL CONTAINER WEPTOOL FOOD POTION SCROLL SPELL WAND COIN GEM ROCK "
          "EYEWEAR XTRA_SCROLL_LABEL").split()
objs = []
for m in re.finditer(r"^(%s)\(" % "|".join(MACROS), body, re.M):
    i, depth = m.end() - 1, 0
    while True:
        c = body[i]
        if c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0: break
        i += 1
    call = re.sub(r"/\*.*?\*/", "", body[m.start():i + 1], flags=re.S)
    kind = m.group(1)
    if kind == "OBJECT" and "NoDes, NoDes" in call:
        continue
    args = [a.strip() for a in re.split(r",(?![^(]*\))", call[call.index("(") + 1:-1])]
    objs.append(dict(kind=kind, call=call, args=args, sn=re.findall(r"[A-Z_][A-Z0-9_]*", call)[-1]))
names = [t[0] for t in OBJ if "shimmering" not in t[0]]
assert len(names) == len(objs), (len(names), len(objs))
for o, (n, px) in zip(objs, [t for t in OBJ if "shimmering" not in t[0]]):
    parts = n.split(" / ")
    o["look"], o["name"], o["px"] = parts[0], parts[-1], px

SKILL_FAMILY = {"P_DAGGER": 1, "P_KNIFE": 1, "P_SHORT_SWORD": 2, "P_BROAD_SWORD": 2, "P_LONG_SWORD": 2,
                "P_SABER": 2, "P_TWO_HANDED_SWORD": 3, "P_AXE": 4, "P_PICK_AXE": 5, "P_CLUB": 6,
                "P_MACE": 6, "P_MORNING_STAR": 6, "P_FLAIL": 6, "P_HAMMER": 6, "P_QUARTERSTAFF": 7,
                "P_POLEARMS": 8, "P_SPEAR": 8, "P_TRIDENT": 8, "P_LANCE": 8, "P_BOW": 9, "P_SLING": 9,
                "P_CROSSBOW": 9, "P_DART": 10, "P_SHURIKEN": 10, "P_BOOMERANG": 10, "P_WHIP": 11,
                "P_UNICORN_HORN": 12}
CLOAK_STYLES = ["faded pall", "coarse mantelet", "hooded cloak", "slippery cloak", "leather cloak",
                "tattered cape", "opera cloak", "ornamental cope", "piece of cloth", "robe", "apron",
                "mummy wrapping"]
DRAGONS = ["gray", "gold", "silver", "red", "white", "orange", "black", "blue", "green", "yellow"]
ARMSLOT = {"HELM": "helmet", "CLOAK": "cloak", "SHIELD": "shield", "GLOVES": "gloves", "BOOTS": "boots",
           "DRGN_ARMR": "suit"}
SUBSLOT = {"ARM_SUIT": "suit", "ARM_SHIRT": "shirt", "ARM_CLOAK": "cloak", "ARM_HELM": "helmet",
           "ARM_SHIELD": "shield", "ARM_GLOVES": "gloves", "ARM_BOOTS": "boots"}

items = []
for idx, o in enumerate(objs):
    k, call = o["kind"], o["call"]
    slot = None
    if k in ARMSLOT:
        slot = ARMSLOT[k]
    elif k == "ARMOR":
        sub = next((t for t in re.findall(r"ARM_[A-Z]+", call)), None)
        slot = SUBSLOT.get(sub)
    elif k == "EYEWEAR":
        slot = "eyewear"
    elif k == "AMULET":
        slot = "amulet"
    elif k in ("WEAPON", "PROJECTILE", "BOW", "WEPTOOL"):
        slot = "weapon"
    if not slot:
        continue
    it = dict(id=idx, name=o["name"], look=o["look"], slot=slot, px=o["px"])
    if slot == "weapon":
        sk = [s.replace(" ", "") for s in re.findall(r"-?\s*P_[A-Z_]+", call) if "P_NONE" not in s]
        s0 = sk[0] if sk else ""
        it["family"] = 10 if s0.startswith("-") else SKILL_FAMILY.get(s0, 0)
        if k in ("WEAPON", "WEPTOOL"):
            it["two"] = o["args"][4] == "1"
    if o["name"].endswith("dragon scales"):
        it["hide"] = True
    if o["name"].endswith("dragon scale mail"):
        it["dragon"] = DRAGONS.index(o["name"].split()[0])
    if slot == "cloak":
        look = o["look"]
        it["cloak"] = CLOAK_STYLES.index(look) + 1 if look in CLOAK_STYLES else 0
        if o["name"] in ("robe", "alchemy smock", "mummy wrapping"):
            it["front"] = True
    items.append(it)

# absurd things to hold: a thing held up, tinted with its own colour
HELD = {"expensive camera": "expensive camera", "magic lamp": "magic lamp", "tin opener": "tin opener",
        "magic marker": "magic marker", "Candelabrum of Invocation": "Candelabrum of Invocation",
        "corpse": "cockatrice corpse", "gain ability": "potion (ruby)",
        "heavy iron ball": "heavy iron ball"}
for idx, o in enumerate(objs):
    if o["name"] in HELD and o["kind"] not in ("WEAPON", "WEPTOOL"):
        items.append(dict(id=idx, name=HELD[o["name"]], look=o["look"], slot="weapon", px=o["px"],
                          family=0, held=True))

# ---- bodies: tiles and the anchors RhDoll.java measures
def A(**kw):
    a = dict(head=[0, 0], torso=[0, 0], main=[4, 10], off=[11, 10], hands=None, feetRow=13,
             feetCols=[5, 6, 9, 10], short=False, keep=[])
    a.update(kw)
    return a
ANCH = {
    "archeologist": A(head=[0, 1], torso=[0, 1], main=[4, 11], off=[11, 11], feetRow=14, feetCols=[5, 6, 7, 9, 10, 11]),
    "barbarian": A(feetRow=14, feetCols=[5, 6, 9, 10]),
    "cave dweller": A(), "healer": A(feetRow=-1), "knight": A(),
    "monk": A(head=[0, 2], hands=[6, 9, 7, 9, 9, 9, 10, 9], feetRow=-1),
    "cleric,male": A(head=[0, -1], main=[4, 9], off=[11, 9], feetRow=-1),
    "cleric,female": A(main=[4, 9], off=[11, 9], feetRow=-1),
    "ranger": A(head=[1, 0], torso=[1, 0], main=[5, 10], off=[12, 10], feetCols=[6, 7, 10, 11]),
    "rogue": A(head=[0, 2], torso=[0, 2], main=[4, 12], off=[11, 12], feetRow=14, feetCols=[5, 6, 9, 10]),
    "samurai": A(head=[0, 1], torso=[0, 1], main=[4, 11], off=[11, 11], feetRow=14, feetCols=[5, 6, 9, 10]),
    "tourist": A(head=[0, 1], torso=[0, 1], main=[4, 11], off=[11, 11], feetRow=14, feetCols=[5, 6, 9, 10]),
    "valkyrie": A(), "wizard": A(feetRow=-1),
    "apothecary": A(head=[-1, -1], main=[4, 10], off=[9, 10], hands=[3, 9, 9, 10], feetCols=[5, 6, 8, 9]),
    "human": A(), "elf": A(),
    "dwarf": A(main=[4, 11], off=[8, 11], feetCols=[4, 5, 7, 8], short=True, keep=[5, 9, 6, 9, 7, 9, 6, 10]),
    "gnome,male": A(main=[4, 11], off=[8, 11], feetCols=[4, 5, 7, 8], short=True, keep=[5, 9, 6, 9, 7, 9, 6, 10]),
    "gnome,female": A(main=[4, 11], off=[8, 11], feetCols=[4, 5, 7, 8], short=True),
    "orc": A(head=[-2, 1], torso=[-2, 0], main=[2, 10], off=[9, 10], feetCols=[2, 3, 4, 6, 7, 8]),
}
ROLES = [("archeologist", "Archeologist"), ("barbarian", "Barbarian"), ("cave dweller", "Cave dweller"),
         ("healer", "Healer"), ("knight", "Knight"), ("monk", "Monk"), ("cleric", "Priest"),
         ("ranger", "Ranger"), ("rogue", "Rogue"), ("samurai", "Samurai"), ("tourist", "Tourist"),
         ("valkyrie", "Valkyrie"), ("wizard", "Wizard"), ("apothecary", "Apothecary")]
RACES = [("human", "Human"), ("elf", "Elf"), ("dwarf", "Dwarf"), ("gnome", "Gnome"), ("orc", "Orc")]
bodies = []
for group, lst in (("role", ROLES), ("race", RACES)):
    for key, label in lst:
        for g in ("male", "female"):
            name = f"{key},{g}"
            a = ANCH.get(name) or ANCH[key]
            bodies.append(dict(id=name, key=key, label=label, gender=g, group=group,
                               px=MOND[name], anchor=a))

# ---- starting kits, read from u_init.c: the first weapon is wielded, armour worn
u = open(f"{ROOT}/src/u_init.c").read()
KITARR = {"archeologist": "Archeologist", "barbarian": "Barbarian_0", "cave dweller": "Cave_man",
          "healer": "Healer", "knight": "Knight", "monk": "Monk", "cleric": "Priest",
          "ranger": "Ranger", "rogue": "Rogue", "samurai": "Samurai", "tourist": "Tourist",
          "valkyrie": "Valkyrie", "wizard": "Wizard", "apothecary": "Apothecary"}
sn2item = {}
for idx, o in enumerate(objs):
    sn2item[o["sn"]] = idx
kits = {}
for key, arr in KITARR.items():
    m = re.search(r"static const struct trobj %s\[\] = \{(.*?)\n\};" % arr, u, re.S)
    ents = re.findall(r"\{\s*([A-Z_0-9]+),\s*[^,]+,\s*(\w+_CLASS)", re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S))
    kit, weapon_done = {}, False
    for sn, cls in ents:
        idx = sn2item.get(sn)
        it = next((i for i in items if i["id"] == idx and not i.get("held")), None)
        if not it:
            continue
        if it["slot"] == "weapon":
            if cls == "WEAPON_CLASS" and not weapon_done and it.get("family") != 10:
                kit["weapon"] = idx
                weapon_done = True
        elif it["slot"] == "eyewear":
            continue           # lenses start in the pack
        elif cls == "ARMOR_CLASS" and it["slot"] not in kit:
            kit[it["slot"]] = idx
    kits[key] = kit

# ---- costume: what each role's own tile already wears (rh_costume[] in winandroid.c)
COSTUME = {"archeologist": ["fedora", "leather jacket"],
           "apothecary": ["alchemy smock", "high boots", "lenses"],
           "cave dweller": ["leather armor"], "knight": ["ring mail", "helmet"],
           "monk": ["robe"], "cleric": ["robe"], "rogue": ["leather armor"],
           "samurai": ["splint mail"], "tourist": ["Hawaiian shirt"],
           "wizard": ["cloak of magic resistance"]}
byname = {i["name"]: i["id"] for i in items if not i.get("held")}
costume = {k: [byname[n] for n in v] for k, v in COSTUME.items()}

scene = {k: OTHD[k] for k in ("floor of a room", "main walls horizontal", "main walls tlcorn",
                               "main walls trcorn", "main walls vertical", "staircase down")}
scene["kitten,female"] = MOND["kitten,female"]
json.dump(dict(palette=pal, bodies=bodies, items=items, kits=kits, costume=costume, scene=scene),
          open(OUT, "w"), separators=(",", ":"))
print(len(bodies), "bodies,", len(items), "items;", {k: len(v) for k, v in kits.items()})
print("valkyrie kit:", {s: next(i["name"] for i in items if i["id"] == v) for s, v in kits["valkyrie"].items()})
print("apothecary kit:", {s: next(i["name"] for i in items if i["id"] == v) for s, v in kits["apothecary"].items()})
