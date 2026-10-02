# Garrison composition preview (P3) result — 2026-09-30

Claude, 15:55 UTC. Answers `Docs/CLAUDE_GARRISON_COMPOSITION_PREVIEW_2026-09-30.md`. The engine jobs were 130–139 and ran from 14:50 to 15:41 UTC. The job logs print local time, which is UTC−7.

**Scope held.**

- The only map written was the new disposable candidate `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_P3Candidate1`, along with its receipt.
- The live `Content/LevelPrototyping/CarrowGateGarrison.umap` was `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC` before and after every job and step.
- Preview3 (`8FCD23B9B51906A786AF0A117FC3B8A27B0B1AB3869071AFE6B62ABF6096C585`) is untouched, together with its receipt and evidence. So are the earlier previews `CB1Preview` and `CB1Preview2`.
- Nothing was deleted.
- None of the following happened: Git, locks, commits or pushes; writes to the live map or live saves; changes to shared assets or collision; messages to Shane; menu, mech, water or config work.

**This is a reviewable candidate, not reference acceptance.**

- The rear reservation uses P1's provisional envelope. It is not Connor's hangar size, and no hangar is built: only a reservation is marked.
- The tower and low-block arrangement is a layout proposal for Connor. The buildings are Shane's.

## 1. At a glance

| Item | Result |
|---|---|
| Identity audit (job 131, read-only on the source) | Each building and its door frame form a complete two-actor assembly. Nothing is attached, nothing else overlaps them, and nothing references them. Checked in a full-level T3D export, the level blueprint, `Source/`, `Config/` and `Content/`. The door frames are self-contained automatic doors. Section 2. |
| P3 layout | **Command** (the 24.4 m tower) moves to the control platform's rear-outer corner, keeping its orientation; its door faces the seaward apron. **Mess_Hall** (the 10.9 m low block) lines the spine edge, turned −90° so its door opens onto the spine. There is **7.0 m** of walkway between them. Both buildings stand entirely on the new deck, and each door frame moves rigidly with its building. Section 3.1. |
| Rear reservation | Rear edge, centred on the spine axis: x −500…4390, y 1819.4…5680.6, i.e. **48.9 m deep × 38.6 m wide**. **Provisional:** the gate sets the width and PlayerStart sets the depth. The straight apron to the spine is at least 31.8 m clear. Section 3.2. |
| Base under it | Same as Preview3: 68 of 76 generated pieces are identical, and its 7 prop moves are unchanged. The reservation's 4 edge markings move and 4 inner-line markings are added. |
| Manifest | 111 rows: 76 create, 11 move (the 4 assembly actors plus 7 props), 23 hold, 1 platform hide. Each move row carries the full actor identity and exact source and target transforms. There are no stale paths to the old door positions. |
| Lifecycle (real engine, job 133) | copy → actor-for-actor verify (2983/2983) → apply+save → reload-verify → saved repeat (no-op, bytes unchanged) → revert+save → reload-verify (assemblies back exactly) → re-apply+save → verify. **All passed.** Section 5. |
| Everything else unchanged (job 139, new) | Read-only comparison of the candidate against the source, actor for actor over 15 fields: **2971 identical**. The 11 moves sit exactly on their plan targets. The platform shows only its planned treatment. There are 76 planned pieces and **0 unexpected differences**. All 23 held actors are identical. Section 6. |
| Pawn clearance: engine sweeps (Pawn profile) | 6 of 7 routes are clear, including both relocated entrance approaches and the route past the helicopter. The forecourt → pier centreline is blocked by `Docks_Crane_01`. 7 of 43 pawn-wide pier lanes run the full length, along both edges. Section 7.2. |
| Pawn movement: scripted PIE (not a person playing) | The pawn reached forecourt → spine, spine → pad beside the helicopter, spine → control, both relocated entrance approaches, reservation → spine, and the existing road → gate → forecourt route (the gate opened). It stalls at the crane on the pier centreline, but both pier edge lanes were walked end to end (96.2 m). Section 7.3. |
| Entrances | Both door leaves open and both approaches are clear. However, each building's own collision stops the pawn **110 cm behind the door line**. The result is identical at the **original** positions in Preview3, so it is **pre-existing** and was not caused by the move. The interiors cannot be entered through these frames. Section 7.3. |
| Captures | 7 lit editor shots and a separate annotated comparison board. World lighting and assets are unchanged. Section 8. |
| Preservation | Live map `FAFFD601…` at every step. The 110 protected files (the earlier 106 plus the 4 door blueprint/mesh files) are identical in all 20 snapshots, and the 106 also match the 13:28 UTC baseline. 0 content writes outside the preview folder. No Unreal process is left running. Section 9. |

