# Garrison pier finish preview (PF1) result — 2026-09-30

Claude, 17:45 UTC. This answers `Docs/CLAUDE_GARRISON_PIER_FINISH_PREVIEW_2026-09-30.md`. Engine jobs 140–146 ran from 16:28 to 17:32 UTC; the job logs print local time (UTC−7).

**Candidate, left saved and applied for review:**
`/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_PierFinish1`
(`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_PierFinish1.umap`, SHA256 `C904EF8C6B35850BD9E6498A0C8B93ABFFAB758A2E756F6E1BACAA6675D75DA2`, the last `applied` entry in its receipt). No test process is running.

**Scope held.** The only map written was this new candidate (plus its receipt). The live `CarrowGateGarrison.umap` stayed `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC` before and after every step. P3Candidate1 `550234E3…` and Preview3 `8FCD23B9…` are unchanged, and so are their receipts and evidence. Nothing was deleted. There was no Git, no locks, no commit or push, no shared asset or collision change, no material repaint, and no message to anyone.

**One revision inside this task (r1 → r2).** The first pass (r1: 20 cm lines, 30 cm dashes) did not read in the reference-framed overhead, which is the same lesson as the baseline's 30 cm reservation lines. The same candidate was therefore reverted exactly with the r1 plan and re-applied as r2: 40 cm markings (the width of P3's pad ring), and the four trucks 75 cm nearer the channel edge so the wider lane lines keep clear of them. Everything below is r2 unless it is marked r1. The r1 evidence is kept in `run1/`.

## 1. At a glance

| Item | Result |
|---|---|
| Pier corridor | The crane is turned to lie along the pier (yaw −90 in P3 → 0) against the outboard (berth) coping, beside the ship. The four trucks stay in a row on the inboard side, 75 cm nearer the channel edge than in P3. **A straight 6.0 m marked lane** runs from the forecourt join to the pier-end edge line (x 10182…18480, y −221.7…378.3). |
| Measured with collision (engine, Pawn profile) | The pier lane scan swept 85 pawn-wide lanes, 25 cm apart, from x 9882 to 18300. 33 were clear: 29 between the crane and the trucks, and 4 beyond the trucks along the channel edge. The clear pawn-centre band between the crane and the trucks is **y −274.3…446.0 (720 cm)**, so the **obstacle-free corridor is 788 cm**. It is bounded by the crane's and truck 4's own collision, and the marked lane lies inside it. The Pawn-profile sweeps along the lane in both directions and along both lane edges are clear on floor z 385. |
| Pawn movement (scripted PIE) | **16 of 16 routes reached.** They include the pier lane in both directions (96.5 m, 16.1 s each), both lane edges, the three altered joins, both door approaches (the coping stays out of them; the nearest is 732 cm from the Command route), a deliberate step up onto the control platform's rear coping and along it, Codex's passage [10982,3750] → [13900,5850] → [14100,7300] → [11300,7300] (13.05 s), and the existing road → gate → forecourt route. None stalled and none fell. |
| Deck finish | 72 new pieces, all tagged `IB_GarrisonPierFinish` plus the run tag: **18 coping** (M_Bastion_Concrete, BlockAll, an 8 cm walkable curb), **18 fascia** (M_Bastion_Concrete, NoCollision), **36 markings** (NoCollision: 18 edge lines, 4 lane lines, 12 route dashes, 2 door bars, all 40 cm). They cover every one of the 18 water edges of the spine, control platform, pier and pad. The dark water gaps and the octagon are kept. |
| **Marking colour: not yellow** | The only existing marking material, `MI_Landmass_HelipadMarking`, sets a parameter called `Color`, but its parent `M_FlatCol` exposes `Base Color`. The yellow therefore never applies, and the engine reports the instance's effective Base Color as **0.18 grey** (Metallic 0, Roughness 1). The lines read warm grey in sun and dark grey in shade. This also holds for P3's pad ring, spine dashes and reservation outline. Fixing it needs a material change that this brief does not allow; options are in section 8. |
| Joins, doors, helicopter | The coping crosses a deck join only at its water corners (0 samples away from the water). Doors and door approaches are clear of coping. Measured from the helicopter's footprint box, the nearest new piece is a pad edge line 777 cm away and the nearest coping 847 cm, so nothing new is inside its clearance. There are 0 new coplanar overlaps. |
| vs P3 | All 76 P3 pieces are identical, and so are 6 of the 11 moves (ship, helicopter, both buildings and door frames). The only changes are the crane and the four trucks, plus the 72 tagged pieces. The 23 held actors, the platform treatment, the reservation (48.9 × 38.6 m, provisional) and the composition are identical. |
| Lifecycle (real engine) | r1 (job 142): copy verified 2983/2983 → apply → reload-verify → saved repeat (no-op) → revert → verify → re-apply → verify. r2 (job 145): verify r1 → **exact revert with the r1 plan** → verify clean against both plans → apply r2 → reload-verify → saved repeat (no-op, bytes unchanged) → revert → verify → re-apply → verify-final. **All passed.** |
| Everything else unchanged | Candidate vs source, actor for actor (job 145): 2983 source actors against 3131 in the candidate. **2971 identical**; 11 moves and the platform treatment exactly as planned; 148 generated pieces; **0 unexpected**; 23/23 held actors identical. |
| Preservation | 116 protected files (shared assets, the live map, the earlier previews, their receipts and the live saves) are unchanged in every snapshot from before-140 to after-146. There were 0 content writes outside the preview folder and 0 owned processes left. |

