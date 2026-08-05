# Kaiju Fight — Organ Phase Wiring + Test Plan

The boss fight now has a spine in C++: **Armored → OrganPhase → Exposed → Dead**
(demo deliverable d4: armour break, organ phase, death). Compiled and pushed;
everything below is editor wiring + PIE verification.

## What the code does
- Armor pool (existing) soaks everything. On break → **OrganPhase**.
- OrganPhase: hits on live **organ spheres** damage the organ. Body hits are
  dampened (`HardenedBodyMultiplier`, default 0.25) — "shoot the glowing bits."
  Buried organs still work: if the capsule catches a shot aimed at an organ,
  the shot line is extended and the first organ sphere it passes through takes
  the hit.
- Each organ destroyed: kaiju-level event + `OrganBreakDamagePercent` (8%) of
  MaxHealth chunked instantly. All organs down → **Exposed**.
- Exposed: all damage × `ExposedDamageMultiplier` (2.0) until death.
- Zero-armor species skip straight to OrganPhase on first hit; a BP with no
  organs placed skips OrganPhase (fight still completes — nothing hard-locks).
- Replication follows ADR-002: server mutates, OnReps mirror every beat
  (phase, organ pops) on clients. All BP hooks fire on every machine.

## Editor wiring (Connor or Shane, ~10 min)
1. **BP_Kaiju** (or your placeholder kaiju BP): Add Component →
   `IB Kaiju Organ Component` × 3. Drag each sphere onto the body — belly,
   throat, flank. Make them read as targets: add a small emissive sphere mesh
   as a *child* of each organ (cosmetic only). Sphere radius ~80–150.
2. **DA_Kaiju_* species asset**: new `Fight` category — defaults are sane.
   For a fast first test: MaxHealth 3000, ArmorHealth 800, OrganHealth 300.
3. Optional but recommended: **Add Component → IB Loot Drop Component** on the
   same BP, assign a loot table — kaiju death now pays out per-player loot
   (needs the Asset Manager `IBItem` row from MENUS_UI_WIRING §2).
4. BP hooks now available on the kaiju: `On Phase Changed`,
   `On Organ Destroyed (Organ, OrgansRemaining)`, plus existing
   `On Armor Broken` / `On Died`. Wire roars/FX/HUD there when ready.

## PIE test script (in order)
1. **Solo, low-HP species values.** Shoot the kaiju: armor bar should deplete
   with zero health movement. On break: log `armor BROKEN`, log
   `fight phase -> OrganPhase`, `BP_OnArmorBroken` fires.
2. Shoot a **body** part: health moves slowly (0.25×). Shoot an **organ
   sphere**: organ pops after ~300 dmg → log `fight phase` stays OrganPhase,
   `On Organ Destroyed` fires with correct remaining count, health chunks 8%.
3. Pop all 3 → log `fight phase -> Exposed` → body damage now visibly faster
   (2×) → death → `On Died`, corpse stops colliding, despawns ~8s.
4. **Aim test for buried organs**: aim square at an organ half-sunk into the
   torso — it must still take organ damage (the shot-line probe). If a shot
   ANYWHERE on the body pops organs, radii are too big — shrink spheres.
5. **2-player listen server**: client shoots organs — pops/phases/FX must show
   on BOTH screens (OnRep path). Client host-migration not in scope.
6. **Mech test (d4 proper)**: board the mech, kill the kaiju with the cannon.

## Known caveat — check Shane's ArmCannon damage path
If the mech cannon applies damage with the generic **Apply Damage** BP node,
it lands in HealthComponent's AnyDamage bridge and **bypasses armor AND
organs** (pre-existing hole, matters more now). Fix in the cannon BP: on hit,
call the **Handle Take Damage** interface message on the hit actor (pass the
hit result through) instead of Apply Damage. The infantry hitscan path
already does this correctly in C++.

## What I could not test from here
Compile is verified. Everything in the PIE script above is runtime behavior —
needs eyes on screen. Items 1–4 are solo and take ~5 minutes with low values.
