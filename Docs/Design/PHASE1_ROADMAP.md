# IRON BREACH — PHASE 1 ROADMAP & CONTENT MANIFEST
*"The Waterline" release (v1.0 through first major patch) · July 2026*
*Companion docs: `Docs/Story/02_IRONBREACH_Narrative_Bible.md` (§ refs), `Docs/Story/01_RESEARCH_Narrative_Analysis.md` (law refs)*

---

## 1. WHAT "PHASE 1 COMPLETE" MEANS

One sentence: **a player can enlist, play the full Waterline campaign, live in two open-world zones with public events and secrets, compete in PVP, grind a modifier dungeon weekly, and finish the arc by raiding the Green Tomb — where the thing the campaign has pointed at since minute one is the final boss.**

The bible already built Phase 1's shape for us: the campaign (§VII) plants Port Halcyon / CHALLENGER mythology from M1 (Static's podcast, the corpse-mountain skyline, the Green Tomb codex), and Raid 1 (§X.1) *is* the Green Tomb. Campaign teaches the de-escalation grammar in M15; the raid demands it at scale. Nothing new needs inventing — Phase 1 is the bible's launch year, scoped.

| Pillar | Phase 1 deliverable |
|---|---|
| Campaign | The Waterline — 15 missions, 3 acts (§VII) |
| Open world | 2 patrol zones w/ public events, biome-matched roaming kaiju, secrets, mini-dungeons, loot, easter eggs |
| PVP | "Wargames" (Concord combat-sim framing) — 2 modes, 3 maps, 6v6 |
| Nightfall-style | "Directive Ops" — 3-player matchmade dungeon with weekly modifiers |
| Raid | **THE GREEN TOMB** — 5 encounters, final boss CHALLENGER |
| Meta | Loot/rarity, character progression, vendor + bounty loop, lore collectibles |

---

## 2. WHAT ALREADY EXISTS (build from here, don't restart)

✅ **C++ combat core:** HealthComponent (death/restart events, engine-damage bridge), HitscanWeaponComponent (data-driven), IDamageableInterface, ECC_Pawn trace fixes — the damage loop is proven in playtests.
✅ **Enemy AI:** IBEnemyAIController (patrol/chase/attack, LOS, lose-interest) + IBCharacter_Enemy (fire cooldown, spread, aggro-on-damage, ragdoll death) — this is the **human enemy** base (Wading radicals / Meridian PMC) and the template for kaiju Class D behavior.
✅ **Kaiju framework:** UKaijuSpeciesData (5-tier classification, height→scale, armor pool, organ count) + AIBCharacter_Kaiju (armor-first damage, OnArmorBroken, species-driven setup) — compiled, ready for content.
✅ **Open-world zone 1 started:** Lvl_Plains — 2 km World Partition map, mountain-ring basin, Megascans grass biome (~194K instances), birch stands, 6-building medieval village, daylight pass. **This becomes the Carrow Exclusion Zone.**
✅ **Weapon/character content (Shane, via Multi-User):** SM_Rifle, WBP_Crosshair, BP_IBCharacter_Infantry, BP_IronBreachGameMode, IA_Shoot input, mannequin anim work.
✅ **Pipeline:** UE 5.8, VS 2026, Multi-User server, GitHub repo, Fab asset flow, narrative bible + research doc.

Biggest gaps (honesty first): **networked multiplayer** (everything above is single-player logic — replication is a project, not a task), **save/persistence**, **loot/inventory**, **the frames** (no Caryatid gameplay exists yet), and **all mission/quest scripting tooling**.

---

## 3. SYSTEMS BACKLOG (the invisible 60% of the work)

