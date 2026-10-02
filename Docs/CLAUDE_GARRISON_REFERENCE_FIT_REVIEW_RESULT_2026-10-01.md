# Garrison reference fit and next layout pass: result (2026-10-01)

Claude, 01:55 UTC. Answers `Docs/CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_2026-10-01.md`.

**Scope held.** This was read-only level analysis.

- No engine process, job or capture ran. The queue still holds only the inert `153-yellow-after.hold`.
- No map, candidate, asset, material, config or lighting was written. No actor moved. Nothing was deleted.
- No Git, locks, commit, push, cleanup or messages to others.
- New files are confined to this document, the status update, and the task folder `Saved/GarrisonRestructure/20261001-claude-referencefit/`. That folder holds analysis, board, plan and hash evidence (section 8).
- The 451 protected files, PS1's map, material and receipt, the reference image and the live map were rehashed at 00:35 UTC and again at 01:46 UTC. Every one matches (section 7).

**Not a reference match.** PS1 now has the reference's deck topology and paint: the spine, the left control platform, the octagonal pad and the pier with an outboard berth. The overall widths agree. The reference is still **not** matched: two layout gaps remain at the rear, plus art and asset limits and Connor's absent hangar.

An independent verification pass checked every number and citation against the evidence. Its corrections are included.

## 1. At a glance

| Item | Result |
|---|---|
| Comparison board | `board/rf-board.png` (1682×2087, plus JPG). Six labelled tiles:<br>**A** the reference, unchanged.<br>**B** PS1's overhead still from job 178, unchanged.<br>**C** a copy of the reference with PS1's actual geometry drawn through the reference's best-fit projection.<br>**D** a copy of PS1's still with the reference's features carried through the same fit into PS1's known camera.<br>**E** PS1's deck plane re-projected into the reference's framing.<br>**F** a generated plan in metres.<br>Plus a findings card. Nothing was annotated on a map or the game UI. |
| Camera vs layout | PS1's still has a **known camera**. Its model matches deck edges in the still within 5.7 px, and it draws the forecourt at **0.73×** the pad's scale.<br>The reference has **no camera**. A pinhole was fitted on accepted anchors only. Its error falls monotonically to **17.0 px rms** at a near-orthographic lens, so the reference is drawn with almost no perspective.<br>So **"narrower at the rear" is camera, not layout.** In plan the forecourt is **124.9 m** wide; the reference's compound is **127 m** (band 127–138). |
| Gap 1 (layout) | **The rear is detached and over-deep.**<br>• PS1: 106.8 m of deck behind the quay, then a **26.25 m water strip**, then a straight flat shore at x −3125.<br>• Reference: the compound runs **47–59 m** behind the quay, and its rocky, wooded shore wraps both rear corners. The waterline meets the rear-right corner at x 4329–5433 and runs along the left side to x 8055–8557. |
| Gap 2 (layout; assets and ownership block it) | **The flanks are under-built.**<br>• Reference: seven low service-block fronts plus a small tower, in two rows framing a 28 m apron.<br>• PS1: Armory and Medical on the left, Barracks alone at the rear-right, and the right flank empty.<br>Arranging rows is blocked because the existing buildings are pinned by unresolved associations and no further service-building assets exist. |
| Gap 3 (art/asset) | Surface material, dressing, and the proportions of the drawn pier and ship (section 4). |
| Not counted | **Connor's hangar.**<br>• Reference's hangar front: x 4904–5974. Reservation mouth: x 4390.<br>• Reference's hangar: 60–69 m wide with wings, 28–32 m at the core. Reservation: 38.6 m.<br>No resize. Conflicts are in section 5.7. |
| **Recommended next pass** | **RS1, rear shore attachment and land shoulders** (section 5). A new disposable candidate from PS1 with:<br>• land at the mainland's own level, filling the water strip and wrapping both rear corners along the reference's waterline;<br>• a planted terrace on the empty rear-left flank;<br>• a rock rim;<br>• trees copied from the mainland's existing tree kit.<br>**254 new actors.** Nothing existing is moved, hidden or edited. The dry-run manifest, plan and overlay are in `plan/`. The offline checks found **0 problems**. |
| Gameplay readiness | Section 6. Evidence exists for:<br>• routes, doors and the land gate on the candidates;<br>• deployment and return on the **live** map only;<br>• one drown snap-back.<br>Still open: a spawn check on the final candidate, deployment after any promotion, more drop points, and the PS1 decal check on feet, the helicopter and vertical surfaces. |