## 2. Identity audit before moving (read-only)

`Scripts/ib_garrison_assembly_audit.py` loads the source map in a commandlet and never saves. It records each target by its full object identity:

- components with their collision;
- attach parents and children;
- actors whose bounds overlap it.

It then exports the whole level as T3D and searches every actor block for references to the four targets.

| | Command | Mess_Hall |
|---|---|---|
| Members | `StaticMeshActor_58` (Command) + `BP_DoorFrame_C_3` (Command_DoorFrame) | `StaticMeshActor_60` (Mess_Hall) + `BP_DoorFrame_C_4` (Mess_Hall_DoorFrame) |
| Attach parents / attached children | none / none | none / none |
| Other actors overlapping the bounds | none (only the ground slab `GarrisonPlatform_New` that every building stands on) | none (the same) |
| Referenced by other actors (T3D, 2989 actor blocks) | none | none |
| Level blueprint | no references | no references |
| `Source/`, `Config/` | no match | no match |
| `Content/` (binary search) | only the garrison map itself (the disposable previews excluded) | the same |
| **Verdict** | **complete two-actor assembly** | **complete two-actor assembly** |

The door frames are `BP_DoorFrame` instances. Each has four components:

- a query-only trigger `Box`;
- the leaf `NODE_AddStaticMeshComponent-5` (`SM_Door`, BlockAllDynamic);
- the frame meshes;
- a `Door Control` timeline.

In play the leaf slides from relative z 200 to −195. None of the level's gameplay actors references the buildings: the five act directors, `BP_M1_KaijuSpawner`, PlayerStart and the weapon rack.

**First attempt resolved from evidence.** Job 130 reported "incomplete", but both reasons were tool artefacts, so nothing was guessed and nothing moved on that verdict:

- its selected-actor T3D export was empty (146 bytes) in the commandlet;
- its overlap test counted the ground slab.

Tool v6 exports the full level and names the ground slab as background. Its run (job 131) is the audit of record: `…/audit2/audit.json` `8343ADB81599FD93941CA0B4F82DC7170EB140F3C421CA61E49FAE11CFF1E2B2`, with `level.t3d` `32C071DD7AE52CC37A96F2EA6D4E28AA64FA91F7C10E2E26949470F73AAFF2A5` (4,680,209 bytes). The plan refuses to compose P3 without this audit, or if the audit shows an incomplete assembly or a different map hash. The harness tests the first two.

## 3. The P3 candidate

Frame: land/rear is −X, sea is +X, and image-right is −Y (the docks side). The deck top is at z 385.

### 3.1 Control platform (x 11082…14532, y 5675…10275)

| | Command (tower, 24.4 m) | Mess_Hall (low block, 10.9 m) |
|---|---|---|
| Building | `518.0 5770.0 380.0` yaw −90 → **`11967.5 8899.1 380.0` yaw −90** (turned 0°) | `318.0 2854.0 380.0` yaw −90 → **`12458.8 6379.5 380.0` yaw 180** (turned −90°) |
| Door frame | `875.1 5934.8` yaw −89.79 → **`12324.6 9063.9` yaw −89.79** | `870.8 2890.4` yaw 90.38 → **`12495.2 5826.7` yaw 0.38** |
| Footprint | x 11232…12671, y 7683…10122 | x 11232…13684, y 5775…6983 |
| Door faces | +X: the seaward apron (18.6 m deep, open to the spine) | −Y: the spine |
| Approach (6 m out) | `12924.6 9063.9`: on the deck, pawn-clear | `12495.2 5226.7`: on the spine, pawn-clear |
| Edge margins | rear 150, outer 152.6, seaward 1860.8, to the spine seam 2007.8 cm | rear 150, spine seam 100, seaward 848, outer 3292 cm |
| On the new deck | 100 % of 1348 samples; max dz 0.0 cm | 100 % of 1180 samples; max dz 0.0 cm |

