# Garrison BS1 boulder shore: result (2026-10-01)

Claude, 16:50 UTC. Answers `Docs/CLAUDE_GARRISON_BOULDER_SHORE_2026-10-01.md` (brief SHA256 `07FEF402…`).

**Scope held.**

- One new disposable candidate, `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore1`, copied from SP2 (`68CA73DE…`). It is the only Content file this task wrote (every job: `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`). `BoulderShore1_Materials` was not needed and does not exist.
- Edited: exactly the 35 RS1 coast-rim rocks (16 left, 19 right), resolved by RS1's and SP2's recorded identities. Added: 26 BS1-owned rocks (12 left, 14 right) on the same two rims. Nothing inland, on the rear wall or on the terrace.
- The other 19 RS1 rocks, all 82 RS1 ground pieces, trees, water, lighting, sky, gameplay actors and Connor's reservation are unchanged (fresh reload: 3508 of SP2's 3543 actors identical; the 35 differ only as planned).
- SP2's map, receipt and three instances, the 2,129 protected files, Codex's nine SP2 artifacts, the live map, earlier previews and saves are unchanged (section 8).
- No source asset, mesh, material, collision asset, config or project setting edited. No live promotion, Git, cleanup or shared change. The queue again holds only `153-yellow-after.hold`.

**Outcome.**

- The two rims now read as a continuous, irregular band of broad, fractured grey outcrops with smaller stones and open inlets. SP2's isolated miniature peaks and exposed straight slab edges are gone from the reference framing, both coast obliques and the water-side view (board, section 7).
- Treatment **T1b**: `SM_Mountain_05` and `SM_Mountain_Plateu_01`, cut deep into their height range at the sea surface; `MI_SP2_Rock_02` read-only. It was rendered on one stretch first (jobs 214 and 215) and the stretch went into the plan exactly as rendered, except two rocks moved 1.5–2 m to keep a drown inlet open.
- **Collision:** the shortlisted meshes each carry a single convex hull over the whole terrain tile, so exactly these 61 rocks get the profile `NoCollision` (`BlockAll` → `NoCollision` on the 35). SP2's 35 rim rocks had invisible hull colliders on 238 of 894 coast-grid points, 67 of them over open water. BS1 has none. Every existing route behaves as in SP2 (scripted PIE, section 6).
- **Main remaining gaps:** the rocks' submerged surfaces show through the single-layer water as pale skirts; players walk through rock where it overlaps the land band. Both are in section 9.

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore1.umap`, SHA256 `49154B4EB7959041EEE6752D25C6CC0CCF5B603D58BB63523442E57971A01599` (applied) |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_BoulderShore1.json`, SHA256 `8DB374D1DF5939BF825335D75515436F035CD34F90221D61CB65D6E67D5620EB`.<br>History: created `76D35C68` → applied `61F2B8FA` → restored `B5217062` → applied `F22F84F9` → restored `81B67C07` → applied `49154B4E`. |
| **Counts** | SP2 3543 actors → BS1 **3569**: 3508 identical, **35 edited** (16 left, 19 right), **26 new** (12 left, 14 right).<br>61 rocks: 43 outcrops (all 35 edits + 8 new) and 18 stones (new). Meshes: `SM_Mountain_Plateu_01` 28 outcrops + 9 stones, `SM_Mountain_05` 15 outcrops + 9 stones. |
| **Materials** | `MI_SP2_Rock_02` on slot 0 of all 61, referenced read-only. No new instance, no parameter change. |
| **Collision change** | `NoCollision` on exactly the 61 (`BlockAll` → `NoCollision` on the 35; new rocks `NoCollision`). Walkability (`default`) and step-up (`ECB_YES`) unchanged and verified. No asset or other actor changed collision. |
| **Lifecycle** | **PASS** (section 5): clean copy identical to SP2; guarded apply and save; fresh reload shows only the planned changes; saved repeat is a no-op; ownership negatives refused (8 applied-state, 6 clean-state cases); restore equals SP2 actor for actor (twice); re-apply; final fresh verify.<br>Two faults stopped jobs 216 and 218 (a test-harness undo in job 216's negatives, after its apply had saved; the restore's pre-save comparison in job 218). Neither failed step saved anything; both were fixed and the steps re-run (5.3). |
| **Routes (scripted PIE, real pawn, same walks on SP2 and BS1)** | 4/4 RS1 coast drowns recovered at the same spots and times; 6/6 walks out through the rock band recovered onto land (SP2: 3 of them first stood on invisible hulls); both coast paths walked end to end with **0 stops** (SP2: 8 and 1 stops at rim-rock hulls); 6 jump-climbs at the two deck ends per map, **0 bypasses** in either; both rim ends cross onto the mainland; the rear-wall drop and return through ramp and gate 19.27 s in both. |
| **Collision queries** | Rim/new rock colliders: SP2 240 of 894 grid points (238 invisible, 67 over open water without visible rock); BS1 **0**. Anchor contacts: SP2 103, BS1 **0**. |
| **Renders** | Job 223, one session, SP2 then BS1 from disk, same 7 cameras on the same tick schedule: 14/14 written, 0 errors, no dirty package, editor **exit 0**. Board `board/bs1-board.png`. In-game: 3 settled frames and a 22-frame scripted traversal on BS1. |
| **Preservation** | 2,125 of 2,125 project files of Codex's 2,129 match (4 engine files unchanged by every job stamp); Codex's 9 SP2 artifacts match; 2,224 files of this task's first stamp unchanged; every after-stamp identical (section 8). |
| **Processes** | 20 engine processes (17 commandlets, 3 GUI), all logs closed normally, 0 access violations, 0 critical/fatal lines; `OWNED_PROCESSES_LEFT=0` after every job. |

