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
| [`normandy_tribunal_reference.html`](normandy_tribunal_reference.html) | — | Static reference catalogue of the Tribunal's vis sources and library holdings (source for `tribunal_data.json`'s vis/library sections). |
| [`open_questions.html`](open_questions.html) | `open_questions.json` | The Storyteller page — split into **Questions** (need a GM ruling), **Threads** (dangling narrative hooks), and **Consequences** (already happened, fallout pending). Editable resolution status, same autosave/Save pattern as the workbook. |
| [`ships.html`](ships.html) | `ships.json` | Fleet & crew roster — time-based crew snapshots plus an "All Ships" reference tab covering the full fleet history (including lost/retired hulls). Click a crew member for a character-card sidebar (full stat sheets are a planned addition, see below). |
| [`hiberian.html`](hiberian.html) | `maps/*.jpeg` | Extracted reference data + regional maps for the Hibernian Tribunal (Connacht, Leinster, Meath, Munster, Ulster), relevant to the party's Ireland arc. |

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

## Local preview

Any of these pages needs to be served over HTTP (not opened via `file://`)
for their JSON `fetch()` calls to work — e.g. from the parent directory:

```
python3 -m http.server 8934 --directory sjorseidr
```

## Foundry VTT REST API

The live Foundry world (`sjorseidr`, Ars Magica 5e / arm5e system) is
reachable through the [FoundryVTT REST API Relay](https://foundryrestapi.com)
when the GM has the world open and the relay module running. This is **not**
wired into any page yet — it's a data source being explored for a future pass
at pulling real character sheets into the Fleet & Crew page (replacing the
"coming soon" sidebar stub) and cross-checking open questions against actual
sheet data.

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
| `GET /get?clientId=&uuid=` | Full entity JSON by UUID (e.g. `Actor.9ek4ZhrnGmHO5n2b`) — characteristics, Arts, virtues/flaws/abilities/spells (as embedded Items), laboratory, familiar, apprentice, house/parens/sigil, pending XP, everything. Query params, **not** a `/get/{uuid}` path — that 404s. |
| `GET /sheet?clientId=&uuid=&format=png` | Screenshot of the rendered actor sheet as an image, not JSON. |

Typical call shape:
```
curl -s "https://foundryrestapi.com/get?clientId=<clientId>&uuid=Actor.<id>" \
  -H "x-api-key: <key>"
```

`clientId` comes from `/clients` and changes if the world's relay connection
resets, so always re-check `/clients` at the start of a session rather than
assuming a cached one is still valid.

## Open threads on this archive itself

See [`open_questions.html`](open_questions.html) — it tracks the project's
own in-fiction unknowns, not meta/tooling issues. As of this writing, the
Fleet & Crew page's character sidebar is a deliberate stub pending the
Foundry API work described above.