- **Walkway.** The walkway runs between the back of Mess_Hall and the side of Command. It is **700 cm** wide (target 700) and runs from the rear margin to the seaward apron.
- **Overlap and support.** There is none and no loss. The platform held nothing but the old slab before the move (audit). The nearest other building is Medical, 10.9 m (Mess_Hall) and 11.1 m (Command) away across the control gap. No prop target lands on either relocated footprint.
- **Door moves.** Each door frame rotates with its building about the building's pivot. The door's offset and yaw relative to its building are therefore unchanged, and the door normal is the building's local +Y.
- **Why Command keeps its yaw.** The tower keeps its designed front, with its door, facing the open sea-side apron. The 7 m walkway reaches that apron, and the plan grid, the engine sweep and the scripted PIE walk all reach the door approach from the spine.
- **Option for Connor.** If the tower's door should face the walkway itself (−Y, toward Mess_Hall), that means a −90° turn and a new footprint. It is a quick plan change, but not what this candidate shows.

### 3.2 Rear reservation (provisional, space only)

| | |
|---|---|
| Outline | x **−500 … 4390**, y **1819.4 … 5680.6**; mouth +X, on the spine axis y 3750 |
| Size | **48.9 m deep × 38.6 m wide**: P1's safe envelope, **provisional** and not Connor's hangar dimensions |
| Width constraint | The main gate's footprint reaches y 1219.4. Adding 6 m clearance gives y 1819.4, mirrored about the axis so the reservation stays centred. |
| Depth constraint | From the forecourt's rear edge (x −500) to PlayerStart − 3 m. PlayerStart (4690, 4024) is unchanged in this pass. Moving it forward would let the reservation run to x 8058. |
| Before the move | The area held exactly the four assembly actors plus the ground slab. Nothing is in it now. |
| Apron to the spine | The straight band x 4390…10182, as wide as the reservation, is **at least 31.8 m clear** (at x 8690, where Medical reaches in). PlayerStart stands 3 m in front of the mouth; it has no collision and is not an obstacle. |
| Markings | An 80 cm outline plus a 40 cm inner line 1.5 m inside it, in `MI_Landmass_HelipadMarking`, with no collision. The plan render labels the dimensions and constraints. Readability is reported in section 8. |

Compared with Preview3, whose shallow reserve sat forward at x 1822…4390 and y 750…6750, the reservation now starts at the true rear edge.

### 3.3 Plan and manifest

`…/plan/`: `plan.json` `53589671009BBBACC7DAA435B4E6951462A4A39416E594DCDE020C315D9F1F05`, `manifest.csv` `185528CC164225FDCBC736FF51552299A42355537E6BEFDE23C21A724A802CE9`, `report.txt` `8734D8AE1759D67FBC80A0938A97CCA7FB0EC68CFAD2965E66B9C7D773B7460E`. The plan is engine job 132, read-only on the source.

- **Plan result.** 0 problems, and the apply preflight on the source is CLEAN.
- **Preserved-ground check.** Every held anchor keeps 100 % of its deck samples: Armory, Barracks, Medical and their doors, the gate and its approaches, PlayerStart, BP_WeaponRack and the three Cubes.
- **Path checks.** The paths show no missing ground and steps of at most 8.5 cm, on the existing land ramp.
- **Old door paths removed.** The forecourt → old Command/Mess_Hall door paths are gone, replaced by routed paths to the relocated approaches.

The assembly rows in `manifest.csv` (`op` = move) are:

| role | label | identity | from | to |
|---|---|---|---|---|
| assembly building | Mess_Hall | `…PersistentLevel.StaticMeshActor_60` | 318.0 2854.0 380.0, yaw −90.00 | 12458.8 6379.5 380.0, yaw 180.00 |
| assembly door | Mess_Hall_DoorFrame | `…PersistentLevel.BP_DoorFrame_C_4` | 870.8 2890.4 380.0, yaw 90.38 | 12495.2 5826.7 380.0, yaw 0.38 |
| assembly building | Command | `…PersistentLevel.StaticMeshActor_58` | 518.0 5770.0 380.0, yaw −90.00 | 11967.5 8899.1 380.0, yaw −90.00 |
| assembly door | Command_DoorFrame | `…PersistentLevel.BP_DoorFrame_C_3` | 875.1 5934.8 380.0, yaw −89.79 | 12324.6 9063.9 380.0, yaw −89.79 |

