# Garrison forecourt finish preview (FF1) result — 2026-09-30

Claude, 21:45 UTC. This answers `Docs/CLAUDE_GARRISON_FORECOURT_FINISH_PREVIEW_2026-09-30.md`. Engine jobs 160–164 ran from 20:07 to 20:53 UTC; the job logs print local time (UTC−7).

**Candidate, left saved and applied for review:**
`/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1`
(`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1.umap`, SHA256 `181159BF9FB6A68598D7CFC297B71118FF3019F15B62ACD590E9E4EE3A08C1C3`, the last `applied` entry in its new receipt).

**New material instance:**
`/Game/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber`
(file SHA256 `93A7971E1D152D075A52D72AC4604D788F65D67846243491E5923FAB0896F9CE`). No test process is running. The job queue holds only the inert `153-yellow-after.hold`.

**Scope held.**

- Written in Content: only the new candidate map and the new material instance. The candidate's new receipt is in Saved.
- Byte-identical before and after every job (10 snapshots of 328 files, section 8):
  - YM1's map `AF25734A…`, material instance `B9E3E18F…` and receipt `C2A52B76…`, plus 101 files of YM1's evidence folder;
  - all 224 files of Codex's protected list, each matching Codex's recorded hash. These include the live map `FAFFD601…`, the five earlier preview maps with the three earlier receipts, the shared `MI_Landmass_HelipadMarking`, `M_FlatCol`, `M_Bastion_Concrete` and the four save games.
- Nothing was deleted. There was no Git, no locks, no commit or push, no message to anyone and no live-map promotion.
- The rear hangar is not built. P3's reservation outline keeps its position and size (its 8 markings are recoloured with the rest), and its approach stays clear: only non-colliding paint crosses it.

## 1. At a glance

| Item | Result |
|---|---|
| New candidate | Duplicated from the accepted YM1 bytes (`AF25734A…`) after a receipt preflight (YM1 receipt `C2A52B76…`, last state `applied` at those bytes). YM1 was fingerprinted alone in its own process: 3131 actors and 3158 in-game components. The copy was then verified alone against that fingerprint: 3131 of 3131 actors identical. The candidate has its own receipt; YM1's receipt was never written. |
| Material instance | New, in its own subfolder. Parent `M_FlatCol` (unchanged). The only override is **`Base Color` = (0.85, 0.60, 0.22, 1.0)** (linear), a muted amber. Metallic 0 and Roughness 1 are inherited, so the paint stays matte and non-emissive. After save and reload the engine reports that effective Base Color. YM1's instance is untouched. |
| Forecourt finish | **125 new actors**, all tagged `IB_GarrisonForecourtFinish` and filed in the outliner folder `Carrowgate Garrison/Forecourt FF1`: quay coping and fascia on the forecourt's water edges, inset edge lines, a painted cross-road along the seaward edge, gate-road and axis-road lines, door bars and three short dashed service lanes. The ring's 64 new segments are counted among the 125. Section 2 lists them. |
| Paint | All generated paint now uses the new instance: the 91 existing markings (**91 slot changes**, YM1 instance → FF1 instance) and the 105 new paint pieces. The engine readout found 91/91 and 105/105 on the new instance in both the editor world and the PIE world. The three inherited live-map users of the shared instance were not touched. |
| Pad ring | Remade from **32 × 408 cm chords, 1.5 cm proud, to 96 × 125 cm segments, 0.5–0.6 cm proud**. The radius (18.9 m) and the 40 cm width are unchanged. The 32 existing ring actors keep their position and yaw and are shortened and lowered; each original transform is in the receipt. 64 new segments fill the gaps. All paint is NoCollision. Helicopter clearance is unchanged: the helicopter was not moved, and its bounding box already reached the ring's circle before and after (0 cm in the plan's check for both rings). |
| Lifecycle (real engine, job 162) | preflight → apply+save → reload-verify → saved repeat (a no-op; bytes unchanged) → revert+save → reload-verify → re-apply+save → verify-final. **All passed**: every step's own status was complete. Each commandlet process exited 1 because of the pre-existing startup ensure, as in YM1. |
| Candidate vs YM1 | Reloaded and compared actor for actor and component for component: 248 planned changes (125 new pieces, 32 ring edits, 91 slot changes), **0 missing, 0 unexpected**. The other 3040 actors are identical. After the revert there were 0 differences from YM1. |
| Movement | **11 affected scripted PIE routes: all reached.** They are the land join, the pier and spine entrances beside the new corners, the cross-road, three door routes and a step onto the new curb. 9 of the 11 capsule sweeps are clear. Two are blocked by objects the real pawn passed (the closed gate leaf in the editor world, and a reviewed pier truck). Lane scans of the three roads are clear across the painted width. Section 7. |
| Visual | Matched before/after captures (same cameras and world lighting). They include the lit overhead in the reference's orientation (wider framing), a forecourt ground view, PIE player-camera views of the cross-road, gate road and pad, and a 16-frame moving camera across the ring's near joints. Paint hue: YM1 49–50° overhead, FF1 37.5–38.3° overhead (broad gate) and 33.5–36.5° up close, the reference 30.5–32°. The near arc reads as smooth, thin paint; the far side of the ring still breaks into dashes at eye height, as it did in YM1. Sections 5–6. |
| Preservation | 328 protected files identical in all 10 snapshots (before-160 … after-164). Content writes outside the disposable folder: 0. Owned processes left: 0. |
| Engine health | **Not a clean engine run.** All 16 engine processes logged the pre-existing GameFeatureData ensure, and the two GUI runs also logged the known `BP_Mech` compile errors. All 16 logs close normally, with no access-violation, critical or fatal line. However, the before-capture editor (job 163) returned `0xC0000005` after its log had closed. Section 9. |