## 2. Pier props: identity audit and the relocated props

Job 140 was read-only on the source; its output is `audit-pier/audit.json`. `Docks_Crane_01` and `SM_Truck_Cargo`, `_Cargo2`, `_Cargo3` and `_Cargo4` are each a standalone single actor:

- one StaticMeshComponent (BlockAll);
- no attach parent or children;
- no references in the full-level T3D export (2989 blocks) or the level blueprint.

At the source spots, the only bounds overlap any of them has is with the 45°-turned ship's box (truck 4 overlaps nothing). The ship is an independent prop and stays at its P3 berth.

| Prop | Source (loc / yaw) | PF1 r2 target (loc / yaw) | Supported footprint (mesh-bounds box at the target) |
|---|---|---|---|
| Docks_Crane_01 | (11190, −5073, 80) / −135 (P3: −90) | (15108.5, −763.8, 380) / **0** | x 14108.0…16113.6, y −1220.0…−310.5. **100 % on the pier deck**, 55 cm inboard of the berth edge (5 cm inboard of the coping), so no part is over the coping or water. Same height relative to its deck as at the source. |
| SM_Truck_Cargo4 | (12687, −439, 85) / 0 | (11382, 608.6, 385) / 0 | x 11104.9…11658.5, y 467.0…749.8. 100 % on deck. |
| SM_Truck_Cargo | (13152, −900, 85) / 0 | (12182, 608.6, 385) / 0 | x 11904.9…12458.5, same y. 100 % on deck. |
| SM_Truck_Cargo3 | (13612, −1363, 85) / 0 | (12982, 608.6, 385) / 0 | x 12704.9…13258.5, same y. 100 % on deck. |
| SM_Truck_Cargo2 | (13966, −1838, 85) / 0 | (13782, 608.6, 385) / 0 | x 13504.9…14058.5, same y. 100 % on deck. |

- **Trucks:** their boxes end 175 cm from the channel edge (y 925). In P3 and r1 they ended 250 cm from it (actor y 533.6, box edge y 674.8); r2 moves them +75 cm in y only.
- **Crane:** it stands on its own footprint beside the ship, with its jib side toward the berth. None of its collision reaches into the lane (see the lane scan in section 3).
- **Engine check:** job 146 confirmed every prop and assembly in the saved candidate at its plan transform. The saved crane is at (15108.5, −763.8, 380), yaw 0, and the four trucks are at y 608.6; all five report `at_plan: true`.

## 3. The pier corridor: what was measured

The design widths below are plan geometry, not movement. They come from mesh-bounds boxes at the target transforms and are conservative.

- Clear band between the crane's box and the trucks' boxes: y −310.5…467.0, **777.5 cm**.
- Marked lane: 600 cm between the lines' inner edges, centred in that band. That leaves 88.7 cm from each lane edge to the nearest box.
- Lane lines: 40 cm wide, outside the lane. Their outer edges are 48.7 cm from the trucks and 48.8 cm from the crane.
- The lane is 1053 cm from the berth edge and 547 cm from the channel edge.