The scales are unchanged. Every row is part of the verified apply and of the exact revert.

## 4. Tool changes and offline harness

| `Scripts/` file | SHA256 (device) | Change |
|---|---|---|
| `ib_layout_garrison.py` | `59170F1C5995DC107AAFB66AB854309D9BB675DAE720089A6172FFE00992585D` | See the list below the table. |
| `ib_garrison_assembly_audit.py` (new) | `6F19081CEB86DFFDD43DF7D685BE606EFF1E900CA154A142EBEF110C803C42F7` | Read-only identity audit (section 2) |
| `ib_garrison_composition_capture.py` (new) | `0873B74E35642EFEE9BA442C30F0346E0F194B3178CF61196B8A95181E0E6252` | GUI-editor shots, Pawn-profile sweeps and scripted PIE walks. Never saves. |
| `ib_garrison_clearance_check.py` (new) | `701012C89BA8B773CA4A82A7524ECE7C80F037D1893871463F339C24BD7E4D8D` | Door sweeps at deck level (as-is, and with the frame ignored), route sweeps with a clamped floor probe, a pier lane scan, door walks with leaf tracking, and extra route walks. Never saves. |
| `ib_garrison_candidate_diff.py` (new) | `7FE36D82CDD0E786420A56F22474B26EA69C7848EDD49EC449DFBE935FB718D4` | Read-only candidate-against-source comparison, actor for actor (section 6) |
| `ib_render_garrison_plan.py` | `D25A6D7179A9B80D4246A34B7AD694CDE50F1D7693D5B2D719B15A2E46E62D8A` | Draws the relocated buildings, door-normal arrows, routes and the labelled provisional reservation. Panel titles are no longer clipped. |
| `ib_garrison_composition_board.py` (new) | `4DF71849B6722011B12847976269B5FAAD848E88AC96F5FDDEC468F0938186E8` | Comparison board. Its footer text comes from the evidence JSONs. |

The `ib_layout_garrison.py` changes:

- `--composition P3` / `IB_GARRISON_COMPOSITION`, which requires the identity audit;
- building placement by rule, with doors moved rigidly;
- the rear reservation;
- composition checks: footprints on the deck, edge margins, door facing, walkway, apron, occupants;
- a 50 cm pawn-clearance route planner;
- no stale door paths;
- **actor-level collision in the generated-piece check**.

**Actor-level collision.** `piece_issues` now also fails a generated deck whose **actor** collision is off. Component collision alone could leave a visually intact deck that drops the pawn through, and such a deck no longer passes apply or verify.

**Regression check.** Without `--composition`, the tool's plan, manifest (`3578AE17…`) and report are byte-identical to Preview3's; the plan differs only in `created_utc`.

**Offline harness** (a mock engine, not evidence of engine behaviour):

- `drive_lifecycle` **39/39**. This now includes an injected `actor collision disabled` deck: it is refused at the pieces stage, the platform is untouched, and nothing is saved.
- `drive_p3` **23/23**:
  - audit refusals;
  - injected failures of a building rotation, a door location, the tower location and deck actor collision;
  - apply, reload and saved repeat;
  - a revert refused over a later edit to a moved building;
  - an exact revert and re-apply.
- `drive_diff` **8/8**. A held actor moved, an assembly scale changed, an untagged piece and the platform's actor collision left on are each reported as unexpected. The map files are never written.

## 5. Lifecycle on the real engine (job 133)

Each step ran in a new commandlet process with the isolated UserDir `…/20260930-claude-composition/user`. Every step exits 1 because of the pre-existing GameFeatureData errors: 23 appear before the script and 0 during it. Logs are in `…/run1/logs/c-*.log`.