## 2. What changed, exactly

Only these differ from YM1. The plan (`plan/ff1_plan.json`, `3D51EE8D…`) lists every piece, every ring edit and the 91 per-slot assignment records. The receipt holds the counts and the 32 original ring transforms (`ring_before`). The ownership manifest (`run1/reapply-save/ownership_manifest.json`, `4087F9F8…`) lists the 125 new labels, the 32 reshaped ring actors and the repainted-slot count.

| Kind | Count | Mesh / material | Collision | Top (deck = 385.0) |
|---|---|---|---|---|
| quay coping (50 cm on the deck + 10 cm lip over the water) | 9 | `/Engine/BasicShapes/Cube`, `M_Bastion_Concrete` | BlockAll | 393.0–393.8 (the +8 cm PF1 curb; 0.4 cm steps where pieces meet) |
| quay fascia (6 cm proud of the deck face, down to 45 cm below the water at −35) | 11 | Cube, `M_Bastion_Concrete` | NoCollision | 356.0 (bottom −80) |
| inset edge lines (40 cm, centred 100 cm inboard) | 9 | Cube, FF1 instance | NoCollision | 386.5 / 386.8 |
| edge stubs meeting the pier's and spine's PF1 edge lines | 3 | Cube, FF1 instance | NoCollision | 386.5 |
| axis-road lines | 2 | Cube, FF1 instance | NoCollision | 386.5 |
| gate-road lines | 2 | Cube, FF1 instance | NoCollision | 386.5 |
| cross-road landward line (3 segments) | 3 | Cube, FF1 instance | NoCollision | 386.5 |
| cross-road centre dashes (300 × 40 cm every 600 cm) | 8 | Cube, FF1 instance | NoCollision | 386.5 |
| door bars (300 × 40 cm, centred 50 cm in front of the door frame) | 3 | Cube, FF1 instance | NoCollision | 386.5 |
| service-lane dashes | 11 | Cube, FF1 instance | NoCollision | 386.5 |
| **new** pad-ring segments | 64 | Cube, FF1 instance | NoCollision | 385.5 / 385.6 |
| **total new actors** | **125** | | | |
| existing ring actors `IBGC_Pad_Ring_00…31` reshaped | 32 | unchanged mesh | unchanged (NoCollision) | 386.5 → 385.5 / 385.6 |
| slot-0 material of the 91 generated markings | 91 | YM1 instance → FF1 instance | unchanged | unchanged, except the 32 ring actors |

- **All FF1 paint bottoms sit at 383.5** (the 105 new pieces and the 32 reshaped ring actors). That is 1.5 cm below the deck, so the paint also reaches below the top of the pad's chamfer fillers (384) and never floats above a lower deck piece. Where two FF1 paint pieces overlap, their tops differ by 1–3 mm, so FF1 adds no coplanar overlap (the plan's check found 0). Alternating the ring tops also removed the 32 coplanar joint overlaps of P3's old ring. The other eight pre-existing coplanar overlaps, the corners of P3's reservation outline, are unchanged from YM1 (same material, same surface) and were not filmed.
- **Ring edit, for example `IBGC_Pad_Ring_00`:**
  - before: location (19122.0, 4525.0, 385.5), yaw 90, scale (4.08211, 0.4, 0.02);
  - after: location z 384.5, scale (1.24987, 0.4, 0.02);
  - the odd-numbered segments sit at z 384.55 with scale z 0.021.