## 2. Assets and the chosen form

### 2.1 Shortlist and probe (jobs 212–213)

Six existing meshes from `/Game/Landscaping/IcelandEnviroment/Static_Meshes/`, all Nanite, one material slot, `CTF_USE_DEFAULT`:

| Mesh | Local box (cm) | Why on the list |
|---|---|---|
| `SM_Mountain_05` | 1024 × 1024 × 31–444 | broad fractured massif, cliffs |
| `SM_Mountain_Plateu_01` | 1024 × 1024 × 29–381 | flat-topped massif, wide ledges |
| `SM_Mountain_04` | 1024 × 1024 × 27–228 | low massif |
| `SM_Iceland_Mountain_02` | 102400² × −1311–36371 | SP2 family (used by the rim) |
| `SM_Iceland_Eroded_Mountain` | 102400² × 7389–42674 | SP2 family (used by the rim) |
| `SM_Mountain_01` | 102113² × −347–39805 | SP2 family; excluded: its massif reaches the tile edge |

Job 212's probe step failed (the commandlet's `spawn_actor_from_object` returned None). Job 213 re-ran it with `spawn_actor_from_class` + `set_static_mesh`. It spawned each mesh in memory far below the level, never saving, and traced its simple and complex collision on a grid (`run1/probe/probe_data.json`, `722570B7…`).

**Every mesh is a terrain tile whose only simple collision is one convex hull over the whole tile.**

- At T1b's cut levels the hull footprint is about 2.6–11× the visible rock's (outcrops) and 6.5–25× (stones), with margins of metres.
- SP2's 35 rim rocks already carried such hulls: up to 3.37 m above their visible surface (median of the per-rock maxima 2.29 m), over far more area than the visible rock.

### 2.2 Trial (jobs 214–215, in memory, never saved)

One stretch of the left rim (arc 63–118 m, rim rocks 008–014 plus six new rocks), the same targets in every variant, foot-level, oblique, water-side and reference-fit cameras. Board band TRIAL.

- **T1** (job 214): broad fractured massifs `SM_Mountain_04/05/Plateu_01` on `MI_SP2_Rock_02`.
- **T2** (job 214): the textured SP2 families `SM_Iceland_Mountain_02` and `Eroded`. They still read as miniature mountains (pointed silhouettes, snow-capped crowns cut off).
- T1 read as coastal outcrops, but every submerged part of its tiles lay within 1.5 m of the surface and showed through the water as a pale fringe with straight tile edges.
- **T1b** (job 215, chosen): T1's targets with each mesh cut deeper (outcrops `SM_Mountain_05` f 0.64, `Plateu_01` f 0.68; stones 0.84/0.82; `SM_Mountain_04` targets take `Plateu_01`) and made taller (×1.3 / ×1.2). The tiles' low ground now lies 3.6–6.3 m down (outcrops) and 2.8–4.2 m (stones) on the trial stretch, and 3.4–7.3 m / 2.2–5.5 m across the final plan. Same material, same targets.