| Step | What | Result | Candidate after |
|---|---|---|---|
| `c-copy` | Duplicate the source to the new package and save only it | copied | `1B374352…` |
| `c-copy-verify` | New process: load the source, then the copy, and compare | 2983 of 2983 actors match; 0 missing, extra or differing; receipt `created` | `1B374352…` |
| `c-verify-created` | Verify the clean state | 0 differences; the assemblies are at their source transforms | `1B374352…` |
| `c-apply-save` | Preflight, then pieces (checked, including actor collision), then moves (all 11 checked for location, rotation and scale), then the platform last, then a full check, then save | `APPLY verified and saved` | `21355364B9441B77998F6693F106D9FB445144940ADC84F33CF22A21C7B4C728` |
| `c-verify-applied` | **Reload** in a new process and verify | **0 differences**: building and door transforms survive save and reload | `21355364…` |
| `c-repeat-apply-save` | The same apply with save, in a new process | `already applied … nothing changed, nothing saved`; bytes unchanged | `21355364…` |
| `c-revert-save` | Validation first (refuses any conflict), then the exact revert, a clean-state check and save | `REVERT verified and saved` | `9B332912E2E34B2F73DD6D4FDBB3E4A70799279B1C731C2DA9012AB695C59009` |
| `c-verify-reverted` | Reload and verify the clean state | **0 differences**: all four assembly actors are back at their exact source transforms, no generated actor is present, and the platform flags equal the captured before-state | `9B332912…` |
| `c-reapply-save` | Apply with save | `APPLY verified and saved` | `550234E37695D83CF45E58B78FA00723DE83C226490FBD931C718D8C96250FF7` |
| `c-verify-final` | Reload and verify | 0 differences | `550234E3…` |

The receipt is `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_P3Candidate1.json`. Its history is `created 1B374352…` (15:08:48Z), `applied 21355364…` (15:10:17Z), `reverted 9B332912…` (15:12:36Z), `applied 550234E3…` (15:14:11Z).

Byte backups:

- `…/backup/P3Candidate1-created.umap` (`1B374352…`);
- `…/backup/P3Candidate1-applied.umap` (`550234E3…`).

The guards were extended, not changed:

- the receipt lifecycle;
- the refusal of the source map (`LIVE_WRITE_ENABLED = False`);
- the stale-target refusal;
- the revert that refuses to overwrite a conflicting edit.

For that reason the full refusal matrix of Preview3's job 127 was not re-run on the engine. The new actor-collision failure path was exercised only in the harness. On the engine, all 76 pieces passed that check in both applies and in every verify.

## 6. Everything else unchanged (job 139, read-only)

`ib_garrison_candidate_diff.py` loads the source map and then the candidate in one commandlet and saves neither. For every actor it records 15 fields by object name:

- label, class, location, rotation, scale;
- hidden flag, actor collision;
- root component class, visibility, collision profile and collision state;
- mesh, attach parent, tags, outliner folder.

Each difference is then classified against the plan.

| Source actors | Candidate actors | Identical | Planned moves at their targets (0.5 cm / 0.05°) | Platform treatment only | Planned pieces (tag, label, folder, location, mesh) | **Unexpected** |
|---|---|---|---|---|---|---|
| 2983 | 3059 | **2971** | **11** | **1** | **76** | **0** |

- **Held actors.** All **23 of 23** are identical in every field: Armory, Barracks and Medical with their door frames, `SM_MainGate_Tripo`, `BP_MainGateDoor`, PlayerStart, BP_WeaponRack, `Cube`, `Cube2`, `Cube3`, `concrete_bunker_3d_model`, `harbor guard tower 3d model`, `2026-09-04-10-03-41-983`, `IB_Harbor_Surface`, `Water_Placeholder` and `Seawall_Main`…`Seawall_Main5`.
- **Assemblies.** In the candidate, the four assembly actors have no attach parent and no children.
- **Platform.** The only differences are its four treated flags, plus its collision profile name reading `Custom`. The engine renames a preset profile whenever collision is set on it. The recorded `BlockAll` is restored by the revert, which step `c-revert-save` verified.
- **Files.** Both map files were byte-identical before and after the comparison.
- **Output.** `…/diff/candidate_diff.json` `06AA2948C196BFCDCCA5AB2563253FBEF62C80F73ECA5F430DF73D427ED6EDB1`.

## 7. Evidence, kept separate

### 7.1 Geometry (plan; no movement)

- Deck support comes from the plan geometry, from footprint samples against the new deck boxes: sections 3.1 and 3.3.
- **Routes.** These use a 50 cm A* grid over the deck, keeping 60 cm from the deck edges and from inflated obstacle boxes, then string-pulled. Clearances near 60 cm are the planner's minimum at a corner, not a narrow passage.