- Each old actor k becomes segment 3k of the 96. It keeps its XY and its yaw (the tangent at 11.25° × k around the pad), because the old and new segment centres coincide there.
- Each segment is tangent to the circle at its midpoint. The ends' deviation outside the circle drops from 11 cm to 1 cm, the overlap of neighbouring segments from about 36 cm to about 1 cm, and the bend at each joint from 11.25° to 3.75°.
- `ring_before` in the receipt holds all 32 original transforms. The revert restored them exactly (section 4).
- **Assignments:** the 91 are the same labels YM1 recoloured:
  - P3's ring (32), spine dashes (15) and reservation outline (8);
  - PF1's 36 markings.
- Each assignment is recorded with its actor, component, slot, mesh, collision profile, `from` instance and original override list. The inherited `Helipad_North_H_L`, `_R` and `_Bar` still use the shared instance.

## 3. Layout: quay edges, cross-road and service lanes

In the reference framing, land is at the top (−X), the sea is at the bottom (+X) and the docks side (−Y) is on the right.

- **Source of the geometry.** A read-only probe of YM1 (job 160, `probe/site.json`, `2E67A09A…`) used the **current world bounds** of the eight forecourt decks and chamfers, not their pivots. It also traced vertically outside every edge to find water.
  - The planned outline matches the actual decks: 0 samples off-deck 5 cm inside it, and 0 on-deck 5 cm outside it.
  - All 436 compared edge samples agree with the probe on which runs face water.
- **Quay edges.** Every exposed water run got PF1's treatment (coping, fascia and an inset edge line), with these exceptions:
  - **Land connection:** the two gatehouse flanks beside the land ramp got fascia only.
  - **Pier and spine entrances:** kept open. The coping stops at the inboard face of the pier's and spine's own PF1 coping, and short stubs join the edge lines.
  - **Medical's seaward face:** the coping is narrowed to 40 cm there. It stays 4.4 cm clear of Medical's visual box, so no building is shifted.
  - **P3 rear reservation:** fascia only along its rear stretch, leaving Connor's hangar outline untouched.
  - **Clearances:** edge lines stop 1 m short of buildings and `SM_MainGate_Tripo`.
  - **Checks:** paint off deck 0; overlaps with actors 0; curbs across openings 0.
- **Cross-road.** An 8 m band runs along the forecourt's seaward strip, from the docks-side edge (y −2420) to 1 m short of Medical (y 4900).
  - It is bounded by the new seaward edge line and a new landward line (x 9242). A dashed centre line runs at x 9662.
  - The landward line is broken where the gate road and the axis road enter, so the roads flow into it.
  - This is the cross-road "where the spine enters": it runs from the pier entrance on the right, past the spine entrance, to the left-side approaches at Medical.
- **Gate road.** Two lines run from just inside the gate (x 1044) to the seaward edge. They sit on **exactly the pier's 6 m service-lane line centres** (y −241.7 and 398.3), so the pier lane now visibly continues to the gate. The painted clear width is 600 cm.
- **Axis road.** Two lines run from the reservation mouth (x 4390) to the seaward edge, on **the spine's lane-line centres** (y 3150 and 4350). The painted clear width is 1160 cm. P3's centre dashes along the axis are kept (now amber).
- **Building approaches (only what circulation needs).**
  - Barracks (door on its +Y side): a door bar and a dashed lane from the gate road.
  - Armory (door on its −Y side): a door bar and a dashed lane from the axis road along x 6895.
  - Medical (door on its −X side): a door bar and an L-shaped dashed lane from the axis road along x 7900, then +X to the door.
  - There are no parking rows and no props.
- **Measured corridors, from the plan** (painted width; nearest obstacle to the band):
  - axis road: 1160 cm; Medical 670 cm;
  - gate road: 600 cm; `BP_MainGateDoor` 196 cm at the gate itself;
  - cross-road: 800 cm; Medical 100 cm at its end.
