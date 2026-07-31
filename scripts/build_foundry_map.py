#!/usr/bin/env python3
"""
build_foundry_map.py — emit foundry-map.json, the lookup the character creator's
"Export to Foundry (arm5e)" uses to translate corpus entities into the arm5e
Foundry VTT system's internal codes.

These codes (ability keys, House codes, spell Range/Duration/Target short codes)
are arm5e-system enums, NOT corpus data, so they are sourced from the installed
arm5e system: module/config.js + lang/en.json. Point the script at the version
that matches the world you import into (default: the 3.0.1 "Stentorius" build the
Sjórseiðr world was exported from).

    python3 scripts/build_foundry_map.py
    python3 scripts/build_foundry_map.py "/path/to/arm5e/module/config.js" "/path/to/arm5e/lang/en.json"

Emits foundry-map.json into the repo (committed, so the site stays no-build).
Re-run if the arm5e system version changes.
"""
import json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "/home/hewhocutsdown/Working/Ars Magica/2026 Ars Magica/arm5e-3.0.1-Stentorius"
DEF_CFG = os.path.join(BASE, "module", "config.js")
DEF_EN = os.path.join(BASE, "lang", "en.json")

# --- stable enum tables (arm5e codes; small + rarely change) ---------------
TECH = {"Creo":"cr","Intellego":"in","Muto":"mu","Perdo":"pe","Rego":"re"}
FORM = {"Animal":"an","Aquam":"aq","Auram":"au","Corpus":"co","Herbam":"he",
        "Ignem":"ig","Imaginem":"im","Mentem":"me","Terram":"te","Vim":"vi"}
RANGES = {"Personal":"personal","Touch":"touch","Eye":"eye","Voice":"voice",
          "Sight":"sight","Arcane":"arc","Arcane Connection":"arc"}
DURATIONS = {"Momentary":"moment","Concentration":"conc","Diameter":"diam",
             "Sun":"sun","Ring":"ring","Moon":"moon","Year":"year"}
TARGETS = {"Individual":"ind","Circle":"circle","Part":"part","Group":"group",
           "Room":"room","Structure":"struct","Boundary":"bound","Taste":"taste",
           "Touch":"touch","Smell":"smell","Hearing":"hearing","Sight":"sight",
           "Vision":"sight"}
# corpus Virtue/Flaw Category -> arm5e VF `type`
VF_TYPE = {"Social Status":"social","General":"general","Hermetic":"hermetic",
           "Supernatural":"supernatural","Personality":"personality","Story":"story",
           "Heroic":"heroic"}
# corpus Size -> arm5e impact.value
VF_IMPACT = {"Minor":"minor","Major":"major","Free":"free"}

# Standard ArM5 default Characteristic per ability key (confirmed against the
# provided world exports where present; the rest are the core-book defaults).
DEFAULT_CHA = {
    "animalHandling":"com","areaLore":"int","athletics":"dex","awareness":"per",
    "bargain":"com","brawl":"dex","carouse":"sta","charm":"pre","chirurgy":"dex",
    "concentration":"sta","craft":"dex","etiquette":"com","folkKen":"per",
    "guile":"com","hunt":"per","intrigue":"com","knowledge":"int","leadership":"pre",
    "legerdemain":"dex","livingLanguage":"com","music":"com","organizationLore":"int",
    "profession":"com","ride":"dex","stealth":"qik","survival":"per","swim":"str",
    "teaching":"com",
    "artesLib":"int","law":"int","deadLanguage":"int","medicine":"int",
    "philosophy":"int","theology":"int","academicAbility":"int",
    "hermeticCode":"int","dominionLore":"int","faerieLore":"int","finesse":"per",
    "infernalLore":"int","magicLore":"int","magicTheory":"int","parma":"sta",
    "penetration":"sta","arcaneAbility":"int",
    "bows":"per","singleWeapon":"dex","greatWeapon":"str","trownWeapon":"dex",
    "martialAbility":"dex",
    "animalKen":"per","dowsing":"per","enchantingMusic":"com","entrancement":"pre",
    "magicSensitivity":"per","premonitions":"per","secondSight":"per",
    "senseHolyAndUnholy":"per","shapeshifter":"sta","supernatural":"int",
    "wildernessSense":"per",
}
# corpus ability name -> arm5e key, where normalized-label matching fails.
ABILITY_OVERRIDES = {
    "(Area) Lore":"areaLore", "Code of Hermes":"hermeticCode",
    "Order of Hermes Lore":"organizationLore", "Dead Language":"deadLanguage",
    "Thrown Weapon":"trownWeapon", "Great Weapon":"greatWeapon",
    "Artes Liberales":"artesLib", "Parma Magica":"parma",
    "Sense Holy and Unholy":"senseHolyAndUnholy",
    # parameterized families -> arm5e base key (the specific is carried in `option`)
    "Craft (Type)":"craft", "Craft Poppets":"craft", "Craft: Farrier":"craft",
    "Profession (Type)":"profession",
    "(Mystery Cult) Lore":"organizationLore", "House Bjornaer Lore (Arcane)":"organizationLore",
    "House Merinita Lore":"organizationLore", "Judaic Lore":"organizationLore",
    "Civil and Canon Law":"law", "Common Law":"law", "Islamic Law":"law", "Rabbinic Law":"law",
    "Theology: Christian":"theology", "Theology: Islam":"theology", "Theology: Judaism":"theology",
}
CATEGORY_ROOT = {  # config table -> en.json label root
    "GENERAL_ABILITIES":"general", "ACADEMIC_ABILITIES":"academic",
    "ARCANE_ABILITIES":"arcane", "MARTIAL_ABILITIES":"martial",
    "SUPERNATURAL_ABILITIES":"supernatural",
}


