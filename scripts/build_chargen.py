#!/usr/bin/env python3
"""
build_chargen.py — extract the data the character creator (chargen.html) needs
from the resolved Ars Magica (armdef) DSL corpus.

Like build_rules.py, this slices the ~10.5 MB resolved corpus down to compact,
runtime-fetchable JSON so the site stays no-build and corpus-driven (never
hard-coding rules text). It writes two files into the repo:

  chargen.json         characteristics + cost table, houses, arts, virtues,
                       flaws, abilities, verbatim creation-rule passages, and
                       the RAW point/XP budgets.
  chargen-spells.json  the core spells (Technique/Form/level/RDT/ritual + text),
                       lazy-loaded only when the spell step opens.

Re-run after any corpus update:

    python3 scripts/build_chargen.py
    python3 scripts/build_chargen.py "/path/to/armdef-0.5-full.resolved.json"

Verbatim rule: extracted DESCRIPTION text is reproduced exactly (only whitespace
preserved). The numeric budgets below are transcribed from the corpus entity
"Detailed Character Creation" (also shipped verbatim in chargen.json so the UI
shows the actual rule alongside the machine-readable numbers).
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CORPUS = ("/home/hewhocutsdown/Working/Titterpig Utilities/"
                  "titterpig-corpora/armdef/0.5/armdef-0.5-full.resolved.json")

# Characteristic name -> the key magi.json uses in its `characteristics` object.
CHAR_KEYS = {
    "Intelligence": "int", "Perception": "per", "Strength": "str",
    "Stamina": "sta", "Communication": "com", "Dexterity": "dex",
    "Quickness": "qik",
    # Presence has no standalone Characteristic entity in core (it pairs with
    # Communication for social rolls); magi.json still carries a `pre` slot.
}
# Art name -> magi.json arts key.
ART_KEYS = {
    "Creo": "cr", "Intellego": "in", "Muto": "mu", "Perdo": "pe", "Rego": "re",
    "Animal": "an", "Aquam": "aq", "Auram": "au", "Corpus": "co", "Herbam": "he",
    "Ignem": "ig", "Imaginem": "im", "Mentem": "me", "Terram": "te", "Vim": "vi",
}

# Verbatim from the corpus entity "Detailed Character Creation" (also shipped in
# chargen.json under creationRules so the UI displays the rule text itself).
BUDGETS = {
    "source": "armdef-0.5-core-character-creation",
    "characteristicPoints": 7,
    "characteristicCostNote": "pyramid: a score of +/-n costs/returns n(n+1)/2 points",
    "virtueFlaw": {
        "minorPoints": 1,
        "majorPoints": 3,
        "magiCompanion": {"maxFlawPoints": 10, "virtuesMatchFlaws": True},
        "grog": {"maxMinorFlaws": 3, "maxMinorVirtues": 3, "majorsAllowed": False},
    },
    "earlyChildhood": {
        "nativeLanguageXp": 75,
        "nativeLanguageScore": 5,
        "spreadXp": 45,
        "childhoodAbilities": [
            "(Area) Lore", "Athletics", "Awareness", "Brawl", "Charm",
            "Folk Ken", "Guile", "Living Language", "Stealth", "Survival", "Swim",
        ],
    },
    "laterLifeXpPerYear": {"normal": 15, "wealthy": 20, "poor": 10},
    "apprenticeship": {"xp": 240, "spellLevels": 120,
                       "spellLevelCap": "Technique + Form + Intelligence + Magic Theory + 3"},
    "postApprenticeshipPerYear": 30,
    "confidence": {"score": 1, "points": 3},
}

# Castable spell parameters for guideline-based design: code -> (label, magnitude).
# Magnitudes are RAW (matching ARM5E.magic.{ranges,durations,targets}.impact).
SPELL_RANGES = [("personal", "Personal", 0), ("touch", "Touch", 1), ("eye", "Eye", 1),
                ("voice", "Voice", 2), ("sight", "Sight", 3), ("arc", "Arcane Connection", 4)]
SPELL_DURATIONS = [("moment", "Momentary", 0), ("conc", "Concentration", 1),
                   ("diam", "Diameter", 1), ("sun", "Sun", 2), ("ring", "Ring", 2),
                   ("moon", "Moon", 3), ("year", "Year", 4)]
SPELL_TARGETS = [("ind", "Individual", 0), ("circle", "Circle", 0), ("part", "Part", 1),
                 ("group", "Group", 2), ("room", "Room", 2), ("struct", "Structure", 3),
                 ("bound", "Boundary", 4), ("taste", "Taste", 0), ("touch", "Touch", 1),
                 ("smell", "Smell", 2), ("hearing", "Hearing", 3), ("sight", "Vision", 4)]

CREATION_RULE_ENTITIES = {
    "detailedCharacterCreation": "Detailed Character Creation",
    "characteristicBuying": "Characteristic Buying",
    "personality": "Personality at Creation",
    "reputations": "Reputations at Creation",
    "confidence": "Confidence at Creation",
    "equipment": "Equipment at Creation",
}


def desc(entity):
    for b in entity.get("blocks", []) or []:
        if b.get("keyword") == "DESCRIPTION":
            return b.get("value") or ""
    return ""


def prop(entity, name):
    for p in entity.get("properties", []) or []:
        if isinstance(p, dict) and p.get("name") == name:
            return p.get("value")
    return None


def cite(entity):
    srcs = entity.get("sources") or []
    if not srcs:
        return None
    return srcs[0][:-6] if srcs[0].endswith(".ttrpg") else srcs[0]


def char_cost_table(max_abs=3):
    """Pyramid buying table: score n -> point cost (negative scores return points)."""
    rows = []
    for n in range(-max_abs, max_abs + 1):
        cost = (abs(n) * (abs(n) + 1)) // 2
        rows.append({"score": n, "points": cost if n >= 0 else -cost})
    return rows


def main():
    corpus_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CORPUS
    if not os.path.exists(corpus_path):
        sys.exit(f"corpus not found: {corpus_path}")

    corpus = json.load(open(corpus_path, encoding="utf-8"))
    ents = corpus.get("entities", [])
    by_name = {}
    for e in ents:
        by_name.setdefault(e["name"], e)

    def ext(e):
        return e.get("extends") or ""

    # Characteristics (order matches magi.json fields; Presence appended as a
    # slot with no core Characteristic entity).
    char_order = ["Intelligence", "Perception", "Strength", "Stamina",
                  "Communication", "Presence", "Dexterity", "Quickness"]
    pres_keys = {"Presence": "pre"}
    characteristics = []
    for name in char_order:
        e = by_name.get(name)
        characteristics.append({
            "name": name,
            "key": CHAR_KEYS.get(name) or pres_keys.get(name),
            "text": desc(e) if e else "",
            "source": cite(e) if e else None,
        })

    houses = []
    for e in ents:
        if ext(e) == "Hermetic House":
            houses.append({
                "name": e["name"],
                "houseType": prop(e, "House Type"),
                "prima": prop(e, "Prima"),
                "domusMagna": prop(e, "Domus Magna"),
                "benefit": prop(e, "Benefit"),
                "freeVirtue": prop(e, "Free Virtue"),
                "text": desc(e),
                "source": cite(e),
            })
    houses.sort(key=lambda h: h["name"])

    techniques, forms = [], []
    for e in ents:
        if ext(e) == "Hermetic Technique":
            techniques.append({"name": e["name"], "key": ART_KEYS.get(e["name"]),
                               "text": desc(e), "source": cite(e)})
        elif ext(e) == "Hermetic Form":
            forms.append({"name": e["name"], "key": ART_KEYS.get(e["name"]),
                          "text": desc(e), "source": cite(e)})

    def parse_list(val):
        if not val:
            return []
        try:
            v = json.loads(val)
            return v if isinstance(v, list) else [val]
        except Exception:
            return [val]

    virtues, flaws = [], []
    for e in ents:
        kind = ext(e)
        if kind == "Virtue":
            virtues.append({"name": e["name"], "size": prop(e, "Size"),
                            "category": prop(e, "Category"), "text": desc(e),
                            "source": cite(e)})
        elif kind == "Flaw":
            flaws.append({"name": e["name"], "size": prop(e, "Size"),
                          "category": prop(e, "Category"), "text": desc(e),
                          "source": cite(e)})
    virtues.sort(key=lambda x: x["name"])
    flaws.sort(key=lambda x: x["name"])

    abilities = []
    for e in ents:
        if ext(e) == "Ability":
            abilities.append({
                "name": e["name"],
                "abilityType": prop(e, "Ability Type"),
                "specialties": parse_list(prop(e, "Specialties")),
                "cannotUseUntrained": prop(e, "Cannot Use Untrained"),
                "text": desc(e),
                "source": cite(e),
            })
    abilities.sort(key=lambda x: x["name"])

    creation_rules = {}
    for key, ename in CREATION_RULE_ENTITIES.items():
        e = by_name.get(ename)
        if e:
            creation_rules[key] = {"name": ename, "text": desc(e), "source": cite(e)}
        else:
            sys.stderr.write(f"WARNING: creation-rule entity missing: {ename!r}\n")

    # Spells -> separate file (lazy-loaded at the spell step). Only true
    # Formulaic Spells (starting spells are formulaic) — this excludes spell
    # *guidelines*, guideline sets, enchanted devices, and hedge spells that
    # also carry Technique/Form props.
    spells = []
    for e in ents:
        if ext(e) != "Formulaic Spell":
            continue
        te, fo = prop(e, "Technique"), prop(e, "Form")
        if te and fo:
            spells.append({
                "name": e["name"],
                "technique": te, "form": fo,
                "level": prop(e, "Level"),
                "generalLevel": bool(prop(e, "General Level")),
                "range": prop(e, "Range"), "duration": prop(e, "Duration"),
                "target": prop(e, "Target"), "requisite": prop(e, "Requisite"),
                "ritual": bool(prop(e, "Ritual")),
                "text": desc(e), "source": cite(e),
            })
    spells.sort(key=lambda s: (s["technique"], s["form"],
                               int(s["level"]) if str(s["level"]).isdigit() else 0,
                               s["name"]))

    # Spell design guidelines from the "<Te> <Fo> Guidelines" entities' GUIDELINES blocks.
    import re as _re
    guidelines = []
    for e in ents:
        if not e["name"].endswith(" Guidelines"):
            continue
        te, fo = prop(e, "Technique"), prop(e, "Form")
        gb = next((b for b in e.get("blocks", []) if b.get("keyword") == "GUIDELINES"), None)
        if not (te and fo and gb):
            continue
        for row in gb.get("rows", []):
            label = row.get("label", "")
            cells = row.get("cells", [])
            effect = (cells[0].get("value") if cells else "") or ""
            m = _re.match(r"Level\s+(\d+)", label)
            level = int(m.group(1)) if m else ("General" if "general" in label.lower() else label)
            guidelines.append({"technique": te, "form": fo, "level": level, "effect": effect})

    def param_rows(rows):
        return [{"code": c, "label": lab, "magnitude": mag} for c, lab, mag in rows]

    meta = {
        "edition": corpus.get("edition"),
        "spec_version": corpus.get("spec_version"),
        "generated_from": os.path.basename(corpus_path),
        "note": ("Character-creation data sliced from the resolved armdef corpus "
                 "for chargen.html. Regenerate with scripts/build_chargen.py after "
                 "a corpus update."),
    }

    chargen = {
        "meta": meta,
        "budgets": BUDGETS,
        "characteristicCost": char_cost_table(3),
        "characteristics": characteristics,
        "houses": houses,
        "arts": {"techniques": techniques, "forms": forms},
        "virtues": virtues,
        "flaws": flaws,
        "abilities": abilities,
        "creationRules": creation_rules,
        "spellsFile": "chargen-spells.json",
        "spellCount": len(spells),
        "guidelines": guidelines,
        "spellParams": {"ranges": param_rows(SPELL_RANGES),
                        "durations": param_rows(SPELL_DURATIONS),
                        "targets": param_rows(SPELL_TARGETS)},
    }
    chargen_spells = {"meta": meta, "spells": spells}

    out_main = os.path.join(REPO, "chargen.json")
    out_spells = os.path.join(REPO, "chargen-spells.json")
    with open(out_main, "w", encoding="utf-8") as f:
        json.dump(chargen, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(out_spells, "w", encoding="utf-8") as f:
        json.dump(chargen_spells, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"wrote {out_main}  ({os.path.getsize(out_main)/1024:.1f} KB)")
    print(f"  edition {meta['edition']} spec {meta['spec_version']}")
    print(f"  characteristics {len(characteristics)} | houses {len(houses)} | "
          f"arts {len(techniques)}+{len(forms)}")
    print(f"  virtues {len(virtues)} | flaws {len(flaws)} | abilities {len(abilities)}")
    print(f"  creation-rule passages {len(creation_rules)}/{len(CREATION_RULE_ENTITIES)}")
    print(f"  spell guidelines {len(guidelines)} rows across "
          f"{len(set((g['technique'],g['form']) for g in guidelines))} Te/Fo tables")
    print(f"wrote {out_spells}  ({os.path.getsize(out_spells)/1024:.1f} KB) | "
          f"spells {len(spells)}")


if __name__ == "__main__":
    main()
