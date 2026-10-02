# Garrison SR1 service rows preview: result (2026-10-01)

**Brief:** `Docs/CLAUDE_GARRISON_SERVICE_ROWS_PREVIEW_2026-10-01.md` (Codex, after accepting RS1 as the base).
**Status:** DONE. Stopped for Codex's review. This is a disposable candidate only: no live promotion, no shared write, no Git.
**Evidence:** `Saved/GarrisonRestructure/20261001-claude-servicerows/` (index in section 10).

**Summary.** I measured the free ground, the candidate meshes and their dependencies first.

- **Where shells fit.** One strip on the right flank takes low exterior shells safely: south of the gate road, between the Barracks and the cross-road. It holds **two** shells, each with clear walkways all round.
- **What SR1 adds.** Two shells of the existing Armory mesh at uniform ×13, turned 180°, standing on the Barracks' building line.
- **What stays the same.** RS1's 3,541 actors are unchanged; SR1 has 3,543.
- **Fit to the picture.** Each shell's seaward front falls inside the fitted front-x band of a picture block: `R1_back` and `R2_front_b`. Those are two of the picture's three right-flank blocks.
- **Residual for review.** Every low military mesh carries a baked building number: "03" on the Armory mesh, "07" on the Mess_Hall mesh. The shells are turned so their "03" looks over the sea-side (rear) walkway, away from the gate road, the street walkway, the apron, the spawn and the door routes. It is still visible from that walkway, from the cross-road's south end along the deck edge, and from the RS1 right coast (section 3.3).
- **What is still missing.** The picture's third right block covers our gate road's north line and verge. Its left rows stand where the Armory, the terrace and part of the approach band are (section 7.2). Section 9 names the asset that would close the gap.

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows1`<br>`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows1.umap`<br>SHA256 `5C5ABD104B60BEB78CD65F7513771097A883A933687E10F29D8B344CBF8F5400` (SR1 applied) |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ServiceRows1.json`, SHA256 `3479FC827D878E97AEF99D5DC953048E3D1A5E6A1A50CAACBC8BBB92C60FEEF9`.<br>History: created → applied → reverted → applied. Each entry has the file hash; the apply and revert entries also have the plan hash `6CEB8D57…`.<br>Both applies recorded the same exact identities: `StaticMeshActor_1002` (RightBack) and `StaticMeshActor_1003` (RightFront), class `StaticMeshActor`, mesh `/Game/TripoModels/Armory/Armory.Armory`. |
| **Changed counts** | RS1 3,541 actors → SR1 **3,543**: 3,541 inherited (all identical) + **2 new**, `IBGC_SR1_Shell_RightBack` and `IBGC_SR1_Shell_RightFront`. |
| **The shells** | Armory mesh, uniform ×13, yaw 180, base z 380. The base sits 5 cm into the 385 deck, as the inherited Armory's does (pivot z 380).<br>Each shell is **12.74 × 11.45 × 8.80 m**. The street face is a closed hex bay door, 5 cm behind the Barracks' front (the Barracks' engine y-max is −955.6; the shells' is −960.4). See section 3. |
| **Fit** | Passages: Barracks → RightBack **7.93 m**; RightBack → RightFront **7.93 m**; RightFront → cross-road line **4.42 m**.<br>Rear walkway to the deck-edge coping: **3.45 m** (the Barracks leaves 2.11 m). Street walkway to the gate-road line: **6.99 m**.<br>Distances: reservation ≥ 29.7 m; its −Y 6 m band ≥ 24.2 m; approach band 27.8 m; nearest door approach (Barracks) 24.5 m.<br>No paint is covered. See section 2. |
| **Lifecycle** | **PASS** (jobs 190, 192):<br>• copy verified actor for actor;<br>• plan-check gated on the copy's fingerprint digest;<br>• bounds spawned in memory, never saved;<br>• saved apply and reload verify;<br>• saved repeat byte-identical;<br>• 4 ownership negatives refused or failed to verify; nothing saved;<br>• exact SR1-only revert, verified against RS1;<br>• re-apply and final verify: **3,541 identical, 0 changed, 0 missing, 2 extra = 2 planned, 0 unexpected**.<br>See section 4. |
| **Bounds and collision** | • Engine boxes match the plan within 0.5 cm.<br>• No unexpected 3D intersection with any of the 218 inherited anchors. 3 expected ones: the 5 cm base embed in `Deck_02` and `Deck_03`.<br>• All 78 keep-out checks pass. 0 paint overlaps.<br>• GUI queries: 10 capsule lanes clear; 56 face sweeps all stop on the shell, 0 initial overlaps; 6 contacts, all expected.<br>• Pawn collision is the mesh's own per-polygon collision mesh (`Armory_Collision`, 23,666 triangles, `CTF_USE_COMPLEX_AS_SIMPLE`), not a box. The capsule stops 21–235 cm inside the box on every face.<br>See section 5. |
| **Pawn (scripted PIE, not manual play)** | **17 of 17 driven walks** ended as expected, with **0 driven teleports** (job 193, game time):<br>• settled spawn at PlayerStart (offset 0 cm);<br>• PlayerStart → spine 10.6 s; reservation mouth → spine 10.4 s;<br>• Barracks / Armory / Medical doors 1.53 / 6.77 / 5.47 s;<br>• street and rear walkways past both shells 7.43 s each;<br>• three passages 2.8 s each;<br>• a loop 90 cm round each shell 9.17 s;<br>• into each closed bay: stopped at the door, 90.5 cm inside the box face; back out 0.7 s;<br>• city road → ramp → gate → gate road → cross-road 22.33 s.<br>Kaiju spawner: enabled throughout, 0 Kaiju. Its zone spheres have collision disabled in this level (RS1 job 186), so no overlap could register. See section 6. |
| **Non-interactive** | Plain `StaticMeshActor`s. No Blueprint, door frame, interaction, sign or service actor is cloned. Their doors are modelled closed: no opening.<br>No C++ source or Blueprint asset references the Armory mesh; only the live garrison map and the disposable previews do. |
| **Board** | `board/sr1-board.png` (1940×2764; JPG copy). Every tile is labelled RENDER, PICTURE or DIAGRAM:<br>• matched RS1/SR1 overheads;<br>• the picture, then RS1 and SR1 in the picture's fitted framing with the picture's own block-front pixels overlaid;<br>• top-downs and a PIE-path diagram;<br>• eye-level views of both apron sides, both directions of the gate-road corridor and both walkways;<br>• the before/proposed plan.<br>See section 7. |
| **Preservation** | At 06:13 UTC:<br>• Codex's 1,251 records: **1,249/1,249 project files match**. The 2 engine BasicShapes are compared by the jobs' own stamps.<br>• All 1,421 project files of this task's first stamp: 0 changed.<br>• All 8 before/after stamps of jobs 190–193 are byte-identical.<br>• Live map `FAFFD601…` unchanged; RS1 `882F9D20…` and its receipt unchanged.<br>• The four save files match Codex's bytes. |
| **Processes and errors** | 19 engine processes, all owned, all exited; `OWNED_PROCESSES_LEFT=0` after every job.<br>• 17 commandlet steps exit 1 (the known GameFeatureData ensure) with complete reports.<br>• GUI probe exit 0.<br>• GUI check: the editor returned `0xC0000005` **after its log had closed normally**. Every result was written before shutdown and the map was unchanged. PF1 job 146 and FF1 job 163 did the same (their job logs).<br>• All 19 logs closed normally; 0 access-violation, critical or fatal lines.<br>• Error lines = RS1's baseline plus the intended negative-test refusals. See section 8. |
| **Remaining gap** | • Block fronts: 5 vs the picture's 7.<br>• The picture's third right block (`R2_front_a`) covers the gate road's north line and verge.<br>• The apron is still the 38.6 m reserved approach.<br>• Asset need: a number-free low service block (section 9). |