Engine collision (job 146) used the editor world and Pawn-profile capsule sweeps (radius 34 cm, half-height 88 cm). These are collision queries, not movement.

- **Lane scan:** 85 capsule sweeps run along the pier (x 9882…18300), one every 25 cm across it. 33 reach the end unobstructed: 29 between the crane and the trucks, and 4 beyond the trucks along the channel edge (y 789…864). The contiguous clear band of pawn centres is y −274.3…446.0 (720.3 cm). The first blocked centres are −275.1 (`Docks_Crane_01/StaticMeshComponent0`) and 446.8 (`SM_Truck_Cargo4/StaticMeshComponent0`). That makes the obstacle-free corridor **788 cm** (the 720 cm band plus the 68 cm capsule). The marked lane (−221.7…378.3) is inside the band. From the scan (the last clear and first blocked centres, ± the 34 cm radius), the real collision faces are about y −308.7 (crane) and about y 480.4 (trucks). The crane's box (−310.5) is therefore about 2 cm conservative and the trucks' box (467.0) about 13 cm conservative. Measured from real collision, the lane edges keep **about 87 cm** (crane side) and **about 102 cm** (truck side). The lane lines' outer edges keep about 47 cm and about 62 cm.
- **Sweeps:** These routes were swept and are clear, with no blocked segment and no sample without floor:
  - forecourt → pier end and back along the lane: 195 samples each, 96.5 m, floor 385.0 throughout. The long leg runs at y 100, 22 cm off the lane's centre line; the start and goal sit on the centre line (y 78.3).
  - both lane edges, crane side at y −182 and truck side at y 338: 385 samples each, 96.2 m;
  - the forecourt → spine join.

Scripted PIE (job 146) drove the real `BP_IBCharacter_Infantry_C` with movement input. This is not a person playing.

- Along the lane (the same route, long leg at y 100), forecourt → pier end: reached, 3/3 waypoints, 16.08 s, 96.5 m, capsule centre z 475.2 throughout.
- Pier end → forecourt: reached, 16.08 s.
- Crane-side edge (y −182) and truck-side edge (y 338): both reached end to end, 96.2 m in 16.05 and 16.06 s, 0 cm drift.
- "Drift" is the tool's largest distance from the route polyline and includes the stop at the goal. For these two routes it is 54 and 41 cm. Their first and last legs are short jogs (28 cm and 22 cm) between the centre line and y 100, all inside the lane.

The r1 layout, with trucks at y 533.6, measured a 713 cm obstacle-free corridor and 645 cm pawn-centre band. Its walks also reached. It is superseded, and its evidence is in `run1/`.

## 4. The deck finish

