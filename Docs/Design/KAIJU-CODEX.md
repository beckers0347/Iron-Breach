# KAIJU CODEX — Phase 1 Species Roster
## v1.0 · Aug 2026 · canon: Narrative Bible §I.2/§II · schema: `KaijuSpeciesData.h`

Purpose: one `DA_Kaiju_*` asset per row, creatable today with the fields that already exist (MaxHealth, ArmorHealth, OrganCount, OrganHealth, HardenedBodyMultiplier, OrganBreakDamagePercent, ExposedDamageMultiplier, HeightMeters, WalkSpeed). Numbers are FIRST-PASS tuning seeds calibrated against current weapons (rifle 25/hit, mech cannon ~BaseDamage on DA_ArmCannon) — tune in playtest, keep the RATIOS.

Doctrine reminders (bible-locked): species get field designations; **individuals** (Class A+) get hadal-trench names and documented behavior. Kaiju gestate in bedrock, erupt, execute a function, and calcify if uninterrupted. They are grown, not sent. Paired ganglia = the organ system's fictional root — every kaiju's weak points are its dyadic signal nodes, which is WHY popping them staggers it: you are interrupting a sentence.

---

## CLASS D — "Shoals" (20–40 m, swarm/pack) · infantry content
| Species (field name) | Role | HP | Armor | Organs × HP | Ht | Speed | Notes |
|---|---|---|---|---|---|---|---|
| **SKITTERLING** | pack rusher | 400 | 0 | 1×100 | 8 m* | 550 | The daily grammar. No armor phase — first contact goes straight to OrganPhase. Spawned 4–8 |
| **CARAPACE** | pack anchor | 1,200 | 400 | 2×150 | 15 m | 300 | Teaches the armor phase at squad scale |
| **LAMPREY** | wall-crawler | 800 | 150 | 1×200 | 12 m | 480 | Vertical threat for city blocks; organ on the BACK (placement teaches repositioning) |

*Class D fiction floor is 20 m; gameplay uses smaller "juvenile shoal" variants so infantry combat reads — codex logs them as immature instances. The 20–40 m table entries are the ADULTS (mini-boss tier): **SKITTERLING BROODMOTHER** 2,500/800, 3×250, 24 m, 260.

**M1 opening contact:** the garrison's Act III skirmish (see mission doc) uses 3–4 stock SKITTERLING/CARAPACE instances, no new DA needed — infantry plus the one on-base mech hold the line. This is deliberately winnable, so PALAWAN's Class B reveal right after reads as a real step up rather than more of the same.

## CLASS C — Territorial (40–80 m) · squad + heavy weapons, mech optional
| Species | Role | HP | Armor | Organs × HP | Ht | Speed | Notes |
|---|---|---|---|---|---|---|---|
| **BASE KAIJU → rename RIDGEBACK** | the demo boss | 3,000→12,000 | 800→4,000 | 3×60→3×900 | 5→48 m | 250 | Current `DA_Kaiju_Alpha` IS this species at test values; left column = today, right = real tuning when the mech fight is calibrated |
| **MAWCROWN** | siege biter | 16,000 | 6,000 | 4×800 | 62 m | 200 | Armor concentrated frontally (place organs flank/rear — forces the squad to split from the mech) |

*(PALAWAN reclassified to Class B — see below. M1's opening skirmish now uses a handful of Class D individuals instead; see that section.)*

## CLASS B — Aggressive (80–120 m) · Tandem warfare begins
| Species | Role | HP | Armor | Organs × HP | Ht | Speed | Notes |
|---|---|---|---|---|---|---|---|
| **PALAWAN** *(individual, M1)* | first contact | 40,000 | 16,000 | 4×2,200 | 82 m | 210 | RECLASSIFIED from Class C (was: campaign boss, 20,000/7,500/3×1,200/74 m — numbers below are the real tuning, keep the old row out of continuity). The franchise's first confirmed Class B contact — lower end of the tier on purpose, since one under-crewed garrison mech has to survive contact with it, not win. Doctrine still holds: infantry cannot break its armor. Ends M1 by throwing the garrison's mech off the battlefield into the mountains (Act V) — not defeated, disengages/calcifies afterward per the original Aftermath beat, just post-engagement instead of un-engaged. Its species template doubles as the B-class floor. |
| **BULWARK** | the wall | 45,000 | 20,000 | 4×2,500 | 95 m | 150 | The bible's line: "nothing on treads reliably stops one." Infantry CANNOT break its armor alone (HardenedBodyMultiplier 0.15) — the fight that sells boarding the Caryatid |
| **TONGA** *(individual, M5)* | bridge-breaker | 55,000 | 24,000 | 4×3,000 | 96 m | 180 | Kills Lt. Rhodes. Faster than BULWARK; its speed IS the horror |
| **VITYAZ** *(individual, KIA 2035)* | codex-only | — | — | — | 110 m | — | The frame program's stolen anatomy source. Ledger entry, never fought — DATA SEALED until Y1 |

## CLASS A — Highly Intelligent (120–200 m) · raid tier, ELEVEN individuals ever
Phase-1 ships ONE, as the Green Tomb raid's living gatekeeper (the raid's true center is CHALLENGER's calcified body — Raid 1 answers "what was its function" wordlessly, bible §X.1):
| Individual | Official / soldier name | HP | Armor | Organs × HP | Ht | Notes |
|---|---|---|---|---|---|---|
| **SUNDA** | "Warden" to the line units | 220,000 | 90,000 | 6×8,000 | 150 m | Patrols the Green Tomb approaches like it is GUARDING the corpse (feeds Reading A). Raid boss: armor break per-limb, organ phases gated by mechanics, Exposed windows timed |
| *(reserve: SIRENA "Grief")* | Y1 raid | — | — | — | 170 m | Codex stub only, DATA SEALED |

## CATASTROPHE (200 m+) · never a health bar in Phase 1
CHALLENGER (the Green Tomb itself), HORIZON (2043), ATACAMA (2045): environments and history, not encounters. CHALLENGER's calcified mass is Raid 1's terrain. Rule: a Catastrophe fight is a franchise event, not a content drop.

---

## Organ placement grammar (per class, matches the shot-line probe)
- **D:** 1–2 organs, big and readable — teaching tier.
- **C:** 3 organs — one front-low (free), one flank (movement), one high/rear (mech or coordinated). The demo RIDGEBACK follows this.
- **B:** 4 organs, none reachable from the ground alone — two require the mech's height, ONE requires an infantry player on the kaiju-facing scaffolds/ridges while the mech holds aggro (the co-op sentence in one anatomy).
- **A:** 6 paired organs — three DYADS. Raid rule: a dyad only stays down if both nodes die within a short window (the dyadic grammar as mechanics; bible §II.3). Singles regenerate.

## Ledger integration
Every species above = one `DA_Item_*` (Category=Collectible, bShowInLedger) OR the codex rides the kaiju DA directly in a later pass. FieldGuideEntry text: write in the Breakwater's clinical-with-scars voice, one sensory detail per entry, no lore dumps. Undiscovered = DATA SEALED (already supported). Individuals' soldier-name reveals are Ledger discoveries, not cutscenes.

## Asset checklist (Shane / scripted)
1. Rename `DA_Kaiju_Alpha` → `DA_Kaiju_Ridgeback` when convenient (redirector-safe moment only).
2. New DAs per row: D-tier first (Skitterling/Carapace reuse current mesh at different scales — species system already handles it).
3. Spawner pools: `MinClass/MaxClass` already filter — Carrow zone pool = D swarm + C solo; TestLevel1 = Shane's call.
4. The python asset script can generate all of these next session — say the word.
