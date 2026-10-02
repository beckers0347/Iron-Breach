# Garrison reference fit and next layout pass: result (2026-10-01)

Claude, 01:40 UTC. Answers `Docs/CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_2026-10-01.md`.

**Scope held.** This was read-only level analysis.

- No engine process, job or capture ran. The queue still holds only the inert `153-yellow-after.hold`.
- No map, candidate, asset, material, config or lighting was written. No actor moved. Nothing was deleted.
- No Git, locks, commit, push, cleanup or messages to others.
- The only new files are this document, the status update, and the task folder `Saved/GarrisonRestructure/20261001-claude-referencefit/`. That folder holds analysis, board, plan and hash evidence. Section 8 lists every file.
- The 451 protected files, PS1's map, material and receipt, the reference image and the live map were rehashed before and after. All match (section 7).

**Not a reference match.** PS1 has the reference's deck topology and paint: the spine, the neck, the left control platform, the octagonal pad and the pier with an outboard berth. Widths agree too. The reference is still **not** matched. Two layout gaps remain at the rear, plus the art gap and Connor's hangar.

## 1. At a glance

| Item | Result |
|---|---|
| Comparison board | `board/rf-board.png` (1682×2087, plus JPG). Six labelled tiles, all annotated on copies of the evidence images:<br>A: the reference, unchanged.<br>B: PS1's overhead still from job 178, unchanged.<br>C: the reference with PS1's actual geometry drawn through the reference's best-fit projection.<br>D: PS1's still with the reference's features carried through the same fit into PS1's known camera.<br>E: PS1's deck plane re-projected into the reference's framing.<br>F: a plan in metres. |
| Camera vs layout | **PS1's camera is known.** The model matches deck edges in the still within 5.7 px, and that camera draws the forecourt at **0.73×** the pad's scale.<br>**The reference has no camera.** A pinhole was fitted on accepted anchors only. Its error falls steadily as the lens lengthens, reaching **17.0 px rms** at a near-orthographic lens (about 2.4 m at the pad). So the reference is drawn almost without perspective.<br>**Result:** "narrower at the rear" is camera, not layout. In plan the forecourt is **124.9 m** wide and the reference's compound **127 m** (band 127–138). |
| Gap 1 (layout) | **The rear is detached and over-deep.**<br>PS1 has 106.8 m of deck behind the quay, then a **26.25 m water strip**, then a straight flat shore at x −3125.<br>In the reference the compound runs **47–59 m** behind the quay and its rocky, wooded shore wraps both rear corners. The waterline meets the rear-right corner at x 4329–5433 and runs along the left side to x 8055–8557. |
| Gap 2 (layout; assets and ownership block it) | **The flanks are empty.** The reference has about eight low service blocks in two rows framing a 28 m apron.<br>PS1 has Armory and Medical on the left, Barracks alone at the rear-right, and an empty right flank.<br>The pass is blocked because the existing buildings are pinned by unresolved associations and no further service-building assets exist. |
| Gap 3 (art/asset) | Surface material, dressing and props differ, and so do the proportions of the drawn pier and ship (section 4). |
| Not counted | **Connor's hangar.**<br>The reference's hangar front sits at x 4904–5974; the reservation's mouth is at 4390.<br>The reference's hangar is 60–69 m wide with its wings and 28–32 m at the core; the reservation is 38.6 m.<br>No resize. Conflicts are listed in section 5.7. |
| Recommended next pass | **RS1, rear shore attachment and land shoulders.** Section 5.<br>A new disposable candidate from PS1, containing:<br>• land at the mainland's own level filling the water strip and wrapping both rear corners along the reference's waterline;<br>• a planted terrace on the empty rear-left flank;<br>• a rock rim;<br>• trees copied from the existing mainland tree kit.<br>It adds **285 new actors** and moves, hides or edits nothing. Dry-run manifest, plan and overlay are in `plan/`; the offline checks found **0 problems**. |
| Gameplay readiness | Section 6. Evidence exists for:<br>• routes, doors and the land gate on the candidates;<br>• deployment and return on the **live** map only;<br>• one drown snap-back.<br>Still open: a spawn check on the final candidate, deployment after any promotion, more drop points, and the PS1 decal check on feet and vertical surfaces. |

## 2. Method: separating perspective from geometry

