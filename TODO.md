# Sjórseiðr — TODO / work log

_Working list for the covenant site. Newest concerns at the top of each section._

## Open questions to resolve

- [ ] **What is the difference between the covenant *page* and the covenant *ledger*?**
  `covenant.html` is currently a 0-second redirect stub → `covenant_ledger.html#covenant`
  (the old Covenant Sheet was merged into the Ledger's first "Covenant" tab). Nothing
  navigational links to `covenant.html` anymore — only a historical text mention in
  `open_questions.json` (q025). **Decide:** keep the redirect for old bookmarks/links, or
  delete `covenant.html` outright? Then document the canonical page so this doesn't come up again.

## 2026-08-22 session — verification & reconciliation

- [ ] **Prep reconciliation** (deferred until events verified): retire the now-played scenes
  (s6, s8, s9, s13, s15, s16), resolve **U6** and fold the outcome into **c026**, update **t025**,
  and reconcile the **s7** Foxglove stub.
- [ ] **Proposed events still awaiting review/approval:** p086 (Regiones the Third — cliffhanger),
  p087 (Valdemar's Isle-of-Man pitch), p069 (Legends of Brittany copy), p049/p063/p066/p067,
  and the declared Winter-1224-25 plans p072–p077.
- [ ] **Aurelius** (Scarem Montem) is a provisional NPC stub — flesh out House/stats if kept.

## GM rulings still open (changeset "unresolved" list)

- [ ] U1 — Isle-of-Man aura *source/realm* (aura 3 recorded; source undescribed).
- [ ] U2 — form of Confluensis's first squeeze (s11 / t078).
- [ ] U4 — Faerie-vs-Magic for Llewellyn's gambit & Paulus's ward at Carnac.
- [ ] U5 — The Unbroken Ring tuning (t082).
- [ ] U7 — do the party learn what's on Carnac L4 before or after needing the murfolk.
- [ ] U8 — who contests the Diedne Garden (t082).
- [ ] U9 — Wilhelm: return / keep / weaponise the Liège cipher chests (s6 / t028).
- [ ] U10 — Foundry regio levels still zeroed now that s15–s18 specify auras 7/8/9/10.
- [ ] U11 — season alignment on the slate (s1/s6 Summer vs s8–s10 Fall).

## XP tracker

- [ ] #17 — Dustin, Fall 1222 (5 XP) unallocated, pending the player's spend choice.
- [ ] 16 unresolved cells not ruled this pass (e.g. Éogan Summer 1222 fae-vis 15 Aquam;
  Dustin Winter 1222 "Learn Teaching from Henri" 22 Teaching) — see `xp_rulings.json` → `unresolved`.

## Site cleanups

- [ ] Chronicle: three broken `image*.png` references (`image.png`, `image 1.png`, `image 2.png`)
  404 on load — track down the source event(s) and fix or remove.