- **Closest paint to a building:** the Armory door bar, 29 cm from the Armory. It is centred 50 cm in front of the door frame, so its near edge is 30 cm from it.
- **Measured corridors, from the engine lane scans** (section 7): all three roads are clear across and beyond their painted width.
- **Verified routes as constraints.**
  - The earlier forecourt → pier route (y 78–100) lies inside the gate road.
  - PlayerStart / reservation mouth → spine (y 3750–4024) lies inside the axis road.
  - The earlier city road → gate route runs at y −251, 9 cm outside the gate road's −Y line centre, over NoCollision paint. It was re-walked (section 7).
- **Local constraints, reported rather than forced.** On the landward edge, two fragments were not laid: a 465 cm coping fragment and a 395 cm edge-line fragment. Each is isolated between the reservation keep-out and the gate keep-out. No protected assembly was moved to fit anything.

## 4. Lifecycle and reversibility (real engine)

Each step ran in its own commandlet process, with the map loaded first and alone. Tools: `Scripts/ib_garrison_forecourt_finish.py` (`66BC7889…`) and `Scripts/ib_garrison_forecourt_plan.py` (`D2EF5296…`).

**Reuse.** The new scripts are built from the existing ones where that worked; the originals are unchanged:
- **Finish tool:** derived from YM1's paint-correction tool, with the same receipt states, stale-target refusal and one-map-per-process fingerprint comparison. It adds spawning and removing the new pieces and reshaping the ring actors.
- **Check script:** a copy of YM1's check with the forecourt cameras, moving frames and routes added. The original is unchanged.
- **Planner:** new. PF1's finish came out of the whole-garrison layout planner, whose plan covers every move and piece, so reusing it would have meant re-planning the layout. The new planner is smaller and reuses PF1's quay dimensions and checks.
- **Site probe:** new and read-only. It was needed to read the forecourt decks' actual world bounds.

| Job / step | Result | Candidate after |
|---|---|---|
| 160 site probe (read-only, YM1) | 3131 actors; 8 forecourt decks, 10 edges, 2788 rear-grid traces; map unchanged | — |
| 161 base-fingerprint | YM1 alone: 3131 actors, 3158 in-game components (18 editor-only skipped) | — |
| 161 copy → copy-verify | `duplicate_asset` of YM1 → the copy loaded alone: 3131/3131 identical; receipt `created` | `4676591F70F1` |
| 161 material, material again | instance created (`93A7971E…`), then `already-created-verified` | `4676591F70F1` |
| 162 plan-check | preflight clean: no FF1 actors present, ring at its recorded transforms, 91 on YM1's instance, labels free, assets present | `4676591F70F1` |
| 162 apply + save → verify-applied | applied-verified → verified: 248 planned changes, 0 missing, 0 unexpected | `3F9E7DF81C14` |
| 162 saved repeat | already-applied-verified; not saved; **bytes unchanged** | `3F9E7DF81C14` |
| 162 revert + save → verify-reverted | reverted-verified (125 removed, 32 ring transforms and 91 slots restored) → verified: **0 differences from YM1** (3131/3131) | `8C6576E3E353` |
| 162 re-apply + save → verify-final | applied-verified → verified: 248 planned, 0 missing, 0 unexpected | **`181159BF9FB6`** |

- The receipt `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ForecourtFinish1.json` (`F703F4A1…`) records created → applied → reverted → applied. The last entry matches the file on disk.
- The tool refuses to act when the target is not at the receipt's last bytes, or when YM1's map or instance changed. Those refusals, and forged-receipt, label-collision, failed-spawn and failed-save cases, were exercised only in the offline harness (29/29 cases); none arose on the engine.
- The reverted file's bytes differ from the created copy's, because a save re-serialises the package. The fingerprint comparison is the check, as in YM1.
- The effective Base Color was read back after every reload. The Python setter returned `False`, as it did in YM1; the reloaded value is what counts.

## 5. Captures and colour

Jobs 163 (before, YM1) and 164 (after, FF1) used the same check script (`Scripts/ib_garrison_forecourt_check.py`, `D59A85EE…`), the same cameras, world lighting and timing, and one GUI editor each in an isolated UserDir. Nothing was saved and there were no lighting or post-process changes. Board: `board/ff1-board.png`, with the approved reference (SHA `33491BF3…`, verified) beside FF1's overhead at the top.