**Geometry.** `analysis/rf_geometry.py` reads three inputs and writes `analysis/geometry.json`:

- PS1's base fingerprint;
- FF1's site-probe bounds;
- the PF1 plan.

The script confirms that the only differences between the YM1 bounds and FF1's transforms are the 32 ring actors and FF1's 125 pieces. Every building and deck bound is therefore current for PS1, because PS1 is FF1 plus one decal.

The same file records the mainland's existing environment kit: 1232 trees, each a canopy and trunk pair, plus the three rock meshes with their materials and native sizes.

**PS1's camera.** The camera is known: eye (28513.4, 3750, 19795.4), target (11350.6, 3750, 385), horizontal FOV 90°, 1920×1080, from PS1's `ring_checks.json`.

- **Validation.** Projected deck edges were compared with brightness edges in the still on four lines: the pad, the pier, the forecourt and the control platform. The differences are 0.1–2.0 px, except 4.5–5.7 px on two coping/shadow edges.
- **Perspective shrink.** This wide, near camera draws the forecourt at 3.18 px/m against 4.36 px/m at the pad, i.e. **0.73×**.

**Reference fit.**

- **Anchors.** The reference was read by eye on 2–3× gridded crops (±5 px; `analysis/reference_points.json`). Only **12 accepted anchors** were used: 5 pad vertices, the spine's 2 quay corners and 5 control-platform corners. These are the features already set from this picture and accepted. The pier is deliberately not an anchor.
- **Scan.** A pinhole camera was fitted at each focal length from 1200 to 25000 px.
- **Result.** The rms falls monotonically from 36.2 px to 17.0 px, and a free plane homography also gives 16.5 px. So the reference is drawn close to an orthographic oblique view, pitch about 44°.
- **Plausible band.** Focal lengths within 30 % of the best fit, i.e. 3000–25000 px with rms 17.0–22.0 px. Stronger perspective (F ≤ 2200, rms 25.2–36.2 px) is reported but rejected.
- **The picture's own inconsistency** is the anchor residual: 7–29 px, about 2.4 m at the pad's scale.

**Mapping.** Each reference feature was back-projected to the plane it lies on, deck (z 385) or water (z −35), under every focal length in the band. Every number below is a best value with its band. These are indicative positions for review, not a survey.

## 3. The six features (`analysis/fit.json`, board tiles C, D, F)