## 2. Method: separating perspective from geometry

**Geometry.** `analysis/rf_geometry.py` writes `analysis/geometry.json` from three inputs:

- PS1's base fingerprint, which is FF1's;
- the YM1 bounds from FF1's site probe;
- the PF1 plan.

It confirms that the only differences between YM1 and FF1 are the 32 ring actors and FF1's 125 new pieces. Every building and deck bound is therefore current for PS1, since PS1 is FF1 plus one decal, with the 96 ring segments hidden.

The file also records:

- the mainland's existing environment kit: 1232 trees, each a canopy and trunk pair with BlockAll on both, and the three rock meshes with their materials and native sizes;
- the FF1 paint and quay pieces;
- the Kaiju spawner's sphere components.

**PS1's camera** comes from PS1's `ring_checks.json`: eye (28513.4, 3750, 19795.4), target (11350.6, 3750, 385), horizontal FOV 90°, 1920×1080.

- **Validation.** Projected deck edges were compared with brightness edges in the still, across the pad, the pier, the forecourt and the control platform. They agree within 0.1–2.0 px, except 4.5–5.7 px on two coping and shadow edges.
- **Perspective.** The forecourt is drawn at 3.18 px/m against 4.36 px/m at the pad, i.e. 0.73×.

**Reference fit.**

- **Anchors.** Points were read by eye on 2–3× gridded crops (±5 px) and recorded in `analysis/reference_points.json`. Only **12 accepted anchors** were used: 5 pad vertices, the spine's 2 quay corners and 5 control-platform corners. These features were set from this picture and already accepted. The pier is deliberately not an anchor.
- **Scan.** A pinhole camera was fitted at nine focal lengths from 1200 to 25000 px. The rms falls monotonically from 36.2 to 17.0 px, and a free plane homography gives 16.5 px. The picture is therefore close to an orthographic oblique view, pitch about 44°.
- **Plausible band.** Focal lengths within 30 % of the best fit: 3000–25000 px, rms 17.0–22.0 px. Stronger perspective (F ≤ 2200, rms 25.2–36.2 px) is reported but rejected.
- **Residuals.** Per-anchor residuals are 7–28.5 px, i.e. 1.1–4.1 m at the pad's scale; the rms of 17.0 px is about 2.4 m. That is the picture's own inconsistency.

**Mapping.** Each mapped reference feature was back-projected to the plane it lies on (deck z 385 or water z −35) under every focal length in the band. Mapped positions are given as best value (band). They are indicative positions for review, not a survey.

## 3. The six features (`analysis/fit.json`; board tiles C, D, F)