## 2. Measured first: free ground, meshes and dependencies

### 2.1 Free ground (engine bounds on the clean copy, job 190)

The site stage recorded all 218 inherited actors in the forecourt region: engine bounds, oriented mesh box and collision.

On the nominal right flank (x 4646…10182, y −2500…1819), apart from the deck slabs (`Deck_02`/`03`) and the edge fascia, the only inherited actors are:

- paint;
- the deck-edge coping;
- the cross-road and gate lines.

The Barracks ends at x 4646. Its `Cube` stands at x 4561–4611.

| Keep-out ("+ 3 m" = a 3 m clear walkway beside it) | Bounds (cm) |
|---|---|
| Hangar reservation (unchanged) | x −500…4390, y 1819.4…5680.6. 6 m side bands: y 1219.4…1819.4 and 5680.6…6280.6 |
| Straight approach (never filled) | x 4390…10182, y 1819.4…5680.6 |
| Gate road, painted lines included, + 3 m | x 1043.8…10182, y −261.7…418.3 |
| Gate-road walking corridor (no shell inside) | From the Barracks' building line (y −955.6) to the approach (y 1819.4); x 1043.8…10182 |
| 8 m cross-road, lines included, + 3 m | x 9222…10102, y −2420…4899.9 |
| Central axis + 3 m | x 4390…10182, y 3130…4370 |
| Door approaches + 3 m | Each door frame plus its painted route to the road (Barracks, Armory, Medical) |
| Buildings, doors, Cubes, rack, spawn, gate + 3 m | Engine boxes |
| Deck-edge coping + 3 m | `Coping_01`, y −2510…−2450; quay coping, x 10132…10192 |

That leaves three candidate areas:

- **South strip** (right flank, south of the gate road): from the Barracks (x 4646) to the cross-road's 3 m shoulder (x 8922), and from 3 m off the coping (y −2150) to the Barracks' building line (y −955.6). That is **42.8 × 11.9 m**.
- **North strip**, between the road's 3 m shoulder (y 718.3) and the approach (y 1819.4): **11.0 m** deep, or **5.0 m** if the reservation's 6 m side clearance is carried along the approach, as on the left flank. The whole strip lies inside the gate-road walking corridor.
  - The plan record's verdict text says 9.0 m. That figure used the probe stage's provisional 2 m approach margin; the plan's own rule gives 11.0 m.