- **Views.**
  - `overhead-reference`: the reference's orientation, with wider framing;
  - `forecourt-ground`: above the pier/spine inlet, looking landward across the cross-road to the gate and axis roads;
  - `forecourt-quay`: the new docks-side coping and fascia from the water;
  - `medical-front`: the narrowed coping;
  - `pad-ring`;
  - PIE player-camera views: `pie-crossroad` (standing on the cross-road), `pie-crossroad-to-pier`, `pie-gate-road` and `pie-pad-ring`.
- **Exposure comparability.** Over the pixels that did not change, the pairs differ by at most 4.9 levels (mean absolute per channel) and 2.3 levels of mean luma.
- **Colour against the reference** (`board/ff1-board-stats.json`). Method:
  - The reference is sampled inside the same five deck boxes YM1 used.
  - The 91 existing markings are located in the overhead with YM1's own PF1 → YM1 capture pair of the same camera (read-only). Those same pixels are then read in this task's YM1 and FF1 captures. Only 0.31% of them differ between YM1's evidence capture and this task's YM1 capture.
  - "New pieces" are the pixels that turned amber outside those markings.

| Overhead, YM1 gate (hue 25–70°) | broad (sat ≥ 0.25) | strict (sat and value ≥ 0.45) |
|---|---|---|
| reference deck paint | (160,129,97), hue 30.5°, sat 0.39 — 34,631 px | (185,141,90), 32.2°, 0.51 — 7,337 px |
| YM1, the 91 markings | (170,159,108), 49.4°, 0.36 — 5,613 px | (191,176,99), 50.2°, 0.48 — 511 px |
| **FF1, the same 91 pixels** | (174,153,116), **38.3°**, 0.33 — 4,344 px | (146,118,76), 36.0°, 0.48 — only 47 px |
| **FF1, new pieces** | (147,129,99), **37.5°**, 0.33 — 3,083 px | (139,114,69), 38.6°, 0.50 — only 121 px |

The broad gate is the representative row for FF1: at about 21 cm per pixel the 40 cm lines are two pixels wide and mix with the grey deck, so few FF1 pixels pass the strict gate. The wider amber gate (hue 15–70°) gives the same picture: reference 31.0°, FF1 38.9° and 37.0°.

- **Up close.** FF1 paint in the changed pixels of the close views measures hue 33.5–36.5°. Examples: `pie-crossroad` (179,137,76), `forecourt-ground` (156,125,77) and `pie-pad-ring` (129,105,71). YM1's result measured 44–53° in its views.
  - `forecourt-quay` (32.6°) is left out: most of its changed pixels are the new concrete fascia, not paint.
  - `overhead-topdown` (41.7°, 1,637 px) is left out: seen straight down, the thin lines are mostly mixed pixels.
- **Assessment.** The paint moved from golden yellow to muted amber/gold, within about 4–8° of the reference's hue overhead. The close views are nearer still, though the reference itself is only an overhead. At the overhead's scale the 40 cm lines are thinner and paler than the reference's broad painted bands: the hierarchy is more restrained than the reference's (section 10). No retint was made: the brief's criterion is a visually sound comparison, not pixel matching. The tool can retint the instance in place with history, but that is covered only by the offline harness.

## 6. Pad ring at eye height (moving camera)

`board/ff1-pad-joints-moving-camera.png` sets 8 successive frames of each run side by side. `board/ff1-pad-near-arc-all16-after.png` shows the band of all 16 FF1 frames that holds the near arc. `board/ff1-pad-joints-after.gif` and `-before.gif` hold all 16 frames of each run. `board/ff1-pad-joints-after-left-crops.png` and `-right-crops.png` are full-resolution crops of every second FF1 frame.

- **Camera.** An editor viewport camera in game view, 1.65 m above the deck, outside the ring and 5.6–7.3 m from its near arc. It moves 30 cm per frame over 4.5 m, with the same settings throughout.
- **FF1, near arc (about 5.6–20 m from the camera).** In all 16 frames and in the full-resolution crops, the ring reads as a continuous, smooth arc lying flat on the deck:
  - no visible facets or kinks;
  - no gaps or bright overlap at joints;
  - no breakup or flicker between successive frames.