| Feature | Reference (best fit, band) | PS1 actual | Verdict |
|---|---|---|---|
| **Broad rear compound** | **Width at the quay:** 127 m (127–138).<br>**Deck behind the quay at the rear corners:** 47 m (47–59). | Forecourt **124.9 m** wide (y −2500…9993) and **106.8 m** behind the quay (x −500…10182). | **Width matches.** The narrow look is camera (tile B's 0.73× rear scale).<br>**Depth is a layout gap:** PS1 has 48–60 m more deck behind the reference's rear line (60 m at the best fit). |
| **Low service buildings flanking a central apron** | Seven block fronts 11.7–18.1 m wide (one of them a pair of about 7.5 m blocks), plus a small tower.<br>**Front rows:** base fronts at x 8079–8788, 14–21 m behind the quay.<br>**Back rows:** x 4257–6920.<br>**Apron between the front rows:** about 28 m (y 2043…4872). | **Left:** Armory (x 5668…8118); Medical (x 8658…10138, reaching the quay).<br>**Right:** Barracks alone at the rear (x 1977…4646). The right flank x 4646…10182, y −2500…1819 holds only paint. | **Layout gap,** blocked by assets and ownership (gap 2). |
| **Straight central spine and neck** | The spine's quay corners and the pad vertices are fit anchors. They also fix the neck, where the spine meets the pad's V-notches. Residuals: 9–14 px at the quay corners, 7–28.5 px at the pad. | Spine 38.5 m wide, 43.5 m from the quay to the pad's top flat (x 10182…14532). | **Consistent.** These are fit anchors, so the residuals measure the picture's own consistency, not a match. |
| **Left tower and low operations block** | Control-platform anchors: 11–22 px. Tower at the outer-rear corner; low block toward the spine. | P3's arrangement: Command at the outer-rear corner, Mess_Hall along the spine. | **Consistent** in footprint and arrangement. Building style is art. |
| **Front octagonal pad** | Pad anchors 7–28.5 px. The largest, 26–28.5 px (about 4 m), is on the left flat. | 54 m octagon, offset 7.75 m to image-left. | **Consistent** within the picture's own error. |
| **Right parallel pier and outside berth** | Pier drawn **5.1 m wide at the root and 9.8 m at the end**, diverging **11°** from the spine. Ship about as long as the pier. | Pier 22 m wide and parallel: PF1's choice, to fit the crane, the trucks and a 6 m lane. Ship 57.8 m against a pier of 84 m. | **Proportion difference.** The pier is kept as an accepted relationship. Ship length is art/asset. |
| **Rocky wooded shore connection** | The waterline meets the rear-right corner at **x 4329–5433** and runs along the left side to **x 8055–8557**, wrapping the compound. The hangar is backed into land. | **Land edge:** a straight, flat CityGround edge at **x −3125**: the edge slab `CityGround_00` covers y ±151.7 m (top −5.1, sand-coloured `M_AI_MountainGround`).<br>**Water:** a **26.25 m strip** behind the forecourt; the 15 m ramp is the only connection.<br>**Trees:** the nearest mainland canopies stand 16 m or more behind the edge. | **Layout gap** (gap 1). Ground material and tree density are art. |

**The brief's three observations, resolved:**

- **"Narrower at the rear"** is the camera. PS1's still is a wide 90° view whose rear is drawn at 0.73× the pad's scale, while the reference is near-orthographic. In plan the widths agree to within 2–10 %.
- **"Sparser at the rear"** is real, for two reasons:
  - PS1's deck runs 48–60 m deeper than the reference's compound. That extra depth holds only the reservation outline on the left and centre, and the gate, gate road and Barracks on the right.
  - The flanks lack the reference's service rows.
- **"The shoreline reads as a straight boundary"** is real. It is the unchanged mainland edge, 26 m behind the forecourt.

## 4. Ranked remaining gaps (at most three)

1. **Layout: rear depth and shore attachment.** This is the top third of the picture.
   - **Reference:** the compound ends about 47–59 m behind the quay, the hangar is recessed into land, and the rocky, wooded shore meets both rear corners and runs along the left side.
   - **PS1:** the forecourt runs on to x −500. Beyond the reservation's mouth line (x 4390) there is only:
     - empty deck on the left;
     - the gate, gate road and Barracks on the right;
     - then open water, and a straight land edge.
   - **RS1** (section 5) addresses the layout part of this gap.
2. **Layout, blocked by assets and ownership: flank service rows.** Rows cannot be arranged without owner decisions:
   - **Barracks:** three unassociated `Cube` actors sit inside its footprint.
   - **Armory:** the unassociated `BP_WeaponRack` stands beside it (bounds 0.65 m apart; pivot 2.65 m from Armory's footprint).
   - **Assets:** the project has no further military service-building meshes. The five Tripo buildings are each already used once, and the mainland's town meshes are civilian.

   An asset decision should come before a layout pass: new service blocks, or approved duplicates.
3. **Art/asset: surfaces, dressing and drawn proportions.**
   - The deck is a uniform light material; the reference shows dark, weathered concrete.
   - The mainland ground is sand-coloured; the reference shows a forest floor.
   - There are no apron vehicles, containers or yard clutter. PS1 has only the four pier trucks, the crane and the helicopter.
   - The reference's pier is about 2–4× narrower than PS1's, and its warship is about as long as the pier.

   None of this is layout.

**Not counted as our work.** Connor's hangar is the reservation: x −500…4390, y 1819.4…5680.6, 48.9 × 38.6 m. It is unchanged.

## 5. The one recommended next pass: RS1, rear shore attachment and land shoulders

### 5.1 What and why

RS1 addresses gap 1 with existing assets only. It keeps every accepted relationship and anchor. Nothing existing is moved, hidden or edited; every new piece is tagged and can be removed by tag.

- **Base:** a new disposable candidate copied from PS1 (`4AC42632…`).
- **Proposed name:** `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1`.
- **Geometry source:** FF1's fingerprint `181159BF…`, which is PS1's base.

The pass adds four things:

1. **Land at the mainland's own level.** Top −5, matching the CityGround top (measured −5.1). It fills the 26 m strip behind the forecourt and adds two shoulders wrapping the rear corners along the reference's best-fit waterline. The new land reaches the forecourt's left side to x 8125 (coast attach 8200) and the right side to x 5400. The reference gives 8055–8557 and 4329–5433.
2. **A planted terrace.** Top 400, 15 cm above the deck. It covers the **empty** rear-left flank behind the reservation's mouth line (x ≤ 4390) and keeps 6 m from the reservation's side (y ≥ 6280.6). This is where the reference has land behind its left buildings.
3. **Rocks.**
   - a rim along the new waterline;
   - low rocks where a forecourt wall now faces land, with tops at least 1.77 m below the deck top;
   - rocks against the terrace face, with tops at least 1.87 m below the terrace top;
   - a few on the terrace itself.
4. **Trees.** Each copies a random existing mainland tree: the same canopy mesh, scales and trunk. They are placed by a seeded Poisson sampler at 9 m spacing.

The ramp road remains the only way in, now running through wooded land. The reference's own road enters at the hangar's image-left instead (section 5.7).

### 5.2 Generated content (dry run `plan/rs1_plan.json`, `plan/rs1_manifest.csv`)

Seed 20261001. Labels `IBGC_RS1_*`, tags `IB_GarrisonCB1` and `IB_GarrisonRearShore`, folder `Carrowgate Garrison/Rear Shore RS1`.

| Element | Count | Geometry | Asset (existing, unmodified) | Collision |
|---|---|---|---|---|
| Land slabs | 43 | Cube boxes on 7.5 m x-bands, with finer bands at the landing chamfers and along the terrace stair.<br>The coast is taken at each band's centre line. That leaves 146 m² of water inside the coast and 70 m² of land outside it; the rock rim dresses both.<br>Slabs stay 10 cm off every deck face and clear of the ramp. z −40…−5; 13,112 m² in all. | `/Engine/BasicShapes/Cube` with CityGround's `M_AI_MountainGround` | BlockAll |
| Terrace slabs | 9 | Two rectangles plus a 7-step stair along the rear-left chamfer. z −40…400, so outside the deck they read as an earth bank. 1,679 m². | Same | BlockAll |
| Rocks | 54 | 35 on the coast rim, 9 wall rocks (tops ≤ 208), 5 against the terrace face (tops ≤ 213), 5 on the terrace. Each is a mountain mesh scaled to boulder size, with vertical stretch 0.89–3.02 (median 1.52). | `SM_Iceland_Eroded_Mountain`, `SM_Iceland_Mountain_02`, `SM_Mountain_01` with their `M_AI_MountainRock_*` materials | BlockAll, as on the mainland's mountains |
| Trees | 74 (148 actors) | 71 on the new land, 3 on the terrace. Canopy keep-outs:<br>• half-width + 1.5 m from the walkable deck;<br>• + 2 m from the ramp and the coast;<br>• + 6 m from the gate;<br>• + 3 m from the terrace's inner edges. | GV_Vol7 shrub canopies (mesh-default materials) with a `Cylinder` trunk in `M_Bastion_Bark` | BlockAll on canopy and trunk, as on every existing mainland tree (base fingerprint) |
| **Total** | **254 new actors** | +7.8 % on PS1's 3257 actors | No new asset, no material edit | |

**Before and after.**

- **Before:** land edge x −3125; 26.25 m of water behind the forecourt; the rear-left flank is empty deck at 385.
- **After:**
  - land at top −5 over x −3125…8125, y −9788…15202 (as slabs, outside the deck);
  - terrace at top 400 over x −510…4390, y 6280.6…10003.

**Coast polylines** (world cm):

- **Left:** (−3125, 15100) → (2338, 15226) → (3762, 14351) → (4214, 13321) → (4653, 12883) → (5406, 12819) → (5845, 12309) → (6074, 11576) → (6193, 10989) → (6733, 10703) → (7486, 10349) → (8200, 10013).
- **Right:** (5400, −2510) → (5618, −3052) → (5844, −3633) → (5963, −4219) → (6082, −4804) → (6736, −5363) → (6961, −5942) → (6546, −6554) → (5695, −6893) → (4623, −7097) → (3769, −7587) → (3134, −8365) → (2725, −9607) → (−3125, −9800).

The left start stays inside `CityGround_00`'s edge span.

**Terrace boxes.**

- x 1182…4390 by y 6280.6…10003;
- x −510…1182 by y 6280.6…8000;
- 7 stair steps over x −510…1182, from y 8000 up to the chamfer line (+10 cm).

**Images.**

- `plan/rs1_plan.png`: the diagram.
- `plan/rs1_on_ps1_still.png`: the proposal drawn on a copy of PS1's still through its known camera. Not a render.

### 5.3 Identities (all unchanged; object names in `…PaintStability1:PersistentLevel.`)

**Forecourt and ramp pieces** (each piece's role in `rs1_plan.json` checks):

| Role | Pieces |
|---|---|
| Abutted by new land (within 15 cm) | `IBGC_Forecourt_Deck_00` (`StaticMeshActor_0`), `Chamfer_02/03` (`_7/_8`), `IBGC_Ramp_Deck_00` (`_9`) |
| Under the terrace | `Deck_01/02` (`_2/_3`), `Chamfer_00` (`_5`) |
| Not touched | `Deck_03` (18.3 m away), `Chamfer_01` (1.9 m away) |

**FF1 pieces partly buried under the terrace.** They remain present and unchanged.

- quay pieces: `IBGC_FF_Fore_Coping_06/07/08` (`StaticMeshActor_181/182/183`) and `Fascia_08/09/10` (`_192/193/194`);
- paint: `EdgeLine_06/07/08` (`_201/202/203`).

That is about 75 m of coping, plus the matching edge lines. The terrace top (400) sits above the coping top (393.4).

**Held anchors.** Clearance is the plan distance to the nearest new piece.

| Anchor | Object | Nearest new piece | Clearance |
|---|---|---|---|
| PlayerStart | `PlayerStart_0` | terrace | 22.8 m |
| Barracks; its door | `StaticMeshActor_54`; `BP_DoorFrame_C_1` | land outside the deck edge, 3.6 m below the base | 2.7 m; 11.1 m |
| Cube, Cube2, Cube3 | `StaticMeshActor_69/70/71` | land | 7.6, 7.6 and 4.06 m |
| Armory; its door | `StaticMeshActor_56`; `BP_DoorFrame_C_2` | land outside the edge, 3.85 m below | 3.9 m; 16.5 m |
| BP_WeaponRack | `BP_WeaponRack_C_2` | land | 22.2 m |
| Medical; its door | `StaticMeshActor_1`; `BP_DoorFrame_C_0` | land | 25.8 m; 33.1 m |
| Command; its door | `StaticMeshActor_58`; `BP_DoorFrame_C_3` | land | 31.1 m; 40.6 m |
| Mess_Hall; its door | `StaticMeshActor_60`; `BP_DoorFrame_C_4` | land | 43.3 m; 58.1 m |
| Gate leaf | `BP_DoorFrame_C_6` | land | 6.05 m |
| **Gate** | `StaticMeshActor_280` | `Land_10/11` lie under the gate's overhanging bounding-box corners (about 1.0 × 2.2 m each), 3.81 m below the gate's base | plan overlap, vertical gap 3.81 m |
| Reservation (deck area) | | land abutting the deck's rear face from outside (x < −500) | 0.1 m |
| Control platform, pier, ship, crane, helicopter | | | 29.6, 45.2, 56.2, 80.8, 87.2 m |

The 0.1 m to the reservation is intended: the reference's hangar backs onto land. Its sides keep 6 m, and its straight approach band (x 4390…10182) is untouched.

### 5.4 Ownership

- **Candidate-owned** (Claude's tool, Codex's review): all 254 pieces.
- **Referenced, not modified:** CityGround's material, the mainland's rock and tree meshes and materials, and the engine Cube and Cylinder.
- **Untouched:**
  - Shane's buildings, gate, door frames, Cubes and weapon rack;
  - Connor's reservation;
  - all `CG Mainland` actors;
  - FF1's pieces;
  - the water actors, directors and spawner;
  - the PS1 decal.

### 5.5 Access, door and collision dependencies

- **Land gate and entry.** The ramp corridor (x −3500…−1118, y −1000…500) gets land beside it at −5. No tree stands within its canopy + 2 m of the ramp or its canopy + 6 m of the gate.
  - The gate is **expected** to remain the only way in: the new land is 3.9 m below the deck, beyond the 45 cm step.
  - Rocks are kept at least 1.77 m below the deck top and 1.87 m below the terrace top, so they should not work as steps.
  - Climbing has not been tested; 5.6 adds an attempt.
- **Exit (behaviour change).** A player can now drop off the forecourt's rear or side walls onto land. Before, that edge led to water and Drown snap-back. The way back is over the city ground to the ramp's foot (x −3500, z 10, a 15 cm step) and in through the gate. This is flagged, not hidden.
- **Doors.** No door frame, approach or door lane is touched.
  - Nearest new piece to a building door frame: 11.1 m (Barracks).
  - Gate leaf: 6.05 m, with land 3.9 m below it.
- **Water and drown.** New coast edges drop into water, so Drown applies there (`DrownWaterZ` −35, below the land top of −5). The strip behind the forecourt stops being water.
- **Kaiju spawner** (`BP_M1_KaijuSpawner_C_1`). Its spawn sphere (radius 30 m, centred at (−10617, −105), read from the site probe's component bounds) is 45.2 m from the nearest new land. Its 100 m proximity sphere, which already covers the ramp, now also covers 31 % of the strip land.
- **Navigation.** No NavMesh exists in the level, before or after.
- **Walkable deck.** No tree or rock stands on or over the walkable deck. On the terrace, a 15 cm step is walkable.

### 5.6 Minimum checks for RS1

Reuse the PS1/FF1 tooling and receipts. Do not run the old full matrix.

1. **Plan.** Regenerate the dry run from the copy's own fingerprint. Require 0 problems and the same counts.
2. **Lifecycle.**
   - Copy PS1 → RS1 and verify all 3257 actors identical.
   - Apply and save; reload and verify.
   - Confirm a saved repeat is a no-op.
   - Revert exactly: all RS1-tagged pieces removed, 0 other differences. Re-apply and verify.
   - Diff the candidate against PS1: **only the 254 planned creates, 0 unexpected**.
3. **Engine overlap check.** Each rock's and tree's real bounds against the deck faces, fascia, coping, gate, ramp and door frames. The dry run models rocks as discs from the median native width with a 15 % margin; real widths vary by up to about 11 %. Confirm `Land_10/11` do not intersect the gate mesh.
4. **Scripted PIE with the real infantry pawn.**
   - Existing routes:
     - city road → ramp → gate → gate road;
     - PlayerStart → spine;
     - reservation mouth → spine;
     - the Barracks and Armory door routes.
   - Three new routes:
     - forecourt → terrace step and back;
     - drop from the forecourt's rear edge onto the strip land, then walk via the ramp and gate back onto the forecourt;
     - one step off a shoulder's coast into the water, expecting a Drown snap-back to land.
   - One climb attempt from the land via the rocks toward the deck and terrace. It should fail.
5. **Sweeps.** Three capsule lanes along the ramp, clear of new pieces.
6. **Captures.**
   - PS1's overhead-reference camera, before and after.
   - A reference-matched camera from this fit: eye (56311, 5969, 40946), target (11532, 3028, 385), horizontal FOV 23.6°, roll 1.1° (fit F 4000, 20.1 px rms).
   - One eye-level view along the gate road toward the gate.
   - One eye-level view of the terrace from the forecourt.
   - Rerun the board into a new folder: `IB_RF_STILL=<still> IB_RF_EYE=x,y,z IB_RF_TARGET=x,y,z IB_RF_HFOV=<deg> IB_RF_LABEL="RS1 (job N)" IB_RF_OUT=<new folder> python3 …/analysis/rf_board.py`. This task's `board/` stays untouched.
7. **Preservation.** The 451 protected files, PS1's map, material and receipt, the live map, and no shared-asset writes.

### 5.7 Conflicts and choices for Codex's review (not resolved here)

- **The reference's road is on the other side.** The reference draws its road entering at the hangar's image-left. Under the fit it runs from x 1323 to 5263 along y ≈ 6770–6900, which is **through RS1's terrace**.
  - PS1 keeps the road and gate on the image-right. Earlier results recorded that as a deliberate choice, because the gate is Shane's.
  - If the road ever moves to the reference's side, the terrace must be trimmed or cut.
- **A wider hangar.**
  - At the reference's 60–69 m (with wings), its left side would reach about y 6750–7200 and overlap the terrace's inner edge (y 6280.6) by about 5–9 m. The terrace is generated and can be trimmed.
  - On the right, any wider hangar already meets the gate road and gate. That conflict exists today.
- **A deeper hangar.** Beyond x −500 it would overlap RS1's land, which is removable. The deck already ends at x −500.
- **The drop-off exit** (5.5). If unwanted, a later pass could add edge rails or blocking. RS1 does not.
- **FF1's coping and edge lines.** About 75 m of FF1's accepted rear-left coping, plus the matching edge lines, is buried under the terrace.
- **Art limits.**
  - The land uses the mainland's sand-coloured material, not the reference's forest floor.
  - Rocks are scaled mountain meshes, stretched up to 3×.
  - The land is staircased; the rock rim dresses the steps.
  - Beyond the shoulders' ends (y > 15100 and y < −9800), the old straight edge remains. That is outside the reference's frame.

## 6. Gameplay-readiness checklist

This uses existing evidence only; nothing was re-run.

| Item | Existing evidence | Status for PS1 | Still needed |
|---|---|---|---|
| **Spawn** | `PlayerStart_0` at (4690, 4024, 539) is held identical in every candidate (P3 diff job 139; FF1 and PS1 fingerprints).<br>PlayerStart → spine was reached in P3 (11.2 s) and PF1 (10.48 s, `Docs/…PIER_FINISH…RESULT` §6). | Spawn point and route are fine. The game's own spawn on a candidate was not recorded. | One PIE start on the final candidate: pawn at PlayerStart, settled at z ≈ 475, no overlap. |
| **Moved entrances (Command, Mess_Hall)** | P3 jobs 134–138: both approaches reached and both leaves open (z 200 → −195).<br>PF1: spine → Command approach 11.53 s, → Mess_Hall 3.61 s, Codex's passage route 13.05 s; Codex's own walk 13.09 s. | Approaches work. **The interiors cannot be entered:** the building's collision sits 110 cm behind the door line, identically at the original positions. This is pre-existing. | An owner decision on interiors (Shane/Connor). |
| **Other entrances (Armory, Barracks, Medical)** | FF1 job 164: Barracks door route 1.5 s, Armory 6.8 s, Medical 5.5 s, all reached. | Reached. | The same interior question. |
| **Weapon rack** | `BP_WeaponRack_C_2` is held identical in every candidate. | Not exercised on a candidate. | One approach and interact on the final candidate. |
| **Mission, deployment, return** | **Live map only.** `Saved/ReferenceArtPass/crewqa-host-20260922-2348.log`, lines 1702, 1873, 1925, 2099 and 2100:<br>• PASS listen lobby and Watch;<br>• PASS Carrow Gate arrival, stable 8 s;<br>• PASS return to Watch;<br>• PASS redeployment, stable 8 s;<br>• COMPLETE at 23:51:55 UTC.<br>The directors reference only each other and an optional `GarrisonMech`; no director uses world positions (current-baseline result). | Not exercised: the candidates are not the `carrow_gate` destination. | Rerun `IB.DeploymentCheck` after any promotion (owner decision). `BP_Mech` is still missing; that is a separate blocker, not touched. |
| **Land-gate access** | P3: city road → gate → forecourt reached in 8.9 s, with the leaf opening.<br>FF1 job 164: the 130.6 m land join reached 4/4 in 21.6 s through the gate. | Reached. PS1 changed no collision. | Re-walk after RS1, since the ramp then runs through land. |
| **Water and drown recovery** | Preview job 128 (`Docs/…PREVIEW_RESULT` §6.3): one scripted channel drop; the pawn was back on its exact spine rest spot 1.29 s later.<br>The harbor surface has 0 simple collision shapes; `DrownWaterZ` is −35. | One observation, at one spot. | One drop each into the 9 m control gap and off the pier's outboard edge. After RS1, the new-coast drop and the land-drop recovery walk (5.6). |
| **PS1 decal on feet, helicopter and vertical surfaces** | `IBGC_PS1_PadRingDecal`, decal size (10, 1950, 1950), pitch −90.<br>It projects ±10 cm about z 385 over a 39 m square. The analytic ring sits at r 18.9 m ± 0.2 m.<br>The helicopter's bounds corners reach r 19.2 m, so its parts could cross the ring band. | Not checked visually. | **Visual check only, no rendering rewrite.** The PIE infantry pawn currently renders without its skeletal mesh (FF1 result: missing skeletal mesh / `CurrentVisualData is NULL`), so either:<br>• stand a skeletal-mesh stand-in on the ring line and look at its feet from eye height and close up; or<br>• read the pawn mesh component's Receives Decals flag.<br>Also inspect the helicopter where it crosses the ring band, and any prop later placed on the ring. |
| **Known unrelated issues** | The GameFeatureData ensure on every launch; `BP_Mech` compile errors and the missing garrison mech; the infantry pawn's missing visual data. | Unchanged; out of scope. | n/a |

The three save files Codex noted were written at 21:51–21:52 UTC on 09-30. They are preserved at their current bytes. Both records are kept, and nothing about them was investigated.

## 7. Preservation

| Snapshot | File | Time (UTC) | Result |
|---|---|---|---|
| Before | `hashes/protected-before.json` (`44962DFB…`) | 00:35 | 451 / 451 protected files match Codex's `protected-current.json`.<br>Also matching: PS1 map `4AC42632…`, material `4F6A2A1A…`, receipt `FADED192…`, reference `33491BF3…`, live map `FAFFD601…`. |
| After | `hashes/protected-after.json` (`DCC1390D…`) | 01:46 | 451 / 451 match, 0 changed since before. The five extra files match too. The queue holds only `153-yellow-after.hold`. |

- **No engine.** No Unreal process was started and no job was queued.
- **Writes.** On the device, writes were confined to the task folder, this document and `Claude outputs/CLAUDE_STATUS.md`. The status file was backed up first to VM `~/work/CLAUDE_STATUS.before-rf.md`.
- **Leftover cache.** One early Python import left `analysis/__pycache__/rf_fit.cpython-310.pyc` in the task folder. It is harmless and was left in place, since nothing is deleted.

## 8. Paths

**Evidence.** Everything is under `Saved/GarrisonRestructure/20261001-claude-referencefit/`.

| File | SHA256 | What |
|---|---|---|
| `board/rf-board.png` | `EA7023D2CFD8D71C0BB996433111760D30CDF749175BD3541B26A7E25D316A6F` | The comparison board |
| `board/rf-board.jpg` | `31B1B9FD…` | JPG copy |
| `board/rf-findings-card.png` | `5D525D1A…` | Findings card |
| `board/tiles/tile-C.png` … `tile-F.png` | `A95BD2C1…`, `AF381CC3…`, `C144C615…`, `C98AA628…` | Board tiles |
| `board/board_index.json` | `F6178F33…` | Board index |
| `analysis/geometry.json` | `8BDF743AFF63ACB2104AB69319426915DE72BE5406C94D729AFB9F64BD781420` | Current geometry, the mainland kit, paint and quay pieces, spawner spheres |
| `analysis/fit.json` | `62F20F520C2C1BBBC54936AA954E02740A9E89E8405EF43ECC4E57D52D063FF7` | Cameras, fit scan, mapped features, comparisons |
| `analysis/reference_points.json` | `0594F6ECE7A1014D701730BFE449DC1F401E5B7E895A08794DEC3EC8B4A62FAB` | Reference pixels read: anchors and features |
| `analysis/rf_geometry.py` | `74D4EA5B…` | Tool (numpy, OpenCV, Pillow) |
| `analysis/rf_fit.py` | `83339000…` | Tool |
| `analysis/rf_board.py` | `92F4D1A9…` | Tool |
| `plan/rs1_plan.json` | `E88BA0E2575004EA387B730A997FE42DB2DB7B044A1BDDBDFEC0F0FC4286166B` | RS1 dry run: rules, before/after, regions, pieces, identities, checks |
| `plan/rs1_manifest.csv` | `F41C15C3B4502DB58CA5DFB95D8EB76726A684E9D036ADB0BA34A13795FBFEF8` | 254 create rows plus one hold row |
| `plan/rs1_plan.png` | `9D6ABC58…` | Diagram |
| `plan/rs1_on_ps1_still.png` | `E1E71F46…` | Overlay on a copy of PS1's still |
| `plan/rs1_dryrun.py` | `09515C3B…` | Offline generator (numpy, matplotlib, Pillow, OpenCV) |
| `hashes/protected-before.json` | `44962DFB…` | Preservation, before |
| `hashes/protected-after.json` | `DCC1390D882003DB0437AA7B4B4125140901C09E2B44CFF204BD81D55DB990C1` | Preservation, after |

**Inputs (read only).**

| File | SHA256 |
|---|---|
| `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png` | `33491BF3…` |
| `…/20260930-claude-paintstability/capture-ps1/editor/overhead-reference.png` | `7EA11C94…` |
| `…/capture-ps1/ring_checks.json` | `0F5B3F14…` |
| `…/run1/basefp/base_fingerprint.json` | `75F60ACE…` |
| `…/20260930-claude-forecourtfinish/probe/site.json` | `2E67A09A…` |
| `…/20260930-claude-pierfinish/plan2/plan.json` | `20F26D60…` |
| `…/20260930-claude-paintstability/plan/ps1_plan.json` | `A96C7305…` |

**Rerun from the project root.** The tools read their inputs without changing them, and each rewrites only its own outputs in this task folder:

```
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/rf_geometry.py
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/rf_fit.py
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/rf_board.py
python3 Saved/GarrisonRestructure/20261001-claude-referencefit/plan/rs1_dryrun.py
```
