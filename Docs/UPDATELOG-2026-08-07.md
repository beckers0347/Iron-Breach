# IRON BREACH — Update Log · Aug 4–7, 2026

Repo: `beckers0347/Iron-Breach` · commits `1c91d8c → 347eb88` · all builds green · 24 days to demo gate (Aug 31)

---

## Shipped

### Menus / Inventory / Loot spine (`1c91d8c`)
- Applied the Menus_UI bundle: 47 files, ~4,200 lines
- Replicated inventory + equipment on new `IBPlayerState`, click-to-equip request seam
- Ledger (collection log) subsystem, pan-zoom zone map with POI pins, system screen
- Loot tables + per-player instanced drops (your drops are yours — Destiny rule)
- Damage-contributor tracking on HealthComponent (feeds loot eligibility, later assists/XP)
- Two fixes vs the bundle: `Slot` param renames (UWidget::Slot collision)

### Kaiju boss fight — demo d4 (`1366f09`)
- `UIBKaijuOrganComponent`: replicated weak-point spheres, own health pool, collision that weapon traces hit
- Fight phase machine on the kaiju: **Armored → Organ Phase → Exposed → Dead**, replicated with BP hooks per beat
- Species tunables: OrganHealth, HardenedBodyMultiplier (0.25), OrganBreakDamagePercent (8% chunk per pop), ExposedDamageMultiplier (2×)
- Shot-line probe: organs buried inside the capsule still take hits when aimed at
- Docs: `KAIJU_FIGHT_WIRING.md`

### Session flow + menu brains + boot screen (`86b2b0b`)
- `EIBSessionStatus` events on every host/join/leave beat — a silent menu reads as broken
- `UIBMainMenuWidget` C++ base: Solo/Host/Join/Quit optional binds, status line, input-mode law enforced before travel, buttons recover on failure
- Host destination fixed: was stale `Lvl_Plains`, now the same mission map Solo uses
- **Boot screen** (Connor): smoke material + logo flicker + any-key handoff, wired as the game's startup widget
- Docs: `MAINMENU_SESSIONS_WIRING.md`

### Shane's drop (merged `6381380`)
- XP subsystem wired into kaiju armor damage, XP save/tuning, popup widget
- Kaiju auto-spawner + `WBP_KaijuHealth` boss bar
- Amethyst Arc rifle model, scope screen material, kaiju mesh + anim BP
- Merged clean against the organ-phase code — zero conflicts in either direction

### Wiring + live test pass (`347eb88`)
- 3 organ spheres placed on BP_Kaiju (r22, capsule-local)
- WBP_MainMenu reparented to `IBMainMenuWidget`; Btn_Solo/Btn_Quit renamed, Btn_Host/Btn_Join/Txt_Status added; old BP click graphs deleted (C++ owns clicks now)
- DA_Kaiju_Alpha: OrganHealth 60 (was default 4000 vs a 200 HP test body)

## Verified in PIE (tested, not assumed)
- Boot → smoke drifts, logo flickers, any key → menu ✔
- Solo click → mission map, input live, no freeze ✔
- Host click → session created → travel → **listening on port 17777** ✔
- Join with no host → "SEARCH COULD NOT START" narrated, buttons + cursor recover ✔
- Kaiju spawns with 3 organs registered, hunts the player, armor breaks → `OrganPhase` ✔
- Shane's XP hook fires through the armor path without incident ✔

## Bugs found & fixed during testing
- **BP_Kaiju AutoPossessAI was "Placed in World"** — spawned kaiju never got a controller and stood motionless. Now Placed-or-Spawned; the spawner produces a live hunter.
- **4000 HP organs on a 200 HP species** — proportion fixed.

## Known issues / next up
- **Organ pops → Exposed → death**: staged but needs a human 3-minute play test (aim). Each pop should chunk the boss 8%; last pop → 2× damage window.
- **Two-instance Join**: PIE's NULL OSS rejected FindSessions; the failure UX is verified, actual join needs two packaged instances or Steam (Connor + Shane).
- **Host/Join buttons are unstyled gray pills** — awaiting Connor's art pass. Same for the Txt_Status font (suggest Chakra Petch, caps, wide tracking).
- **ArmCannon damage path** (Shane): if it uses the generic Apply Damage node it bypasses armor AND organs — swap to the Handle Take Damage interface message. See KAIJU_FIGHT_WIRING §caveat.
- **Menus content pass** (Shane): BP_IBPlayerState/Controller + GameMode wiring, screen registry, WBPs, IMC_Menus — MENUS_UI_WIRING §3–6. Asset Manager rows (IBItem, IBMapZone) still pending.
- **meshy plugin build junk** broke its third merge — proposal on the table: gitignore `Plugins/meshy/Binaries` + `Intermediate`, needs Shane's OK.
- **First packaged build** (demo d6) — never attempted; highest-risk unknown on the demo list.
- Gunner seat retry still parked (fixes in history, untested).

## Demo gate math (Aug 31)
d1 boot→menu→mission ✔ · d2 infantry combat ✔ · d3 board + drive ✔ · d4 kaiju kill — one play-test from done · d5 Steam co-op — host proven, join needs the 2-instance test · d6 packaged build — not started. **Call it 3.5 / 6 with 24 days.**