def norm(s):
    # Keep parenthesized words (corpus "(Area) Lore"); drop only the en.json
    # "{option}" placeholder and all punctuation.
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("{option}", ""))


def parse_config(cfg):
    src = open(cfg, encoding="utf-8").read()
    houses = {}
    m = re.search(r"houses\s*=\s*\{(.*?)\n\};", src, re.S)
    for code, label in re.findall(r'\n\s*"?([a-z\-]+)"?:\s*\{\s*label:\s*"([^"]+)"', m.group(1)):
        houses[label] = code
    abilities = {}  # key -> {category, option}
    for table, root in CATEGORY_ROOT.items():
        mm = re.search(r"ARM5E\." + table + r"\s*=\s*\{(.*?)\n\};", src, re.S)
        if not mm:
            continue
        body = mm.group(1)
        # split into per-key blocks at top-level (2-space-indented) keys
        keys = re.findall(r"\n  ([a-zA-Z][a-zA-Z0-9]*):\s*\{", body)
        opt = set(re.findall(r"\n  ([a-zA-Z][a-zA-Z0-9]*):\s*\{[^{}]*?option:\s*true", body, re.S))
        for key in keys:
            abilities[key] = {"category": root, "option": key in opt}
    return houses, abilities


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        p = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, p))
        else:
            out[p] = v
    return out


def main():
    cfg = sys.argv[1] if len(sys.argv) > 1 else DEF_CFG
    en_path = sys.argv[2] if len(sys.argv) > 2 else DEF_EN
    for p in (cfg, en_path):
        if not os.path.exists(p):
            sys.exit(f"not found: {p}")

    houses, abil_cfg = parse_config(cfg)
    en = flatten(json.load(open(en_path, encoding="utf-8")))
    # arm5e key -> display label (from arm5e.skill.<root>.<key>)
    key_label = {}
    for flatkey, label in en.items():
        m = re.match(r"arm5e\.skill\.(general|academic|arcane|martial|supernatural)\.([a-zA-Z0-9]+)$", flatkey)
        if m and m.group(2) in abil_cfg:
            key_label[m.group(2)] = label
    label_to_key = {norm(v): k for k, v in key_label.items()}

    # corpus abilities
    corpus = json.load(open(os.path.join(REPO, "chargen.json"), encoding="utf-8"))
    abilities_map = {}
    unmatched = []
    for a in corpus["abilities"]:
        name = a["name"]
        if name == "Ability":
            continue
        key = ABILITY_OVERRIDES.get(name) or label_to_key.get(norm(name))
        if not key and norm(name) in {norm(k) for k in abil_cfg}:
            key = next(k for k in abil_cfg if norm(k) == norm(name))
        if not key:
            unmatched.append(name)
            continue
        info = abil_cfg.get(key, {})
        abilities_map[name] = {"key": key, "category": info.get("category", "general"),
                               "option": info.get("option", False),
                               "defaultChaAb": DEFAULT_CHA.get(key, "int")}

    # houses: corpus "House Bonisagus" -> code via label "Bonisagus"
    house_map = {}
    for h in corpus["houses"]:
        label = h["name"].replace("House ", "").strip()
        if label in houses:
            house_map[h["name"]] = houses[label]

    out = {
        "meta": {"source": f"arm5e {os.path.basename(os.path.dirname(os.path.dirname(cfg)))}",
                 "note": "arm5e Foundry export codes. Regenerate with scripts/build_foundry_map.py."},
        "houses": house_map,
        "abilities": abilities_map,
        "techniques": TECH, "forms": FORM,
        "ranges": RANGES, "durations": DURATIONS, "targets": TARGETS,
        "vfType": VF_TYPE, "vfImpact": VF_IMPACT,
    }
    path = os.path.join(REPO, "foundry-map.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"wrote {path} ({os.path.getsize(path)/1024:.1f} KB)")
    print(f"  houses {len(house_map)} | abilities matched {len(abilities_map)} | "
          f"ranges {len(RANGES)} durations {len(DURATIONS)} targets {len(TARGETS)}")
    if unmatched:
        print(f"  UNMATCHED abilities ({len(unmatched)}): {', '.join(unmatched)}")


if __name__ == "__main__":
    main()
