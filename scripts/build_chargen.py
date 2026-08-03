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


import re as _re_desc

# Parenthetical cross-references and page citations that clutter the player-facing
# chargen descriptions: "(see Faith & Flame, page 67)", "(see page 233)", "(page 85)",
# "(pages 29 and 64)". These are editorial pointers, not rules text. We strip ONLY
# these parentheticals and tidy the surrounding whitespace — pronunciations like
# "(BOH-neeSAH-goos)" or "(KWAEsee-tor)" don't start with see/page/chapter, so they
# are preserved. The verbatim source remains untouched in the corpus; this cleans
# only the chargen slice. (Owner request, 2026-08-02.)
_REF_PARENS = _re_desc.compile(
    r"\s*\((?:see|See)\b[^)]*\)|\s*\((?:pages?|Chapters?|chapters?)\b[^)]*\)")
# Inline (non-parenthetical) cross-reference clauses, e.g.
# "…, described in Guardians of the Forests, page 92" — drop the whole clause.
_REF_INLINE = _re_desc.compile(
    r",?\s*(?:as\s+)?described in [^.]+?,\s*pages?\s+\d+(?:\s+and\s+\d+)?", _re_desc.I)


def clean_desc(s):
    """Strip page/cross-book reference clutter from a player-facing description."""
    if not s:
        return s
    t = _REF_PARENS.sub("", s)
    t = _REF_INLINE.sub("", t)
    t = _re_desc.sub(r"\s+([,.;:])", r"\1", t)   # no space left before punctuation
    t = _re_desc.sub(r"[ \t]{2,}", " ", t)        # collapse doubled spaces
    return t.strip()


def prop(entity, name):
    for p in entity.get("properties", []) or []:
        if isinstance(p, dict) and p.get("name") == name:
            return p.get("value")
    return None


def prop_obj(entity, name):
    """Full property dict (for reading `nested` lists, e.g. Characteristics/Arts)."""
    for p in entity.get("properties", []) or []:
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def cell(row, key):
    """Value of a keyed cell in a table row; falls back to the first bare cell."""
    cells = row.get("cells", []) or []
    for c in cells:
        if c.get("key") == key:
            return c.get("value")
    return None


def _int(v, default=None):
    try:
        return int(str(v).replace("+", "").strip())
    except (TypeError, ValueError):
        return default


import re as _re_tpl


def parse_caret_list(val):
    """Parse a Virtue/Flaw LIST value like
    `[^"The Gift", ^"Greater Immunity"("Fire"), ^"Affinity with Art"(^"Creo")]`
    into [{name, detail?|size?}]. A parenthesized Minor/Major/Free is a Size
    qualifier; anything else is the parameter/detail."""
    out = []
    if not val:
        return out
    for m in _re_tpl.finditer(r'\^"([^"]+)"(?:\(\s*\^?"([^"]+)"\s*\))?', val):
        item = {"name": m.group(1)}
        arg = m.group(2)
        if arg:
            if arg in ("Minor", "Major", "Free"):
                item["size"] = arg
            else:
                item["detail"] = arg
        out.append(item)
    return out


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


# --- Magic Character flat-prose statblock parsers (RoP:Magic) ----------------
# The 48 Magic Characters are authored as prose strings, not structured fields.
# These parsers were validated byte-for-byte against the source (Arkliss pilot)
# and across all 32 loadable beings (0 power-parse failures) before use.
_CHAR_ABBR = {"Int": "int", "Per": "per", "Pre": "pre", "Com": "com",
              "Str": "str", "Sta": "sta", "Dex": "dex", "Qik": "qik"}
_POWER_HDR = _re_tpl.compile(
    r"([A-Z][\w'’ \-]{1,45}?),\s*"
    r"((?:[\d–\-]+\s*|variable\s*)points?|constant),\s*"
    r"(Init\s*[^,]+?|constant|[+\-–]?\d+),\s*"
    r"([A-Z][a-z]+(?:\s+or\s+[A-Z][a-z]+\.?)?)")