### 3.1 Netcode & online foundation — *the critical path*
- [ ] Convert combat core to replicated gameplay (server-authoritative damage, health, kaiju AI; client prediction for movement/shooting). Decide early: **listen server (launch) vs dedicated (patch 1)** — recommend dedicated-ready architecture, listen-server ship.
- [ ] EOS integration (already initialized in logs): sessions, matchmaking, friends/party (fireteam of 3 for world/dungeon, 6 for raid, 6v6 PVP), voice optional.
- [ ] Zone instancing model: patrol zones host ~9 players/instance (Destiny-style bubble), campaign private, dungeon/raid/PVP lobbied.
- [ ] Kaiju replication strategy: Class C/B are *large* actors — LOD'd movement replication, server-side destruction states, org an-break events as RPCs.
- [ ] Player persistence: profile, inventory, quest flags, collectible ledger (cloud save via EOS Player Data Storage or simple backend).

### 3.2 The Frames (campaign Acts 2–3 + raid finisher moments)
- [ ] AIBCharacter_Frame (LONGSTONE): two-seat design — Phase 1 scope decision: **pilot + AI co-pilot (Mara)** in singleplayer; co-op second seat is a stretch goal.
- [ ] Frame combat verbs: grapple/lock, seam-blade, resonance trigger (per bible §III.2 — hands finish); frame-scale traversal; artery power meter (mystery bound to gameplay, L38).
- [ ] Sync/clasp UI layer (heartbeat mix, sync bar, Stage-2 tinnitus fingerprint at −30 dB, L27).
- [ ] Scale tech: camera/audio grammar for 90 m machines (bell footfalls), city-block destruction budget.

