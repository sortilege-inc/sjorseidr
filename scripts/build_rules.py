#!/usr/bin/env python3
"""
build_rules.py — extract a compact rules.json for the Sjórseiðr site from the
resolved Ars Magica (armdef) DSL corpus.

The site pages (integrating_magic.html, ships.html fleet-crew sheets) render
VERBATIM rules text — spell/virtue/flaw descriptions and the Laboratory
Integration passages — pulled at runtime from ./rules.json instead of being
hard-coded into the pages or baked into magi.json/npcs.json.

The full resolved corpus (armdef-0.5-full.resolved.json) is ~9.6 MB, far too
large to fetch per page, so this script slices out only what the site uses:

  * the ordered Laboratory "Original Research -> Breakthrough -> Integration"
    passages that integrating_magic.html reproduces, and
  * the DESCRIPTION text of every spell / virtue / flaw referenced by any
    character in magi.json + npcs.json (matched on normalized name).

Re-run this whenever the corpus is updated OR characters change:

    python3 scripts/build_rules.py
    # or point at a specific corpus:
    python3 scripts/build_rules.py "/path/to/armdef-0.5-full.resolved.json"

Verbatim rule: the extracted text is reproduced exactly as the corpus stores it
(only whitespace is preserved); no paraphrase. The pages do light **bold** /
*italic* / paragraph rendering only.
"""
import json
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_CORPUS = "/home/hewhocutsdown/Working/Titterpig Utilities/titterpig-corpora/armdef/0.5/armdef-0.5-full.resolved.json"

# The Laboratory passages integrating_magic.html shows, in page order. Names are
# the exact corpus entity names; each is a def carrying a DESCRIPTION block.
LAB_PASSAGES = [
    "The Breakthrough",
    "Experimentation (Arcane Discovery)",
    "Integration",
    "Creating the Effect",
    "Stabilizing the Unknown",
    "After the Breakthrough",
]


def norm(s):
    """Normalized key for tolerant name matching (case/space-insensitive)."""
    return " ".join(str(s or "").lower().split())


def description(entity):
    for b in entity.get("blocks", []) or []:
        if b.get("keyword") == "DESCRIPTION":
            return b.get("value") or ""
    return ""


def cite_source(entity):
    srcs = entity.get("sources") or []
    if not srcs:
        return None
    # "armdef-0.5-laboratory.ttrpg" -> "armdef-0.5-laboratory"
    return srcs[0][:-6] if srcs[0].endswith(".ttrpg") else srcs[0]


def referenced_names(repo):
    """Every virtue/flaw/spell name any character references, normalized."""
    names = set()
    for fname in ("magi.json", "npcs.json"):
        path = os.path.join(repo, fname)
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        # magi.json -> {"magi":[...]}, npcs.json -> {"npcs":{...} or [...]}
        holder = data.get("magi") if "magi" in data else data.get("npcs", data)
        chars = holder if isinstance(holder, list) else list(holder.values())
        for ch in chars:
            if not isinstance(ch, dict):
                continue
            for fld in ("virtues", "flaws", "spells"):
                for it in ch.get(fld) or []:
                    if isinstance(it, dict) and it.get("name"):
                        names.add(norm(it["name"]))
    return names


def main():
    corpus_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CORPUS
    if not os.path.exists(corpus_path):
        sys.exit(f"corpus not found: {corpus_path}\n"
                 f"pass the path to armdef-0.5-full.resolved.json as an argument.")

    corpus = json.load(open(corpus_path, encoding="utf-8"))

    # Copy the synthesist's merged .ttrpg (sibling of the resolved json) into the
    # repo so the site can offer it as a download. e.g.
    # armdef-0.5-full.resolved.json -> armdef-0.5-full.merged.ttrpg
    merged_name = None
    if corpus_path.endswith(".resolved.json"):
        merged_src = corpus_path[: -len(".resolved.json")] + ".merged.ttrpg"
        if os.path.exists(merged_src):
            merged_name = os.path.basename(merged_src)
            shutil.copyfile(merged_src, os.path.join(REPO, merged_name))
        else:
            sys.stderr.write(f"WARNING: merged .ttrpg not found beside corpus: {merged_src}\n")

    by_name = {}
    for e in corpus.get("entities", []):
        by_name.setdefault(e["name"], e)
    by_norm = {norm(name): e for name, e in by_name.items()}

    # 1. Laboratory Integration passages (ordered).
    laboratory = []
    for name in LAB_PASSAGES:
        e = by_name.get(name)
        if not e:
            sys.stderr.write(f"WARNING: lab passage not found in corpus: {name!r}\n")
            continue
        text = description(e)
        if not text:
            sys.stderr.write(f"WARNING: lab passage has no DESCRIPTION: {name!r}\n")
            continue
        laboratory.append({
            "name": name,
            "source": cite_source(e),
            "text": text,
        })

    # 2. Referenced spell/virtue/flaw descriptions (character sheets).
    refs = referenced_names(REPO)
    entities = {}
    matched = 0
    for r in refs:
        e = by_norm.get(r)
        if not e:
            continue
        text = description(e)
        if not text:
            continue
        entities[e["name"]] = {"text": text, "source": cite_source(e)}
        matched += 1

    out = {
        "meta": {
            "edition": corpus.get("edition"),
            "spec_version": corpus.get("spec_version"),
            "generated_from": os.path.basename(corpus_path),
            "merged_ttrpg": merged_name,
            "note": ("Verbatim rules text sliced from the resolved armdef corpus for "
                     "runtime use by integrating_magic.html and the ships.html fleet-crew "
                     "sheets. Regenerate with scripts/build_rules.py after a corpus or "
                     "character update."),
        },
        "laboratory": laboratory,
        "entities": entities,
    }

    out_path = os.path.join(REPO, "rules.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")

    size_kb = os.path.getsize(out_path) / 1024
    print(f"wrote {out_path}")
    print(f"  edition {out['meta']['edition']} spec {out['meta']['spec_version']}")
    print(f"  laboratory passages: {len(laboratory)}/{len(LAB_PASSAGES)}")
    print(f"  referenced names: {len(refs)} | matched in corpus: {matched} "
          f"| unmatched (kept as sheet fallback): {len(refs) - matched}")
    print(f"  rules.json: {size_kb:.1f} KB")
    if merged_name:
        mkb = os.path.getsize(os.path.join(REPO, merged_name)) / 1024
        print(f"  merged .ttrpg copied: {merged_name} ({mkb/1024:.1f} MB)")


if __name__ == "__main__":
    main()