| Kind | Count | Material | Collision | Dimensions and placement |
|---|---|---|---|---|
| Coping | 18 | M_Bastion_Concrete (the project's wall concrete; world-position mapped, so scale is continuous across seams) | **BlockAll**: an 8 cm walkable curb, under the pawn's 45 cm step | 50 cm on the deck plus a 10 cm lip over the quay face. Top +8 cm above the deck (+8.4 or +8.8 cm where corner pieces overlap and are staggered), face 38 cm. |
| Fascia | 18 | M_Bastion_Concrete | NoCollision (the deck box already blocks) | Facing on the quay wall, 6 cm proud (5.2–6.0 cm where overlapping corner pieces are staggered), from 45 cm below the waterline up to the coping. |
| Edge lines | 18 | MI_Landmass_HelipadMarking | NoCollision (paint) | 40 cm, centred 100 cm inboard of every water edge. They join at the corners of their own deck and at neighbouring-deck corners of up to 95°. At the pad notch's sharper turn they stop at the end of their edge. |
| Lane lines | 4 | same | NoCollision | Pier: outside the 6 m lane, x 10182…18480. Spine: y 3150 and 4350 (axis ±6 m), stopping short of the seaward edge line. |
| Route dashes | 12 | same | NoCollision | 300 × 40 cm every 600 cm on the control apron: along the seaward apron from the spine edge to Command's door line (x 14108); the leg to Command's door; and the leg through the 7 m passage between Mess_Hall and Command toward the platform's rear. |
| Door bars | 2 | same | NoCollision | 300 × 40 cm, centred 50 cm in front of the Mess_Hall and Command door faces. |

**Plan checks (job 144, engine plan, 0 problems):**

- Coping on its deck with the lip over water: 18/18.
- Markings on deck: 36/36.
- Joins: the coping lies under join samples only at the water corners:
  - control|spine 15/690;
  - forecourt|pier 10/220;
  - forecourt|spine 10/385;
  - pad|spine 0/449.
  - In every case, 0 samples away from the water, so the joins stay flush.
- Doors and door approaches are clear of coping.
- Nearest coping per route:
  - pier lane 250 cm;
  - Codex's passage 168 cm;
  - control apron 374 cm.
- Z-fighting:
  - no two new pieces are coplanar (0);
  - overlapping coping tops step 0.4 cm, marks 0.3 cm and fascia 0.4 cm.
- P3's own markings have 40 overlapping pairs. They are unchanged and not caused by this pass.
- Deliberately absent:
  - no finish on the existing forecourt, which is not a new deck;
  - no service props or clutter;
  - nothing inside the helicopter's clearance.

**Material probe (job 144, `material-probe/material_probe.json`, read-only):**

- The instance `MI_Landmass_HelipadMarking` overrides `Color` = (0.95, 0.82, 0.15). Its parent is `/Game/LevelPrototyping/Materials/M_FlatCol`.
- M_FlatCol is DefaultLit and opaque. It exposes the vector `Base Color` (default 0.18 grey) wired to Base Color, the scalar `Metallic` (0) and the scalar `Roughness` (1).
- The parent does not expose `Color`, so the instance's effective Base Color is 0.18 grey.
- The byte name tables of all 16 `MI_Landmass_*` instances carry the same `Color` override on M_FlatCol, so they all render the parent grey.
- The live map uses several of them: Beach, Debris, Helipad, HelipadBroken, HelipadLight, HelipadMarking and HelipadRust.

## 5. Lifecycle and reversibility (real engine)

Every step runs as a separate commandlet process with the isolated UserDir `…/20260930-claude-pierfinish/user`. Each process exits 1 because of the 23 pre-script GameFeatureData errors; the tool's own status is `complete` every time. The one exception is job 144's read-only material probe, which exited 3. Its commandlet crashed at shutdown with an access violation in `python311.dll`, 4 s after the script had written its complete JSON and reported success. Its log's 21 error lines after the script are that crash's banner and callstack. It writes nothing else.

| Job / step | Result | Candidate after |
|---|---|---|
| 142 copy + new-process verify | 2983/2983 actors, receipt `created` | 231003D8AECD |
| 142 apply r1 + save → reload-verify → saved repeat | applied-verified → verified → already-applied-verified (bytes unchanged) | 3BB5F494F516 |
| 142 revert + save → verify → re-apply + save → verify | reverted-verified → verified → applied-verified → verified | 95692ABA0F26 → EE2C6EB2285E |
| 145 verify r1 | verified (the r1-applied backup equals the candidate) | EE2C6EB2285E |
| 145 revert **with the r1 plan** + save | reverted-verified | FE552B833BD1 |
| 145 verify clean against r1, then against r2 | verified, verified | — |
| 145 apply r2 + save → reload-verify | applied-verified → verified | 61155F53A40E |
| 145 saved repeat | already-applied-verified, not saved, bytes unchanged | 61155F53A40E |
| 145 revert + save → verify | reverted-verified → verified | 5D9098B5F16B |
| 145 re-apply + save → verify-final | applied-verified → verified | **C904EF8C6B35** |
| 145 candidate diff (read-only) | 2971 identical, 11 moves + platform + 148 generated as planned, **0 unexpected**, 23/23 held | unchanged |

- **Refusal tests:** v9 changes only PF1 geometry (the marking widths, the trucks' edge keep, keeping a 29 cm edge-line stub) and adds one plan check. The apply/verify/revert code is unchanged, so the accepted engine refusal tests stand. The offline harness reran the whole matrix anyway because the tool changed.
- **Harness results:**
  - PF1 21/21: missing or contrary pier audit refused; injected finish-tag, coping-collision and crane-transform failures refused without saving; revert with a moved coping piece refused.
  - New r1→r2 set 16/16. v9 refuses to apply r2 over the r1-applied candidate and refuses to revert it with the r2 plan. It then reverts r1 exactly and runs the full r2 lifecycle. The P3-only plan, manifest and report are byte-identical under v8 and v9.
  - P3 23/23, lifecycle 39/39, diff 8/8.
- **Receipt:** `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_PierFinish1.json`. The engine's save is not byte-deterministic across sessions, so every reverted state has its own hash.
- **Backups (not used for restore):** `backup/PierFinish1-created.umap`, `-applied.umap` (r1), `-r1-reverted.umap` and `-r2-applied.umap`.

## 6. Evidence, kept separate

- **Geometry (plan, no movement):** section 3's widths, the support percentages in section 2 and the join, door and overlap checks in section 4.
- **Engine collision (editor world, Pawn profile, not movement), job 146:** 15 of 15 routes are clear, with 0 blocked segments and 0 samples without floor (`run2/shots/pierfinish_checks.json` → `sweeps`):
  - PlayerStart → spine;
  - spine → pad beside the helicopter (floor 384–385);
  - both lane directions and both lane edges;
  - spine → control apron;
  - spine → Command and Mess_Hall door approaches;
  - reservation mouth → spine;
  - Codex's passage;
  - the three altered joins: spine → pad beside the notch coping at y 3600, spine → control at x 14100, forecourt → spine at y 3750. All are flush at 385.0.
  - The coping curb (passage → onto the control platform's rear coping → along it → back): floor 385.0…393.4, a largest step of 8.4 cm, under the pawn's 45 cm step height.

  The pier lane scan is in section 3. These are standing-capsule and floor queries only; they say nothing about movement.
- **Scripted PIE (the real pawn, movement input), job 146:** These use `BP_IBCharacter_Infantry_C` (radius 34, half-height 88). Each drift figure includes the stop at the goal.

| Route | Result | Time | Length | Drift |
|---|---|---|---|---|
| PlayerStart → spine | reached | 10.48 s | 63.5 m | 23.5 cm |
| spine → pad beside the helicopter | reached | 13.84 s | 67.5 m | 74.9 cm |
| forecourt → pier end (lane) | reached | 16.08 s | 96.5 m | 54.1 cm |
| pier end → forecourt (lane) | reached | 16.08 s | 96.5 m | 40.8 cm |
| lane crane-side edge, y −182 | reached | 16.05 s | 96.2 m | 0.0 cm |
| lane truck-side edge, y 338 | reached | 16.06 s | 96.2 m | 0.0 cm |
| spine → control apron | reached | 6.86 s | 41.2 m | 29.7 cm |
| spine → Command door approach | reached | 11.53 s | 69.3 m | 42.3 cm |
| spine → Mess_Hall door approach | reached | 3.61 s | 21.6 m | 22.4 cm |
| reservation mouth → spine | reached | 10.39 s | 62.3 m | 0.0 cm |
| Codex's passage route | reached | 13.05 s | 78.6 m | 51.8 cm |
| join spine → pad (y 3600) | reached | 3.05 s | 18.0 m | 0.0 cm |
| join spine → control (x 14100) | reached | 3.36 s | 20.0 m | 0.0 cm |
| join forecourt → spine (y 3750) | reached | 3.19 s | 19.0 m | 0.0 cm |
| coping curb (up 8.4 cm, along, back) | reached | 1.27 s | 8.0 m | 57.8 cm |
| existing road → gate → forecourt | reached | 8.86 s | 53.0 m | 0.0 cm |

- Capsule centre z stayed at 474–475 cm on the decks. It reached 483.6 on the coping and rose from 108.9 cm on the road to 475.1 on the gate route. No walk fell or dropped below the deck.
- The run had 0 script errors and no dirty map packages at exit.
- The GUI editor process returned `0xC0000005` after its log had closed normally ("LogExit: Exiting … Log file closed"). Every result had been written before shutdown, nothing was saved and the candidate hash was unchanged. The identical r1 run (job 143) returned 0. Owned-process cleanup found nothing left running.
- The GUI editor log carries only the known pre-existing groups: the GameFeatureData ensure block, 7 BP_Mech "Update Mech Proximity" compile lines, and one `CurrentVisualData is NULL` line from the pawn. r1 had the same.
- **Not tested:**
  - a person playing;
  - multiplayer;
  - navmesh (the level has none);
  - the door interiors (pre-existing; not in scope);
  - how the markings would look once the colour is fixed.

## 7. Captures (all are UE lit renders; world lighting and assets unchanged)

Location: `Saved/GarrisonRestructure/20260930-claude-pierfinish/run2/shots/`

| File | Kind |
|---|---|
| `overhead-reference.png` | EDITOR view, framed like the approved reference |
| `overhead-topdown.png` | EDITOR view, top-down |
| `pier-lane-ground.png` | EDITOR view, the full clear lane from the pier end (raised) |
| `pier-lane-eye.png` | EDITOR view, the lane at eye height |
| `pier-channel-quay.png` | EDITOR view, coping and fascia along the channel and the dark water gap |
| `control-pad-edge.png` | EDITOR view, control platform and pad edges |
| `spine-control-join.png` | EDITOR view, the spine/control seam at Mess_Hall's door bar |
| `pie-pier-lane-from-forecourt.png` | **GAMEPLAY** (PIE, the player's own camera) |
| `pie-pier-lane-from-pier-end.png` | **GAMEPLAY** (PIE) |
| `pie-control-apron-to-command.png` | **GAMEPLAY** (PIE) |

**Board:** `board/pf1-r2-board.png`. It has four parts, top to bottom:

1. The reference, the site as it is now and the r2 plan.
2. The same overhead crop in r1 and r2.
3. The editor and gameplay grids, each tile labelled.
4. A data-driven footer.

The r1 shots are kept in `run1/shots/` (superseded).

## 8. Remaining issues and decisions

1. **The markings are grey, not yellow** (section 4). The fix is outside this brief because it needs a material change. Two options:
   - **(a)** A new MI, for example `MI_Garrison_DeckPaint_Yellow` on M_FlatCol with `Base Color` (0.95, 0.82, 0.15), assigned to the finish markings only. This has no side effects. In the candidate it is a plan-constant swap followed by the same revert/apply.
   - **(b)** Rename the override in the shared `MI_Landmass_*` family to `Base Color`. This also recolours P3's markings and the live map's landmass and helipad pieces, which have been rendering grey. That is a visible change to the live map, so it is Connor's call.
2. **Shade.** At this sun angle the ship and crane shadow much of the pier, so its lines read dark. They would be darker there even once they are yellow.
3. **Door interiors are pre-existing.** Each building's collision stops the pawn 110 cm behind its door line. This is documented and unchanged, and no shared collision was touched.
4. **Forecourt edges are not finished.** The forecourt is an existing deck, outside "spine, left control platform, right pier and octagonal pad". Its joins to the spine and pier are flush.
5. **P3's own markings have 40 overlapping pairs** (coplanar). They are unchanged; this pass adds none.
6. **Owner calls carried from P3:**
   - the helicopter pose (roll −17.3°, pivot 377 cm below the deck it stands on, kept relative to its deck);
   - the ship's draft (hull bottom 300 cm under the waterline is a visual guess);
   - the hangar itself (Connor's);
   - the Cube associations.
7. **Engine noise, pre-existing:**
   - the 23 GameFeatureData errors before every script;
   - the BP_Mech "Update Mech Proximity" compile errors in the GUI log.

   **Two shutdown crashes seen here:** the probe commandlet (in `python311.dll`) and the GUI editor (`0xC0000005` after its log closed). Both happened after all output was written. Neither is investigated.
8. **Eye-level crease.** A straight crease runs along the pier deck in the eye-level views, in r1 and r2 alike. It lies on P3's own deck piece, not on a finish piece; its cause (a texture or a shadow) is not investigated.
9. **Report cosmetics:** the r2 report prints "REVISION r2: r2: …".

## 9. Hashes and paths

| File | SHA256 |
|---|---|
| **Candidate** `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_PierFinish1.umap` (applied r2) | `C904EF8C6B35850BD9E6498A0C8B93ABFFAB758A2E756F6E1BACAA6675D75DA2` |
| Its receipt `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_PierFinish1.json` (last: applied, plan `20F26D60…`) | `4470B368467189E68E03A5EA27C72BE9463EA2974C9D5AEDF3A2F6EF1C539712` |
| Live `Content/LevelPrototyping/CarrowGateGarrison.umap` | `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC` |
| P3Candidate1 / its receipt | `550234E37695D83CF45E58B78FA00723DE83C226490FBD931C718D8C96250FF7` / `DCDCFD3E3A8FEBD2E798A693DF3E5BEB8642CF7DB71DDFB25AC2FB3438B3F8F4` |
| Preview3 / its receipt | `8FCD23B9B51906A786AF0A117FC3B8A27B0B1AB3869071AFE6B62ABF6096C585` / `A1ED7F96D8DDF770DD9FA43460A5A81F0A890779D634139301F8B73CAACD7265` |
| CB1Preview / CB1Preview2 | `5724E979…` / `F376A70E…` (unchanged) |
| `plan2/plan.json` / `manifest.csv` / `report.txt` (r2) | `20F26D60E6D52CB1477A10945993263CA93FB17B65BFE86FEACEB4A382EB25F9` / `807AEE76…` / `CD92F91E…` |
| `plan/plan.json` (r1, used for the r1 revert) | `A8D396C837D29C0CF8843F96D5C0AB2AAFE4457DA9010E86293BBD5AF88405FA` |
| `audit-pier/audit.json` / `material-probe/material_probe.json` | `1F6BEC3835E4…` / `D7883DA30E14…` |
| `diff-r2/candidate_diff.json` / `run2/shots/pierfinish_checks.json` | `2D8343A037F5…` / `706C9BC084C8…` |
| `run2/evidence.json` (every hash, step, snapshot and shot in one file) | `AE0D81382750C6A1B495F1D01DF697A195B87582E52056A296038B34A82FC7BD` |
| `board/pf1-r2-board.png` (file / RGB pixels) | `3D3357BD0691…` / `16B5604524CC…` |
| Scripts: `ib_layout_garrison.py` v9 / `ib_garrison_pierfinish_check.py` / `ib_garrison_pierfinish_board.py` / `ib_probe_marking_material.py` | `C0DB217BD16D…` / `1C6E0CEF5DB1…` / `16A419B46BD3…` / `D39CC579E37C…` |
| Scripts: `ib_garrison_assembly_audit.py` / `ib_render_garrison_plan.py` / `ib_garrison_candidate_diff.py` | `81222FC93393…` / `5B5D4553E91D…` / `7FE36D82CDD0…` |

Protected files (`hashes/shared-before-140.json` … `shared-after-146.json`, 14 snapshots) number 116:

- 105 shared assets, including the building, door, crane, truck and ship meshes, `MI_Landmass_HelipadMarking`, `M_FlatCol` and the Bastion materials;
- the live map;
- 4 earlier preview maps and 2 receipts;
- 4 live saves.

**0 differ** in any snapshot.

Every job logged `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0` and `OWNED_PROCESSES_LEFT=0`. The GUI job's PIE session wrote `IronBreach_XP.sav` and `IronBreach_Ledger.sav` inside its isolated UserDir (`…/user-gui/Saved/SaveGames`), not into the live `Saved/SaveGames`.

- **Evidence folder:** `Saved/GarrisonRestructure/20260930-claude-pierfinish/`.
- **Contents:**
  - `audit-pier/`;
  - `plan/` (r1);
  - `plan2/` (r2: `plan.json`, `manifest.csv`, `report.txt`);
  - `material-probe/`;
  - `diff/` (r1) and `diff-r2/`;
  - `run1/` and `run2/` (step outputs, logs, shots, `run2/evidence.json`);
  - `backup/`, `hashes/shared-*.json` and `board/`.
- **Job logs:** `Saved/zz_job/logs/140…146-*.log`.
- **Scripts (new or changed in this task):**
  - `ib_layout_garrison.py` (v9);
  - `ib_garrison_assembly_audit.py` (pier set);
  - `ib_render_garrison_plan.py`;
  - `ib_garrison_pierfinish_check.py`;
  - `ib_garrison_pierfinish_board.py`;
  - `ib_probe_marking_material.py`.
