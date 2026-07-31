# Build brief — standalone Ars Magica character-creation feature

Status: **in progress** (started 2026-07-30). Owner decisions locked below.

## Goal
A **standalone, corpus-driven character creator** on the Sjórseiðr site: a guided
page (`chargen.html`) that walks a user through Ars Magica 5e (armdef 0.5)
character creation, pulling ALL rules data and text from the titterpig corpus —
never hard-coded — and exporting a character as a **superset** of the site's
`magi.json` shape (so it renders in `ships.html`, with a Foundry export planned
later). "Standalone" = a new page + one launcher card on `index.html`; existing
pages are otherwise untouched.

## Owner decisions (locked 2026-07-30)
1. **Character types:** Magi, Companions, and Grogs from day one.
2. **Validation posture:** start with **strict RAW** enforcement; design for an
   **advisory toggle** (warn-but-allow) to be added later.
3. **Export:** a **superset** of `magi.json` now; **Foundry export** is a later
   stage.
4. **Spells:** support **both** picking predefined spells and guideline-based
   design — but **start from choosing predefined** (the 737 core spells).
5. **XP / later-life:** a **multi-stage** effort — build the pool framework and
   manual allocation now; deeper automation comes in later stages.
6. **Virtue/Flaw list:** the **full** core set (452 Virtues + 379 Flaws).

## Repo & conventions
- Repo: `/home/hewhocutsdown/Working/2025-2026 Sjórseiðr/sjorseidr`; GitHub Pages
  `sortilege-inc/sjorseidr`, deploys from `main`.
- Static, **no-build**: plain HTML per page + JSON fetched at runtime
  (`fetch('./x.json', {cache:'no-store'})`). No bundler/framework/runtime deps.
  Must run on GitHub Pages and a local `python3 -m http.server`.
- Aesthetic: parchment. Cinzel / EB Garamond / UnifrakturCook; shared palette
  vars (`--parch, --ink, --gold, --rust, --teal, --green, --purple, --line`).
  Copy the `<style>` head + card/section idioms from `index.html` / `ships.html`.
- Git identity per-repo: `Jordan Peacock <jordan@sortilege.online>`. Commit/push
  to `main` **only when asked**; end messages with the Co-Authored-By line.
- Hard rules: **verbatim** rules text (never paraphrase spell/virtue/flaw/ability/
  creation text — only whitespace/HTML-escape transforms; connecting UI prose is
  yours); **no base64 images**; theme-consistent; mobile-responsive; self-contained.

## Precedents to reuse
- `ships.html` is the model for sheet layout + the dice/roll idiom (rollable
  abilities/spells, Penetration + Combat calculators) and for corpus-first text
  with fallback. The finished character must drop into `ships.html`.