def _paren_split(s, seps=";,"):
    out, buf, depth = [], [], 0
    for ch in s or "":
        if ch == "(":
            depth += 1; buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1); buf.append(ch)
        elif ch in seps and depth == 0:
            out.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return [x for x in out if x]


def _endash(s):
    return (s or "").replace("–", "-").replace("—", "-")


def parse_chars_prose(s):
    out = {}
    for seg in _endash(s).split(","):
        m = _re_tpl.match(r"\s*([A-Za-z]{3})\s*([+\-]?\d+)", seg)
        if m and m.group(1) in _CHAR_ABBR:
            out[_CHAR_ABBR[m.group(1)]] = int(m.group(2))
    return out


def parse_might_prose(s):
    m = _re_tpl.match(r"\s*(\d+)\s*(?:\(([^)]+)\))?", _endash(s))
    return (int(m.group(1)) if m else None, (m.group(2).strip() if m and m.group(2) else None))


def parse_abilities_prose(s):
    out = []
    for seg in _paren_split(_endash(s), ","):
        m = _re_tpl.match(r"^(.*?)\s+(\d+)\s*(?:\(([^)]*)\))?$", seg.strip())
        if m:
            out.append({"name": m.group(1).strip(), "score": int(m.group(2)),
                        "specialty": (m.group(3) or "").strip()})
    return out


def parse_personality_prose(s):
    out = []
    for seg in _endash(s).split(","):
        m = _re_tpl.match(r"\s*(.+?)\*?\s*([+\-]\d+)\s*$", seg.strip())
        if m:
            out.append({"name": m.group(1).strip().rstrip("*").strip(), "score": int(m.group(2))})
    return out


def parse_named_list_prose(s):
    out = []
    for tok in _paren_split(s or "", ";,"):
        mult, param = 1, None
        mm = _re_tpl.search(r"\(x(\d+)\)", tok)
        if mm:
            mult = int(mm.group(1)); tok = tok.replace(mm.group(0), "").strip()
        pm = _re_tpl.search(r"\(([^)]*)\)\s*$", tok)
        if pm:
            param = pm.group(1).strip(); tok = tok[:pm.start()].strip()
        if tok.strip():
            out.append({"name": tok.strip(), "count": mult, "param": param})
    return out