### 3.3 Loot, progression, economy
- [ ] Rarity ladder: Field / Line / Pattern / Relic / **Halcyon** (exotic tier) — mirror the lore ladder (L21).
- [ ] Weapon archetypes P1: rifle (have), DMR, shotgun, sidearm, LMG, launcher + 1 exotic per slot with lore flavor text (§XII.7 — one sentence of one person's life each; ship "Idris-Pattern" sidearm).
- [ ] Armor sets: infantry set per zone + PVP set + dungeon set + raid set (Green Tomb set = foam-scarred Halcyon salvage).
- [ ] Vendor/bounty loop: Bricks (garrison quartermaster — hub warmth per bible §VI.8), Bellringer engineer (deterrent bounties), Renn terminal (lore-gated).
- [ ] Power/light-equivalent: **Clearance Rating** (gear score) gates dungeon tiers + raid.

### 3.4 Mission & world tooling
- [ ] Quest/objective framework (campaign scripting, side quests, dialogue/radio system with subtitle pipeline).
- [ ] Public event director (spawn scheduling, escalation, zone-wide announce, reward wrap-up).
- [ ] Collectible/ledger system (Field Tags audio, Renn logs, Lampkeeper files w/ redaction rendering §XII.6).
- [ ] The Nine audio fingerprint plumbing: menu hum (Long Nine at 1/100×), NPC nine-tap idle, loading spinner nine segments (§XIII.1) — cheap now, priceless later.

### 3.5 UX shell
- [ ] Director/map screen (zone select, fireteam, event timers), HUD (extraction-count grammar — rescues over kills), settings/accessibility (subtitle sizes, tinnitus-motif toggle for hearing-sensitive players — §XIX.3 spirit), onboarding FTUE.

---

## 4. CONTENT MANIFEST (the visible 40%)

### 4.1 Campaign — "The Waterline" (bible §VII, built to §VII.A's mystery matrix)
- [ ] **Act 1 (M1–M5)** infantry: Landfall, The Fence, Shoal, Cradle Country, The Longest Hour. Deliverables per mission: blockout → scripted beats → VO scratch → art pass → final mix. Rhodes death (M5) and Idris carry (M1) are non-negotiable beats (L3/L36).
- [ ] **Act 2 (M6–M11)** Tandem: Two Hearts (frame tutorial), First Water, The Step, Eddystone (Ward 9 — no-combat third act of the mission), Grief (SIRENA mirror), Anniversary (vault half-truth).
- [ ] **Act 3 (M12–M15)** Iron Breach: The Wading, Ledger (INGOT mercy-kill), Lantern (Marrick's gate, T2/T3 detonation), The Ninth Bell (seal encounter, worldwide silence, post-credit Daniel).
- [ ] Campaign cast VO: player-adjacent radio (Mara, Marrick, Renn, Bricks, Static, Voss, Elber ×2 scenes) — ~8 principal sessions.
- Scope guardrail: 15 missions is AAA-heavy. **Cut-line version: 10 missions** (merge M2→M3, M7→M8, M12→M13) preserves every twist ledger entry (§VIII depends on M1, M4, M5, M6, M8, M9, M10, M11, M14, M15 — those ten are untouchable).

### 4.2 Open-world zones (Destiny-destination pattern)
**ZONE 1 — CARROW EXCLUSION ZONE** (exists as Lvl_Plains: basin plains + village + birch stands + coastal edge to add)
- Biome kaiju roster (match-the-biome rule): Class D "burrow shoal" pack (plains grass), Class D "spire clinger" variant (village/ruin vertical), 1 roaming Class C **PALAWAN-type** (territorial — patrols the artery line through the basin; zone boss telegraphed by birthquake glow).
- Human enemies: Wading radical cells (sabotage camps), Meridian salvage PMC (dispute sites) — reuse existing enemy AI with faction skins/weapons.
- [ ] **Public events (4):** ➊ *Birthquake* — gestation bloom erupts, destroy the bloom before the Class D clutch matures (escalates if failed: mini-boss hatches). ➋ *Shoal Run* — moving pack crosses the zone; intercept before it reaches the village line. ➌ *Grid Failure* — deterrent pylon sabotaged; defend Bellringer engineers through timed repair (Wading attackers + kaiju attracted by the silence — teaches T2's logic wordlessly). ➍ *Convoy* — escort through birthquake terrain (roaming route).
- [ ] **Rare event (1):** *The Vigil* — **SIRENA surfaces offshore and does not attack.** No objective. No reward marker. It watches the old PALAWAN calcification for nine minutes, then leaves. (§VI.9/§XIII.6 — the community-detonator event; spawn odds ~1 %.)
- [ ] **Mini-dungeons / "Undercrofts" (3, lost-sector pattern — boss + chest + collectible):** ➊ *Gestation Hollow* (glassed birthquake cave, D-pack nest boss), ➋ *The Sealed Metro* (pre-Emergence station, Wading cell leader boss, chalk-arrow environmental story §XII.4), ➌ *Listening Post L-9/71* (decommissioned Lampkeeper lamp station — lore-heavy, Q-series file, drone-turret boss; the wellhead plate from M4 sits at its door, L13).
- [ ] **Secret areas (4+):** Elber's lighthouse (unlocked post-M11, downtime scene space), Mara's rowboat cove (memory-bleed echo), a Pilgrim vigil circle (Low Song verse fragment), buried PHAROS-era wreck plate.
- [ ] **Easter eggs (6+):** nine-tap interaction on the garrison bench (tap it nine times…), Static's tuned radios (podcast episodes; one hides the menu-hum spectrogram), tide-mark rings countable on the sea wall (they increment after community rescue milestones), the 1972 plinth rubbing, a Fab-village well that echoes nine beats, dev-room grade "L-0/71" filing cabinet (locked forever).

**ZONE 2 — THE DROWNED QUARTER (Halcyon Approach)** *(new build — coastal ruins biome; doubles as raid staging + asset kit share with raid)*
- Biome kaiju: amphibious Class D "reef" variants (calcified-coral streets), vertical Class C **SUNDA-type** (nests in high-rise husks), tide-cycle spawning (low tide exposes more map + stronger kaiju — mystery on a gameplay axis, L38).
- [ ] Public events (3): *Tide-Wall Breach* (hold the flood gate), *Harvest Dispute* (Meridian tissue rig goes loud — vats hum, INGOT-precursor mini-boss), *Whale-Fall* (Hermit Fleet burial procession protection — Fleet rep intro for Y1 S2 seeding, L34).
- [ ] Mini-dungeons (2): *The Actuary Vault* (Meridian records office — Q10 breadcrumbs), *Chalk Cathedral* (evacuation shelter, wrong-way arrows).
- [ ] Secrets/eggs (4+): raid-door vista (Green Tomb geofoam visible from everywhere in zone — L4), census graffiti preview wall, a drowned cinema playing the Breakwater charter reel.
- Cut-line: Zone 2 can ship 60 % size (raid staging + 2 events + 1 undercroft) if the schedule bites.

### 4.3 PVP — "WARGAMES" (Concord sim-deck framing; lore-safe: no canon deaths)
- [ ] Modes (2): **Skirmish** (6v6 TDM) and **Waterline** (6v6 3-point control; points are deterrent pylons — capture = your team's "grid" sings).
- [ ] Maps (3): *Academy Basin* (Tandem training yard — reuse Carrow kit), *The Step* (Meridian arcology plaza — M8 kit), *Foam Line* (Drowned Quarter edge — Zone 2 kit). All infantry-scale; **frames stay PVE in Phase 1** (balance + scope; "Frame Duels" is the Phase 2 marketing beat).
- [ ] PVP loot set + emblem track; simple seasonal ladder. Sim-deck UI skin (scanline/Concord blue) so the fiction stays intact (§XIX tone).

### 4.4 "Directive Ops" — the Nightfall-style multiplayer dungeon
- [ ] **Dungeon: VIGIL** (bible §X.4): 3-player escort of Low Marta's sanctioned procession through a live Emergence corridor — sing-line safe paths, hold points at vigil stations, finale defense while the hymn completes. ~25–35 min.
- [ ] **Weekly modifier system ("the Learning," bible Y1 S1 as live-ops):** rotating kaiju adaptations (shield-on-flank week, silence-mechanic week, D-pack frenzy week) + Clearance tiers (Adept/Line/Black-Line) with escalating loot.
- [ ] Second rotation dungeon (cut-line optional): *Bolt-Hole Zero* — remix of the Sealed Metro with Wading boss rework, to keep week-to-week variety until patch 1 adds a true second op.

### 4.5 THE RAID — "THE GREEN TOMB" (Phase 1 finale; bible §X.1)
Six players. Port Halcyon, inside the geofoam sarcophagus. Raid-wide mechanic: **the Quiet** (noise meter — weapons, sprints, comms raise it; thresholds wake the Tomb). The campaign taught de-escalation in M15; the raid is the exam. Multiple bosses, unique mechanics, final boss = the thing the campaign has pointed at since M1's podcast: **CHALLENGER.**

- [ ] **E1 — The Foam Gate.** Entry breach: two teams place cutting charges on the sarcophagus wall while managing the zone-wide noise meter; charge timing must interleave with the Nine's ambient pulse (fire on the beat = muffled). Teaches: the Quiet, the beat. Fail state: premature wake tremor wipes the platform.
- [ ] **E2 — The Chalk Ward.** Traverse the preserved evacuation district following survivor chalk arrows — *the marked route is wrong* (the guilt-arrows from §XII.4); teams must find eleven-year-old counter-evidence (bodies, barricades) to identify true paths while a blind burrowing Class C (**the Sexton**) hunts by sound. Boss: the Sexton — kill windows only while it burrows through "loud" false corridors the team deliberately baits.
- [ ] **E3 — The Census.** The memorial graffiti hall: relay encounter — symbol-matching between separated sub-teams (call/response grammar, dyad pairs of players locked in two-man clasp mechanics), guardian waves of Class D. Per-instance census names render here (§X.1's community-scale Halcyon Census; the nine cross-instance names ship day one, L25).
- [ ] **E4 — The Artery Span.** Crossing the exposed, glowing artery rupture on a collapsing viaduct: alternating silence phases (total weapon lockout — movement puzzle under D-swarm pressure) and burst phases; two teams mirror each other's route on parallel spans — one team's noise budget is spent by the *other* team's actions (two hearts, one shore, mechanically).
- [ ] **E5 — CHALLENGER.** Final boss, dormant-reactive, three phases: ➊ *The Sleeper* — DPS only through resonance windows opened by completing call/response port sequences on its calcified mass; noise meter = enrage. ➋ *The Half-Waking* — it rises to one knee; city-block arena reshuffles; players manage wake-thresholds per quadrant while burning armor plates (armor-first damage system already in C++). ➌ *The Tourniquet* — the reveal phase: its exposed core is *knitted into the artery rupture* — killing it outright re-opens the hemorrhage (wipe). Victory = the M15 grammar: de-escalate — complete the full Nine call/response as a fireteam (relay + silence + timed "answer" beats) to lower it back to rest, *then* a single scored finisher window on the bloom-mass parasitizing it. The Tomb ends quieter than you found it (Q3 answered mechanically, never in text).
- [ ] Raid rewards: Green Tomb armor set, 2 raid weapons + **"Idris-Pattern"** exotic sidearm quest, lore book *What The Foam Kept*, the permanent raid emblem, world-first banner in the garrison hub (L25/L33).
- [ ] Post-raid world-state: garrison memorial wall gains the census names; Bricks' ambient VO updates (L37).

### 4.6 Meta/live hooks that ship in 1.0 (cheap now, load-bearing later)
- [ ] Season screen renders the Long Nine loop-length to the millisecond (**8:47.0**, decaying on the authored curve — §XIII.2's public clock starts at launch).
- [ ] Ward 9 hub space (visitable, three beds visible, bed 22 unmarked — Y2 payoff pre-staged).
- [ ] Collectible ledgers wired for growth (Renn logs 1–9 of 27 ship in P1; L-series files 1–6; Old Verses recording #1).

---

## 5. TIMELINE — MILESTONES, DEPENDENCIES, HONEST DURATIONS

**Assumptions:** 2–3 developers (Connor + Shane + possible contractor for animation/VO), heavy Fab/marketplace asset reuse, the C++ core above as the starting point, PC-only, EOS for online. Ranges = focused part-to-full-time. **Total: ~18–24 months to Phase 1 complete.** (With a 4–5 person team or aggressive cut-lines: 12–15 months. This is the honest math — the pillar list is a small studio's product, and netcode is the tax on every feature.)

| # | Milestone | Contents | Depends on | Duration |
|---|---|---|---|---|
| **M0** | *Done* | Combat core, enemy AI, kaiju framework, Zone 1 terrain, bible | — | ✅ |
| **M1** | **Online foundation** | Replicated combat/AI, EOS sessions/party, save/persistence, GameMode split (zone/mission/PVP) | — | 3–4 mo |
| **M2** | **Loot & progression spine** | Inventory, rarity, weapon archetypes, Clearance Rating, vendor/bounty framework, director map UI | M1 (partial overlap OK) | 2–3 mo |
| **M3** | **Vertical slice** | Carrow Zone playable online: 2 public events, 1 undercroft, roaming Class C, loot drops end-to-end + campaign M1 finished quality | M1+M2 | 2 mo |
| **M4** | **Campaign Act 1 + Zone 1 complete** | M1–M5 shippable, all Zone 1 events/undercrofts/secrets/eggs, human factions | M3 | 2–3 mo |
| **M5** | **Frames online + Campaign Act 2** | LONGSTONE gameplay, sync UI, M6–M11 (Ward 9, SIRENA), AI-Mara co-pilot | M4 | 3–4 mo |
| **M6** | **PVP alpha → beta** | Wargames: 2 modes, 3 maps, sim-deck skin, ladder *(parallel track — can start art during M4)* | M1 | 2–3 mo (parallel) |
| **M7** | **Campaign Act 3 + Zone 2** | M12–M15 (INGOT, Lantern, Ninth Bell), Drowned Quarter (60–100 % scope) | M5 | 2–3 mo |
| **M8** | **Directive Ops** | VIGIL dungeon, modifier system, Clearance tiers, weekly rotation | M5 | 1.5–2 mo |
| **M9** | **THE GREEN TOMB** | 5 encounters, CHALLENGER, raid loot, census system, world-first hooks | M7 (uses Zone 2 kit + frame finisher tech) | 3–4 mo |
| **M10** | **Beta, polish, ship** | FTUE, difficulty passes, perf (kaiju replication under load), accessibility, the Nine fingerprint audit, launch ops | all | 2 mo |

**Critical path:** M1 → M2 → M3 → M4 → M5 → M7 → M9 → M10 (≈ 17–23 mo). PVP (M6) and Directive Ops (M8) ride parallel lanes. **First public moment:** end of M3 (vertical-slice trailer — village, birthquake event, Class C on the skyline). **"What the campaign led up to" integrity check at every milestone:** M1's podcast line records before any raid art exists — the foreshadow ships first (L13).

### Cut-lines (pull in this order if the schedule slips)
1. Zone 2 → 60 % scope (raid staging + 2 events + 1 undercroft)
2. Campaign 15 → 10 missions (merge list in §4.1 — twist ledgers intact)
3. PVP 3 maps → 2, one mode at launch (add Waterline in patch 0.5)
4. Second rotation dungeon → patch 1
5. AI co-pilot depth (Mara barks reduced set)
**Never cut:** the Quiet raid mechanic, the SIRENA Vigil event, the Nine fingerprint plumbing, Ward 9 hub, the season-screen clock. These are the franchise (bible §XIII/§XIV).

### Risk register (top 5)
1. **Netcode underestimation** — mitigate: M1 is sacred; no content work before replication proofs (kaiju + 9 players + event director in one zone).
2. **Frame gameplay scope creep** — mitigate: LONGSTONE is a *campaign vehicle + raid finisher*, not a full sandbox system in P1.
3. **Raid encounter iteration time** — mitigate: E1/E4 prototype during M5 with graybox; raid team = whole team for M9.
4. **Two-person VO/anim ceiling** — mitigate: contract 8 VO sessions + mocap library passes; radio-play staging (bible's radio-first grammar is also the budget's friend).
5. **Multi-User vs. game netcode confusion** — Multi-User Editing is an *editor* collab tool; game replication is separate work (M1). Don't let the editor demo create false confidence.

---

## 6. DEFINITION OF DONE — PHASE 1 SHIP CHECKLIST
- [ ] New player: enlist → M1 → guided to Carrow Zone → first public event → first undercroft → first loot upgrade, inside 90 minutes, no walkthrough needed.
- [ ] Campaign completable solo, all 15 (or 10) missions, all §VIII twist foreshadows verified in-build (replay test per L11).
- [ ] Both zones: every event fires on schedule under 9-player load; rare Vigil verified; all secrets/eggs reachable; collectible ledgers record.
- [ ] Wargames: matchmaking under 2 min at beta population; both modes; no PVE-power bleed.
- [ ] VIGIL: matchmade, three Clearance tiers, weekly modifier rotates.
- [ ] Green Tomb: all 5 encounters; noise/Quiet stable at 6 players; census renders per-instance; world-first tracking live; lore book unlocks.
- [ ] The clock: season screen shows 8:47.0 and decays on the authored curve.
- [ ] Post-credit Daniel scene in; Ward 9 visitable; bed 22 unmarked.
- [ ] Save integrity across all activities; disconnect-rejoin works in dungeon/raid.
- [ ] Phase 2 door open: Y1 S1 ("The Learning") content plan approved, UNDERTOW expansion pre-production started (bible §XI).

*Phase 1 ends where the bible's Year 1 begins: the Tomb is quiet, the clock is public, and the community has nine names to argue about.*