- **Left flank**, between the terrace and the Armory's door approach: 14.8 × 12.7 m, once the 6 m side line is carried along the approach.

### 2.2 Candidate meshes (job 190 site facts; job 191 GUI probe, nothing saved)

Job 191 spawned each candidate alone, in memory, beside the Barracks. For each it took five stills. It also swept the infantry capsule (r 34, half-height 88, from `BP_IBCharacter_Infantry` defaults) at seven offsets toward every face.

It then spawned a provisional four-shell layout for context. Everything was destroyed before the editor quit, and the SR1 map hash was unchanged.

| Mesh (`/Game/TripoModels` unless noted) | Collision | Probe at the tested scale | Verdict |
|---|---|---|---|
| **Armory** (native 98 × 88.1 × 67.7; 1 material) | Complex-as-simple, own collision mesh | ×13: 12.74 × 11.45 × 8.80 m.<br>Closed hex bay door with a chevron on both long faces; recess 2.35 m on the door side, 0.91 m on the back.<br>**Baked "03"** on the door side near its +X end. | **Used** at ×13, turned 180°. At ×15 it is 13.2 m deep and does not fit the strip. |
| **Mess_Hall** (98.1 × 48.3 × 43.7) | Complex-as-simple | ×20: 19.6 × 9.66 × 8.75 m; closed double door.<br>**Baked "07" on both ends.** | Not used: the "07" ends would face the Barracks passage and the cross-road. |
| Barracks / Medical / Command | Complex-as-simple | Barracks 18.3 m and Medical 19.1 m tall (the Medical with its red cross); Command is a tower. A uniform scale-down to low-block height gives storeys of about 2 m. | Rejected |
| Mainland `SM_Building_Warehouse` / `SM_Building_Garage` | One convex hull: the capsule stops 1.2–1.8 cm **outside** the box on every face | Rusted civilian sheds with timber windows | Rejected: not military buildings |

Every building number in the kit is baked into the building's single material: "02" Barracks, "03" Armory, "05" Medical, "07" Mess Hall.

- No number-free low military mesh or material exists in the project, and making one would be a new asset.
- The Armory mesh has the smallest identity footprint available: one number, on one face. That is why the shells are turned (section 3.3).

**Dependencies** (`analysis/dependency_search.txt`).

- No C++ source or Blueprint asset references the Armory or Mess_Hall meshes; only the live garrison map and the disposable previews do. The one source hit is a comment that mentions "the armory".
- `TripoModels/Materials` holds only the Tripo PBR master and its default textures: no per-building variant and no number-free material.
- The Armory mesh has one inherited use, the Armory itself: scale (25, 20, 15), BlockAll, no material overrides.
- The shells use the same mesh default material and BlockAll, also with no override.

### 2.3 Options measured and not taken

| Option | Why not |
|---|---|
| North strip (right side, at the apron edge) | 11.0 m deep (5.0 m with the side clearance carried along), all inside the gate-road walking corridor. The Armory ×13 (11.45 m) does not fit. The only shallow mesh (Mess_Hall ×18, 8.7 m) shows "07" toward the road and the cross-road. |
| Left flank, terrace side | 14.8 × 12.7 m. In any orientation the shell shows "03" to the apron, the terrace or the Armory's own door approach. It would also screen the Armory's left front. |
| A third right-flank shell | Two 12.74 m shells take 41.3 m of the 42.8 m between the Barracks and the cross-road shoulder (1.4 m to spare). Three would need at least 47.2 m, even with 3 m passages. |
| Mess_Hall ×20 in the strip | 19.6 m long. Its "07" ends would face the Barracks passage and the cross-road. |
| Material override or decal over the number | It would need a new or substituted material asset, and the shell would no longer show the mesh's own look. |

## 3. What SR1 adds

### 3.1 The two shells

Engine plan: `plan/sr1_engine_plan.json`, `6CEB8D57…`.

| Label (component) | Picture block | Location (cm) | Engine box x / y / z (cm) | Neighbours (engine) |
|---|---|---|---|---|
| `IBGC_SR1_Shell_RightBack` (`StaticMeshComponent0`) | `R1_back` (front-x band 6237…6920) | (6075.9, −1532.6, 380) | 5438.8…6712.8 / −2105.4…−960.4 / 380…1260.0 | Barracks 7.93 m (its Cube 8.28 m); RightFront 7.93 m |
| `IBGC_SR1_Shell_RightFront` (`StaticMeshComponent0`) | `R2_front_b` (front-x band 8565…8788) | (8143.0, −1532.6, 380) | 7505.9…8779.9 / −2105.4…−960.4 / 380…1260.0 | Cross-road line 4.42 m; quay coping 13.52 m; pier deck 14.02 m |

The engine boxes come from job 192's bounds stage. The plan's footprints differ from them by at most 0.5 cm.

Both shells share these settings:

- mesh `/Game/TripoModels/Armory/Armory.Armory` with its default material `armory_3d_model_Mat`;
- uniform scale 13, rotation (0, 0, 180);
- collision profile BlockAll (QueryAndPhysics);
- tags `IB_GarrisonCB1` + `IB_GarrisonServiceRows`;
- folder `Carrowgate Garrison/Service Rows SR1`.

The manifest is `plan/sr1_manifest.csv`.

**Door and storey size.** The bay portal on the door side is about 4.4 m wide × 4.0 m high at ×13. That is scaled from the inherited Armory, whose door frame fills it: 8.4 × 4.65 m at scale (25, 20, 15). In the stills, the street-side portal is about the same size. The body is one tall bay storey under roof equipment; the 8.8 m height includes the antennas.

**Setbacks and approach routes.**

- The street faces stand 5 cm behind the Barracks' front. From the gate line to the shell faces is 6.99 m, 5 cm more than the Barracks leaves (6.94 m).
- The rear walkway (3.45 m; the receipt and plan text round it to 3.5 m, the PIE route name to 3.4 m) and the three passages (7.93, 7.93 and 4.42 m) connect the road with the deck edge between and around the shells.
- The RightFront's seaward face is 14.0 m behind the quay. The picture's `R2_front_b` front is 13.9–16.2 m behind it, across the fit's focal band.

![SR1 plan](../Saved/GarrisonRestructure/20261001-claude-servicerows/plan/sr1_plan.png)

`plan/sr1_plan.png` is a DIAGRAM from engine bounds, not a render. It shows before (RS1) and proposed (SR1) at the same scale, with the picture's rows and apron marked.

### 3.2 Collision and doors

The Armory mesh uses complex-as-simple collision. Pawns collide with its own 23,666-triangle collision mesh, not with a box. The single convex element in its simple-collision list is not used for pawn queries.

In job 193, 56 capsule sweeps (7 per face) stopped on the shell itself, with no initial overlap. Each stopped inside the engine box:

