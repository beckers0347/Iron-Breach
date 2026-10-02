# Garrison RS1 rear shore preview: result (2026-10-01)

Claude, 04:35 UTC. Answers `Docs/CLAUDE_GARRISON_REAR_SHORE_PREVIEW_2026-10-01.md`.

**Scope held.**

- One new disposable candidate, `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1`, copied from PS1. It is the only Content file this task wrote: every job reports `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`.
- PS1's map, decal material and receipt, the live map, every earlier candidate and receipt, and every mesh and material RS1 references are unchanged (section 7).
- No C++ build. No shared asset, config, source, water or physics change. No live promotion, Git, locks, commit, push, cleanup or messages to others. No service buildings, and nothing built for or resized at Connor's hangar.
- Engine runs used the isolated UserDirs `user/` and `user-gui/` inside the evidence folder. All four save files still match Codex's recorded bytes.
- The queue again holds only the inert `153-yellow-after.hold`.

**Outcome.** RS1 attaches the compound's rear to the mainland and wraps both rear corners with a rocky, wooded shore along the reviewed waterline. It keeps the gate, the ramp and Connor's reservation.

- The reviewed 254-piece plan was applied first (**r1**). Its captures showed a 7.5 m staircase along both new coasts.
- **r2** changes new pieces only: 73 documented deviations on top of the reviewed plan, giving **284 new actors**. Every one of PS1's 3257 inherited actors is identical.
- The actual infantry pawn, in scripted PIE (not manual play):
  - drops off the rear wall onto the new land and returns through the ramp and gate;
  - is moved back onto the new coast at all 4 coast spots, as the existing `Drown()` snap-back does;
  - fails all 18 climb attempts via the rocks and trees.

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1`<br>`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1.umap`<br>SHA256 `882F9D2060EC97916B919C6EA969D361D546FAAE49D8AA17C7510E45DD94A870` (RS1 r2 applied) |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_RearShore1.json`, SHA256 `0033AAD5FC0112B12BBEBE92B68AF8C5541005F5ABAB4FFA143FF5877979042F`.<br>History: created → applied r1 → reverted → applied r1 → reverted → applied r2 → reverted → applied r2. Each entry records the file hash; each apply and revert also records the plan hash. Each apply records the exact object identity of every new piece. |
| **Changed counts** | PS1 3257 actors → RS1 **3541**: 3257 inherited (all identical) + **284 new**.<br>The 284 are 43 land slabs, 28 coast bands, 2 wall bands, 9 terrace slabs, 54 rocks and 74 trees × 2 (canopy + trunk).<br>r2 trims 43 land slabs and adds 30 bands; the terrace, rocks and trees are unchanged from the reviewed plan. |
| **Lifecycle** | **PASS** for r1 and r2:<br>• clean copy verified actor for actor;<br>• plan checked against the copy's fingerprint digest;<br>• saved apply and reload verify;<br>• saved repeat is a no-op (byte-identical file);<br>• 4 ownership negative tests refused or failed to verify, with nothing saved;<br>• exact revert back to PS1's state;<br>• final re-apply.<br>Final verify: 3257 identical, 0 changed, 0 missing, 284 planned, 0 unexpected (section 3). |
| **Bounds and collision** | **Gate corner:** `Land_10/11` overlap the gate mesh's box in plan only. In 3D they sit 3.81 m below it, and the gate mesh has no collision.<br>**Mountain rocks:** oriented boxes reach 1.05–1.11× the plan radius, all inside the plan's 15 % margin. Wall rocks stay ≥ 1.77 m below the deck top; terrace-face rocks ≥ 1.87 m below the terrace top.<br>**Reservation, side bands and approach:** 0 overlaps. The terrace's faces touch the +Y band's outer edge.<br>**Coast (25 cm grid, 9 m deep):**<br>• r1: 129 m² of water inside the line, 74 m² of land outside it;<br>• r2: **0 m²** of water inside, 1.4 m² of land outside (≤ 33 cm).<br>**Contacts:** 166 engine contacts, all expected by rule; 0 unexpected.<br>**Ramp:** three capsule lanes clear. |
| **Pawn routes** | Scripted PIE, job 186, game time:<br>• settled spawn at PlayerStart;<br>• PlayerStart → spine 10.6 s; reservation mouth → spine 10.4 s;<br>• Barracks door 1.53 s; Armory door 6.77 s;<br>• terrace step 3.4 s and 3.73 s (two faces, up and back);<br>• city road → ramp → gate 21.7 s;<br>• **shore drop and return through the gate: 8/8 in 19.27 s**;<br>• **4/4 coast drown recoveries onto the new land**;<br>• **18 climb attempts, 0 bypasses** (section 5). |
| **Spawner** | `BP_M1_KaijuSpawner`, read every 0.5 s and not changed.<br>• Spawning stayed enabled throughout.<br>• Both zone spheres (30 m, 100 m) have collision disabled in this level, so neither reported an overlap. This is true even while the pawn was within 100 m: 25 of the 39 shore-return samples, minimum 70.2 m.<br>• 0 Kaiju at every sample. |
| **Board** | `board/rs1-board.png` (1940×3126; JPG copy). Every tile is labelled as RENDER, PICTURE or DIAGRAM:<br>• matched PS1/RS1 overheads;<br>• the approved picture and RS1 reprojected into its fitted framing, with the picture's own waterline overlaid;<br>• r1 vs r2 top-down;<br>• a footprint and PIE-path diagram;<br>• both coasts;<br>• six eye-level views (section 6). |
| **Preservation** | At 04:07 UTC:<br>• Codex's 456 records: **456/456 match**;<br>• all 1249 project files of this task's first stamp: 0 changed;<br>• all 14 before/after stamps of jobs 180–186 are byte-identical;<br>• live map `FAFFD601…` unchanged;<br>• the four save files match Codex's bytes. |
| **Processes and errors** | 35 engine processes, all owned and all exited; `OWNED_PROCESSES_LEFT=0` after every job.<br>• 32 commandlet steps exit 1 (the known GameFeatureData ensure) with complete reports.<br>• 3 GUI editors exit 0.<br>• No access violation, crash or fatal error.<br>• Error lines match PS1's baseline exactly. The only additions are the intended refusals of the negative tests (section 7). |
| **BP_Mech correction** | The reference-fit checklist's "`BP_Mech` is still missing" is stale. BP_Mech was restored on Sept 30, crew QA passed on the restored set, and it was pushed as `e106831`.<br>Currently observed: BP_Mech loads but logs the same 7 Blueprint compile-error lines as in PS1's runs (section 8). Not repaired. |
| **Next composition gap** | **Flank service rows** (the reference-fit's gap 2). Assets and ownership block it, not layout tooling (section 10). |

## 2. What RS1 adds

### 2.1 The plan, regenerated from the copy

- **Copy.** Job 180 copied PS1 (`4AC42632…`) to the new map (`FA1BAFB0…`).
  - In a new process, it verified the copy actor for actor and component for component: 3257 actors, 3284 components.
  - It wrote the copy's own fingerprint: `run1/copy/copy_fingerprint.json`, digest `33F5D04D…`.
- **Regeneration.** `plan/rs1_regen.py` re-ran the reviewed dry run from that fingerprint.
  - Result: *"regenerated plan identical to the reviewed plan (pieces, counts, checks)"*.
  - The regenerated manifest is byte-identical to the reviewed one (`F41C15C3…`).
  - The geometry is identical apart from provenance.
- **Engine plan.** `plan/rs1_engine_plan.py` converted it to the engine plan `plan/rs1_engine_plan.json` (r1, 254 pieces).
- **Digest gate.** Before any mutation, the engine tool compares the open level's fingerprint digest with the digest the plan was built from. It matched in every plan-check (jobs 181, 182, 184).

Every piece is a new `StaticMeshActor`:

- labels `IBGC_RS1_*`;
- tags `IB_GarrisonCB1` and `IB_GarrisonRearShore`;
- folder `Carrowgate Garrison/Rear Shore RS1`;
- existing meshes and materials only, referenced without edits (`/Engine/BasicShapes/Cube` and `Cylinder`, `M_AI_MountainGround`, the three mountain meshes with their `M_AI_MountainRock_*` materials, eight GV_Vol7 shrub meshes with mesh-default materials, `M_Bastion_Bark`).

### 2.2 Why there is an r2: the coast staircase

r1 was applied, verified and captured (jobs 182 and 183). Its stills showed what the reviewed plan had accepted (top-down on board row 3, left; coast obliques in `check-rs1/editor/`): the land is a set of 7.5 m x-bands, so both new coasts form a 7.5 m staircase. Measured on a 25 cm grid within 9 m of the reviewed coast line:

- r1 left **129.25 m²** of water inside the line;
- it put **73.69 m²** of land outside the line, up to 3.29 m beyond it (`analysis/bounds_check_r1_rerun.json`).

The brief authorises small changes to new pieces for visible coast gaps, so r2 replaces the staircase. **Inherited actors, the coast line, the terrace, rocks and trees are unchanged.**

### 2.3 r2 deviations (new pieces only)

`plan/rs1_coast_r2.py` (offline) writes `plan/deviations_r2.json` (`9A6C0884…`, diagram `plan/coast_r2.png`). `rs1_engine_plan.py` applies it to give `plan/rs1_engine_plan_r2.json` (`9711DEBA…`) and `plan/rs1_engine_manifest_r2.csv` (`6C1F790D…`). The manifest has 284 create rows plus a hold row; the 73 changed rows name their deviation.

| Deviation | Count | What |
|---|---|---|
| Slab trims (`set`) | 43 | Each land slab shrinks to the largest rectangle of its own footprint that lies inside the reviewed coast line. Per slab, the largest end move is 0.8 cm to 6.71 m (median 5.9 cm). Total slab area goes from 13,111.5 to 12,803.9 m². |
| Coast bands (`add`) | 28 | Rotated `Cube` bands in the land material, top −6 (1 cm under the land top so they never z-fight). Each band's outer edge lies on its coast segment.<br>15 bands on the left: 11 segment bands, 3 narrower attach bands and one axis-aligned filler, `Coast_L_AttachFill`, at the corner where the coast meets the forecourt's side. 13 bands on the right.<br>Widths 0.24–6.27 m, 329.5 m in all. Every band stays ≥ 10 cm off the deck and the ramp. |
| Wall bands (`add`) | 2 | `IBGC_RS1_Wall_00/01`, 10.3 × 1.8 m, top −6. They fill the two water wedges between the land and the chamfered deck walls beside the ramp, 10 cm off the deck face. |

**Coverage after r2** (same grid, from the **engine** footprints of job 184's bounds stage, `analysis/bounds_check_r2.json`):

- **0.0 m²** of water inside the line;
- 1.44 m² of land outside it, ≤ 33.4 cm, at convex band joints.

### 2.4 Visual consequence recorded in the receipt

The terrace (top 400) covers the parts of nine FF1 pieces that lie under it:

- coping `IBGC_FF_Fore_Coping_06/07/08` (`StaticMeshActor_181/182/183`);
- fascia `Fascia_08/09/10` (`_192/193/194`);
- edge lines `EdgeLine_06/07/08` (`_201/202/203`).

That is about 75 m of FF1's rear-left quay trim. These actors keep their exact bytes, transforms and properties; their buried parts are just no longer visible. The receipt's `ownership.visual_consequences` records the nine identities, their kinds, and the note that reverting RS1 shows them again unchanged. The pad ring and straight-line rendering were not touched.

## 3. Lifecycle and ownership

Every step is its own `UnrealEditor-Cmd` process with the isolated `user/` UserDir. Times are UTC.

| Job (UTC) | Step | Result | Map after |
|---|---|---|---|
| 180 (02:30–02:33) | base fingerprint; copy; copy verify | 3257 identical, 0 changed, missing, extra or unexpected | `FA1BAFB0…` |
| 181 (02:34–02:36) | plan-check; bounds r1 (254 pieces spawned **in memory**, never saved) | digest match, preflight clean; 0 piece issues; map unchanged | `FA1BAFB0…` |
| 182 (02:41–02:51) | r1: plan-check, apply+save, verify, saved repeat, 4 negatives, revert+save, verify, re-apply+save, verify | each verify vs PS1: 3257 identical, 254 planned, 0 unexpected; repeat byte-identical; revert verify: 0 extra | `06C7DC08…` → `DBBA7FB5…` → `742F760F…` |
| 184 (03:27–03:39) | r1 revert+save and verify (with the r1 plan); r2: plan-check, bounds (in memory), apply+save, verify, saved repeat, 4 negatives, revert+save, verify, re-apply+save, verify-final | all complete; final: **3257 identical, 0 changed, 0 missing, 284 extra = 284 planned, 0 planned missing, 0 unexpected** | `4C0E3FDB…` → `EE83A180…` → `11FC95C6…` → `882F9D20…` |

**Saved repeat.** It reports `already-applied-verified` and saves nothing; the file stays byte-identical (r1 and r2).

**Revert and re-apply bytes.** The reverted and re-applied files did not equal earlier bytes (r1 and r2): a save re-serialises the level. The re-created actors got the same object names each time, as the receipt records. The actor-for-actor fingerprint comparison is the check.

**Ownership rule.** It is written into the receipt. An actor is RS1-owned only if it carries `IB_GarrisonRearShore` **and** its object name, label, class and mesh equal a recorded identity. `IB_GarrisonCB1` alone never selects anything. Revert refuses before changing anything on any conflict. After removal, it saves only if the level's fingerprint again equals PS1's.

**Negative tests.** Each ran in memory with saving blocked. The map was hashed before and after (unchanged), for r1 and again for r2:

| Decoy added in memory | Outcome |
|---|---|
| An extra Cube carrying both RS1 tags with an unrecorded label | REVERT REFUSED: 2 conflicts; nothing changed |
| An untagged Cube using a planned RS1 label | REVERT REFUSED: 1 conflict |
| A Cube with only the shared `IB_GarrisonCB1` tag | Not selected. After removal the level differed from PS1 in 1 way, so the revert did not verify and nothing was saved |
| One recorded RS1 actor with its RS1 tag removed | REVERT REFUSED: 3 conflicts |

**Backups** (evidence only): `backup/RearShore1-copied.umap` (`FA1BAFB0…`), `RearShore1-applied.umap` (`06C7DC08…`, r1) and `RearShore1-r2-applied.umap` (`EE83A180…`).

## 4. Engine bounds and collision

**Bounds stage.** The tool's bounds stage spawns every planned piece **in memory** exactly as apply would, never saving (jobs 181 and 184). It records:

- each piece's actor box and the oriented box of its mesh bounds under its real transform;
- the same for the inherited anchors;
- each mesh's collision setup.

`analysis/rs1_bounds_check.py` tests these offline (`bounds_check_r2.json`). The GUI runs then ran engine collision queries in the editor world.

| Check | r2 result |
|---|---|
| **Gate corner, `Land_10/11`** | Their footprints overlap the gate mesh's oriented box in plan, about 1.0 × 2.2 m each, but there is **no 3D intersection**: land top −5, gate mesh base 376, a gap of 3.81 m. `Wall_00/01` also lie under that box in plan, 3.82 m below. The gate mesh `SM_MainGate_Tripo` has **no collision**. The gate leaf (`BP_MainGateDoor`, BlockAllDynamic) has no new piece within 50 cm. |
| **Mountain-mesh bounds** | The 54 rocks' oriented-box radius is 1.05–1.109× (median 1.097) the dry run's median-width radius. None exceeds the plan's 15 % safety radius; tops are within 0.1 cm of plan.<br>Wall rocks: tops ≥ **1.77 m** below the deck top (385). Terrace-face rocks: ≥ **1.867 m** below the terrace top (400). |
| **Collision setups** | Land, bands and terrace (`Cube`): one simple box each. Rocks: one convex hull each. Trunks (`Cylinder`): one simple shape each.<br>The 8 shrub canopy meshes have **no simple collision shapes** (`CTF_USE_DEFAULT`). They carry BlockAll like the mainland's trees, but the pawn's movement sweeps pass through them. |
| **Reservation** (x −500…4390, y 1819.4…5680.6) | 0 overlaps with the reservation, both 6 m side bands and the approach band x 4390…10182.<br>The check lists two zero-gap entries: `Terrace_00/01`, whose −Y faces lie exactly on the 6 m line (engine y-min 6280.6). They touch it and do not overlap.<br>`Land_13` abuts the deck's rear face from outside, 10 cm beyond x −500, as intended. |
| **3D box overlaps with anchors** | 82 overlap candidates. 61 are expected by rule: the terrace over the buried deck edge, and land or bands meeting `CityGround_00`. The other 21, all explained:<br>• 5 terrace rocks (`Rock_049…053`) whose bases are embedded 50 cm in the terrace above the buried deck edge;<br>• 2 canopies (`Tree_032`, `Tree_061`; no collision) whose foliage hangs over the terrace or quay edge, by up to 2.2 m on the box estimate;<br>• `Rock_034`'s base embedded in the mainland ground.<br>r1's one land-vs-fascia candidate (`Land_15` / `Fascia_09`) is gone in r2. |
| **Engine contact queries** (job 186; each anchor's and each slab's own box as a trace for objects) | 166 contacts, **all expected by rule; 0 unexpected**:<br>• 82 slab or band bottoms (−40/−41) dip 5–6 cm into the hidden `Water_Placeholder`, read as `OverlapAllDynamic`, query only, overlap to Pawn and WorldStatic: it blocks nothing;<br>• 76 are terrace or terrace rocks over the buried deck edge;<br>• 8 are `Land_00/01`, `Coast_L00` and `Coast_R12` meeting `CityGround_00`, each counted from both sides. |
| **Ramp** | Three pawn-capsule lanes (y −750, −250, 250) are clear. Floor 18.8…377.1, largest step 4.2 cm, only `IBGC_Ramp_Deck_00` underfoot, no blocker. |
| **Slab steps, water holes, exposed faces** | r1's 7.5 m staircase is replaced (2.2).<br>The bands' and slabs' side faces show 29–30 cm above the water (−35 to −6/−5) as a thin dark line at the waterline (shore still).<br>On land, joints between slabs and bands show as faint lines: a texture seam, plus a 1 cm step where a band (top −6) meets a slab (top −5). |

## 5. The actual infantry pawn (scripted PIE, not manual play)

**Setup.** `BP_IBCharacter_Infantry_C`:

- capsule radius 34, half-height 88; max step 45 cm; walkable angle 44.8°; max walk speed 600;
- jump Z 420 at gravity −980, giving a **90 cm apex**.

**How it was driven.** A Python script drove it with movement input and jumps in a GUI editor PIE session, with a fixed 1/30 s step.

- The script's attempt to switch off the editor's background throttling reported "unavailable".
- PIE averaged about 19 frames per wall second in job 185 and 36 in job 186 (log frame counter).
- All limits and times are game seconds, so the frame rate changes only wall time.

**No person played.** Not exercised: camera and aim, sprint and aim-down-sights movement, abilities, and multiplayer.

**Authoritative run.** Job 186 (`check-rs1-r2b/rs1_checks.json`, 03:58–04:03 UTC, editor exit 0) used `tools/ib_garrison_rearshore_check_r2b.py`. That is job 185's check script with three classifier corrections and two read-only additions:

- **Corrections.**
  - The stall rule now uses path length, not net displacement. The +Y terrace route goes out and back, so it passes its own earlier points.
  - r2's coast and wall bands count as new land in the drown verdict.
  - The contact rules know the bands and the overlap-only water placeholder.
- **Additions:** the landing floor of the shore drop, and the spawner zones' own settings.

**Job 185's pawn data agrees.** It recorded the same routes and times on the same map bytes. The exception is the +Y terrace route, which job 185 stopped at 3.03 s and labelled "stalled" while the pawn walked back down at 600 cm/s. It labelled the four drowns "not onto the new land" while they ended on `IBGC_RS1_Coast_*`. Job 185 remains the source of the stills.

| Route | Kind | Result (job 186) |
|---|---|---|
| Settled spawn | existing | At PlayerStart's x/y (offset 0 cm), z 475.2 on `IBGC_Forecourt_Deck_02`. Capsule bottom 2.2 cm above the floor, speed 0, after 1.0 s. |
| PlayerStart → spine | existing | reached 3/3, 10.6 s (PF1: 10.48 s) |
| Reservation mouth → spine | existing | reached 3/3, 10.4 s |
| Barracks door route | existing | reached, 1.53 s (FF1 job 164: 1.53 s) |
| Armory door route | existing | reached, 6.77 s (FF1: 6.8 s) |
| City road → ramp → gate → gate road (130.6 m) | existing | reached 4/4, 21.7 s (FF1: 21.6 s), through the gate; no teleport |
| Terrace step, +Y face (from the reservation's side band) and back | new | reached 2/2, 3.4 s; stood on the terrace (capsule centre 490.1 = terrace 400 + half-height 88 + 2.1) |
| Terrace step, +X face (from the forecourt) and back | new | reached 2/2, 3.73 s; stood on the terrace (490.2) |
| **Shore drop and return** (116.8 m) | new | Walked off the rear wall at y −2150 and **landed on `IBGC_RS1_Land_06` (floor −5)** at (−1099.5, −2145.9) after 1.47 s. Walked across the strip land and the mainland ground to the ramp foot, then up the ramp and through the gate. **Reached 8/8 in 19.27 s, back on `IBGC_Forecourt_Deck_02`**. No teleport. |
| **Coast drown recoveries** (2 spots per shoulder) | new | **4/4 "recovered onto the new land."** The pawn walked off the coast; its last recorded capsule centre was −30.2…−35.0. Then, 1.43–1.47 s after the walk began, it moved back 2.8–3.0 m inland in one frame, onto `IBGC_RS1_Coast_L02` (twice), `Coast_R07` and `Coast_R11` (r2 coast bands, floor −6). It was still standing there 2 s later.<br>This matches the existing `Drown()` snap-back in `Source/IronBreach/Infantry/IBCharacter_Infantry.cpp`: `Tick()` calls `Drown()` once the actor's Z drops below `DrownWaterZ` (−35), and `Drown()` teleports the pawn to its last grounded location. The check records the move, not the call; that log line is Verbose. |
| **Climb attempts** | new | 6 targets × 3 starts, each 10 s of movement input with 12 jumps:<br>• wall rocks `Rock_042` (top 208, left wall), `Rock_036` (186, rear wall behind the reservation) and `Rock_038` (173, right wall);<br>• terrace-face rock `Rock_048` (213);<br>• canopies `Tree_032` and `Tree_061` beside the terrace.<br>**18 attempts, 0 bypasses.** Every attempt ended on new land at −5, blocked by the deck or terrace face. Highest capsule centre 175.1, i.e. a 90 cm jump from the land. |

**What this means.**

- The new land is reachable only by dropping off the walls or walking in from the mainland.
- The way back onto the compound is the ramp and gate. None of the 6 tested rock and tree targets served as a step.
- At the 4 tested spots, the new coasts hand the pawn back to land, as the existing `Drown()` snap-back does.

**No gameplay dependency is left unresolved by RS1.** No barriers, rails or gameplay changes were added.

**Spawner during the return** (read only). `BP_M1_KaijuSpawner` at (−10617, −105, 7):

- `IsSpawningEnabled` stayed true at all 39 shore-return samples and all 44 land-join samples.
- Its `SpawnZone` (r 30 m) and `ProximityZone` (r 100 m) spheres have **collision disabled** (`NO_COLLISION`; Custom profile, Pawn response Overlap, overlap events on). Neither reported an overlap.
- That held even though the pawn was inside 100 m of the centre for 25 of 39 return samples (t 1.5–13.5 s, minimum 70.2 m), and for 10 of 44 samples on the existing land join (minimum 71.7 m).
- 0 Kaiju actors at every sample.
- RS1 changes nothing here. Whether the spawner's blueprint enables the zones in another mission state was not explored.

**Superseded r1 run.** Job 183 (r1, 02:51–03:06) averaged about 7.6 frames per wall second in PIE (log frame counter). With the fixed 1/30 s step, its game clock ran at about a quarter of real time, and its limits were measured in wall-clock seconds. The spawn was not settled (z 504, moving) and the two spine routes timed out. Both terrace routes were recorded as "stalled" on the terrace by the displacement-based stall rule that job 186 replaced. Its climbs, 0 bypasses in 18, and its shore return, 8/8, agree with r2.

## 6. Captures and board

**Stills.** Job 185's editor stills (`check-rs1-r2/editor/`) are level-viewport high-resolution renders in game view: 90° lens, 1920×1080, no actor spawned, world lighting unchanged.

**Board.** `analysis/rs1_board.py` assembles `board/rs1-board.png`:

| Row | Tiles (label as on the board) |
|---|---|
| 1 | **BEFORE PS1 (RENDER: editor still, job 178)** at PS1's overhead-reference camera, eye (28513, 3750, 19795) → (11351, 3750, 385). This is the existing PS1 image, not re-rendered.<br>**AFTER RS1 r2 (RENDER, job 185)**: the same camera and lens. |
| 2 | **THE APPROVED PICTURE (unchanged pixels)**.<br>**RS1 in the picture's framing (RENDER, reprojected) + OVERLAY.** A 7680×4320 still from the fitted eye (56311, 5969, 40946), yaw 183.76°, pitch −42.11°, was resampled to the fitted F 4000 px lens and 1.06° roll on 1672×941. That is exact, since both cameras share the eye (`board/rs1-reference-framing.png`). The overlay dashes are the picture's own waterline (green) and compound edge (amber) pixels, and the fit matches the picture's anchors to about 20 px rms. |
| 3 | **RENDER (r1, SUPERSEDED)** rear top-down, job 183; **RENDER (r2, FINAL)** rear top-down, job 185; **DIAGRAM (not a render)**: engine footprints and job 186's recorded PIE paths. In the diagram, white is the shore drop and return, cyan dashed the land join, blue the drown walks (dot = where Drown put the pawn back), and × the highest point of each climb. |
| 4 | RENDER: left and right shoulder coasts (oblique); new land behind the rear wall (eye level). |
| 5 | RENDER, eye level: ramp foot → gate (city road); **gate road → gate** (inside); **forecourt → terrace**. |
| 6 | RENDER, eye level: terrace edge → left shoulder; **left shoulder shore**. |

The header restates the counts and the scripted-PIE outcomes. Its PIE line says "real infantry pawn driven by script, not a person".

**What the images show.**

- The rear now reads as attached land.
- Both coasts are continuous lines on the reviewed waterline. In the reprojected tile they lie close to the picture's own waterline pixels on the left side and within a few metres on the right.
- The straight mainland edge remains only beyond the shoulders.

## 7. Preservation, processes and errors

**Hashes** (`analysis/rs1_preservation.py` → `hashes/preservation-final.json`, 04:07 UTC):

- **Codex's list** (`20261001-codex-referencefit-review/protected-current.json`): 456 records, 455 distinct files (the live map is listed in both slash styles). All 456 rehashed and matching; 0 mismatches.
- **This task's first stamp** (`hashes/shared-before-180.json`, 1251 files): Codex's list, PS1's evidence, the reference-fit packet, Codex's two review folders, every mesh and material RS1 references, and the two engine BasicShapes. The 1249 project files were rehashed now: 0 changed. Each job also compared the two engine files itself.
- **Before/after stamps.** All 14 (jobs 180–186) are byte-identical (`747560C9…`). Every job reports `SHARED_ASSET_OR_SAVE_CHANGES=0` and `PS1_MAP_MATERIAL_RECEIPT_INTACT=True`.
- **Fixed files:**
  - PS1 map `4AC42632…`;
  - live map `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC`;
  - reference image unchanged.
- **Save files.** `IBCharacters.sav`, `IronBreach_Vault.sav` and `IronBreach_XP.sav` (the three written at 21:51–21:52 UTC on 09-30), plus `IronBreach_Ledger.sav`, match Codex's recorded SHA256. They were not restored or investigated.

**Processes** (`analysis/rs1_log_check.py` → `analysis/log_check.json`):

- 35 engine processes: 32 commandlet steps (jobs 180, 181, 182, 184) and 3 GUI editors (jobs 183, 185, 186).
- Every log closes normally.
- Commandlets exit 1: the pre-existing GameFeatureData ensure, also seen in PS1's runs. Every step's own report says `complete`.
- GUI editors exit 0, in 885, 802 and 363 s.
- `OWNED_PROCESSES_LEFT=0` after every job. 35 crash-reporter folders were written in this task's UserDirs, one per process, each an `Ensure` for the same GameFeatureData ensure.

**Errors.**

| Kind | Count | New? |
|---|---|---|
| GameFeatureData ensure block | 45 error lines per commandlet, 26 per GUI run | Pre-existing (PS1 baseline identical) |
| `BP_Mech` Blueprint compile errors | 7 lines per GUI run | Pre-existing (PS1 GUI runs: 7) |
| `CurrentVisualData is NULL` | 1 line per GUI run | Pre-existing |
| `GetSocketInfoByName(WeaponSocket)` warnings during PIE | scale with PIE time (3976 / 8157 / 8167) | Pre-existing kind (PS1 job 178: 286; FF1 job 164: 2883) |
| "Failed to load" lines | only the GameFeatureData class and optional profiler DLLs (VtuneApi, WinPixGpuCapturer, aqProf, Wintab32) | Pre-existing; no content reference missing |
| RS1 negative-test refusals | 28 `LogPython: Error` lines in the 8 negative steps | **New and intended** (section 3) |
| Anything else | 0 access violations, 0 critical or fatal lines | none |

## 8. Correction to the reference-fit checklist: `BP_Mech`

**The stale claim.** `CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_RESULT_2026-10-01.md` §6 says, in the mission row, "`BP_Mech` is still missing; that is a separate blocker". That came from history, not fresh evidence. (Its known-issues row's "missing garrison mech" is still true: no candidate places a mech, see below.) The Sept 30 manager history (`Claude outputs/CLAUDE_STATUS.md`) records:

- the old mech set, including `BP_Mech`, restored locally;
- crew QA on `Lvl_FirstPerson` with the restored set: run 2 `Saved/MechCrewQA/run-20260930-041842-fp` (files dated 11:18–11:21 UTC), **host 6/6, client 13/13 COMPLETE PASS**;
- the restoration pushed as `e106831` at 11:28 UTC.

**Observed now** (no repair):

- `Content/Characters/Mech/Blueprints/Class/BP_Mech.uasset` is present: 146,438 bytes, SHA256 `436C123C65D808D281972D5584AB950532155111C29AA05579F930D5D60FD660`.
- In every GUI run of this task (jobs 183, 185, 186), BP_Mech loads with **Blueprint compile errors**. It calls `UpdateMechProximity`, which no longer exists on `BP_IBCharacter_Infantry_C`; there are three stale-pin errors on that node, and a later warning reads "Blueprint failed to compile: BP_Mech". The same 7 lines appear in PS1's GUI runs.
- The garrison candidates place **no** mech actor: PS1's and RS1's 3257 inherited actors include no mech class. The directors' `GarrisonMech` reference is optional (current-baseline result).
- No other missing content reference was logged (section 7).

Repair stays outside RS1.

## 9. Known limitations

**Art (unchanged assets, as directed).**

- The rocks are mountain meshes scaled to boulder size. Their snow-capped materials read as white ice spikes, not coastal rock.
- The land and bands use the mainland's flat, sand-coloured material. Slab and band joints show as faint lines, and each scaled cube stretches the texture differently.
- At the waterline, a 29–30 cm band or slab face shows as a thin dark line.
- The shrub kit renders dark in this light.
- The terrace is a flat block 15 cm above the deck with sparse dressing: 3 trees and 5 rocks.

**Layout.**

- The straight mainland edge remains beyond the shoulders' ends (y > 15100 and y < −9800), outside the picture's frame.
- RS1 does **not** shorten the compound. The deck still runs 106.8 m behind the quay, against the picture's 47–59 m; that depth is tied to Connor's reservation.
- Nine FF1 trim pieces are buried (2.4).
- The picture's own road would cross the terrace. The gate side was kept by decision.

**Behaviour.**

- Players can now drop off the rear and side walls onto land. The way back is the ramp and gate, about 19 s in the scripted run. No rails were added, as directed.
- Canopies have no pawn collision, as on the mainland.

**Verification limits.**

- Scripted PIE only: one rear-wall drop point, 4 coast spots, and 18 climb attempts at 6 targets.
- Not run: manual play, abilities, sprint, multiplayer and deployment.
- Job 185's three mislabelled verdicts are superseded by job 186 (section 5). r1's GUI run (job 183) is superseded: it ran at about 7.6 frames per second with wall-clock limits.

**Readiness items still open** (checklist, not run in RS1):

- deployment and return after any promotion;
- the weapon-rack interaction;
- the PS1 decal on feet and the helicopter;
- drops into the control gap and off the pier's outboard edge;
- interiors.

The settled-spawn item is now done for this candidate (section 5).

## 10. Next remaining composition gap

**Gap 2 of the reference fit: the flank service rows.**

- **The picture:** seven low service-block fronts plus a small tower, in two rows framing a 28 m apron.
- **PS1 and RS1:** Armory and Medical on the left, Barracks alone at the rear-right, and the right flank empty.

**Blocked by assets and ownership, not layout tooling:**

- three unassociated `Cube` actors sit inside Barracks' footprint;
- `BP_WeaponRack` stands unassociated beside Armory;
- the project has no further military service-building meshes; the five Tripo buildings are each used once, and the town meshes are civilian.

**What has to come first:** an asset decision (new service blocks, or approved duplicates) and owner decisions (Shane and Connor).

**After that:**

- the overall depth, which is tied to Connor's hangar;
- art: materials, rocks, the deck surface, the pier and ship proportions.

This pass does not start either; RS1 stops here for Codex's review.

## 11. Paths

**Candidate and receipt.**

| File | SHA256 |
|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1.umap` | `882F9D2060EC97916B919C6EA969D361D546FAAE49D8AA17C7510E45DD94A870` |
| `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_RearShore1.json` | `0033AAD5FC0112B12BBEBE92B68AF8C5541005F5ABAB4FFA143FF5877979042F` |

**Evidence.** Everything is under `Saved/GarrisonRestructure/20261001-claude-rearshore/`.

| File | SHA256 | What |
|---|---|---|
| `board/rs1-board.png` | `0F2C0D4B1E269C7FB1627AD73547A61D037E813F1B74571F6A4A5E1408F9AB30` | The board (JPG copy `35741500…`) |
| `board/rs1-reference-framing.png` | `E591CD20…` | RS1 reprojected into the picture's fitted camera |
| `board/tile-diagram.png` | `04177ECC…` | Diagram tile |
| `plan/rs1_engine_plan_r2.json` | `9711DEBAEC67811299173405EB9012DA9665D72526B60B03A8A146C1A12C5CBC` | Final engine plan (284 pieces, deviations embedded) |
| `plan/rs1_engine_manifest_r2.csv` | `6C1F790DD49979E7196ABA6E02FE66A1DE414648FC88AB9D282FB2BBE548E845` | Final manifest |
| `plan/deviations_r2.json` | `9A6C0884EE9AB8CE3E063E26A0343A4A694E82292024C9F51767320BB87290F6` | The 73 deviations with reasons and evidence |
| `plan/coast_r2.png`, `plan/rs1_coast_r2.py` | `CE68737A…`, `78B6B81E…` | r2 diagram and generator |
| `plan/rs1_engine_plan.json`, `plan/rs1_engine_manifest.csv` | `0A8CE762…`, `CA0A8FC4…` | r1 engine plan and manifest (254), kept for r1's exact revert |
| `regen/plan/rs1_plan.json`, `regen/regen_report.json` | `43E75D5A…`, `7B4729B6…` | Dry run regenerated from the copy (pieces identical to the reviewed plan; manifest `F41C15C3…` identical) |
| `run1/copy/copy_fingerprint.json` | `BD28CF6C…` (digest `33F5D04D…`) | The copy's fingerprint (the plan's source) |
| `run1/r2-bounds/bounds.json`; `analysis/bounds_check_r2.json` | `3DA0B54A…`; `6FDED496…` | Engine bounds (r2) and the offline checks |
| `analysis/bounds_check.json`, `analysis/bounds_check_r1_rerun.json` | `4650F858…`, `F881E48A…` | r1 bounds checks (the rerun adds the r1 coast grid) |
| `check-rs1-r2b/rs1_checks.json` | `58F93AC97673999054631D8E237E9531432504982DA79B08E57A3D2FF0B6F7AE` | **Authoritative** contacts, lanes and PIE (job 186) |
| `check-rs1-r2/rs1_checks.json`, `check-rs1-r2/editor/*.png` | `BBF87006…` | Job 185: the stills (and first PIE, superseded labels) |
| `check-rs1/rs1_checks.json`, `check-rs1/editor/*.png` | `71C99128…` | Job 183: r1 (superseded) |
| `run1/<step>/rs_<stage>.json`, `run1/logs/*.log` | | Every lifecycle step's report and engine log |
| `analysis/log_check.json` | `3C5BC7C9…` | Process and error summary |
| `hashes/preservation-final.json` | `9E96ECD0…` | Final preservation |
| `hashes/shared-before|after-18N.json` | all `747560C9…` | Per-job stamps |
| `tools/ib_garrison_rearshore.py` | `156F81A1…` | Copy, plan-check, bounds, apply, verify, revert and negative tests. Jobs 182 and 184 ran this version; jobs 180 and 181 ran the earlier `0D768FE1…` |
| `tools/ib_garrison_rearshore_check.py`, `…_check_r2b.py` | `B1EA49A5…`, `1C531B28…` | GUI checks (jobs 185, 186). Job 183 ran the earlier `06AF6236…` |
| `analysis/rs1_bounds_check.py`, `rs1_board.py`, `rs1_log_check.py`, `rs1_preservation.py` | `257BE223…`, `EC7297FA…`, `3380D62B…`, `15696AAA…` | Offline analysis |
| `Saved/zz_job/rearshore_lib.ps1`; jobs `Saved/zz_job/running/180…186-*.ps1`; logs `Saved/zz_job/logs/18N-*.log` | `ED45085A…` | Job runner pieces |

**Rerun the offline parts from the project root.** They read their inputs and rewrite only their own outputs:

```
python3 Saved/GarrisonRestructure/20261001-claude-rearshore/analysis/rs1_bounds_check.py Saved/GarrisonRestructure/20261001-claude-rearshore/run1/r2-bounds/bounds.json Saved/GarrisonRestructure/20261001-claude-rearshore/plan/rs1_engine_plan_r2.json bounds_check_r2.json
python3 Saved/GarrisonRestructure/20261001-claude-rearshore/analysis/rs1_board.py
python3 Saved/GarrisonRestructure/20261001-claude-rearshore/analysis/rs1_log_check.py
python3 Saved/GarrisonRestructure/20261001-claude-rearshore/analysis/rs1_preservation.py
```

**To remove RS1 from the candidate:** run the tool's `revert` stage with `IB_RS_PLAN=plan/rs1_engine_plan_r2.json`, as job 184 did. It removes exactly the 284 recorded identities and saves only when the level equals PS1 again.

**To trim later.** The tool has no partial revert. The terrace, shore and vegetation are separate roles and labels in the plan, so a later trim for Connor's building can be made the way r1 became r2: revert the current revision exactly, then apply a plan revision without the trimmed pieces.