def parse_powers_prose(s):
    s = s or ""
    hdrs = list(_POWER_HDR.finditer(s))
    out = []
    for i, h in enumerate(hdrs):
        end = hdrs[i + 1].start() if i + 1 < len(hdrs) else len(s)
        rest = s[h.end():end]
        rdt = _re_tpl.match(r"\s*R:\s*([^,]+?),\s*D:\s*([^,]+?),\s*T:\s*(\w+)", rest)
        text = rest[rdt.end():].strip() if rdt else rest.strip().lstrip(":").strip()
        out.append({"name": h.group(1).strip(), "cost": h.group(2).strip(),
                    "initiative": h.group(3).strip(), "form": h.group(4).strip(),
                    "range": rdt.group(1).strip() if rdt else "",
                    "duration": rdt.group(2).strip() if rdt else "",
                    "target": rdt.group(3).strip() if rdt else "", "text": text})
    return out


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
                "benefit": clean_desc(prop(e, "Benefit")),
                "freeVirtue": prop(e, "Free Virtue"),
                # Structured free-Virtue options + how they apply: Fixed (grant the
                # one), Choice (pick one), Open (pick a qualifier per Benefit), or
                # Package (grant all — one example tradition, e.g. Ex Miscellanea).
                "freeVirtueOptions": parse_caret_list(prop(e, "Free Virtue")),
                # Houses that don't override the base ENUM report its options list
                # (as a "[...]" string); only a real singular value is a mode.
                "freeVirtueMode": (prop(e, "Free Virtue Mode")
                                   if prop(e, "Free Virtue Mode")
                                   in ("Fixed", "Choice", "Open", "Package")
                                   else "Fixed"),
                "text": clean_desc(desc(e)),
                "source": cite(e),
            })
    houses.sort(key=lambda h: h["name"])

    techniques, forms = [], []
    for e in ents:
        if ext(e) == "Hermetic Technique":
            techniques.append({"name": e["name"], "key": ART_KEYS.get(e["name"]),
                               "text": clean_desc(desc(e)), "source": cite(e)})
        elif ext(e) == "Hermetic Form":
            forms.append({"name": e["name"], "key": ART_KEYS.get(e["name"]),
                          "text": clean_desc(desc(e)), "source": cite(e)})

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
                            "category": prop(e, "Category"), "text": clean_desc(desc(e)),
                            "source": cite(e)})
        elif kind == "Flaw":
            flaws.append({"name": e["name"], "size": prop(e, "Size"),
                          "category": prop(e, "Category"), "text": clean_desc(desc(e)),
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
                "text": clean_desc(desc(e)),
                "source": cite(e),
            })
    abilities.sort(key=lambda x: x["name"])

    # Training packages (Grogs): partial templates that pre-allocate XP without
    # building a whole character. DURATIONS.text lists the duration options; each
    # nested YEARS block carries the per-ability XP grants for that duration.
    TRAINING_EXTENDS = {"Career Training Package": "Career",
                        "Non-Career Training Package": "Non-Career",
                        "Childhood Training Package": "Childhood"}
    training = []
    for e in ents:
        cat = TRAINING_EXTENDS.get(ext(e))
        if not cat:
            continue
        db = next((b for b in e.get("blocks", []) if b.get("keyword") == "DURATIONS"), None)
        if not db:
            continue
        labels = db.get("text") or []
        yblocks = [b for b in db.get("blocks", []) if b.get("keyword") == "YEARS"]
        durations = []
        for i, yb in enumerate(yblocks):
            label = labels[i] if i < len(labels) else (yb.get("label") or "").split(" PRINTED")[0]
            grants = []
            for row in yb.get("rows", []):
                cells = row.get("cells", []) or []
                xpv = next((c.get("value") for c in cells if c.get("key") == "XP"), None)
                if xpv is None:
                    continue
                grants.append({"ability": row.get("label", ""),
                               "xp": int(xpv) if str(xpv).lstrip("-").isdigit() else xpv})
            durations.append({"label": label, "grants": grants})
        training.append({
            "name": e["name"], "category": cat,
            "source": prop(e, "Source"), "page": prop(e, "Page"),
            "abilityTypes": parse_list(prop(e, "Ability Types")),
            "durations": durations, "description": desc(e),
        })
    training.sort(key=lambda x: (x["category"], x["name"]))

    # Full character templates (kind "template" — Grog/Companion/Magus). These
    # pre-build a whole character: characteristics, V/F (with parameters), abilities
    # (as SCORE, converted to XP in the UI), personality, equipment, and — for magi —
    # House, Hermetic Arts, and spells. Covenant templates are excluded (not PCs).
    TEMPLATE_TYPE = {"Grog": "grog", "Companion": "companion", "Magus": "magus"}
    pres_key = {"Presence": "pre"}
    templates = []
    for e in ents:
        if e.get("kind") != "template":
            continue
        ttype = TEMPLATE_TYPE.get(ext(e))
        if not ttype:
            continue
        chars = {}
        cp = prop_obj(e, "Characteristics")
        if cp:
            for n in cp.get("nested", []) or []:
                k = CHAR_KEYS.get(n.get("name")) or pres_key.get(n.get("name"))
                if k:
                    chars[k] = _int(n.get("value"), 0)
        arts = None
        ap = prop_obj(e, "Hermetic Arts")
        if ap and ap.get("nested"):
            arts = {n.get("name"): _int(n.get("value"), 0) for n in ap["nested"]}
        abils, spells, ptraits, choices = [], [], [], ""
        for b in e.get("blocks", []) or []:
            kw = b.get("keyword")
            if kw == "ABILITIES":
                for r in b.get("rows", []) or []:
                    abils.append({"name": r.get("label", ""),
                                  "score": _int(cell(r, "SCORE"), 0),
                                  "specialty": cell(r, "SPECIALTY") or ""})
            elif kw == "PERSONALITY_TRAITS":
                for r in b.get("rows", []) or []:
                    cells = r.get("cells", []) or []
                    ptraits.append({"name": r.get("label", ""),
                                    "score": _int(cells[0].get("value"), 0) if cells else 0})
            elif kw == "SPELLS_KNOWN":
                for r in b.get("rows", []) or []:
                    spells.append({"technique": cell(r, "TECHNIQUE") or "",
                                   "form": cell(r, "FORM") or "",
                                   "level": _int(cell(r, "LEVEL"), 0)})
            elif kw == "CHOICES":
                choices = " ".join(b.get("text") or [])
        fv = parse_caret_list(prop(e, "Free Virtue"))
        templates.append({
            "name": e["name"], "type": ttype, "source": prop(e, "Source"),
            "description": desc(e) or (prop(e, "Description") or ""),
            "characteristics": chars,
            "size": _int(prop(e, "Size")), "age": _int(prop(e, "Age")),
            "apparentAge": _int(prop(e, "Apparent Age")),
            "decrepitude": _int(prop(e, "Decrepitude")),
            "warpingScore": _int(prop(e, "Warping Score")),
            "virtues": parse_caret_list(prop(e, "Virtues")),
            "flaws": parse_caret_list(prop(e, "Flaws")),
            "freeVirtue": fv[0] if fv else None,
            "equipment": parse_list(prop(e, "Equipment")),
            "abilities": abils, "personalityTraits": ptraits,
            "arts": arts, "spells": spells or None,
            "house": ("House " + e["name"]) if ttype == "magus" else None,
            "sigil": prop(e, "Wizard's Sigil"),
            "confidenceScore": _int(prop(e, "Confidence Score")),
            "confidencePoints": _int(prop(e, "Confidence Points")),
            "choices": choices,
        })
    templates.sort(key=lambda x: (x["type"], x["name"]))

    # Realm toolkits — the building blocks for Magic/Faerie characters (the realm
    # modifier). All present in the corpus, verbatim descriptions preserved.
    def toolkit(ext, extra):
        out = []
        for te in ents:
            if te.get("extends") != ext:
                continue
            row = {"name": te["name"], "text": desc(te), "source": prop(te, "Source")}
            for src_prop, key in extra.items():
                row[key] = prop(te, src_prop)
            out.append(row)
        out.sort(key=lambda x: x["name"])
        return out

    realm_toolkits = {
        "magic": {
            "qualities": toolkit("Magic Quality", {"Magnitude": "magnitude"}),
            "inferiorities": toolkit("Magic Inferiority", {"Magnitude": "magnitude"}),
            "powers": toolkit("Common Magic Power", {"Page": "page"}),
        },
        "faerie": {
            "powers": toolkit("Faerie Power", {"Group": "group", "Might Cost": "mightCost",
                                               "Might Cost Value": "mightCostValue",
                                               "Initiative": "initiative", "Form": "form"}),
            "wizardry": toolkit("Faerie Wizardry", {"Section": "section"}),
            "blood": toolkit("Faerie Blood", {"Stock": "stock", "RoP Faerie Note": "note"}),
        },
    }
    # Faerie point-buy budget — the structured "Faerie Character Creation" entity
    # (RoP:Faerie Ch3; added to the corpus so the numbers are read, not re-parsed).
    fc = by_name.get("Faerie Character Creation")
    if fc:
        realm_toolkits["faerie"]["creation"] = {
            "startingMight": _int(prop(fc, "Starting Might")),
            "characteristicPoints": _int(prop(fc, "Characteristic Points")),
            "pretensePointsPerYear": _int(prop(fc, "Pretense Points Per Year")),
            "pretenseReferenceAge": _int(prop(fc, "Pretense Reference Age")),
            "pretensePointsBase": _int(prop(fc, "Pretense Points Base")),
            "defaultMagusAge": _int(prop(fc, "Default Magus Age")),
            "defaultPretensePoints": _int(prop(fc, "Default Pretense Points")),
            "companionVirtuePoints": _int(prop(fc, "Companion Virtue Points")),
            "magusFreeVirtues": _int(prop(fc, "Magus Free Virtues")),
            "magusVirtuePoints": _int(prop(fc, "Magus Virtue Points")),
            "magusVirtuesPerFlaw": _int(prop(fc, "Magus Virtues Per Flaw")),
            "text": desc(fc), "source": prop(fc, "Source"), "page": _int(prop(fc, "Page")),
        }

    # Pre-defined beings (Creature entities) — realm-tagged statblocks used by the
    # realm "load a defined being" pickers. Fully structured: characteristics, V&F,
    # abilities, combat, personality, and powers (each a nested DEF with Cost/Init/Form).
    creatures = []
    for ce in ents:
        if ce.get("extends") != "Creature":
            continue
        chars = {}
        cp = prop_obj(ce, "Characteristics")
        if cp:
            for n in cp.get("nested", []) or []:
                k = CHAR_KEYS.get(n.get("name")) or pres_key.get(n.get("name"))
                if k:
                    chars[k] = _int(n.get("value"), 0)
        abils, ptraits, powers, combat = [], [], [], []
        for b in ce.get("blocks", []) or []:
            kw = b.get("keyword")
            if kw == "ABILITIES":
                for r in b.get("rows", []) or []:
                    abils.append({"name": r.get("label", ""), "score": _int(cell(r, "SCORE"), 0),
                                  "specialty": cell(r, "SPECIALTY") or ""})
            elif kw == "PERSONALITY_TRAITS":
                for r in b.get("rows", []) or []:
                    cells = r.get("cells", []) or []
                    ptraits.append({"name": r.get("label", ""),
                                    "score": _int(cells[0].get("value"), 0) if cells else 0})
            elif kw == "COMBAT":
                for r in b.get("rows", []) or []:
                    combat.append({"label": r.get("label", ""),
                                   "cells": [{"key": c.get("key"), "value": c.get("value")} for c in (r.get("cells") or [])]})
            elif kw == "POWERS":
                for pe in b.get("entities", []) or []:
                    pdesc = next((pb.get("value") for pb in pe.get("blocks", []) if pb.get("keyword") == "DESCRIPTION"), "")
                    powers.append({"name": pe.get("name", ""), "cost": prop(pe, "Cost"),
                                   "initiative": prop(pe, "Initiative"), "form": prop(pe, "Form"),
                                   "text": pdesc or ""})
        creatures.append({
            "name": ce["name"], "realm": prop(ce, "Might Realm"), "form": prop(ce, "Form"),
            "might": _int(prop(ce, "Might")), "size": _int(prop(ce, "Size")),
            "characteristics": chars, "virtuesFlaws": parse_list(prop(ce, "Virtues and Flaws")),
            "abilities": abils, "personalityTraits": ptraits, "combat": combat, "powers": powers,
            "soak": prop(ce, "Soak"), "fatigueLevels": prop(ce, "Fatigue Levels"),
            "woundPenalties": prop(ce, "Wound Penalties"), "vis": prop(ce, "Vis"),
            "appearance": prop(ce, "Appearance"),
            "description": next((b.get("value") for b in ce.get("blocks", []) if b.get("keyword") == "DESCRIPTION"), "") or "",
            "source": prop(ce, "Source"),
        })
    creatures.sort(key=lambda x: (str(x["realm"]), x["name"]))

    # Magic Characters (RoP:Magic) — flat-prose statblocks parsed into structured
    # fields for the Magic realm loader. Guides/lineage/design entries are excluded.
    quality_names = {e["name"] for e in ents if ext(e) == "Magic Quality"}
    inferiority_names = {e["name"] for e in ents if ext(e) == "Magic Inferiority"}
    _guide_re = _re_tpl.compile(r"Character Guide|Character Guides|Designing|Lineage", _re_tpl.I)
    magic_beings = []
    for me in ents:
        if ext(me) != "Magic Character":
            continue
        if prop(me, "Shape") != "character" or _guide_re.search(me["name"]):
            continue
        might, form = parse_might_prose(prop(me, "Magic Might") or prop(me, "Magical Might"))
        quals, infs = [], []
        for it in parse_named_list_prose(prop(me, "Magical Qualities and Inferiorities")
                                         or prop(me, "Magic Qualities and Inferiorities")
                                         or prop(me, "Qualities and Inferiorities")):
            (infs if it["name"] in inferiority_names and it["name"] not in quality_names else quals).append(it)
        magic_beings.append({
            "name": me["name"], "might": might, "form": form,
            "size": _int(prop(me, "Size")), "season": prop(me, "Season"),
            "characteristics": parse_chars_prose(prop(me, "Characteristics")),
            "abilities": parse_abilities_prose(prop(me, "Abilities")),
            "personalityTraits": parse_personality_prose(prop(me, "Personality Trait")),
            "virtuesFlaws": parse_named_list_prose(prop(me, "Virtues and Flaws")),
            "qualities": quals, "inferiorities": infs,
            "powers": parse_powers_prose(prop(me, "Powers")),
            "combat": prop(me, "Combat"), "soak": prop(me, "Soak"), "vis": prop(me, "Vis"),
            "confidence": prop(me, "Confidence Score"), "reputations": prop(me, "Reputations"),
            "appearance": prop(me, "Appearance"),
            "description": next((b.get("value") for b in me.get("blocks", []) if b.get("keyword") == "DESCRIPTION"), "") or "",
            "source": prop(me, "Source"),
        })
    magic_beings.sort(key=lambda x: x["name"])

    # Apprentices — young-character creation (Ch2): the budget entity, the Aging
    # Chart (age -> Characteristic/Size modifiers), Child Virtues/Flaws, and the
    # young-character example statblocks (flat prose, parsed for the loader).
    yc_ent = by_name.get("Young Character Creation")
    young_creation = None
    if yc_ent:
        _keys = [("Characteristic Points", "characteristicPoints"), ("XP Per Year", "xpPerYear"),
                 ("XP Per Year Wealthy", "xpPerYearWealthy"), ("XP Per Year Poor", "xpPerYearPoor"),
                 ("XP Start Age", "xpStartAge"), ("Ability Max Score", "abilityMaxScore"),
                 ("Grog Virtue Flaw Points", "grogVFPoints"), ("Companion Virtue Flaw Points", "companionVFPoints"),
                 ("Child Virtue Flaw Max Age", "childVFMaxAge"), ("Apprenticeship Years", "apprenticeshipYears"),
                 ("Apprenticeship XP", "apprenticeshipXP"), ("Apprenticeship Spell Levels", "apprenticeshipSpellLevels"),
                 ("Apprenticeship XP Per Year Early", "apprenticeshipXPPerYearEarly"),
                 ("Apprenticeship XP Per Year Late", "apprenticeshipXPPerYearLate")]
        young_creation = {k2: _int(prop(yc_ent, k1)) for k1, k2 in _keys}
        young_creation.update({"transitionAges": prop(yc_ent, "Transition Ages"), "text": desc(yc_ent),
                               "source": prop(yc_ent, "Source"), "page": _int(prop(yc_ent, "Page"))})

    def _age_range(lbl):
        nums = _re_tpl.findall(r"\d+", lbl or "")
        if "<" in (lbl or ""):
            return (0, 0)
        if "+" in (lbl or ""):
            return (int(nums[0]), 999) if nums else (0, 999)
        if len(nums) >= 2:
            return (int(nums[0]), int(nums[1]))
        return (int(nums[0]), int(nums[0])) if nums else (0, 0)
    aging_chart = []
    ac = by_name.get("Aging Chart")
    if ac:
        tb = next((b for b in ac.get("blocks", []) if b.get("keyword") == "TABLE"), None)
        for row in (tb.get("rows", []) if tb else []):
            age = row.get("label")
            cells = [c.get("value") for c in row.get("cells", []) or []]
            if age and len(cells) >= 2:
                lo, hi = _age_range(age)
                aging_chart.append({"age": age, "ageMin": lo, "ageMax": hi,
                                    "charMod": _int(_endash(cells[0])), "sizeMod": _int(_endash(cells[1]))})

    def _child_vf(ext_name):
        out = [{"name": x["name"], "size": prop(x, "Size"), "category": prop(x, "Category"),
                "text": desc(x), "source": prop(x, "Source")} for x in ents if ext(x) == ext_name]
        out.sort(key=lambda z: z["name"])
        return out
    child_virtues, child_flaws = _child_vf("Child Virtue"), _child_vf("Child Flaw")

    young_characters = []
    for ye in ents:
        if ext(ye) != "Example Character" or prop(ye, "Source") != "Apprentices":
            continue
        ap = prop(ye, "Age")
        young_characters.append({
            "name": ye["name"], "house": prop(ye, "House"),
            "age": _int(ap.split()[0]) if ap else None,
            "size": _int(_endash(prop(ye, "Size") or "")),
            "characteristics": parse_chars_prose(prop(ye, "Characteristics")),
            "abilities": parse_abilities_prose(prop(ye, "Abilities")),
            "personalityTraits": parse_personality_prose(prop(ye, "Personality Trait")),
            "virtuesFlaws": parse_named_list_prose(prop(ye, "Virtues and Flaws")),
            "combat": prop(ye, "Combat"), "soak": prop(ye, "Soak"),
            "equipment": prop(ye, "Equipment"), "confidence": prop(ye, "Confidence Score"),
            "appearance": prop(ye, "Appearance"),
            "description": next((b.get("value") for b in ye.get("blocks", []) if b.get("keyword") == "DESCRIPTION"), "") or "",
            "source": prop(ye, "Source"),
        })
    young_characters.sort(key=lambda x: x["name"])
    apprentices = {"creation": young_creation, "agingChart": aging_chart,
                   "childVirtues": child_virtues, "childFlaws": child_flaws,
                   "youngCharacters": young_characters}

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
        "trainingPackages": training,
        "characterTemplates": templates,
        "realmToolkits": realm_toolkits,
        "creatures": creatures,
        "magicBeings": magic_beings,
        "apprentices": apprentices,
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
    print(f"  training packages {len(training)} "
          f"({sum(1 for t in training if t['category']=='Career')} Career / "
          f"{sum(1 for t in training if t['category']=='Non-Career')} Non-Career / "
          f"{sum(1 for t in training if t['category']=='Childhood')} Childhood)")
    print(f"  character templates {len(templates)} "
          f"({sum(1 for t in templates if t['type']=='grog')} grog / "
          f"{sum(1 for t in templates if t['type']=='companion')} companion / "
          f"{sum(1 for t in templates if t['type']=='magus')} magus)")
    rm = realm_toolkits
    print(f"  realm toolkits: magic {len(rm['magic']['qualities'])}Q/"
          f"{len(rm['magic']['inferiorities'])}I/{len(rm['magic']['powers'])}P | "
          f"faerie {len(rm['faerie']['powers'])}P/{len(rm['faerie']['wizardry'])}W/"
          f"{len(rm['faerie']['blood'])}B")
    import collections as _c
    cbr = _c.Counter(str(c['realm']) for c in creatures)
    print(f"  pre-defined beings (Creature) {len(creatures)}: " + ", ".join(f"{k} {v}" for k, v in sorted(cbr.items())))
    print(f"  magic beings (Magic Character, parsed) {len(magic_beings)} | "
          f"{sum(len(b['powers']) for b in magic_beings)} powers, "
          f"{sum(len(b['abilities']) for b in magic_beings)} abilities parsed")
    print(f"  apprentices: creation {'ok' if young_creation else 'MISSING'} | "
          f"aging chart {len(aging_chart)} rows | child V/F {len(child_virtues)}/{len(child_flaws)} | "
          f"young characters {len(young_characters)}")
    print(f"  creation-rule passages {len(creation_rules)}/{len(CREATION_RULE_ENTITIES)}")
    print(f"  spell guidelines {len(guidelines)} rows across "
          f"{len(set((g['technique'],g['form']) for g in guidelines))} Te/Fo tables")
    print(f"wrote {out_spells}  ({os.path.getsize(out_spells)/1024:.1f} KB) | "
          f"spells {len(spells)}")


if __name__ == "__main__":
    main()