| Route | Length | Least clearance |
|---|---|---|
| forecourt → spine (PlayerStart → spine) | 63.5 m | 1156 cm (Medical) |
| spine → pad deck beside the helicopter | 67.5 m | 171 cm (Helicopter) |
| forecourt → pier end past the crane and trucks | 96.2 m | **0**: no pawn-width way past the obstacles' boxes on the grid, so the straight centreline is tested in the engine instead |
| spine → control-platform apron | 41.2 m | 68 cm (Mess_Hall) |
| spine → Command door approach | 69.3 m | 60 cm (Mess_Hall corner) |
| spine → Mess_Hall door approach | 21.6 m | 525 cm |
| reservation mouth → spine | 62.3 m | 1250 cm (Medical) |

### 7.2 Engine collision queries (editor world, Pawn profile; not movement)

The queries use `capsule_trace_single_by_profile("Pawn")` with the infantry pawn's own capsule:

- radius 34, half-height 88, max step 45;
- taken from `/Game/Characters/Infantry/BP_IBCharacter_Infantry`;
- the body swept from step height to head height over a clamped floor probe;
- doors in their editor (closed) state.

These are jobs 136 and 137, and their results are identical.

| Route | Result |
|---|---|
| forecourt → spine | clear (129 samples, floor 385) |
| spine → pad beside the **helicopter** | clear (137) |
| forecourt → pier, **centreline** | **blocked**: first block `Docks_Crane_01` at x 14900; 11 blocked segments |
| spine → control platform | clear (83) |
| spine → Command door approach | clear (140) |
| spine → Mess_Hall door approach | clear (45) |
| reservation mouth → spine | clear (127) |

**Pier lane scan.** 43 pawn-wide lanes at 50 cm spacing, y −1231…869:

- **7 run the full length**: the outboard edge at y −1231, −1181 and −1131, and the inboard edge at y 719, 769, 819 and 869;
- the first blocker on the others is `Docks_Crane_01` (30 lanes) or `SM_Truck_Cargo4` (6 lanes).

**Doors** (jobs 137 and 138: deck-level sweep from 6 m outside to 3 m inside):

- As-is, the closed leaf blocks at the door line, as expected in the editor world.
- With the door-frame actor ignored, the first block is the building's own `StaticMeshComponent0`, **110.0 cm behind the door line**. This holds at both P3 doors and at both **original** doors in Preview3.

### 7.3 Scripted PIE (the real pawn driven by movement input; not a person playing)

The pawn was `BP_IBCharacter_Infantry_C` (r 34, hh 88) on the candidate, with the GUI editor on the isolated UserDir `…/user-gui`. Nothing was saved, and the candidate's bytes were unchanged after every run.

| Walk | Result |
|---|---|
| forecourt → spine | reached, 11.2 s |
| spine → pad beside the helicopter | reached, 11.9 s |
| spine → control-platform apron | reached, 10.0 s |
| spine → Command door approach | reached, 11.5 s |
| spine → Mess_Hall door approach | reached, 3.6 s |
| reservation mouth → spine | reached, 10.4 s |
| **existing route: city road → gate → forecourt** | **reached**, 8.9 s. The gate leaf (`BP_DoorFrame_C_6`) was open (z −195) at the threshold and closed again afterwards. The existing functioning route is preserved. |
| forecourt → pier, centreline | **stalled** at x 14863 against `Docks_Crane_01` |
| pier outboard edge lane, y −1181 (job 137) | **reached**: 96.2 m in 16.1 s, 0 cm lateral drift |
| pier inboard edge lane, y 794, past truck 4 and the crane (job 137) | **reached**: 96.2 m in 16.1 s, 0 cm drift |

**Doors, A/B** (jobs 134, 136 and 137 for P3; jobs 135 and 138 for the original positions in Preview3):

- Both leaves open (z 200 → −195).
- The pawn gets **75.9 cm** past the door line.
- It is stopped by the building's own `StaticMeshComponent0`, 110 cm behind the line, at every position.
- **The interiors cannot be entered through these frames, before or after the move.** The move preserved the condition exactly. This is a finding for Connor/Shane, not a regression.

Job 134's `door_leaf_moved = False` for Mess_Hall compared only the before and threshold samples. Its own `door_after` shows z −195, and job 137 tracks the lowest leaf position (−195 for both).

### 7.4 Superseded evidence (kept, not relied on)