**Why the form fits the reference.** These meshes have broad faces, ledges and fractured cliffs at any scale, unlike the peaked mountain crowns. Cut at the sea surface, each leaves a low, wide mass that meets the water along a ragged line and hides the band's straight face. Neighbours overlap into connected stretches, and stones and open inlets break the rhythm.

## 3. The plan

`plan/bs1_plan.json` (`9881238C…`), schema `bs1-boulder-plan-1`, generated offline by `analysis/bs1_make_plan.py` from the probe, RS1's plan and engine bounds, both receipts and the trial spec.

- **Placement rule** (`bs1_targets.RULE`): outcrops every 5.2–7.6 m along each RS1 coast line, 6.2–10.5 m long, 1.5–3.3 m visible height before T1b's factor (final 2.0–3.8 m), offset −0.9…+2.1 m seaward, axis jitter ±28°. A stone every second gap, 1.6–3.0 m long, 0.55–1.2 m high (realised 1.6–2.9 m and 0.5–1.1 m), 2.6–4.8 m out. Vertical scale 0.6–1.6× the horizontal.
- **Seeds** left 20261011 / 20261012, right 20261013. The trial stretch is taken exactly from job 215's T1b states.
- **Inlets.** Each RS1 drown walk crossing stays open (≥ 1.2 m from visible rock, 3 m inland to 4 m out), plus two (left) and three (right) natural recesses.
- **Caps.** Lower rocks near inlets; at most 2.4 m visible within 9 m of a rim end that meets a deck wall (tops ≤ 2.05 m vs the deck's 3.85 m).
- **Assignment.** The 35 rim rocks fill outcrop targets on their own rim in arc order (order-preserving minimum arc distance). Their identities, labels, tags and folder stay. New rocks are `IBGC_BS1_Rock_000…025`, tags `IB_GarrisonCB1` + `IB_GarrisonBoulderShore1`, folder `Carrowgate Garrison/Boulder Shore BS1`.
- **Clearance adjustments.** Nine rocks were moved by the smallest step that clears (one also shortened), recorded per rock in the plan:
  - `RS1_Rock_000` 2.25 m and `RS1_Rock_034` 3.0 m, both off CityGround;
  - `BS1_Rock_010` 0.5 m and `BS1_Rock_012` (shortened 40 %, moved 4.5 m), both off the deck ends;
  - `RS1_Rock_009` 2.0 m and `RS1_Rock_010` 1.5 m — trial-stretch rocks, so this is the stretch's one deviation from the rendered trial — and `RS1_Rock_022/023/026` 0.5–1.7 m, all off the drown-walk inlets.

**Offline checks** (`plan/bs1_plan_checks.json`, 10 cm raster of the probe's visible surfaces):

| | left | right |
|---|---|---|
| Coast line covered by visible rock (on the line / within 1 m) | 80 % / 91 % | 74 % / 87 % |
| Drown-walk clearance | 121 / 125 cm | 122 / 139 cm |
| Visible rock within 30 cm of deck, ramp, gate or CityGround; within 50 cm of a trunk; in the reservation, its side bands or approach | 0 / 0 / 0 | 0 / 0 / 0 |
| Tallest rock above the sea; top within 9 m of the deck end | 3.59 m; 2.02 m | 3.69 m; 1.84 m |
| Visible rock area (SP2 rim) | 545 m² (128) | 557 m² (134) |
| Submerged tile surface under open water within 1.5 m of the surface (tile edges within 3 m) | 177 m² (4.7 m²) | 182 m² (8.4 m²) |

## 4. Collision change

| | SP2 (35 rim rocks) | BS1 (35 + 26) |
|---|---|---|
| Profile / enabled | `BlockAll` / `QUERY_AND_PHYSICS` | **`NoCollision` / `NO_COLLISION`** |
| Collision shape | each mesh's single tile-wide hull | none |
| Walkable slope / step-up | `default` / `ECB_YES` | unchanged |

**Why.** Keeping `BlockAll` would leave invisible mountain colliders (2.6–25× the visible footprint, metres high). Editing the meshes' collision is asset work outside this brief. `NoCollision` per component on exactly these 61 rocks was the only option that adds no invisible collider and changes no asset or other actor.

**Consequences.**

- The rocks block nothing and support nothing: no new walkable surface over the sea, no step toward a wall, and no hull stopping a walk on the coast band (section 6).
- Weapon and camera traces pass through them (Visibility hits on rocks: SP2 49 complex / 93 simple of 155 points; BS1 0).
- Players walk through rock where it overlaps the land band (section 9).

## 5. Lifecycle and ownership

### 5.1 Processes

Each process is its own `UnrealEditor-Cmd` run of one or more batched steps, with the isolated `user/` UserDir and its own fresh first read. Times are UTC.

| Job | Process: steps | Result | Map after |
|---|---|---|---|
| 212 (14:20–14:23) | prepare: basefp · copy: copy · copyverify: copy-verify + probe | SP2 fingerprint 3543 actors, 3570 components, all with relative transforms, digest `1516DB72`; copy identical (digest `1516DB72`), receipt `created`; probe **failed** (spawn returned None) | `76D35C68` |
| 213 (14:25–14:26) | probe (read-only) | complete, never saved | `76D35C68` |
| 216 (15:23–15:26) | apply: verify + apply · repeat: verify + repeat · neg-applied: verify + negatives | apply: 35 edited, 26 spawned, settled-read check 0 unexpected, saved; reload: 3508/3543 identical, 26/26 new, 0 unexpected, digest `29A020B3`; repeat: no-op, file and receipt unchanged; negatives: every case refused, **harness undo fault** (5.3), nothing saved | `61F2B8FA` |
| 218 (15:30–15:32) | neg-applied2 · restore | negatives: **8/8 pass**; restore **refused to save** (5.3), nothing saved | `61F2B8FA` |
| 220 (15:34–15:38) | restore2 · neg-clean · reapply · final | restored and saved; fresh read 3543/3543 identical, 0 unexpected; clean negatives **6/6 pass**; re-applied; fresh verify | `B5217062` → `F22F84F9` |
| 222 (15:40–15:44) | restore3 · restored (verify, fingerprint written) · reapply2 · final2 | restored again: 3543/3543 identical; re-applied; **final: 3508/3543 identical, 35 edited as planned, 26/26 new, 0 unexpected, 3596/3596 components with relative transforms, digest `29A020B3`** | `81B67C07` → `49154B4E` |

- **Every applied fresh read** gives the same digest `29A020B3`. The ownership manifest is identical after all three applies (`E1D6E9AF…`): the re-created rocks got the same object names each time.
- **Repeat.** `already-applied-verified`; nothing saved; 26 BS1-tagged actors of 26 planned (no duplicate).

### 5.2 Ownership rule and negatives

**Rule.**

- An existing rock is edited or restored only if its object name, label, class and mesh equal both RS1's and SP2's recorded identity, its role is `rock`, it carries `IB_GarrisonRearShore`, and its exact state equals the plan's before or after state. The exact state is mesh, full-precision relative transform (0.01 cm, 0.001°, 1e-7), slot-0 override, profile, walkability and step-up.
- A new rock is owned only if it carries `IB_GarrisonBoulderShore1` **and** its object name, label, class and mesh equal the identity recorded when it was spawned.
- `IB_GarrisonCB1` alone never selects anything. Any conflict refuses before a change.

**Negatives.** In memory, with saving blocked; map and receipt hashed unchanged after each run.

- **Applied state** (job 218): extra BS1-tagged decoy; untagged decoy using a new-rock label; shared-tag-only decoy (not selected); a new rock untagged; a new rock moved 10 cm; a rim rock given another mesh; a rim rock untagged; a new rock deleted. All refused or not selected, and every undo returned to "NO REFUSAL".
- **Clean state** (job 220): six cases, the same pattern.

### 5.3 What failed, and what changed (the ownership guard did not change)

1. **Job 216, negatives (harness).** The ownership guard refused every injected case. The test's undo for "move a new rock 10 cm" restored nothing, because the struct `get_editor_property("relative_location")` returns follows the property, so the saved "old" location had moved too. The leftover 10 cm then failed the next two cases' undo checks.
   - Nothing was saved.
   - Both move undos now keep plain floats. Jobs 218 and 220 passed.
   - The as-run tool is kept in `tools/job216-as-run/`.
2. **Job 218, restore (comparison).** The restore removed the 26 and put the 35 back in memory, then refused to save. Its pre-save comparison set that late in-process read against SP2's base fingerprint, which is a process's first read.
   - `IB_Harbor_Surface`'s collision profile name reads `Custom` on a process's first read and `BlockAll` on every later read, in SP2 and BS1 alike. It is logged as read settling in every apply and restore, and every fresh reload reads `Custom` and matches SP2.
   - The restore now carries this process's own first-to-second-read settling over to the base before comparing, only where the base holds the first-read value and never for an edited rock.
   - Job 220 restored; the next process's fresh first read matched SP2 actor for actor.
3. **Restored digest (representation only).**
   - The restored map's fresh read equals SP2 actor for actor and field for field (3543/3543), but its fingerprint digest is `8C6E6F51` against SP2's `1516DB72`.
   - Job 222 wrote the restored fresh read out and compared the text. The only differences are the 35 rim rocks' component relative roll: SP2 `-0.0`, restored `0.0`, equal values.
   - With every `-0.0` written as `0.0`, both digests are `E220C8B8`. SP2 itself stores `-0.0` there (its fresh read and the untouched copy's both read `-0.0`); the restore writes `0.0`.

## 6. Focused collision and play checks (job 223)

One GUI session. SP2 and BS1 were reloaded for this, after the render pass. The same points and walks (`plan/bs1_check_routes.json`, `80000ABF…`) were run on both maps (the settled start of one climb differs by 0.6 m). Raw record `check/bs1_checks.json` (`6E0E97C3…`); condensed `analysis/check_summary.json` (`4C10250D…`); diagram `analysis/pie-paths.png`.

### 6.1 Engine queries (editor world, not movement)

| Query | SP2 | BS1 |
|---|---|---|
| Rim/new rock collision | 35 × `BlockAll` / `QUERY_AND_PHYSICS` | 61 × `NoCollision` / `NO_COLLISION` |
| 155 downward Pawn traces (the highest visible point and visible centroid of 60 BS1 rocks, `BS1_Rock_023` having no visible cell, and the highest visible point of SP2's 35 rim rocks; all points in both maps): first blocker is a rim/new rock | 96 | **0** |
| Same points, Visibility (complex / simple) hits a rim/new rock | 49 / 93 | **0 / 0** |
| 894-point Pawn grid along both coasts (−2…+8 m, every 2 m): rock hits / invisible (no visible rock there, or > 20 cm above it) / over open water without visible rock | 240 / 238 / 67 | **0 / 0 / 0** |
| 1,408 anchor components (land slabs, coast and wall bands, decks, mainland ground, trunks, the other 19 rocks) as box traces: rim/new rocks touching | 103 contacts on 63 anchors | **0** |
| Capsule sweeps along the two coast paths: rock-blocked segments | left 6 (Rocks 005, 008, 014) | **0** |

One BS1 trace point's first blocker is `IBGC_RS1_Rock_043`, one of the unchanged 19 (a wall rock's own hull), the same as in SP2.

### 6.2 Scripted PIE (real infantry pawn; movement input and jumps; not a person playing)

- **Pawn.** `BP_IBCharacter_Infantry_C`, capsule 34 / 88; max step 45; walkable angle 44.8°; speed 600; 90 cm jump apex.
- **Timing.** PIE ran at about 6–8 frames per wall second (estimated from the editor log's frame counter). With `-UseFixedTimeStep -FPS=30`, every limit and time below is game time.
- **Kaiju.** 0 at start and end in both maps.

| Route | SP2 (before) | BS1 (after) |
|---|---|---|
| RS1 coast drowns, 2 spots per shoulder | 4/4 moved back onto `Coast_L02/L02/R07/R11` after 1.43–1.47 s | **identical**: same spots, same times |
| Walks straight out through the rock band (3 per rim, from 3–5 m inland) | 6/6 recovered onto the coast band. Three first **stood on invisible hulls** (13, 31 and 15 samples on rim rocks, up to z 16) and were moved back after 2.3–4.4 s | 6/6 recovered after 1.2–1.53 s; **0 samples on rock** |
| Coast path, left (119 m, 3 m inland) | completed with **8 stops**: six stalls at the hulls of Rocks 005, 008, 012, 013 and 015 (twice), and two drops of more than 2 m after a resume had set the pawn down on top of a hull (2–2.8 m above the land); 60 samples on rock | completed, **0 stops**, 19.7 s, 0 samples on rock |
| Coast path, right (133 m) | 1 stop (Rock 018), 18 samples on rock | **0 stops**, 22.0 s |
| Jump-climbs at both deck ends (3 starts each, 10 s, toward a point on the deck 5.9–7 m inside the wall) | 6/6 held by the wall; highest capsule centre 175.1 | **6/6 held; 0 bypasses**; highest 175.1 |
| Rim end → mainland ground (beside Rock_000 / Rock_034) | reached 2.2 s / 3.1 s (4 samples on Rock_034's hull) | reached 2.2 s / 2.2 s |
| Rear-wall drop and return through ramp and gate (116.8 m) | landed on `Land_06`, back on `Forecourt_Deck_02`, 19.27 s | **identical**, 19.27 s |

**What this shows.**

- BS1 removes SP2's invisible hull colliders from the coast band and the sea edge.
- It extends no walkable surface into the sea, and the rocks offer no step toward the deck walls.
- The coast recoveries, the gate return and the land join are unchanged.
- Not run: manual play, sprint, abilities, deployment, multiplayer.

### 6.3 Brief in-game traversal (BS1 only, ACTUAL game frames of scripted movement)

The game viewport's back buffer (`Shot`), 1723 × 1280, camera 154 cm above the floor.

- **Settled frames** at three poses: the trial stretch at foot level, the backlit left rim, the right shoulder.
- **Traversal.** A 22-frame sequence every 0.2 s while the pawn is driven along the trial stretch's coast path, camera turned 35° toward the sea (`check/pie/`).
- **Board.** It shows the three settled frames and the six traversal frames with the least camera turn; frames taken while the camera turns are motion-blurred.
- The frames carry the game's existing subtitle line. Two traversal frames show the camera inside or against rock over the land band.

## 7. Final paired renders and board

**Session.** Job 223, one GUI session with the isolated `user-gui/` (autosave off), `-UseFixedTimeStep -FPS=30`, tick-counted.

- SP2, then BS1, each loaded from disk and shot with the same seven cameras on the same schedule after its load: reference-fit eye 7680 × 4320, both coast obliques, trial stretch at foot level, water-side close, trial oblique, backlit left-rim eye.
- Shot offsets were 1320–2925 ticks after load (SP2's 5 ticks later, 0.17 s of world time).
- 14/14 PNGs written (`check/editor/*__before-SP2.png`, `*__after-BS1.png`). After each load: 35 rim rocks at the expected state, 26 new present (BS1), dirty packages none. At exit: none.
- **Editor exit 0** after 2,162 s. The SP2 session's exit-time access violation did not recur.
- **Autosave.** The isolated `user-gui/Saved/Autosaves/PackageRestoreData.json` was rewritten at exit (96 bytes, `RestoreEnabled false`, `Packages []`), as in earlier GUI jobs; no package autosave.

**Board.** `board/bs1-board.png` (3000 × 8453, `AD393265…`; JPG `8F1E250B…`) from `analysis/bs1_board.py`. Every tile is labelled:

| Band | Contents |
|---|---|
| SOURCE / RENDER | the approved picture; SP2 and BS1 reference-fit stills reprojected into its framing (same eye, exact; `analysis/framing/`) |
| RENDER | six before/after pairs |
| DETAIL | 1:1 crops: both coasts in the 7680 × 4320 still; both obliques; the waterline; the underwater-skirt gap |
| TRIAL | jobs 214/215: V0, T1, T2, T1b at foot level and from the sea |
| PIE | the in-game frames (6.3) |
| DIAGRAM | the recorded PIE trajectories (not a render) |

**What the images show.**

- **Reference framing:** a continuous rocky rim around both rear shoulders where SP2 showed scattered specks and a straight bright edge. At this scale the band is narrower and lower than the picture's surf-wrapped rocks.
- **Foot level:** low, broad, fractured masses instead of SP2's lone spikes.
- **Water-side:** rock bases sit over the coast band's straight face, which SP2 left exposed.
- **Obliques:** pale submerged rock surfaces under the water in front of the band (section 9).

## 8. Preservation, processes and errors

**Hashes.** `analysis/bs1_preservation.py` → `hashes/preservation-final.json` (`B35DB186…`), 16:47 UTC.

- **Codex's 2,129 records** (13:40:08 UTC): 2,125 project files rehashed, **2,125 match**, 0 mismatches. The 4 engine files (A:) are compared by the job stamps: unchanged from `shared-before-212` to the last after-stamp, and the first stamp equals Codex.
- **Codex's nine SP2 artifacts** (map, receipt, three instances, material spec, ownership manifest, checks, board): **9/9 match**.
- **This task's first stamp** (`hashes/shared-before-212.json`, 2,228 entries: the 2,129 plus SP2's map, receipt, three instances, completed evidence, Codex's review folder, SP2's library and job scripts): 2,224 project files rehashed, 0 changed. All after-stamps (jobs 212–223) are identical.
- **Every job:** `SHARED_ASSET_OR_SAVE_CHANGES=0`, `SP2_MAP_RECEIPT_AND_THREE_INSTANCES_INTACT=True`, `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`. Live map `FAFFD601…`; the approved picture, every earlier preview map and the save files: 18/18 named files match Codex.

**Processes** (`analysis/log_check.json`, `CD84BA32…`): 20 engine processes, all logs closed normally, 0 access violations, 0 critical or fatal lines.

- Commandlets exit 1 (the known GameFeatureData ensure); every step's own report states its status.
- GUI editors (jobs 214, 215, 223) exit 0.
- 20 crash-reporter folders in this task's UserDirs, all `Ensure` (the same GameFeatureData ensure).

| Error kind | Count | New? |
|---|---|---|
| GameFeatureData ensure block | 45 lines per commandlet, 26 per GUI run | pre-existing |
| `BP_Mech` Blueprint compile errors | 7 per GUI run | pre-existing (not repaired) |
| `CurrentVisualData is NULL` | 2 in job 223 (four map loads) | pre-existing kind |
| `M_AI_Foam` compile warning | 1 per GUI run | pre-existing |
| BS1 refusals and failed steps | job 212 probe, job 216 negatives, job 218 restore (section 5.3); the intended refusals of the negative tests | this task, explained |
| Anything else | 0 | — |

## 9. Remaining visual gaps and limitations

**Art.**

- **Underwater skirts.** The submerged parts of each tile show through the single-layer harbour water as pale skirts in front of the band: about 180 m² per rim within 1.5 m of the surface, strongest in the oblique and water-side views. Faint straight tile edges show at 3–4.5 m.
  - A better water surface (later sea task), a deeper cut with taller scale, or a darker underwater material variant would each reduce it.
- **Colour.** SP2's warm/beige sunlit cast remains (material unchanged by design).
- **No surf.** There is no foam or wet band at the waterline, and the coast band's 29–30 cm dark face still shows between rocks and in the inlets.
- **Scale.** The band is lower and narrower than the picture's rocks, and the straight mainland edges beyond the shoulders remain bare.
- **One redundant rock.** `IBGC_BS1_Rock_023` (a right-rim stone) is entirely covered by its neighbours; a later revision can drop it.

**Behaviour.**

- Players walk and see through rock where it overlaps the land and coast band (about 366 m² of visible rock above walkable ground; traversal frames 014/019). Weapon and camera traces pass through the rocks.
- Proper per-rock collision needs either authored simple collision on these meshes (asset work) or separate owned blocking shapes fitted to the visible rock, and a decision.

**Verification limits.**

- Scripted PIE only, at about 6–8 frames per wall second (game time fixed).
- Not run: manual play, packaged build, sprint, abilities, deployment, multiplayer.
- The plan's raster checks and the board are diagnostics; the renders are the visual evidence.

**Queued, not started:** surf, sea colour, forest canopy, lighting warmth, final full gameplay acceptance.

## 10. Paths

Evidence root: `Saved/GarrisonRestructure/20261001-claude-bouldershore/`.

| File | SHA256 | What |
|---|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore1.umap` | `49154B4EB7959041EEE6752D25C6CC0CCF5B603D58BB63523442E57971A01599` | The candidate (applied) |
| `Saved/GarrisonRestructure/receipts/…BoulderShore1.json` | `8DB374D1DF5939BF825335D75515436F035CD34F90221D61CB65D6E67D5620EB` | Receipt (identities, history) |
| `board/bs1-board.png` / `.jpg` | `AD393265892345035F7FB73A9D624B8CA7CE99D8534BAB0A620A5F2344519673` / `8F1E250B9D2E402D…` | Board |
| `check/bs1_checks.json` | `6E0E97C32AE1F2813261439FC91C890B85D1DBB119902BF55D338C0CB13674F8` | Job 223 raw record: renders, state, queries, PIE, frames |
| `check/editor/*.png`, `check/pie/` | — | 14 stills (originals); in-game frames |
| `analysis/check_summary.json`, `analysis/pie-paths.png` | `4C10250D…`, `52CE6CB9…` | Condensed before/after record; trajectory diagram |
| `plan/bs1_plan.json` | `9881238C82C84C0CD0DCDB7D3612CB5A0197C66F2F71A9E7A8984F160B999E61` | The plan (35 edits, 26 new, collision note, 9 clearance adjustments, cameras) |
| `plan/bs1_plan_checks.json`, `plan/bs1_plan_*.png` | `02AE3D6C…` | Offline plan checks and previews |
| `plan/bs1_check_routes.json` | `80000ABF…` | Check points and walks |
| `plan/bs1_trial_spec.json`, `bs1_trial_spec_b.json` | `03D62EF4…`, `C77799FA…` | Trial specs (T1/T2; T1/T1b) |
| `trial/`, `trial2/` | `bs1_trial.json` `2AEA6F87…`, `699591A4…` | Jobs 214/215 shots and records |
| `run1/probe/probe_data.json` | `722570B7…` | Mesh and rim probe |
| `run1/prepare/base_fingerprint.json` | `1333589D…` (digest `1516DB72`) | SP2's fingerprint |
| `run1/<step>/bs_<step>.json`, `run1/logs/*.log` | — | Every lifecycle step's report and engine log |
| `run1/restored/fingerprint_first_read.json`, `run1/final2/fingerprint_first_read.json` | `C7430ECE…`, `B7AAE92A…` | Fresh reads: restored and final applied |
| `run1/reapply2/ownership_manifest.json` | `E1D6E9AF…` | Ownership manifest (same after all three applies) |
| `analysis/log_check.json` | `CD84BA32…` | Process and error summary |
| `hashes/preservation-final.json`, `hashes/shared-*.json` | `B35DB1865359B5D92F4DD556D9AC02BC71F42B3D77738B4563D63A6E60359FB7` | Preservation (16:47 UTC); per-job stamps |
| `tools/ib_garrison_bouldershore.py` | `0C8BEC43…` | Lifecycle tool (job 222). As-run copies: `tools/job212-as-run` `CE0FA242…`, `job213-as-run` `4D8868AB…`, `job216-as-run` `5D8DCBBC…`, `job218-as-run` `47F27D7F…`, `job220-as-run` `529132F8…` |
| `tools/ib_garrison_bouldershore_check.py`, `…_trial.py` | `DD341D75…`, `D6CA1CDD…` (job 214 ran `C6672A13…`, kept in `tools/job214-as-run`) | Final check session; trial sessions |
| `analysis/*.py` | — | Plan generation and checks, routes, board, summary, log check, preservation |
| `Saved/zz_job/bouldershore_lib.ps1`; jobs `Saved/zz_job/running/212…223-bs-*.ps1` | `95D1B95C…` | Job runner pieces |

**Rerun the offline parts on the device.**

From the project root:

```
python3 Saved/GarrisonRestructure/20261001-claude-bouldershore/analysis/bs1_check_summary.py
python3 Saved/GarrisonRestructure/20261001-claude-bouldershore/analysis/bs1_log_check.py
python3 Saved/GarrisonRestructure/20261001-claude-bouldershore/analysis/bs1_preservation.py
```

From the evidence folder: `python3 analysis/bs1_board.py`.

The plan scripts (`bs1_make_plan.py`, `bs1_plan_checks.py`, `bs1_check_routes.py`) also need `scipy`, which the device does not have. They find the project root by themselves.

**To remove BS1 from the candidate:** run the tool's `restore` step with `IB_BS_PLAN=plan/bs1_plan.json`, as jobs 220 and 222 did. It removes exactly the 26 recorded rocks, puts the 35 back at SP2's exact state, and saves only when the level equals SP2 again.