- Target base shape = `magi.json`'s per-magus object: `{ key, name, house, parens,
  sigil, born, age, apparentAge, characteristics:{int,per,str,sta,pre,com,dex,qik},
  size, confidence, decrepitude, warping, arts:{cr,in,mu,pe,re,an,aq,au,co,he,ig,
  im,me,te,vi -> {label,score,xp}}, virtues:[{name,impact,description?}], flaws:[…],
  abilities:[{name,speciality,xp,score}], spells:[{name,technique,form,level,range,
  duration,target,ritual,description?}], personalityTraits, reputations, sanctum,
  familiar, activeWounds, biography }`. The chargen export is a **superset**: add a
  `chargen` block (type, budgets spent/remaining, House free-virtue, parameter
  choices, age math) without breaking the base fields.
- `scripts/build_rules.py` is the extraction pattern.

## Corpus (data source)
`titterpig-corpora/armdef/0.5/armdef-0.5-full.resolved.json` (~10.5 MB — do NOT
ship to the browser). Entity shape: `{ name, kind, extends?, properties:[{name,
type,value,modifiers}], blocks:[{keyword,value}], sources }`. Verbatim text = the
`blocks` entry with `keyword=="DESCRIPTION"` (`.value`). Key taxonomy (verified):
- **Virtues** `extends "Virtue"` (452); **Flaws** `extends "Flaw"` (379). Each has
  props `Size` (Minor / Major / Free / "Major or Minor") and `Category` (Hermetic,
  Supernatural, General, Social Status, Personality, Story, Heroic, …).
  Parameterized ones exist: `Puissant Ability`, `Puissant Art`, `Affinity with
  Ability`, `Affinity with Art`, `Great Characteristic`, `(Area) Lore`, … — allow
  the user to specify the parameter (record as a `detail`).
- **Houses** `extends "Hermetic House"` (12) with props `House Type, Prima, Domus
  Magna, Benefit, Free Virtue` (structured, e.g. `Puissant Ability(Magic Theory)`).
- **Arts** `extends "Hermetic Technique"` (5) / `"Hermetic Form"` (10) — 15 total.
- **Characteristics** `extends "Characteristic"` (7): Intelligence, Perception,
  Strength, Stamina, Communication, Dexterity, Quickness.
- **Abilities** `extends "Ability"` (61) with `Ability Type` + `Specialties`.
- **Spells**: props Technique/Form/Level/Range/Duration/Target/Ritual (~737).
- **Creation rules** in entities: `Detailed Character Creation` (full step list +
  budgets), `Characteristic Buying`, `Personality at Creation`, `Reputations at
  Creation`, `Confidence at Creation`, `Equipment at Creation` + much `guidance`.

## RAW creation numbers (verbatim from `Detailed Character Creation`)
- Virtues/Flaws: Minor = 1 pt, Major = 3 pts. **Grogs:** ≤3 Minor Flaws + equal
  Minor Virtues. **Companions & Magi:** ≤10 pts Flaws, matched by ≤10 pts Virtues.
- Characteristics: start **7 points** (pyramid table; ±n costs n(n+1)/2).
- Early childhood: **75 xp** Native Language (score 5) + **45 xp** across Area
  Lore, Athletics, Awareness, Brawl, Charm, Folk Ken, Guile, Living Language,
  Stealth, Survival, Swim.
- Later life: **15 xp/year** until apprenticeship (magi) / current age (others);
  Wealthy → 20, Poor → 10.
- Apprenticeship (magi): **240 xp** across Arts + non-Supernatural Abilities;
  **120 levels** of spells, none above Te + Fo + Int + Magic Theory + 3.
- Post-apprenticeship (optional): **30 pts/year** split Art xp / Ability xp / spell
  levels.
- Confidence: score 1, 3 points (magi/companions). Personality, Reputation,
  Equipment per the corpus passages.

## Data pipeline
Add `scripts/build_chargen.py` (mirror `build_rules.py`: same corpus path default,
DESCRIPTION-block extraction, argv override, regenerate-after-update docstring).
Emit `chargen.json` (characteristics + cost table, houses, arts, virtues, flaws,
abilities, creationRules verbatim, budgets constants sourced to Detailed Character
Creation, meta). Put the ~737 spells in a separate `chargen-spells.json`
lazy-loaded at the spell step. Keep `rules.json` untouched.

## Flow (stepped wizard)
Concept + type → (magi) House + free Virtue → Virtues & Flaws (full list, live RAW
budget + category rules: The Gift required for magi, exactly one Social Status,
Hermetic V/F require The Gift) → Characteristics (7 pts, pyramid) → Abilities
(childhood 75+45, later-life by age/years, magi apprenticeship 240) → (magi) Arts +
spells (pick predefined; enforce the 120-level budget and the per-spell level cap)
→ Personality / Reputation / Confidence / Equipment → Review + export.

## Output
Autosave to `localStorage`; "Export JSON" downloads the superset object + copy to
clipboard. A finished character must render in `ships.html` if pasted into
`magi.json`. Add ONE card to `index.html`'s grid (title "Character Creator", tag
"Chargen") linking `chargen.html`.

## Verify (prove it)
`python3 scripts/build_chargen.py` clean (report counts + sizes); serve locally and
drive the wizard end-to-end — budgets validate, House free-Virtue applies, export
round-trips into `ships.html`; zero console errors; share proof. Document
regenerating the derived JSON after any corpus update.

## Known later-stage work (blockers / follow-ups)
- Advisory-mode toggle (decision 2, phase 2).
- Foundry export (decision 3, later).
- Guideline-based spell *design* (decision 4 — predefined first).
- Deeper XP-allocation automation and post-apprenticeship years (decision 5).
- Parameterized-virtue UX polish; finer RAW caps (Story-Flaw cap, one Major
  Personality Flaw, etc.) beyond the core budget rules.