- **Job 130 audit.** Superseded by job 131, as explained in section 2.
- **Job 134 route sweeps.** The capture tool's floor probe climbed onto structures (floors of 1705/1762), which confounded its route sweeps. Superseded by jobs 136 and 137.
- **Job 135/136 door sweeps.** The floor probe at the door line landed on the closed leaf and lifted the capsule, so the first wall read −6.9…−7.8 cm. Superseded by the deck-level sweeps in jobs 137 and 138.
- **Job 135/136 logs.** Their `LIVE_MAP_SHA256=MISSING` lines are a job-script bug. The script's `$MAP` collided with the library's `$map`, because PowerShell variable names are case-insensitive. The live map was hashed directly (`FAFFD601…`) and was also verified in both jobs' snapshots. Jobs 137 and 138 use `$TESTMAP`.

### 7.5 Not tested

- A person playing: no manual PIE or packaged build.
- Networked play, AI or navigation (the level has no NavMesh), combat, mechs and the act directors at runtime.
- Falling into the new 9 m control gap. The water behaviour is still expected from collision data plus Preview3's single scripted channel drop, not observed here.
- Lighting builds and performance.

## 8. Captures and comparison board (visual evidence)

The shots were taken in the GUI editor from level viewport cameras, with no actor spawned (job 134). The lighting is the existing `DirLight_PreDawn`, unchanged. Camera positions were chosen so the faces shown are lit. Each shot is 1920×1080, in `…/run1/shots/`.

| File | SHA256 | Shows |
|---|---|---|
| `overhead-reference.png` | `34D6BEE2D5CB0EBCFA6D50B750A71252DA6446466BC2683504E40AE9648CA3BB` | Framed like the approved reference (rear at the top, sun behind the camera). The rear is clear, the tower and low block sit on the control platform, and the pad and pier are in place. |
| `overhead-topdown.png` | `846186CFBD4BC994237914939461619F7CF33DBB454464AB362704070584E326` | Top-down view of the whole composition |
| `control-platform.png` | `EAD36E56C23ED42A7CB86C240EC3945D81C27D9EE5F18D6232C43D58943157EE` | Command (tower) and Mess_Hall (painted 07) on the platform, with the walkway between them. Medical (painted 05, with the red cross) remains on the forecourt behind, across the control gap. |
| `control-tower-entrance.png` | `4ACC7CC0DD886978742DD37CFDAC7A0B3EF659A7B601E530F9BE15606EFDE4D7` | Command's entrance, with the leaf closed in the editor, facing the seaward apron |
| `control-lowblock-entrance.png` | `BF6A4A4DC89537DED3305FE9DA9624902F5382B8F7377FAE65AF8502E1D4BF5A` | Mess_Hall's entrance facing the spine |
| `rear-reservation.png` | `5CF7ACB294C6A23CF9E1D7850521FB18E255E9501D93B5461E50BF42B0F5A159` | From 11 m above the forecourt toward the rear: the outline and inner line are readable, with the gate at the right |
| `rear-reservation-eye.png` | `8F3E983C729A49E3A69906D55D6400904537C4E6361E088E8D2A10F720C57404` | The same line at eye height from 42 m. **The flat outline almost disappears**; see decision 7. |

**Comparison board** (annotations only here, never in the level), in `…/board/`:

- `p3-comparison-board.png` `D91E2E462208977C9AED6B735C9D2F34CB58CFD18660CB1765E25991A95E7A94`, 2400×2764. The top row is the approved reference, today's map and the P3 plan with dimensions, routes and door arrows. Below are the captures with captions. The footer is generated from the evidence JSONs.
- `p3-plan.png` `8C7C42D621E5F56069AB23507DB7A094979B6FC70426EBFA6DD3D9784E4E3B1D`, the plan render alone.
- The device bridge adds a metadata chunk to each PNG on commit. The pixels are identical to the rendered files: RGB pixel SHA256 `9A834286…` and `0448095F…`.

## 9. Preservation