| Face | How far inside the box the capsule stopped |
|---|---|
| Street face | 20.7–91.0 cm (the closed hex door's recess) |
| Sea face | 22.8–234.6 cm (the deeper bay) |
| Ends | 47.7–48.7 cm |

Every clearance in this result is measured to the box, so it is conservative.

**Doors are modelled closed.** In PIE the pawn walked into each street-side bay and stopped at the closed door, 90.5 cm inside the box face. The blocking hit was the shell itself, with its normal facing the street.

The capsule ended 10.2 cm higher than on the open deck. It rested on an edge of the bay's raised threshold: the contact point was at z 422.2 on the shell's collision. The pawn walked back out in 0.7 s.

No door opens onto solid collision, because none opens at all.

### 3.3 Signage and identity: the residual for review

The mesh carries one baked number, "03", on its door-side face near one end. With the shell turned 180°, that face looks over the 3.45 m sea-side walkway.

**Not visible** from:

- the gate road or the street walkway;
- the apron;
- the spawn and the door routes;
- the cross-road's road-side part, the pier or the spine;
- the overhead and reference-fit cameras. In `right-flank-oblique` it is a few pixels and not legible.

**Visible** from three places:

- the sea-side (rear) walkway behind the shells, itself a walking route: at a glancing angle along it, face-on when passing (`rear-walkway-eye`);
- the cross-road's south end, along the deck edge, at a glancing angle;
- the RS1 right coast below the deck edge: both shells, RightFront's foreshortened (`right-coast-eye`).

The receipt's and plan's consequence line says the face looks "away from … every route". The exact statement is every route except the rear walkway itself.

The street side shows a closed hex bay door with a chevron and no number. No sign, label or service actor was cloned.

The "03" seen at the left edge of `apron-left-eye` is the original Armory's own marking.

Removing the number needs a number-free material variant of the mesh, which is a new asset (section 9).

## 4. Lifecycle and ownership

| Job (UTC) | Steps | Result | Map after |
|---|---|---|---|
| 190 (05:07–05:10) | RS1 fingerprint; copy; copy verify; site (read-only) | 3,541 identical; 0 changed, missing, extra or unexpected.<br>Site: 218 actors, 13 meshes; target unchanged by the site stage. | `C01E21C0…` |
| 191 (05:15–05:28) | GUI kit probe (in memory, never saved) | 42 stills, 6 isolated candidates, a provisional four-shell layout; SR1 map unchanged | `C01E21C0…` |
| 192 (05:43–05:54) | plan-check; bounds (2 shells in memory); apply+save; verify; saved repeat; 4 negatives; revert+save; verify; re-apply+save; verify-final | Digest match; preflight clean; 0 piece issues.<br>Each applied verify: **3,541 identical, 0 changed, 0 missing, 2 extra = 2 planned, 0 unexpected**.<br>Repeat byte-identical.<br>Revert verify: 3,541 identical, 0 extra. | `5D8D945C…` → `C12221D3…` → `5C5ABD10…` |
| 193 (05:54–06:10) | GUI check (never saves) | 12 stills, queries and PIE (sections 5–6); SR1 map unchanged | `5C5ABD10…` |

Two files are not byte-identical where one might expect it: the re-applied file vs the first applied file, and the reverted file vs the copy. A save re-serialises the package. The check is the actor-for-actor fingerprint comparison, and both applies produced the same object identities.

**Ownership.**

- An actor is SR1-owned only if it carries `IB_GarrisonServiceRows` **and** its object name, label, class and mesh equal a recorded identity.
- The shared `IB_GarrisonCB1` tag never selects anything.
- The ownership manifest is `run1/reapply-save/ownership_manifest.json` (`2BC60D44…`), identical after both applies. It lists both identities, the referenced-but-not-modified mesh, the consequences and the non-interactive record.

| Ambiguity added in memory (saving blocked) | Outcome |
|---|---|
| An extra Cube carrying both SR1 tags with an unrecorded label | REVERT REFUSED: 2 conflicts; nothing changed |
| An untagged Cube using a planned SR1 label | REVERT REFUSED: 1 conflict |
| A Cube with only the shared `IB_GarrisonCB1` tag | Not selected. After removal the level differed from RS1 in 1 way, so the revert did not verify and nothing was saved |
| One recorded SR1 actor with its SR1 tag removed | REVERT REFUSED: 3 conflicts |

In every negative test the target file and the receipt were unchanged, and the save was never reached.

## 5. Engine bounds and collision

`analysis/bounds_check.json` compares job 192's bounds stage with the 218 inherited anchors and the plan's keep-outs. In that stage both shells were spawned in memory exactly as apply would spawn them.

| Check | Result |
|---|---|
| Engine box vs plan | Within **0.5 cm** in plan and 0.1 cm in height |
| 3D intersections (separating-axis test on oriented boxes) | **0 unexpected.** 3 expected: each shell's base sits 5 cm into the deck it stands on (`Deck_02`; RightFront also `Deck_03`) |
| Keep-outs (78: 39 per shell) | All pass.<br>Nearest: gate-road walking corridor 4.8 cm (the building line, by design); coping 344.6 cm; cross-road 442.1 cm; gate line 698.7 cm; Barracks 793.1 cm.<br>Reservation's −Y band ≥ 24.2 m; approach 27.8 m; spawn ≥ 49.3 m; rack ≥ 83.5 m. |
| Paint | **0 overlaps** with the oriented footprints of every marking. Nearest: the deck-edge line, about 2.7 m behind the shells. |
| Deck support | Every corner on `Deck_02` / `Deck_03` (top 385) |
| GUI collision queries (job 193) | **10 capsule lanes clear**: the gate road, both walkways, the north verge, the three passages, the cross-road and a closed loop 90 cm round each shell (corners included). Floor 385 everywhere; largest step 0 cm.<br>**56 face sweeps**: all hit the shell, 0 initial overlaps.<br>**Contacts**: 6, all expected (each shell's base in its deck, counted from both sides); 0 unexpected. |

## 6. The actual infantry pawn (scripted PIE, not manual play)

Job 193 drove the real `BP_IBCharacter_Infantry` pawn by movement input in PIE, timed in game time. Movement settings: max walk 600 cm/s, jump z 420, max step 45 cm, walkable 44.8°.

**Setup placements vs teleports.** 14 of the 17 walks start with a setup placement (`setup_placement` in each record); these are the only position resets. A driven teleport is any jump of more than 150 cm in one frame. It was checked live, every frame. The stored trajectory is sampled every 0.25 s.

| Walk | Kind | Result (job 193) |
|---|---|---|
| Settled spawn | Existing | At PlayerStart's x/y (offset 0 cm), z 475.2 on `IBGC_Forecourt_Deck_02`. Capsule bottom 2.2 cm above the floor, speed 0, after 1.0 s. |
| PlayerStart → spine (63.5 m) | Existing | Reached 3/3 in 10.6 s (RS1: 10.6 s) |
| Reservation mouth → spine (62.3 m) | Existing | Reached 3/3 in 10.4 s (RS1: 10.4 s) |
| Barracks door approach (nearest door to the shells) | Existing | Reached in 1.53 s (RS1: 1.53 s) |
| Armory door approach | Existing | Reached in 6.77 s (RS1: 6.77 s) |
| Medical door approach | Existing | Reached 2/2 in 5.47 s |
| City road → ramp → gate → gate road → cross-road (134.4 m) | Existing | Reached 4/4 in 22.33 s, through the gate.<br>The Kaiju spawner was read 45 times: spawning enabled throughout, 0 Kaiju, pawn 71.7–200.2 m from it (10 samples within 100 m).<br>Its `SpawnZone`/`ProximityZone` spheres have collision disabled in this level (RS1 job 186), so no overlap could register. |
| Street walkway past both shells, seaward (44.5 m, y −611) | New | Reached in 7.43 s |
| **Rear walkway past both shells, landward (44.5 m, y −2277.7)**: the narrowest, 3.45 m | New | Reached in 7.43 s |
| Passage Barracks \| RightBack (16.7 m, x 5042.3) | New | Reached in 2.8 s |
| Passage RightBack \| RightFront (x 7109.4) | New | Reached in 2.8 s |
| Passage RightFront \| cross-road (x 9001.0) | New | Reached in 2.8 s |
| Loop 90 cm round each shell (55.6 m each) | New | Reached 4/4 in 9.17 s, both shells |
| Into each street-side bay, then back out | New | **In: stalled at the closed door, as expected.** The pawn stopped 90.5 cm inside the box face, blocked by the shell itself; its capsule ended 10.2 cm up, on the threshold edge. **Out:** reached in 0.7 s. Both shells. |

**17 of 17 driven walks ended as expected, with 0 driven teleports**: 12 routes, 4 bay legs and the land join. The board's header counts the 12 routes separately. Every walk ended on the forecourt or spine deck, or on the shell's own sill inside a bay.

Not re-run:

- **The weapon rack.** It is ≥ 83.5 m from the shells, so its approach and interaction were not re-run.
- **The shore.** RS1's shore evidence still applies (RS1 job 186): the shells are on the deck and touch no shore piece, coast band or wall band.

## 7. Captures, board and the picture

### 7.1 Board

`board/sr1-board.png` (1940×2764; `sr1-board.jpg` copy). Every tile says whether it is a RENDER, a PICTURE or a DIAGRAM.

| Row | Tiles |
|---|---|
| 1 | **BEFORE RS1** (RENDER, job 185) and **AFTER SR1** (RENDER, job 193), at RS1's overhead-reference camera: eye (28513, 3750, 19795) → (11351, 3750, 385), 90° lens. |
| 2 | **THE APPROVED PICTURE** (unchanged pixels).<br>**RS1** in the picture's framing (from the RS1 board) + OVERLAY.<br>**SR1** in the picture's framing + OVERLAY: a 7680×4320 still from the fitted eye, resampled to the fitted lens and roll (exact, because both cameras share the eye; `board/sr1-reference-framing.png`).<br>The overlay dashes are the picture's own block-front pixels from the reference-fit packet. |
| 3 | RENDER: whole-forecourt plan, top-down.<br>RENDER: right flank, top-down.<br>DIAGRAM: engine footprints and job 193's PIE paths, turned (land left, sea right). |
| 4 | RENDER, eye level: the gate road from the gate (seaward, into the low sun) and from the cross-road (landward); the street walkway beside the shells. |
| 5 | RENDER, eye level: both sides of the apron, landward; the rear walkway (the "03" faces). |
| 6 | RENDER: from the RS1 right coast (eye level; RightBack's "03" over the deck edge, RightFront's foreshortened); right-flank oblique.<br>DIAGRAM: the before/proposed plan. |

### 7.2 Compared with the picture and RS1

The accepted reference fit maps the picture's block-front pixels onto the deck plane (z 385): see `concept_mapped` in `Saved/GarrisonRestructure/20261001-claude-referencefit/analysis/fit.json`. All values below are collected in `analysis/picture_fronts.json`. Two sources are used:

- **The best fit** (F 25000, 16.96 px rms, about 2.4 m at the pad's scale). The picture is close to an orthographic oblique view.
- **The front-x band** over the accepted focal lengths (F 3000–25000).

The board's reprojection uses the fitted eye at F 4000, which lies inside the band. I back-projected the same pixels through it for the F 4000 values.

Positions shift with the focal length: front x by up to 6.8 m, y by up to 6.6 m. Block-level correspondence is therefore solid; metre-level offsets are not.

| Picture block | Front x: band (best fit) | y extent: best fit / F 4000 | SR1 |
|---|---|---|---|
| `R1_back` (right back) | 6237…6920 (6920) | −406…−1731 / −939…−2392 | **RightBack**: front x 6712.8, **inside the band**; y −960.4…−2105.4 |
| `R2_front_b` (right front, outer) | 8565…8788 (8788) | −259…−1433 / −651…−1909 | **RightFront**: front x 8779.9, **inside the band** (8 cm from the best fit); y −960.4…−2105.4 |
| `R2_front_a` (right front, apron edge) | 8470…8748 (8748) | 283…2043 / −69…1815 | **Not placeable.** It covers the gate road's north part (from y 283 at the best fit, from y −69 at F 4000) and the verge up to the approach band, and at the best fit 2.2 m into it |
| `L3_front_b` | 8257…8657 | 4872…6455 / 4841…6531 | Landward of the Medical, reaching 8.1–8.4 m into our approach band |
| `L3_front_a`, `L2_mid` | 8079…8550, 5900…6806 | 6879…8688 (both) / 7023…8993 | Where the Armory and its rack stand |
| `L_small_tower` | 4738…5903 | 6709…7151 / 6856…7343 | In the free left box; the kit has no small low tower |
| `L1_back_pair` | 4257…5560 | 7261…8765 / 7474…9135 | At the best fit, between the RS1 terrace (x ≤ 4390) and the Armory (x ≥ 5668); at F 4000, on the terrace's edge |

**In y, the picture's right blocks reach toward the road.** At the best fit they come to within 0–1.4 m of its south line; at F 4000, within 3.9–6.8 m of it. The shells keep the Barracks' building line, 6.99 m from it, so the road's walking corridor is unchanged.

**In the board's F 4000 framing,** the shells' seaward base edges sit 10 px (RightBack) and 5–6 px (RightFront) below the picture's `R1_back` and `R2_front_b` lines. That is inside the 17–20 px fit error.

**Compared with RS1,** the right flank changes from "Barracks alone" to a row of three along the deck edge. The left flank, the apron, the reservation and the approach are unchanged.

## 8. Preservation, processes and errors

**Isolation.** All steps used the isolated UserDirs under the evidence folder (`user/`, `user-gui/`). Every job hashed the live map around every step and stopped on any change.

- Every job compared its 1,423-file stamp before and after, and reported `SHARED_ASSET_OR_SAVE_CHANGES=0`. The stamp covers: Codex's 1,251 records, RS1's map, receipt and evidence, the reference-fit packet, Codex's RS1 review folder, all 64 `TripoModels` files (the Armory mesh, its collision mesh, material and four textures included), the mainland warehouse and garage, and the engine BasicShapes.
- All 8 stamps are byte-identical (`CDAE77A3…`).
- `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0` in every job. The only preview file written was `CarrowGateGarrison_ServiceRows1.umap`.
- `hashes/preservation-final.json` (`E62BCFB2…`) at 06:13 UTC:
  - Codex's 1,251 records: 1,249/1,249 project files match. They include the live map, the approved picture, the 8 earlier disposable preview maps and their 6 receipts.
  - First stamp: 1,421 project files, 0 changed. That includes RS1's map (`882F9D20…`) and receipt (`0033AAD5…`), the reference-fit packet, and the approved picture (`References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`, `33491BF3…`).
  - The four save files (`IBCharacters`, `IronBreach_Ledger`, `IronBreach_Vault`, `IronBreach_XP`) match Codex's bytes.
- The queue holds only the inert `153-yellow-after.hold`.

`analysis/log_check.json` (`3EF71BDC…`) covers 19 processes:

| Kind | Count | New? |
|---|---|---|
| GameFeatureData ensure block | 45 error lines per commandlet, 26 per GUI run | Pre-existing (RS1 baseline identical) |
| `BP_Mech` Blueprint compile errors (`UpdateMechProximity`) | 7 lines per GUI run | Pre-existing |
| `CurrentVisualData is NULL` | 1 line in the PIE run | Pre-existing |
| Python error lines | 14 | **Intended**: the negative tests' refusal lines |
| `GetSocketInfoByName(WeaponSocket)` warnings during PIE | 3,226 (job 193) | Pre-existing kind (RS1 GUI runs: 3,976 / 8,157 / 8,167) |
| "Failed to load" lines | 6 per process (the GameFeatureData class; `VtuneApi.dll` in GUI runs) | Pre-existing |
| Crash-reporter folders | 19, all the GameFeatureData ensure at startup (`SecondsSinceStart` 0) | Pre-existing kind |
| Access-violation / critical / fatal lines in any log | 0 | — |

**One exit-time crash.** Job 193's editor returned `0xC0000005` after its log had closed normally ("LogExit: Exiting… Log file closed"). By then all results had been written (`finished_utc` 06:09:45; log closed 06:09:51), nothing had been saved, and the SR1 hash was unchanged. The same happened in PF1 job 146 and FF1 job 163 (their job logs). No crash report was written for it. Not investigated.

## 9. Remaining gaps and the specific asset need

| Gap | Measured | Needs |
|---|---|---|
| Block count | SR1: 5 block fronts (Barracks, Armory, Medical + 2 shells). Picture: 7, plus a small tower. | 2 more blocks (see the next two rows) |
| Right apron-edge block (`R2_front_a`) | The picture's block covers the gate road's north part and verge, up to (best fit: 2.2 m into) the approach band | A layout decision on the gate road (not proposed). The verge beside it is 11.0 m deep, or 5.0 m with the 6 m side clearance carried along. |
| Left rows | The picture's left blocks stand where the Armory, its rack and the terrace are, and up to 8.4 m into the approach band | The fixed Armory/Medical and Connor's hangar decision |
| Apron width | 38.6 m reserved approach (y 1819.4…5680.6) vs the picture's ~28–30 m (best fit y 2043…4872; F 4000 y 1815…4841) | Connor's hangar decision |
| Building heights | Barracks 18.3 m and Medical 19.1 m stay fixed; the picture's blocks are low | Fixed by the brief |
| Signage | One baked "03" per shell, on the sea face | **Asset:** a number-free material variant of the Armory mesh. Or: a new low service-block mesh, about 12–19 m front × 9–14 m deep × 7–9 m high, with a closed door, no baked number and per-polygon collision. |
| Variety | Both shells use the same mesh | A second low block type (e.g. the picture's paired ~7.5 m blocks) and a small low tower (~5 m) |

**Brief items not fully met.**

- **"Do not clone … signage or service identities"**: only partly met. No sign, label, door frame or service actor was cloned, but each shell repeats the Armory mesh's baked "03" (section 3.3). Removing it needs the asset above.
- **"Up to four exterior shells"**: two were placed. Measured fit and the baked numbers rule out a third and fourth (section 2.3).

**Not covered by this pass:** manual play, multiplayer and crew runs, mech deployment, AI navigation, final art, lighting and performance.

## 10. Evidence index

`Saved/GarrisonRestructure/20261001-claude-servicerows/` (SHA256, first 16 hex digits):

| File | SHA256 | What |
|---|---|---|
| `plan/sr1_plan.py` | `75106322034983A0` | The planner: keep-outs, footprints, checks, engine plan, manifest, diagram |
| `plan/sr1_engine_plan.json` | `6CEB8D57B1C50029` | Engine plan (2 pieces; source fingerprint digest `A321826C…`) |
| `plan/sr1_plan_check.json` | `6C9702E28148616A` | Keep-outs, clearances, passages, options not taken |
| `plan/sr1_manifest.csv` | `3B2D331F50D63245` | Manifest |
| `plan/sr1_plan.png` | `9DB3DC49904E48BA` | DIAGRAM: before / proposed |
| `plan/probe_spec.json` | `94C0BF1929A876C7` | Probe spec (job 191) |
| `tools/ib_garrison_servicerows.py` | `6F352BF597164891` | Copy / site / plan-check / bounds / apply / revert / verify / negative tool |
| `tools/ib_garrison_servicerows_probe.py` | `1D3A7330A7233F95` | GUI kit probe |
| `tools/ib_garrison_servicerows_check.py` | `32FD3595C473F4DF` | GUI check (stills, queries, PIE) |
| `run1/site/site.json` | `8A80364D5408C0B6` | Site record (218 actors, 13 meshes) |
| `run1/bounds/bounds.json` | `91D83C1408BF95E9` | Bounds stage (shells in memory) |
| `probe/sr1_probe.json` | `413DF7A166146DF3` | Probe record; stills in `probe/editor/` |
| `check-sr1/sr1_checks.json` | `F67B4995B5139DB3` | Job 193 record; stills in `check-sr1/editor/` |
| `analysis/bounds_check.json` | `7F39FB6E70F63206` | Engine-bounds checks (`analysis/sr1_bounds_check.py`, `56F7C2054987BDB7`) |
| `analysis/log_check.json` | `3EF71BDCA106B38B` | Logs and crash folders (`analysis/sr1_log_check.py`, `9EF7B404AE1FC6C8`) |
| `analysis/dependency_search.txt` | `6646DA078F6A214E` | Referencer search for the building meshes, plus the `TripoModels` inventory |
| `analysis/picture_fronts.json` | `8512CAC5F9CA5734` | Picture block fronts on the deck plane (best fit, band, F 4000) vs the shells (`analysis/sr1_picture_fronts.py`, `5865FFF9228BC3BA`) |
| `board/sr1-board.png` / `.jpg` | `BF0447915C20AAC6` / `F02DCE23F973AD69` | The board (`analysis/sr1_board.py`, `7519AE67A368F647`) |
| `board/sr1-reference-framing.png` | `486A1056D36C6392` | SR1 in the picture's framing |
| `hashes/preservation-final.json` | `E62BCFB2DDA87348` | Preservation (`analysis/sr1_preservation.py`, `ECF7471D9369F45A`) |
| `hashes/shared-{before,after}-{190…193}.json` | all `CDAE77A37C0F395A` | The 8 before/after stamps (1,423 files each) |
| `run1/verify-applied/`, `verify-reverted/`, `verify-final/sr_verify.json` | `D0E7DB531ECFCE3A`, `C2E213086710CEBA`, `DF00D9845F75DA18` | The actor-for-actor verify reports |
| `run1/apply-save/` and `run1/reapply-save/ownership_manifest.json` | both `2BC60D44D9B19077` | Ownership manifest, identical after both applies |
| `backup/ServiceRows1-copied.umap`, `-applied.umap`, `-receipt-final.json` | `C01E21C0…`, `5D8D945C…`, `3479FC82…` | Backups |

**Job scripts:** `Saved/zz_job/running/190-sr-copy.ps1` (`ADC7AA5D…`), `191-sr-probe.ps1` (`4AA35C6F…`), `192-sr-lifecycle.ps1` (`0312FF14…`) and `193-sr-check.ps1` (`E483E078…`), each with exit 0. They use `Saved/zz_job/servicerows_lib.ps1` (`3C168D3E…`).

**Job logs:** `Saved/zz_job/logs/190-sr-copy.log`, `191-sr-probe.log`, `192-sr-lifecycle.log` and `193-sr-check.log`. Step logs are in `run1/logs/`, `probe/logs/` and `check-sr1/logs/`.

**Provenance.** The SR1 tools are derived from RS1's tools, which are unchanged; they live in the evidence folder, not in `Scripts/`. No engine, project-setting, plugin or C++ change; no build. The probe's own description says "three offsets", but it swept seven per face.

**Written by this task:**
- the SR1 candidate map and its receipt;
- the evidence folder;
- the job scripts and logs under `Saved/zz_job/`;
- this result;
- the status file (`Claude outputs/CLAUDE_STATUS.md`).

No other Content file was written (`CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`). No Git, locks, commit or push. No live promotion and no shared write.

