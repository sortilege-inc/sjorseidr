# Sjórseiðr — Covenant Archive

A data-driven set of static pages chronicling the Ars Magica campaign of
**Sjórseiðr**, a ship-based independent covenant of the North Sea. Everything
here is plain HTML/CSS/JS reading from local JSON — no build step, no
server-side code. Open [`index.html`](index.html) to get around.

## Pages

| Page | Data file(s) | What it's for |
|---|---|---|
| [`index.html`](index.html) | — | Landing page, links everything below. |
| [`sjorseidr_chronicle.html`](sjorseidr_chronicle.html) | `verified_events.json`, `proposed_events.json` | The covenant's full story timeline, most-recent-first, split into Verified (canon) and Proposed (drafted from a session transcript, awaiting GM review). Filterable by activity type (collapsed by default — 33+ types) and free text. |
| [`normandy_tribunal_1223.html`](normandy_tribunal_1223.html) | inline `DATA` blob | Interactive map of the Normandy Tribunal's 24 covenants, toggling between covenant profiles and tournament standings. |
| [`tribunal_workbook.html`](tribunal_workbook.html) | `tribunal_data.json` | Editable scoring workbook — vis sources, library prizes, tournament brackets/tally, and a "Prizes Claimed So Far" rollup. Edits autosave to `localStorage`; Save downloads an updated JSON. |
| [`normandy_tribunal_reference.html`](normandy_tribunal_reference.html) | — | Static reference catalogue of the Tribunal's vis sources and library holdings (source for `tribunal_data.json`'s vis/library sections), plus a vis-category glossary (Seisin/Legacy/Tropaeum/Luctatio) and a Notable Opponents section for the 1223 Tourney, both pulled from Notion. |
| [`open_questions.html`](open_questions.html) | `open_questions.json` | The Storyteller page — split into **Questions** (need a GM ruling), **Threads** (dangling narrative hooks), and **Consequences** (already happened, fallout pending), editable with the same autosave/Save pattern as the workbook. Also carries a **GM Reference** tab (Notion-sourced): a 41-entry Bruges NPC roster none of whom have been used in play, a sea-fae bestiary, and a Criamon riddle bank. |
| [`ships.html`](ships.html) | `ships.json`, `magi.json`, `npcs.json`, `ship_details.json` | Fleet & crew roster — time-based crew snapshots plus an "All Ships" reference tab covering the full fleet history (including lost/retired hulls). Click a crew member for a sidebar card: the six PC magi (`magi.json`) and 32 grogs/companions/NPC magi (`npcs.json`) get a full Foundry-sourced stat sheet, five of them (Dagmar, Éogan, Willem, Heynric, Father Lachlan) with a full narrative biography pulled in from Notion; the 3 remaining names with no Foundry sheet (Hilda, Karl, Rody) get the lightweight note card from `ships.json`'s `characters{}`. Crew chips are color-coded by category (PC magus / NPC magus / companion / grog / other). The "All Ships" cards also carry each ship's hull dimensions, enchanted devices, and laboratory stats (`ship_details.json`), Foundry-sourced. |
| [`covenant.html`](covenant.html) | `covenant.json` | Covenant sheet — founding year, tribunal, saga, aegis/regio, loyalty, yearly finances, covenant-wide virtues & flaws, and (from Notion) the full Covenant Charter and a founding note. Meta only; library/vis/full inhabitant census stay in the workbook and `ships.json`. |
| [`hiberian.html`](hiberian.html) | `maps/*.jpeg` | Extracted reference data + regional maps for the Hibernian Tribunal (Connacht, Leinster, Meath, Munster, Ulster), relevant to the party's Ireland arc. |
| [`reference.html`](reference.html) | `reference.json` | Miscellaneous GM tables pulled from Notion, in three tabs: North Sea/Baltic sailing times (+ the Bruges–Bordeaux route), trade goods & 1220s banking practices, and a World Gazetteer (Bergen, the Rhine-Tribunal duchies, English/French ports, Bruges' civic structure). |

## Data pipeline

The canon record (`verified_events.json`) started as an export of the
campaign's Notion database. New sessions are processed from raw transcripts
(`*.txt` files in the parent directory) through a small set of one-off Python
scripts that live **outside this repo**, in the parent `2026 Ars Magica/`
folder (`_build_proposed_sessionN.py`, `_inline_chronicle_data.py`, etc.) —
they aren't checked in here since they're throwaway per-session tooling, not
part of the published site.

Rough flow per session:
1. Read the session transcript, draft events into a `PROPOSALS` list matching
   the established schema (title/icon/timeline/date/cast/activity_type/body).
2. Run the build script → writes `Proposed Logs/*.md` (human-readable drafts,
   also outside this repo) and merges into `proposed_events.json`.
3. Run `_inline_chronicle_data.py` → re-embeds both JSON files into
   `sjorseidr_chronicle.html` so it works standalone via `file://` or a static
   host without a fetch/CORS dance.
4. GM reviews the Proposed entries on the chronicle page; anything confirmed
   gets hand-promoted into `verified_events.json` (and dropped from
   `proposed_events.json`).

`tribunal_data.json` and `ships.json` get hand-patched alongside this as new
sessions confirm standings, prize claims, or crew assignments.

`magi.json` (the six PC magi's full stat sheets — characteristics, arts,
virtues/flaws, abilities, spells, personality traits) was generated by a
one-off script pulling each actor via the Foundry REST API's `/get` endpoint
(see below) and normalizing the arm5e system's raw item list into that
shape; the script isn't checked in here, same rationale as the session
tooling above. It's a **snapshot**, not a live view — re-run the pull to
refresh it. `ships.json`'s `characters{}` names are matched to `magi.json`
by exact string, with one known spelling mismatch handled via an alias map
in `ships.html` (`Wilhelm` vs. Foundry's `Willhelm` Stienauer).

Portrait images for the five magi with real Foundry portraits were
downloaded into `portraits/` (Willhelm has no portrait set in Foundry, so
his card falls back to a placeholder glyph).

`npcs.json` covers the other 32 named crew members — grogs, companions, and
NPC magi — using the same extraction shape as `magi.json` (so the sidebar
renders both with the same code), plus a `charType` field straight from
Foundry (`magus`/`companion`/`grog`/`entity`/`mundane`) that also drives the
crew-chip color coding. Unlike `magi.json`, entries are keyed by the
`ships.json` canonical name directly (with the raw Foundry name kept in
`foundryName`) rather than needing a separate alias map, since most of these
32 differ from their ships.json name only by a Foundry-added descriptive
suffix (e.g. "Pieter van Dijk" → "Pieter van Dijk - Surgeon") — `Dietrich`
is the one real exception, filed in Foundry as "Deitrich Stienauer" (both
a spelling and surname difference; ships.json's `characters{}` doesn't give
him a surname). Portraits were downloaded for the 18 of 32 that had a real
Foundry image (rest use the generic silhouette icon, same fallback as
Willhelm's).

Three names on the Fleet & Crew page have no Foundry actor at all — **Hilda**,
**Karl**, and **Rody** — and keep the flavor-only stub card.

Foundry's `charType` didn't always match `ships.json`'s prose, and GM
review (2026-07-13) sorted out which side was right:
- **Marina** is confirmed a magus — Foundry was right, `ships.json`'s old
  "Crew" was stale. Updated `characters.Marina.role` to "Magus".
- **Garrat Coffin** is confirmed a companion — Foundry was right,
  `ships.json`'s old "Grog" was stale. Updated `characters["Garrat
  Coffin"].role` to "Companion".
- **Dietrich** is confirmed a companion — here Foundry was *wrong* (typed
  `magus`); corrected by hand in `npcs.json` since there's no write
  endpoint on the REST API to fix it at the source, so the live Foundry
  sheet itself still says `magus`. Also confirmed: his surname is
  Stienauer (he's Wilhelm's brother), matching the Foundry actor name
  "Deitrich Stienauer" already used as his `foundryName`. Updated
  `characters.Dietrich.role` to "Companion" too.

**Giden** and **Rán** weren't covered by that review and are still open
questions — Giden's Foundry `charType` is `companion` (untouched,
unverified), and both his and Rán's sheets are otherwise essentially blank
in Foundry (a name and a char type, zero characteristics/virtues/
abilities) — so their sidebar cards will look sparse; that's the actual
state of the Foundry data, not an extraction bug.

`covenant.json` and `ship_details.json` were generated the same way (one-off
script, not checked in), pulling:
- the covenant actor (`Sjórseiðr`, subType `covenant`) for `covenant.json`'s
  founding/tribunal/aegis/loyalty/finances/virtues/flaws;
- each ship's **standalone** `possessionsCovenant` Item (found via `/search`,
  not the covenant actor's own embedded copy — see below) for hull type,
  dimensions, and flavor description;
- the 5 enchanted-device Items (Bell of Summoning, Brooch of Lungs of the
  Fish, the Magical Astrolabe, the Freshwater Barrel, the Master's Chart) —
  each device's "Enchantments" are a nested `system.enchantments.effects[]`
  list on the device Item itself, not separate documents;
- each ship's standalone `laboratory`-subtype Actor (filed in the ship's
  Foundry folder alongside its owning magus) for lab stats.

**The covenant actor embeds its own stale copies** of the ship/lab list
(`possessionsCovenant`/`labCovenant` items) — confirmed to lag the
standalone directory in every case checked (missing ships entirely, older
modification timestamps, one stale name). `ship_details.json` was built from
the standalone copies, not the covenant-embedded ones. One genuine content
conflict surfaced: the standalone Maelstrom's Maw Item says hull "(Buss)"
and current owner "Kor Ex Flambeau"; the covenant-embedded copy says
"(Knarr)" and "Tytalus Elementalist" (Nequam, the ship's pre-1220 owner).
Resolved per GM call: standalone is current. This also established the
model used for `ship_details.json`'s `currentOwner`/`formerOwner`/
`covenantStatus` fields — Maelstrom's Maw and Tide of Memory both carry a
`formerOwner` (Nequam, Solving) alongside their `currentOwner`, and
Maelstrom's Maw additionally has `covenantStatus: "absent"` since the ship
itself is missing and shouldn't count toward covenant mechanical costs/
benefits even though its crew/lab data stays on record.

Adamant and Hound of Cassel have no `possessionsCovenant` record in Foundry
at all (Adamant is Valerian's personal ship, not covenant property; Hound of
Cassel's disposition is still undecided) — Adamant does have a laboratory
actor, Hound of Cassel has neither. Hound of Cassel's `standing_crew` in
`ships.json` was also empty even though its `owner` field already named
Wilhelm — added him to `standing_crew` so he shows up as a clickable chip
on that card too, not just unclickable owner text.

The Magical Astrolabe's Item has `quantity: 5` and its description says
"each ship in the fleet is issued with one" — per GM call, it's replicated
onto all 5 of the core fleet's `possessionsCovenant` ships (Tide of Memory,
Brineborn, Scholar's Wake, the Gloaming, Maelstrom's Maw), not onto Veðrdreki
(explicitly separate from the main fleet) or Adamant (no ship record). The
Bell of Summoning and Master's Chart (`quantity: 1` each) stay on Tide of
Memory only, matching `ships.json`'s existing description. The Brooch of
Lungs of the Fish is a wearable personal item, not ship-bound, and isn't
attached to any ship card.

## Local preview

Any of these pages needs to be served over HTTP (not opened via `file://`)
for their JSON `fetch()` calls to work — e.g. from the parent directory:

```
python3 -m http.server 8934 --directory sjorseidr
```

## Foundry VTT REST API

The live Foundry world (`sjorseidr`, Ars Magica 5e / arm5e system) is
reachable through the [FoundryVTT REST API Relay](https://foundryrestapi.com)
when the GM has the world open and the relay module running. As of 2026-07-13
this powers `magi.json`, `npcs.json`, `covenant.json`, and `ship_details.json`
(one-time pulls, not a live view — see above); cross-checking open questions
against live sheet data is still a possible future pass.

- **Base URL:** `https://foundryrestapi.com`
- **Auth:** `x-api-key: <key>` header on every request. Key is **not**
  stored in this repo — treat it like any other credential.
- **Docs:** `https://foundryrestapi.com/docs/api` (per-endpoint reference);
  full page list under `/docs/api/{auth,canvas,chat,clients,dnd5e,effects,
  encounter,entity,events,fileSystem,macro,playlist,roll,scene,search,
  session,sheet,structure,user,utility,websocket}`.

Endpoints confirmed working against the live world:

| Endpoint | Notes |
|---|---|
| `GET /clients` | Lists connected Foundry instances — `worldId`, `worldTitle`, `systemId`, `isOnline`, and (when online) `clientId`, needed for every other call. |
| `GET /search?clientId=&query=` | Full-text search across world *and* compendium entities. Results are tagged `resultType: WorldEntity` vs `CompendiumEntity` — filter on that to avoid matching the arm5e system's built-in creature/spell compendia. An empty `query` with `filter=actor` returns compendium noise; a real name (e.g. `query=Dagmar`) finds the actual PC. |
| `GET /get?clientId=&uuid=` | Full entity JSON by UUID (e.g. `Actor.9ek4ZhrnGmHO5n2b`) — characteristics, Arts, virtues/flaws/abilities/spells (as embedded Items), laboratory, familiar, apprentice, house/parens/sigil, pending XP, everything. Query params, **not** a `/get/{uuid}` path — that 404s. Also works on `Item.<id>` and, usefully, `Folder.<id>` (returns just the folder's own name/type, not its contents — see limitation below). |
| `GET /sheet?clientId=&uuid=&format=png` | Screenshot of the rendered actor sheet as an image, not JSON. |

**No folder-listing endpoint.** `/structure` returns `{"folders":{}}` regardless
of params tried (`type=Actor`, `type=Item`) — there's no way to ask "what's in
folder X" directly. The only way to enumerate a folder's contents is to
`/search` for items you already suspect are in there by name and check the
`folder` field on the results match. `/search` itself is also noisy: an
empty or short query returns compendium spam (creature/spell/ability
compendia bundled with the arm5e system) capped at 200 results, so it's
only reliable for known-name lookups, not "list everything of type X."

Typical call shape:
```
curl -s "https://foundryrestapi.com/get?clientId=<clientId>&uuid=Actor.<id>" \
  -H "x-api-key: <key>"
```

`clientId` comes from `/clients` and changes if the world's relay connection
resets, so always re-check `/clients` at the start of a session rather than
assuming a cached one is still valid.

## Notion merge (2026-07-13)

The campaign also has a Notion workspace (`sortilege.notion.site`) that predates
the Foundry migration and was the *original* source for a lot of the fleet/
covenant flavor text already in this repo. It's no longer current — this repo
is — but it wasn't complete either, so a one-time extraction + classification
+ selective merge pass was run against it.

**Extraction**: a recursive crawler (not checked in — one-off script, same
rationale as the session tooling above) walked the whole page tree under a
given root page via the [Notion API](https://api.notion.com/v1) — `GET
/blocks/{id}/children` recursively for page content, `POST
/databases/{id}/query` for any nested database, downloading every image block
before its signed S3 URL expired (~1hr). Output went to a `notion_export/`
folder *outside* this repo (sibling to `sjorseidr/`, not checked in) as one
Markdown file per page. 197 pages came out of that pull. One wrinkle: a few
"database rows" turned out to be full nested databases themselves (Foundry-style,
not simple pages) — `GET /pages/{id}` 400s on those with `"is a database, not a
page"`; the crawler retries as `GET /databases/{id}` when it sees that.

**Scope**: per GM direction, only content nested under the "Salve Sodales:
Sjórseiðr Campaign Wiki" child database counts as player-facing and is
eligible to merge into this site. Everything outside that (the root page's own
huge GM-planning toggle, "Ars Magica Foundry VTT Notes", "Mythic Europe Notes
(not-player-facing)", "GM NPCs (not-player-facing)", "Player Info" and its
~15 sub-pages) is GM-only — not merged this pass, and ultimately destined for
`open_questions.json` rather than any player-facing page. A "Covenants"
database nested *inside* the Wiki turned out to be reused cross-campaign GM
reference (covenants with no Sjórseiðr connection, e.g. Horsingas in Loch
Leglean) and was treated as GM-only too, as was a generic "Tribunals" list.

**What actually merged**:
- `magi.json` — added `biography` to Dagmar (the actual in-fiction origin of
  his Ghostly Warder flaw, plus his answers to the Criamon riddles) and Éogan
  Dobhartha (full childhood, the Treaty of Cnoc Maol Réidh, his parens, the
  Well Dreams that are the source of his personal vis).
- `npcs.json` — added `biography` to Willem "Sour" Jensen, Heynric the
  Merchant, and Father Lachlan (birth name, physical description, personal
  beliefs); added `shortDescription`/`originallyFrom`/`playedBy` to several
  others (Ka'wa'ill is explicitly "the merman prince"; Marina's house is now
  confirmed **Merinita**, resolving the unmapped Foundry house code `mta`
  from last pass). `ships.html`'s sheet renderer now shows all of these, plus
  `born` (was already in the data from Foundry but never actually rendered
  anywhere — fixed while adding the new fields).
- `covenant.json`/`covenant.html` — added the full Covenant Charter (membership,
  hospitality, voting, the 10/20/30/40-year tenure ladder, Spring 1220
  proposed amendments) and a founding note + preferred-ports list.
- `reference.json`/`reference.html` — new page, North Sea/Baltic sailing-time
  matrix between 13 ports. The source table has some internal asymmetry
  (Bruges→London reads 4 days, London→Bruges reads 3) and a couple of
  apparent gaps — transcribed as-is rather than smoothed over.
- `normandy_tribunal_reference.html` — added a glossary box defining Seisin/
  Legacy/Tropaeum/Luctatio, terms `tribunal_workbook.html` already uses
  throughout without ever explaining.
- `open_questions.json` — added thread `t026`, an unsigned letter to Solving
  from someone signing only "V.," found in GM notes but never reflected in
  the chronicle or picked up at the table.

**Judgment calls made along the way**: Stijntje Kuiper's Foundry `charType`
of `magus` looked like the same kind of error as the Dietrich case last
round, but the GM confirmed it's correct as-is — she's Gifted and
apprenticed, which counts as a magus mechanically even before her Gauntlet;
no data changed. Two names from the classification pass are still open:
**Giden**'s Foundry `charType` (`companion`) was never independently
verified the way Marina/Garrat Coffin/Dietrich were, and **Rán**'s status is
likewise unconfirmed. Ka'wa'ill's Foundry sheet has `born: 1223` — the
campaign's current year, which for a grown merman prince reads as an unset
placeholder rather than a real birth year; left as-is, not fabricated a fix.

### GM-only content merge (same day, second pass)

The rest of the Notion export — root page, Foundry VTT Notes, Mythic Europe
Notes, the 37-entry "GM NPCs" database, Player Info and its ~15 sub-pages —
got the same extraction-then-classify treatment as the player-facing slice
above. Per GM direction, all of it lives on `open_questions.html` now rather
than scattered across player-facing pages — either as new Question/Thread/
Consequence items, or (for content that's reference material rather than a
question) a new **GM Reference** tab on that same page.

Two research agents did the first read-through on the largest chunks
(Player Info's 15 sub-pages, and Mythic Europe Notes) and reported back
structured candidates rather than raw text, to keep the classification
consistent without burning through the session's context reading ~140 files
directly. Everything they flagged was cross-checked against the live site
data before being written — this caught a few things worth calling out:

- **The tourney bracket gap is real, and it's already on the site.**
  `tribunal_data.json`'s own bracket data has the exact same blank cells
  the GM's old Notion prep does — Sjórseiðr reached the semifinal/final of
  Dimicatio and Hastiludium (after winning three straight rounds in each)
  and the *first* round of Certamen (which they lost), but the later
  results were never filled in on either side. Added as `q021`, and used
  to fact-check the new Notable Opponents section on
  `normandy_tribunal_reference.html` — each opponent there is now tagged
  **won** / **lost** / **unresolved** against the actual bracket, not just
  copied from GM prep as if every matchup happened.
- **A named suspect for Valerian's disappearance surfaced mid-pass.** Sir
  Odo van Aerschot, a Brabantine-loyalist knight, is explicitly noted in
  the Mythic Europe Notes as "suspected to be behind several disappearances
  in Bruges — including Valerian's." Added to the Bruges roster and folded
  into thread `t030`, which already tracked several looser leads (a
  dockhand's, a lantern-boy's account) pointing the same direction.
- **Some prep was clearly never played and is marked as such.** The
  Certamen bracket only ever reached Myrrha of Fudarus (round 1, lost) —
  Proctor of Confluensis, Tacticus of Bellum Iocari, and Aurelian of
  Merces Aurea were prepped for rounds the party never reached, and the
  Notable Opponents section says so explicitly rather than implying they
  were faced. Likewise, `Valerian_de_Castellane.md` (an early draft
  portraying him as a vengeful fugitive antagonist) directly contradicts
  his current status as a fully-statted PC magus and covenant member —
  discarded rather than merged, since it's superseded by actual play.
- **Two low-confidence Threads (`t032`, `t033`)** — a Montverte alliance
  offer and a Merces Aurea separatist pitch, both from tourney GM prep —
  are flagged in their own context as unconfirmed whether they were ever
  actually raised at the table, rather than presented as settled fact.

What landed where:
- **`open_questions.json`** — 14 new Question/Thread/Consequence items
  (`q021`–`q022`, `t027`–`t035`, `c023`–`c025`), plus a new `gmReference`
  block: the 41-entry Bruges NPC roster (37 street-level locals + 4 noble
  houses, cross-linked to the relevant open questions), a sea-fae bestiary
  organized by ocean depth with its companion poem, and the 15-Art Criamon
  riddle bank that Dagmar's own character-sheet riddle answers (from the
  first Notion pass) draw four entries from.
- **`reference.json`/`reference.html`** — gained two more tabs: Trade &
  Banking (North Sea trade goods by region, 1220s credit/moneylending
  practices) and a World Gazetteer (Bergen — where the *Adamant* was
  built — the Rhine-Tribunal duchies bordering Normandy, English ports
  led by a detailed Southampton with four named merchant families, French
  ports led by Rouen, and Bruges' civic/legal structure). The original
  travel-times tab also gained the Bruges↔Bordeaux ketch route.
- **`normandy_tribunal_reference.html`** — new Notable Opponents section,
  12 opponents across all three individual-and-team tourney events, each
  fact-checked against the actual bracket as described above.
- **Skipped outright**: `Ars_Magica_Foundry_VTT_Notes.md` (pure arm5e
  system-tooling Q&A with the system's developer, zero campaign content)
  and the stale `Valerian_de_Castellane.md` draft mentioned above.

### Last-updated marker

`index.html` shows a "Last updated" line in the footer, sourced from
`build_info.json` (`{commit, updatedAt}`). Since a file can't describe the
hash of the commit it's part of, this is regenerated as a small follow-up
commit at the end of a work session, referencing whatever commit was just
made — there's inherently one commit of lag, which is normal for this
pattern without a CI step to do it automatically.

## Open threads on this archive itself

See [`open_questions.html`](open_questions.html) — it tracks the project's
own in-fiction unknowns, not meta/tooling issues. As of this writing, the
Fleet & Crew page's character sidebar is fully wired for the six PC magi
(`magi.json`) and 32 more grogs/companions/NPC magi (`npcs.json`); only
Hilda, Karl, and Rody (no Foundry sheet) still get the lightweight note-card
stub. Ship hull/enchanted-device/laboratory detail (`ship_details.json`)
covers 6 of the 8 ships.json entries — Adamant has a lab but no ship record,
Hound of Cassel has neither (see the data pipeline section above for why).
The covenant sheet (`covenant.json`) is meta-only for now — inhabitants,
library, lab texts, and vis sources weren't pulled this pass since they may
duplicate `tribunal_workbook.html`.

The covenant's Aegis level, Aegis penetration, and regio levels are all
recorded as 0 in Foundry — `covenant.html` flags this inline as possibly
just unconfigured rather than narratively true; worth a GM glance.

One `magi.json` quirk that looks like an error but isn't: several magi
(notably Dustin Page, and to a lesser extent Éogan Dobhartha and Valerian
de Castellane) have runs of Arts sitting at exactly "5" across techniques
or forms — confirmed by the GM as intentional, not stale data (Dustin, for
one, was built to hit the minimum Arts needed to take on an apprentice, not
maximize any one Art). Ability scores are computed client-side from raw
Foundry XP totals using the standard ArM5 cost table, so they won't reflect
Puissant/Affinity bonuses that aren't already baked into the stored XP —
that part is still worth a GM sanity-check.