- **YM1 (same frames).** On the near arc the 32-chord polygon's kinks are plainly visible.
- **Far side of the ring (beyond about 25 m), in both runs.** At eye height the 40 cm line there is thinner than a pixel, and it breaks into evenly spaced dashes. The dash pattern shifts from frame to frame, so it would read as crawl or shimmer in motion.
  - `board/ff1-pad-far-arc-frames00-03-after-then-before.png` shows frames 0–3 of each run.
  - The independent check projected the ring into frame 0 (assuming the editor's 90° field of view) and measured how much of its path shows paint. FF1: 100% at 5–20 m, 98% at 20–28 m, 66% at 28–36 m and 29% at 36–44 m (part of the last band is behind the helicopter). YM1: 100%, 100%, 83% and 46%.
  - So this is pre-existing aliasing of a thin line at a grazing angle, not a joint defect. FF1's lower profile makes it slightly worse, probably because YM1's 1.5 cm strip showed a little side face.
  - Fixing it would take a different technique (decal or material markings) or wider far lines, which is a decision beyond this pass (section 10).
- **PIE view.** The `pie-pad-ring` player-camera view shows the same smooth near arc.
- **Limits.** This is one path and 16 still editor frames at 1920 × 1080, not a video or a PIE flight. Gameplay anti-aliasing in motion was not assessed.

## 7. Movement and collision

**Sweeps** are engine capsule queries (the pawn's own capsule, `Pawn` profile) in the editor world. They are not movement. **Walks** are the real `BP_IBCharacter_Infantry` pawn in PIE (radius 34, half-height 88), driven through waypoints by scripted movement input. They are not a person playing. Both ran in job 164 on FF1.

| Route (length) | Sweep | Real pawn |
|---|---|---|
| land join: city road → gate → gate road (130.6 m) | blocked by `BP_MainGateDoor`: the closed gate leaf in the editor world, the same object earlier previews recorded on this path | **reached** 4/4 in 21.6 s, through the gate (56 cm drift while turning at the corners). The capsule rose from 108.9 to 475.3 up the land ramp. |
| pier entrance on the lane (19 m) | clear, floor 385 | **reached**, 3.2 s |
| pier entrance beside its −Y curb (17 m) | clear | **reached**, 2.9 s |
| pier entrance beside its +Y curb (17 m) | blocked by `SM_Truck_Cargo4`, a reviewed pier truck at its plan position | **reached**, 2.9 s, sliding 20 cm around the truck |
| spine entrance beside its −Y curb (17 m) | clear | **reached**, 2.9 s |
| spine entrance on the axis (19 m) | clear | **reached**, 3.2 s |
| cross-road, docks-side end → Medical's corner (68.7 m) | clear | **reached**, 11.5 s |
| Barracks door route (9 m) | clear | **reached**, 1.5 s |
| Armory door route (40.3 m) | clear | **reached**, 6.8 s |
| Medical door route, two legs (33 m) | clear | **reached**, 5.5 s (53 cm drift at its corner) |
| onto the new docks-side coping, along it and back (6.4 m) | clear; floor 385 → 393.5 (the curb's +8.5 cm step) | **reached** 3/3 in 1.0 s (51 cm drift, as each 70 cm waypoint radius cuts the corners). The capsule rose 8.4 cm onto the coping and back down. |

- **Deck-level routes.** On every route except the land ramp and the curb step, the capsule centre stayed at 475.1–475.2 cm. That is the deck (385) plus the half-height (88) plus the movement component's usual ~2 cm floor gap, the same gap as on the curb (393.5 + 88 + 2 = 483.5). So the pawn never climbed onto the new pieces. Drift on the straight routes was 0–20 cm.
- **Lane scans** (the body capsule swept along each road at 25 cm steps across it):
  - gate road: 21/21 pawn-centre lines inside the painted band clear; the whole scan of ±2 m around the paint is clear (≥ 10.7 m);
  - axis road: 44/44 clear (≥ 16.2 m);
  - cross-road: 29/29 clear. The clear band runs from the scan's landward limit to the deck's seaward edge (≥ 11.4 m); the next line lies over water.
- **Assemblies.** The crane, the four trucks, Mess_Hall and Command with their door frames all stand at their reviewed plan positions. Every other gameplay actor is identical in the fingerprint comparison (section 4).
- **Not rerun.** The full prior 16-route/build matrix was not repeated. The paint is NoCollision, and the only new collision is the 8 cm PF1-style curb on the water edges.

## 8. Preservation and files

- **Protected files.** At every job boundary the runner rehashed 328 protected files natively:
  - Codex's 224;
  - YM1's map, instance and receipt;
  - 101 YM1 evidence files (engine UserDirs excluded).
- `run1/evidence.json` (`A5324B5B…`) checks all 10 snapshots:
  - every snapshot is identical to the first;
  - **224/224** match Codex's `protected-current.json`;
  - **3/3** YM1 hashes match the brief;
  - every job reports `SHARED_ASSET_OR_SAVE_CHANGES=0`, `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0` and `OWNED_PROCESSES_LEFT=0`.

| File | SHA256 |
|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1.umap` (new, applied) | `181159BF9FB6A68598D7CFC297B71118FF3019F15B62ACD590E9E4EE3A08C1C3` |
| `Content/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber.uasset` (new) | `93A7971E1D152D075A52D72AC4604D788F65D67846243491E5923FAB0896F9CE` |
| `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ForecourtFinish1.json` (new) | `F703F4A1B535D71FFF4DF13A48BCD94CF7036267440B115AC9E05B7CC326C12F` |
| `…/run1/reapply-save/ownership_manifest.json` (final; the first apply's copy is kept too) | `4087F9F8870C473A4A522A1953FCE05D7BC8287B12051FCE292EA6B36EED836F` |
| `Scripts/ib_garrison_forecourt_plan.py` (new) | `D2EF529682B069D0AA185BC42F027C96B33154543E04894A734944CE027C5890` |
| `Scripts/ib_garrison_forecourt_finish.py` (new) | `66BC7889257B0143B7FA9D374A902E0955D47A39668F77AECABB7D3A93F95BFB` |
| `Scripts/ib_garrison_forecourt_check.py` (new; derived from the yellow check. `ib_garrison_yellow_check.py` `44C60C75…` and `ib_garrison_paint_correction.py` `FCD658A2…` are unchanged) | `D59A85EE39D5FA254AF60F11465C36FD21F4446F6BBB440B75BB7801A662968B` |
| `Saved/zz_job/forecourt_lib.ps1` (new) | `E9D4FEE6A224FD9E36EA404963A86084A44FA7843D20CD717331DC51DE21F1EB` |
| job files in `Saved/zz_job/running/` (each job wrapper's `.exit` is 0; the commandlets inside exited 1, see section 9): 160 `07521E20…`, 161 `55E510D5…`, 162 `4C54ACAE…`, 163 `8F13A35B…`, 164 `48B05A33…`; logs `Saved/zz_job/logs/16[0-4]-forecourt-*.log` | as listed |
| `…/probe/ff1_site_probe.py` (new, read-only probe) | `4FAEE754B1FEF3B81BCAD04712EF08924B363E334E986980EA260920A58584C8` |
| `…/plan/ff1_plan.json`; `…/probe/site.json`; `…/run1/basefp/base_fingerprint.json` | `3D51EE8D…`; `2E67A09A…`; `0C933564…` |
| `…/board/ff1-board.png`; `…/board/ff1-pad-joints-moving-camera.png`; `…/board/ff1-pad-near-arc-all16-after.png`; `…/board/ff1-pad-far-arc-frames00-03-after-then-before.png`; `…/board/ff1-board-stats.json` | `4BA675E8…`; `8B317BD7…`; `1D4B0951…`; `BDC83D9C…`; `E4A5B127…` |
| read-only checks: `run1/ff1_log_check.py` → `run1/log_check.json`; `run1/ff1_evidence.py` → `run1/evidence.json`; `board/ff1_board.py` | `FF8B80A1…` → `5A2D76BA…`; `603A616B…` → `A5324B5B…`; `94C0981A…` |
| this document and `Claude outputs/CLAUDE_STATUS.md` | reported in the status file and the handoff |

## 9. Engine health and limitations

1. **Engine health: not a clean run.** `run1/log_check.json` covers all 16 engine processes (the probe, 13 commandlet steps and 2 GUI runs) and records the per-log counts quoted here.
   - **Exit codes:** each of the 14 commandlet processes exited 1 because of the startup ensure below, as in YM1. The tools' own step statuses were all complete.
   - **Startup ensure:** every process logged the pre-existing GameFeatureData ensure (`AssetBaseClassLoaded`, AssetManagerTypes.cpp line 82). In each commandlet log it accounts for all 45 error lines: 23 at startup and 22 repeated in the closing "Warning/Error Summary". In each GUI log it is 26 of the 34 error lines.
   - **Crash-reporter folders:** each process also wrote one unattended crash-reporter folder for that ensure (16 folders, all `CrashType Ensure`, none a crash).
   - **GUI-only errors:** both GUI logs also show the known `BP_Mech` "Update Mech Proximity" compile errors (7 lines) and one `CurrentVisualData is NULL` line. During PIE, the infantry pawn's missing skeletal mesh also produces many `GetSocketInfoByName(WeaponSocket)` warnings (2883 in job 164), in proportion to walk time, as in PF1/YM1.
   - **Nothing else:** no log has an error line of any other kind, and none has a Python error line.
   - **Shutdown:** all 16 logs end with "Log file closed", and none contains an access-violation, critical or fatal line.
   - **Job 163's editor** returned `0xC0000005` after its log had closed, as PF1's r2 check once did. Every result was already written, nothing was saved, and YM1 stayed at its bytes. Job 164's editor exited 0.
2. **Sweeps cannot open doors.** The land-join sweep stops at the closed gate leaf in the editor world. The PIE walk is the evidence for that route.
3. **A sweep line was badly chosen.** The "+Y curb" check runs 1.75 m inside the pier's +Y edge, where the reviewed trucks are parked. The pawn slid past; the 6 m lane itself is clear.
4. **Colour is a measured approximation** of an illustration under different lighting (section 5). A retint of this candidate's instance is possible, but is covered only by the offline harness.
5. **The moving-camera check is a sample** (section 6). It shows the near arc clean. The far side of the ring aliases into crawling dashes at eye height, as in YM1.
6. **The forecourt's straight lines use PF1's accepted marking height** (1.5 cm proud, 1.8 cm on three edge lines raised where they overlap). Only the ring was thinned, as the brief asked. The same 0.5 cm treatment could be applied to the straight lines if wanted.
7. **Carried unchanged:**
   - door interiors;
   - helicopter pose and ship draft;
   - deck textures and lighting;
   - the unrelated items in the older playtest punchlist.

## 10. Remaining gaps against the reference

- **Connor's rear hangar.** The reference's large hangar is still only P3's reserved outline and approach. The building is Connor's to make.
- **Existing asset appearance.** The reference's detailed, weathered concrete, varied deck tones, dense vehicles and dressing, and cliffs/surf differ from the project's current uniform deck material, buildings and props. Those are asset or lighting work, outside this pass.
- **Road and paint weight.** FF1 lays one cross-road, two through-roads and three door lanes as 40 cm lines. The reference shows heavier road bands and more service markings around every building. More lanes would need design decisions, not just a finish.
- **Paint hue.** It is about 4–8° yellower than the reference overhead. One retint is available if Codex wants it closer.
- **Far-distance paint shimmer.** 40 cm geometry lines, the pad ring included, break into crawling dashes beyond about 25 m at eye height. This was already true in YM1. It is a rendering-technique question (decals or material markings, or wider far lines) for a later decision.
- **Remaining functional verification.**
  - Only the 11 affected scripted routes, sweeps and scans ran. There was no human playtest, no full route/build matrix and no packaged build.
  - Spawn, deployment, return and interactions were not re-exercised, beyond the preserved actors being identical in the fingerprint comparison.
  - The GameFeatureData, `BP_Mech` and infantry-mesh issues and the GUI teardown crash remain. There is no live integration.

## 11. Paths

- **Evidence:** `Saved/GarrisonRestructure/20260930-claude-forecourtfinish/`
  - `probe/`: site probe;
  - `plan/`: plan, report, render;
  - `run1/`: step reports and logs, `basefp/`, `copy/`, `material*/`, ownership manifests, `evidence.json`, `log_check.json`;
  - `before/` (YM1) and `after/` (FF1): shots, `frames/` and `forecourt_checks.json`;
  - `board/`: board, moving-camera sheet, GIFs, joint crops, far-arc frames, colour statistics;
  - `backup/`: the created and applied copies;
  - `hashes/`: 10 protected snapshots;
  - `user/`, `user-gui/`: isolated engine UserDirs.
- **Job logs:** `Saved/zz_job/logs/160…164-forecourt-*.log`.
- **Candidate:** `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1`.
- **Material instance:** `/Game/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber`.
- **Base (unchanged):** `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1` (`AF25734A…`) with `MI_YM1_DeckPaintYellow` (`B9E3E18F…`).

Stopped for Codex review.