| Feature | Reference (best fit, band) | PS1 actual | Verdict |
|---|---|---|---|
| **Broad rear compound** | Width at the quay **127 m** (127–138). Deck behind the quay at the rear corners **47 m** (47–59). | Forecourt **124.9 m** wide (y −2500…9993) and **106.8 m** behind the quay (x −500…10182). | Width matches; the apparent narrowness is camera (tile B's 0.73× rear scale). **Depth is a layout gap:** PS1 has 48–60 m more deck behind the reference's rear line. |
| **Low service buildings flanking a central apron** | 8 blocks plus a small tower, 12–18 m wide each.<br>Front rows have base fronts at x 8079–8788 (14–21 m behind the quay).<br>Back rows are at x 4257–6920.<br>The apron between the front rows is about 28 m (y 2043…4872). | Left: Armory (x 5668…8118) and Medical (x 8658…10138, reaching the quay).<br>Right: Barracks alone at the rear (x 1977…4646).<br>The right flank x 4646…10182, y −2500…1819 is empty except paint. | **Layout gap**, blocked by assets and ownership (gap 2). |
| **Straight central spine and neck** | Anchor residuals 9–14 px at the quay corners. | Spine 38.5 m, x 10182…14532. | Matched within the reference's own inconsistency. |
| **Left tower and low operations block** | Control-platform anchors 11–22 px. Tower at the outer-rear corner, low block toward the spine. | P3 arrangement: Command at the outer-rear corner, Mess_Hall along the spine. | Matched in footprint and arrangement. Building style is art. |
| **Front octagonal pad** | Pad anchors 7–29 px. The largest, 26–28 px or about 4 m, is on the left flat. | 54 m octagon, offset 7.75 m to image-left. | Matched within tolerance. |
| **Right parallel pier and outside berth** | Pier drawn **5.1 m wide at the root and 9.8 m at the end**, diverging **11°** from the spine. Ship about as long as the pier. | Pier 22 m wide and parallel (PF1's choice for the crane, trucks and a 6 m lane). Ship 57.8 m against a pier of 84 m. | Proportion difference, kept as an accepted relationship. Ship length is art/asset. |
| **Rocky wooded shore connection** | The waterline meets the rear-right corner at **x 4329–5433** and runs along the left side to **x 8055–8557**, wrapping the compound. The hangar is backed into land. | Straight flat CityGround edge at **x −3125** across y ±154.9 m (top −5.1, sand-coloured `M_AI_MountainGround`). A **26.25 m water strip** sits behind the forecourt. The 15 m ramp is the only connection. The nearest mainland trees stand 16 m or more behind the edge (38 canopies in x > −160 m, y −120…200 m). | **Layout gap** (gap 1). The ground material and tree density are art. |

The resolution of the brief's two observations:

- **"Narrower at the rear"** is the camera. PS1's still is a wide 90° view whose rear is 0.73× smaller. The reference is near-orthographic. In plan the widths agree to 2–10 %.
- **"Sparser at the rear"** is real, on two counts:
  - PS1's deck runs about 50 m deeper than the reference's compound, and that depth is empty except the reservation outline;
  - the flanks lack the service rows.
- **"The shoreline reads as a straight boundary"** is real. It is the unchanged mainland edge, 26 m behind the forecourt.

## 4. Ranked remaining gaps (at most three)

1. **Layout: rear depth and shore attachment.** This is the top third of the picture.
   - **Reference:** the compound ends about 47–59 m behind the quay. The hangar is recessed into land, and the rocky, wooded shore meets both rear corners and runs along the left side.
   - **PS1:** the forecourt runs on to x −500. The zone between the reservation's mouth line (x 4390) and the land is empty deck on the left, the gate, road and Barracks on the right, and then open water. The land edge is a straight line.
   - **Next pass:** RS1 (section 5) closes the layout part of this gap.
2. **Layout, blocked by assets and ownership: flank service rows.** Arranging rows needs owner decisions that a preview cannot make:
   - Barracks contains three unassociated `Cube` actors inside its footprint;
   - Armory has the unassociated `BP_WeaponRack` 2.65 m outside it;
   - the project has no further military service-building meshes. Only the five Tripo buildings exist, each already used once; the mainland's town meshes are civilian.

   An asset decision (new service blocks, or approved duplicates) should come before a layout pass.
3. **Art/asset: surfaces, dressing and drawn proportions.**
   - The deck is a uniform light material; the reference has dark, weathered concrete.
   - The mainland ground is sand-coloured; the reference has a forest floor.
   - There are no vehicles, containers or rooftop units.
   - The reference's pier is 2–4× narrower and its warship about as long as the pier.

   None of these is layout.

**Not counted as our work.** Connor's hangar is the reservation (x −500…4390, y 1819.4…5680.6, 48.9 × 38.6 m), unchanged.

## 5. The one recommended next pass: RS1, rear shore attachment and land shoulders

### 5.1 What and why

This pass addresses gap 1 with existing assets only, and keeps every accepted relationship and anchor. Nothing existing is moved, hidden or edited. Everything is new, tagged and removable by tag, on a **new disposable candidate copied from PS1** (`4AC42632…`): proposed `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1`.

It adds four things:

- **Land at the mainland's own level.** Top −5, the CityGround top (measured −5.1). It fills the 26 m strip behind the forecourt and forms two shoulders around the rear corners, along the reference's best-fit waterline. The left shoulder attaches to the forecourt side at x 8200; the right one meets the right side at x 5400 (the reference gives 8055–8557 and 4329–5433).
- **A planted terrace.** Top 400, 15 cm above the deck. It covers the **empty** rear-left flank behind the reservation's mouth line (x ≤ 4390) and keeps 6 m from the reservation's side (y ≥ 6280.6). This is where the reference has land behind its left buildings.
- **Rocks.** A rim on the new waterline, low rocks below the deck edge where a forecourt wall now faces land, and a few on the terrace.
- **Trees.** Each copies a random existing mainland tree (same canopy mesh, scales and trunk), placed by a seeded Poisson sampler at 9 m spacing.

The ramp road stays the only way in and now runs through the wooded land, as the reference shows ("a road enters through rocky, wooded land").

### 5.2 Generated content (dry run `plan/rs1_plan.json`, `plan/rs1_manifest.csv`)

Seed 20261001. Labels are `IBGC_RS1_*`; tags `IB_GarrisonCB1` and `IB_GarrisonRearShore`; folder `Carrowgate Garrison/Rear Shore RS1`.

| Element | Count | Geometry | Asset (existing, unmodified) | Collision |
|---|---|---|---|---|
| Land slabs | 40 | Cube boxes on 7.5 m x-bands with extra breaks at the landing chamfers, the forecourt's rear face and the terrace stair. Conservative toward water, 10 cm off every deck face, clear of the ramp. z −40…−5. Total 12,816 m². | `/Engine/BasicShapes/Cube` with CityGround's `M_AI_MountainGround` | BlockAll |
| Terrace slabs | 9 | Two rectangles plus a 7-step stair along the rear-left chamfer. z −40…400, so outside the deck they read as an earth bank. Total 1,679 m². | Same | BlockAll |
| Rocks | 58 | 35 on the coast rim; 13 wall rocks with tops ≤ 330, below the deck edge; 5 against the terrace face; 5 on the terrace.<br>Each is a mountain mesh scaled to boulder size, vertical stretch 0.89–3.02 (median 1.62). | `SM_Iceland_Eroded_Mountain`, `SM_Iceland_Mountain_02`, `SM_Mountain_01` with their `M_AI_MountainRock_*` materials | BlockAll, as on the mainland |
| Trees | 89 (178 actors) | 83 on the new land, 6 on the terrace. Canopy half-width median 3.8 m, height median 10.2 m. | GV_Vol7 shrub canopies (mesh-default materials) with a `Cylinder` trunk in `M_Bastion_Bark` | BlockAll, as on the mainland |
| **Total** | **285 new actors** | PS1 has 3257 actors, so +8.8 %. | No new asset, no material edit | |

**Coast polylines.** These are world cm, from `fit.json`'s best fit, attached to the forecourt:

- **Left:** (−3125, 15400) → (2338, 15226) → (3762, 14351) → (4214, 13321) → (4653, 12883) → (5406, 12819) → (5845, 12309) → (6074, 11576) → (6193, 10989) → (6733, 10703) → (7486, 10349) → (8200, 10013).
- **Right:** (5400, −2510) → (5618, −3052) → (5844, −3633) → (5963, −4219) → (6082, −4804) → (6736, −5363) → (6961, −5942) → (6546, −6554) → (5695, −6893) → (4623, −7097) → (3769, −7587) → (3134, −8365) → (2725, −9607) → (−3125, −9800).

**Terrace boxes.** x 1182…4390 by y 6280.6…10003; x −510…1182 by y 6280.6…8000; then 7 stair steps over x −510…1182 from y 8000 up to the chamfer line (+10 cm).

**Diagram.** `plan/rs1_plan.png`. `plan/rs1_on_ps1_still.png` draws the proposal on a copy of PS1's overhead still through its known camera; it is not a render.

### 5.3 Identities (all unchanged; object names in the PS1 package, `…PaintStability1:PersistentLevel.`)

- **Abutted, unchanged.** The forecourt decks `IBGC_Forecourt_Deck_00…03` / `Chamfer_00…03` and the ramp `IBGC_Ramp_Deck_00`.
- **Partly buried under the terrace (still present, unchanged).** FF1's `IBGC_FF_Fore_Coping_06/07/08`, `Fascia_08/09/10` and the paint `EdgeLine_06/07/08`. The terrace top (400) is above the coping top (393.4).
- **Held anchors and their clearance to new pieces:**

| Anchor | Object | Nearest new piece | Clearance |
|---|---|---|---|
| PlayerStart | `PlayerStart_0` | terrace | 22.8 m |
| Barracks + door | `StaticMeshActor_54` + `BP_DoorFrame_C_1` | land outside the deck edge, 3.6 m below | 2.7 m / 11.1 m |
| Cube, Cube2, Cube3 | `StaticMeshActor_69/70/71` | land | ≥ 4.1 m |
| Armory + door | `StaticMeshActor_56` + `BP_DoorFrame_C_2` | land outside the edge, below | 3.9 m / 16.5 m |
| BP_WeaponRack | `BP_WeaponRack_C_2` | land | 22.3 m |
| Medical + door | `StaticMeshActor_1` + `BP_DoorFrame_C_0` | rock | 28.0 m / 34.7 m |
| Gate | `StaticMeshActor_280` | land beside the landing chamfer, 3.8 m below the gate's base | 0.15 m |
| Gate leaf | `BP_DoorFrame_C_6` | land | 6.1 m |
| Command, Mess_Hall, doors | `StaticMeshActor_58/60`, `BP_DoorFrame_C_3/4` | | > 30 m |
| Control platform, pier, ship | | rock | 32.6 m, 45.7 m, 56.7 m |
| Reservation | | land abutting the deck's rear face from outside (x < −500) | 0.1 m |

The 0.1 m to the reservation is intended: the reference's hangar backs onto land. Its sides keep 6 m, and its straight approach band x 4390…10182 is untouched.

### 5.4 Ownership

- **Candidate-owned (Claude's tool, Codex's review).** All 285 pieces.
- **Referenced, not modified.** CityGround's material, the mainland's rock and tree meshes and materials, the engine Cube and Cylinder.
- **Untouched.**
  - Shane's buildings, gate, door frames, Cubes and weapon rack;
  - Connor's reservation;
  - all `CG Mainland` actors;
  - FF1's pieces;
  - water actors, directors and the spawner;
  - the PS1 decal.

### 5.5 Access, door and collision dependencies

- **Land gate.** The ramp corridor (x −3500…−1118, y −1000…500) gets land beside it at −5. No tree is placed within its canopy half-width plus 2 m of the ramp, and none within its canopy plus 6 m of the gate.
  - **Entry:** the gate remains the only way in. The new land is 3.9 m below the deck and cannot be stepped up (max step 45 cm).
  - **Exit:** a player can now drop off the forecourt's rear or side walls onto land. Before, that edge led to water and Drown snap-back. They can walk back over the city ground to the ramp's foot (x −3500, z 10, a 15 cm step) and in through the gate.
  - This is a behaviour change at those edges. It is flagged, not hidden.
- **Doors.** No door frame, door approach or door lane is touched. The nearest new piece to any door frame is 11.1 m away, at Barracks.
- **Water and drown.** New coast edges drop into water, so Drown should apply (`DrownWaterZ` −35, below the land top −5). The strip behind the forecourt stops being water.
- **Spawner.** `BP_M1_KaijuSpawner_C_1` spawns within its 30 m sphere at (−10617, −105), at least 45 m from any new land. Its 100 m proximity sphere already covers the ramp and now also the strip land.
- **Navigation.** The level has no NavMesh before or after.
- **Walkable deck.** No tree or rock stands on the walkable deck. On the terrace, a 15 cm step is walkable.

### 5.6 Minimum checks for RS1

Reuse the PS1/FF1 tooling and receipts; do not run the old full matrix.

1. **Plan.** Regenerate the dry run from the copy's own fingerprint and require 0 problems with the same counts.
2. **Lifecycle.** Copy PS1 → RS1 and verify all 3257 actors identical. Then apply and save, reload and verify, check that a saved repeat is a no-op, revert exactly (all RS1-tagged pieces removed and 0 other differences), re-apply and verify. Then a candidate-against-PS1 diff: **only the 285 planned creates, 0 unexpected**.
3. **Scripted PIE (the real infantry pawn)**, existing routes:
   - city road → ramp → gate → gate road;
   - PlayerStart → spine;
   - reservation mouth → spine;
   - the Barracks and Armory door routes;
   - forecourt → terrace step and back.

   Two new ones:
   - drop from the forecourt's rear edge onto the strip land, then walk via the ramp and gate back onto the forecourt;
   - one step off a shoulder's coast into the water, expecting a Drown snap-back to land.
4. **Sweeps.** Three capsule lanes along the ramp, clear of new pieces.
5. **Captures.**
   - PS1's overhead-reference camera, before and after;
   - a reference-matched camera from this fit: eye (56311, 5969, 40946), target (11532, 3028, 385), horizontal FOV 23.6°, roll 1.1° (fit F 4000, 20 px rms);
   - one eye-level view along the gate road toward the gate;
   - one eye-level view of the terrace from the forecourt;
   - rerun `analysis/rf_board.py` on the new still.
6. **Preservation.** The 451 protected files, PS1's map, material and receipt, the live map, and no shared-asset writes.

### 5.7 Conflicts and choices for Codex's review (not resolved here)

- **Wider hangar.**
  - On the left, a hangar of the reference's 60–69 m width with wings would reach about y 6750–7200 and meet RS1's terrace inner edge (y 6280.6) by about 5–9 m. The terrace is generated and can be trimmed.
  - On the right, any wider hangar already meets the gate road and gate. That conflict exists today.
- **Deeper hangar.** The land now abuts the deck's rear face, so the reservation cannot grow past x −500. It could not before either: the deck ended there.
- **Drop-off exit.** Exiting the compound by dropping off its rear walls is a new behaviour. If unwanted, a later pass could add edge rails or blocking, but RS1 does not.
- **FF1 coping and edge lines.** About 75 m of FF1's accepted rear-left coping, and the matching edge lines, is buried under the terrace.
- **Art limits.**
  - The land is the mainland's sand-coloured material, not the reference's forest floor.
  - Rocks are scaled mountain meshes, stretched up to 3× vertically.
  - Land slabs are staircased on 7.5 m bands, with finer bands at the landing chamfers and along the terrace stair. The rock rim dresses the steps; no slab crosses to the water side of the coast line.
  - Beyond the shoulders' ends (y > 15400 and y < −9800) the old straight edge remains. That lies outside the reference's frame.

## 6. Gameplay-readiness checklist (existing evidence only; nothing re-run here)

| Item | Existing evidence | Status for PS1 | Still needed |
|---|---|---|---|
| **Spawn** | `PlayerStart_0` is held identical in every candidate (P3 diff job 139, FF1 and PS1 fingerprints) at (4690, 4024, 539).<br>PlayerStart → spine reached: P3, 11.2 s; PF1, 10.48 s (`Docs/…PIER_FINISH…RESULT` §6). | Spawn point and route are good. The game's own spawn on a candidate was not recorded. | One PIE start on the final candidate: pawn at PlayerStart, settled at z ≈ 475, no overlap. |
| **Moved entrances (Command, Mess_Hall)** | P3 jobs 134–138: both approaches reached and both leaves open (z 200 → −195).<br>PF1: spine → Command approach 11.53 s, → Mess_Hall 3.61 s, Codex's passage route 13.05 s; Codex's own walk 13.09 s. | Approaches work. **Interiors cannot be entered:** building collision sits 110 cm behind the door line, identical at the original positions (pre-existing). | Owner decision on interiors (Shane/Connor). |
| **Other entrances (Armory, Barracks, Medical)** | FF1 job 164: Barracks door route 1.5 s, Armory 6.8 s, Medical 5.5 s, all reached. | Reached. | Same interior question. |
| **Weapon rack** | `BP_WeaponRack_C_2` held identical in every candidate. | Not exercised on a candidate. | One approach and interact on the final candidate. |
| **Mission, deployment, return** | **Live map only.** `Saved/ReferenceArtPass/crewqa-host-20260922-2348.log` lines 1702, 1873, 1925, 2099 and 2100: PASS listen lobby and Watch; PASS Carrow Gate arrival stable 8 s; PASS return to Watch; PASS redeployment stable 8 s; COMPLETE (23:51:55 UTC).<br>Directors reference only each other and an optional `GarrisonMech`; no director uses world positions (current-baseline result). | Candidates are not the `carrow_gate` destination, so this was not exercised. | Rerun `IB.DeploymentCheck` after any promotion (owner decision). `BP_Mech` is still missing: a separate blocker, not touched. |
| **Land-gate access** | P3: city road → gate → forecourt reached in 8.9 s with the leaf opening.<br>FF1 job 164: 130.6 m land join reached 4/4 in 21.6 s through the gate. | Reached. PS1 changed no collision. | Re-walk after RS1, because the ramp then passes through land. |
| **Water and drown recovery** | Preview job 128 (`Docs/…PREVIEW_RESULT` §6.3): one scripted channel drop, back on the exact spine rest spot 1.29 s later.<br>Harbor surface has 0 simple collision shapes; `DrownWaterZ` −35. | One observation, one spot. | One drop each into the 9 m control gap and off the pier's outboard edge. After RS1, one drop off a new coast edge and the land-drop recovery walk (5.6). |
| **PS1 decal on feet and vertical surfaces** | `IBGC_PS1_PadRingDecal`: decal box (10, 1950, 1950) with pitch −90. It projects ±10 cm about z 385 over a 39 m square; the analytic ring is r 18.9 m ± 0.2 m.<br>The helicopter reaches r 17.5 m, so it cannot receive the ring. | Not checked visually. | **Visual check only, no rendering rewrite:**<br>• PIE pawn standing on the ring line: look at the feet, both from the player camera and close up (does the character mesh receive decals?);<br>• any prop moved onto the ring in future. |
| **Known unrelated issues** | GameFeatureData ensure on every launch; `BP_Mech` compile errors and the missing garrison mech; `CurrentVisualData is NULL` on the infantry pawn. | Unchanged, out of scope. | n/a |

The three save files Codex noted (written 21:51–21:52 UTC on 09-30) are preserved at their current bytes, and both records are kept. They were not investigated.

## 7. Preservation

- **Before.** `hashes/protected-before.json`, 01:00 UTC: 451 / 451 protected files match Codex's `protected-current.json`. Also matching: PS1 map `4AC42632…`, material `4F6A2A1A…`, receipt `FADED192…`, reference `33491BF3…`, live map `FAFFD601…`.
- **After.** `hashes/protected-after.json`: the same result (see the status update).
- **No engine, no job.** No Unreal process was started.
- **Writes.** Device writes were confined to the task folder, this document and `Claude outputs/CLAUDE_STATUS.md`. The status file was backed up first, at VM `~/work/CLAUDE_STATUS.before-rf.md`.
- **Byte-code cache.** One Python import on the device left `analysis/__pycache__/rf_fit.cpython-310.pyc` in the task folder. It is harmless and was left in place, since nothing is deleted.

## 8. Paths

Everything is under `Saved/GarrisonRestructure/20261001-claude-referencefit/`.

| File | SHA256 | What |
|---|---|---|
| `board/rf-board.png` (`.jpg`) | `94049DD1C92C816FA4BE58710DA44A4B88B60B993127DE919A8D1130DF9B4CAC` (`0DDF62E4…`) | The comparison board |
| `board/rf-findings-card.png`, `board/tiles/tile-{C,D,E,F}.png`, `board/board_index.json` | `5D525D1A…`, `A95BD2C1…`, `AF381CC3…`, `C144C615…`, `C98AA628…`, `F6178F33…` | Board parts |
| `analysis/geometry.json` | `65E5914CB16E4137BF13F055024AFC4E499EB1F77446CFDF1C9BB4DFE50EB727` | Current geometry and the mainland kit |
| `analysis/fit.json` | `75A785EE14E6F894F4A5D0618F9627B845D93432CA802EED11D780F4BA841A58` | Cameras, fit scan, mapped features, comparisons |
| `analysis/reference_points.json` | `0594F6ECE7A1014D701730BFE449DC1F401E5B7E895A08794DEC3EC8B4A62FAB` | Reference pixels read (anchors and features) |
| `analysis/rf_geometry.py`, `rf_fit.py`, `rf_board.py` | `BCE59A39…`, `83339000…`, `48720B45…` | Read-only tools (numpy, OpenCV, Pillow) |
| `plan/rs1_plan.json` | `76606A336AC222AEA023E88B40F10A1AC1898CF3CD35636B97CFD01800D9E603` | RS1 dry run: regions, pieces, identities, checks |
| `plan/rs1_manifest.csv` | `4ACFFB5A26DCF90D8D8CA343EA155B09E8A227BF9D7668D0ECC12D1FE5627221` | 285 create rows plus one hold row |
| `plan/rs1_plan.png`, `plan/rs1_on_ps1_still.png` | `479AA194…`, `7233D42B…` | Diagram; proposal drawn on a copy of PS1's still |
| `plan/rs1_dryrun.py` | `1D68987D…` | The offline generator (matplotlib, numpy) |
| `hashes/protected-before.json`, `hashes/protected-after.json` | `44962DFB…`, (status) | Preservation |

**Rerun, read-only, from the project root:**

```
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/rf_geometry.py
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/rf_fit.py
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/rf_board.py
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/plan/rs1_dryrun.py
```