| Check | Result |
|---|---|
| Live map | `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC` before and after every job (130–139) and every lifecycle step. A step stops its job if the live map changes. |
| Shared assets and live saves | 110 protected files: the 106 from the preview task, plus `BP_DoorFrame`, `SM_Door`, `SM_DoorFrame_Corner` and `SM_DoorFrame_Edge`. All **20 snapshots** (`…/hashes/shared-before-130.json` through `shared-after-139.json`) are identical, and the 106 also equal the 13:28 UTC baseline (`shared-before-120.json`). |
| Content writes | 0 outside `_GarrisonPreview_Disposable`. Inside it, only `CarrowGateGarrison_P3Candidate1.umap` is new, next to the kept `CB1Preview`, `CB1Preview2` and `CB1Preview3`. |
| Preview3 | `8FCD23B9…`, unchanged in every job. Its receipt and evidence are untouched. |
| UserDir | Commandlets used `…/20260930-claude-composition/user`; the GUI editor used `…/user-gui`. |
| Processes | Every commandlet was awaited to exit, and each GUI run was awaited under a timeout; all GUI runs exited on their own. The owned-process check in jobs 130–138 used the preview task's folder pattern (copied from `preview_lib.ps1`), so on its own it proves nothing for this task. Job 139 listed every Unreal-family process on the machine: **0**. The pattern now matches both task folders. |
| Evidence index | `…/run1/evidence.json` `841991DF7B135D81691B32660453ACD9E766E053766A2E4ED257358FFF267B80`: jobs, steps, receipt, all hashes and the per-snapshot comparison. |

## 10. Findings and decisions for Connor/Shane

1. **Hangar size and PlayerStart** (Connor). The reservation is P1's provisional 48.9 × 38.6 m envelope. Moving PlayerStart forward would allow a depth up to x 8058.
2. **Building interiors** (Shane/Connor). The Command and Mess_Hall meshes are solid 110 cm behind their door lines. This is pre-existing, and the move preserved it. Opening them means changing the buildings' collision or assets, which this pass does not do.
3. **Tower door direction** (Connor). The door currently faces the seaward apron. The alternative faces the walkway (a −90° turn and a new footprint).
4. **Pier crane** (Connor). `Docks_Crane_01` on the pier centreline blocks 30 of 43 lanes. Passage exists along both edges: 3 clear pawn lanes outboard of the crane and 4 inboard of truck 4, at 50 cm lane spacing. The crane could move to the outboard edge instead.
5. **Helicopter pose.** It has roll −17.3° and a pivot 377 cm below its deck. Is it a deliberately downed prop or a misplaced import? The pose is kept relative to the pad.
6. **Ship draft.** The hull bottom sits 3 m under the waterline. The mesh's real waterline is unknown; adjust after a look.
7. **Reservation markings.** These are flat lines, readable from above but almost invisible at eye height. Wider lines or upright markers are possible if wanted; only flat markings were added, per "reserve space only".
8. **Cube, Cube2, Cube3.** Their association is still unknown, so they are kept exactly as they are.
9. **Road side.** The road enters at the hangar's image-right, where the gate already is. The reference draws it at image-left. It is kept, because the gate is Shane's.

## 11. For Codex's in-game review

- **Candidate.** `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_P3Candidate1`, left in its verified `applied` state `550234E3…`. Open it in the editor or PIE.
  - Spawn at PlayerStart and walk up the spine; the control platform is on the +Y (left) side.
  - Mess_Hall's door is on the spine at (12495, 5827).
  - Command's door faces the apron at (12325, 9064).
  - The reservation is behind PlayerStart.
- **Revert** (exact, validation-first). Run a commandlet with `IB_GARRISON_PLAN=…/20260930-claude-composition/plan/plan.json`, `IB_GARRISON_TARGET_LEVEL=<candidate>`, `IB_GARRISON_APPLY=1`, `IB_GARRISON_REVERT=1` and `IB_GARRISON_SAVE=1`. To verify only, set `IB_GARRISON_VERIFY=1`.
- **Evidence** is under `Saved/GarrisonRestructure/20260930-claude-composition/`:
  - `audit2/`, `plan/`;
  - `run1/`: logs, shots, `composition_checks.json`, `evidence.json`;
  - `clearance/{p3-candidate, p3-candidate-2, preview3-original, preview3-original-2}/clearance_checks.json`, with SHA256 `0B24C7DD…`, `BD891992…`, `E2CBB36B…` and `48B48437…`;
  - `diff/`, `board/`, `hashes/`, `backup/`.
- **Job scripts and logs** are `Saved/zz_job/running/130…139-*.ps1` and `Saved/zz_job/logs/130…139-*.log`.
- **Cleanup after review.** The whole `Content/_GarrisonPreview_Disposable/` folder and its receipts are disposable and not for commit. Nothing was deleted in this task.
