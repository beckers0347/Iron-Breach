# Garrison BS3 shore recovery proof: result (2026-10-01)

Brief: `Docs/CLAUDE_GARRISON_SHORE_RECOVERY_PROOF_2026-10-01.md` (`F17A59FA...`). Evidence: `Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/`. Candidate: `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3` (BS3, `FDF8219D...`, applied). Receipt `...BoulderShore3.json` (`656013F7...`).

**Scope held.** BS3 is a new disposable copy of BS2 (`2D642903...`, unchanged). Of the three actors the brief allows, two changed and one was verified unchanged:

- `IBGC_BS1_Rock_006` (left stone): moved horizontally 68.0 cm, and given a component-local Unwalkable walkable-slope override.
- `IBGC_BS1_Rock_018` (right crevice stone): moved horizontally 37.2 cm, turned +6 deg in yaw, and given the same component-local override.
- `IBGC_RS1_Rock_025` (the outcrop): unchanged, verified at BS2's exact state.

Nothing else changed:

- z, pitch, roll and scale are as before. So are the meshes (BS2's four collision variants, reused read-only), materials, BlockAll and step-up.
- No actor was added, hidden or deleted. There is no filler, and no water or floor change.
- No shared code, shared body setup or other rock changed.
- The live map, BS2, its receipt, its assets and the 2,748 protected files are unchanged.
- Nothing was promoted. No Git operation ran during the proof jobs.

**Outcome.**

- **Left, isolated stone: fixed.** The stone's top is no longer a safe point. 35 of the 36 placements on and around it ended on connected land through `Drown()`. That covers island 66, job 226's landing, the 24-point stone-top grid, the 5 scan spots and four of the five landing points around left wedge 19. The 36th (point 3) is on `RS1_Rock_013`, not the stone; see below. All 13 uninterrupted routes from clear land ended on land and walked back to their start. On BS2, the same placements and the same full-speed jump hold the pawn on the stone (job 236 control).
- **Right, waterline crevice: fixed.** The stone's arm now lies flush against the outcrop's east face, so the crevice is visibly closed. All 33 placements at the old crevice, on the stone and at the nearby scan spots returned the pawn onto land. So did all 7 routes. On BS2, the crevice placement still holds (job 236 positive control).
- **Two holds remain in the two areas.** Neither is on an actor BS3 changed:
  - **Right wedge 01** is beside the unchanged outcrop. Fixing it needs a 90 cm move of the 7.3 m outcrop, or a 6-10 deg turn plus 30-60 cm. That is not a reasonable local adjustment (section 2.3).
  - **A standing pocket on `RS1_Rock_013`'s top**, 30 cm north of left wedge 19's old point. It holds identically on BS2, and `RS1_Rock_013` is not in the editable set.
- This is a two-area proof only. It is not acceptance of BS3 for gameplay, and the other known holds remain queued.

## 1. At a glance

| | BS2 as saved | BS3 (applied) |
|---|---|---|
| Island 66 (stone top, BS2 placement) | held (jobs 230, 236) | `Drown()` onto land |
| Left wedge 19: the five landing points around it | 5 of 5 held (job 236) | 4 returned onto land; point 3 held on `RS1_Rock_013` (identical on BS2) |
| Full-speed jump toward job 226's landing | lands on the stone; `Drown()` returns to the stone; held (job 236) | lands on `RS1_Rock_013`, returns there, then walks to land |
| Left stone: 24-point top grid and 5 scan spots | (the top was the hold) | 29 of 29 `Drown()` onto land |
| Crevice (BS2 placement) | held (jobs 230, 231, 236) | the 5 surface points there all `Drown()` onto land |
| Right stone: 23-point top grid and 5 scan spots (including the translation-only V) | - | 28 of 28 `Drown()` onto land |
| Uninterrupted routes from clear land | - | 20 of 20 ended on land and walked back to their start. 17 through a `Drown()` return to their take-off point; 1 through a return onto `RS1_Rock_013`, then a walk to land; 2 walk-ins walked back out |
| Walking ticks on a changed stone / LastSafeLocation set on one | - | 0 / 0 |
| Right wedge 01 (unchanged outcrop) | held | held (unchanged; stop reason) |
| Stone shots (OnServerHit + replica trace) | - | 2 of 2 areas hit the stone, twice each |
| Clear-line water shots | - | 4 of 4 hit nothing |
| Lifecycle (apply, reload, no-op, restore, re-apply, verify) | - | PASS: restore equals BS2's digest; 11 + 10 fault cases refused (shared-tag decoys never selected) |
| Preservation | - | PRESERVED: Codex 2,447 + 12, all 8 stamps (2,748) identical |

## 2. The changes and why

Static models: BS2's collision of the 61 rocks and the RS1 land pieces, as in BS2 (`analysis/bs2_world.py`, `bs2_walk.py`, byte-identical copies). Four checks ran on them:

- **slots:** a capsule fits snugly between opposed walls (`bs3_snug.py`).
- **pits:** resting basins above the drown line.
- **hangs:** steep opposed contacts without a floor.
- **islands:** standing areas not walk-connected to land.

These models chose the candidates; the PIE proof decides.

### 2.1 Left: `IBGC_BS1_Rock_006` (translation 68.0 cm + Unwalkable; no yaw)

In BS2 the stone was an offshore stone east of `RS1_Rock_013`'s tip. Two problems:

- **An isolated standing area on its top:** island 66, 1.23 m2 in the static floor model.
- **A narrow neck at its west end against `RS1_Rock_013`:** left wedge 19. The neck was 22.8 cm wide at z -34 and 83.4 cm at z +40.

`analysis/bs3_design.json` scanned translations of 30-95 cm. The smallest move that opens the neck to at least 90 cm at the sea surface is (+55, -40) cm (68.0 cm). It gives:

- a neck of 90.7 cm at z -34 and 116.5 cm at z 0;
- slot cells touching the stone fall from 597 to 18. 8 of them are notches between the stone's own faces, and 10 lie between it and `RS1_Rock_013` at the detector's 90 cm upper bound;
- no pit and no island on the stone;
- visible share 0.996 of BS2's.

No horizontal move within a reasonable silhouette joins the stone's top to land, so the top is still an island. The component-local Unwalkable override removes it as a safe point: the movement cannot use it as a floor or record it as LastSafeLocation. The override alone would not have opened the neck.

### 2.2 Right: `IBGC_BS1_Rock_018` (translation 37.2 cm + yaw +6 deg + Unwalkable)

The crevice was the narrow end of an acute V. The stone's north-east arm met `RS1_Rock_025`'s east face at the sea surface. In the static model:

- 323 slot cells touched the stone;
- 3 pits, with the capsule resting at centre z 33.6, above the drown line;
- 8 islands on the stone.

**Translation first** (`bs3_design.json`). The smallest move that takes the arm out of the old crevice is (-60, -30) cm (67.1 cm). It removed the pits and islands, but the V stayed at the arm's tip: 29 + 9 snug cells, 66-86 cm wide, at z -34..0. Other translations either kept more of the V, or started a matching V at the stone's south-west end. Opening the stone away from the outcrop needs about 1.5 m.

**A small yaw was therefore needed** (`analysis/bs3_design_yaw.json`, `design_right_yaw.png`). The study turned the stone about its visible centre by -10..+10 deg with visible shifts of -90..-20 / -50..+20 cm (384 combinations). Only two combinations leave no slot cell touching the stone at all (3 cm grid). The smaller one is +6 deg with the visible centre shifted (-60, -30). That means:

- the relative location moves (-33.1, -17.0) cm;
- the yaw goes from 34.08 to 40.08 deg;
- the arm lies flush along the outcrop's east face, so the crevice is closed rather than narrowed.

What remains in the static model:

- one slot cell and one low hang at the stone's south-west end (67.2 cm, z -15);
- a hang between two of the stone's own faces on its top, which BS2 also had;
- no pit, no island;
- visible share 1.11 of BS2's: slightly more of the stone shows beside the outcrop.

The fine scan (+4..+8 deg, six shifts) found nothing cleaner. The same component-local Unwalkable override removes the stone's small standing areas (0.14 m2 and less).

### 2.3 `IBGC_RS1_Rock_025` and right wedge 01: unchanged (stop reason)

Right wedge 01 is the acute (39 deg) V where the outcrop's west face crosses the sea edge of the coast slab `IBGC_RS1_Coast_R10`. A translation only slides that V along the edge. The static slot scan (`bs3_design.json`, `r01`) still finds it for moves of up to 80 cm toward land. It loses it at 90 cm, or with a -6 to -10 deg yaw plus 30-60 cm.

Either option moves or turns the whole outcrop:

- Its visible part is 7.3 m x 5.5 m (24 m2) and rises to z 213 (2.5 m above the sea surface).
- A 6-10 deg turn alone moves its ends by 0.4-0.6 m.
- Either option re-forms the outcrop's north-side slots against `RS1_Rock_024` and the slab. The slot cells change from 709 to 545, at new places.

That is not a small local adjustment within the reference silhouette, and checking the re-formed north side would widen the task. So the outcrop is left at BS2's exact state, and right wedge 01 stays a regression control. It holds on BS3 exactly as on BS2.

The plan's text calls the outcrop "6.5 m". The measured visible extent is 7.3 m.

### 2.4 Exact relative transforms (root `StaticMeshComponent0`; plan `plan/bs3_plan.json`, `6523599C...`)

| Actor (object name) | BS2 [x, y, z, roll, pitch, yaw, sx, sy, sz] | BS3 | Walkable override |
|---|---|---|---|
| `IBGC_BS1_Rock_006` (`StaticMeshActor_1010`) | 6250.7, 11675.3, -502.6, 0, 0, -1.46, 1.010713, 1.010713, 1.236782 | **6305.7, 11635.3**, -502.6, 0, 0, -1.46, (same scale) | default -> **Unwalkable** (instance flag True) |
| `IBGC_BS1_Rock_018` (`StaticMeshActor_1023`) | 3700.6, -8690.0, -594.8, 0, 0, 34.08, 0.925396, 0.925396, 1.480634 | **3667.5, -8707.0**, -594.8, 0, 0, **40.08**, (same scale) | default -> **Unwalkable** (instance flag True) |
| `IBGC_RS1_Rock_025` (`StaticMeshActor_462`) | 3465.8, -8101.6, -630.2, 0, 0, -115.51, 1.385602, 1.385602, 2.216962 | unchanged | default |

Identities are BS2's recorded ones (BS2 receipt `F162F20B...` and ownership manifest `0EDBBDD2...`): object name, label, class, tags and component. No tag selects anything.

The yaw reads back as 40.080002, the stored single-precision value. The tool's checks allow 0.001 deg.

## 3. Copy and focused lifecycle (jobs 233-234; nine commandlet processes, -NullRHI, isolated UserDir)

- **Copy (job 233).**
  - BS2 was fingerprinted first in its process: 3,569 actors and 3,596 components, with all three editable actors at their recorded object names. Digest `A0F8F41F...`.
  - It was duplicated to BS3 before any map was loaded.
  - A fresh process found 3,569 of 3,569 actors identical and 0 JSON text differences. Receipt: created.
- **Lifecycle (job 234).** Each process started with its own fresh first read.
  - **apply.** Verify on the created state (3,569 identical), then apply:
    - Writes: Rock_006 location + override; Rock_018 location + rotation + override.
    - Transition check: 0 unexpected.
    - Read settling: one value, as in BS1 and BS2. `IB_Harbor_Surface`'s profile reads Custom on the first read and BlockAll after.
    - Only the BS3 map was saved.
  - **applied.** A fresh reload verified:
    - 3,567 actors identical, plus the 2 planned ones, 0 unexpected;
    - all 3 editable actors at their exact recorded state;
    - override read back after the load as `[WALKABLE_SLOPE_UNWALKABLE, 0.0, True]` on both stones.

    Then the no-op repeat: nothing saved, file and receipt unchanged. Then 11 fault cases, nothing saved. 10 were refused: back-at-BS2, override-cleared, moved, unchanged-moved, yaw-back, untag, BS3-tagged decoy, label decoy, asset manifest, missing. The shared-tag-only decoy was never selected.
  - **restore.** Back to BS2's exact state: location, rotation, override cleared to `[DEFAULT, 0.0, False]`. The before-save comparison with BS2 showed 0 unexpected.
  - **restored.** A fresh verify found 3,569 of 3,569 identical. The raw digest `A0F8F41F...` equals BS2's, and the signed-zero-normalised digests are equal (`6F824237...`). Then 10 fault cases. 9 were refused: moved-only, override-only, moved, unchanged-moved, yaw-only, untag, BS3-tagged decoy, label decoy, asset. The shared-tag-only decoy was never selected.
  - **reapply** and **final.** Applied again, then a fresh verify: digest `983AC0CC...`, identical to the first applied state.
- **Receipt:** created `808C27A2` -> applied `0D44866A` -> restored `E83658D2` -> applied `FDF8219D`. The byte hashes differ between saves of the same state, as with BS2. Ownership manifest: `run1/apply/ownership_manifest.json` (`3EA7FF78...`).

## 4. Two-area PIE proof (job 235) and controls (job 236)

### 4.1 Session

- **Editor session.** One GUI editor session per job (`-UseFixedTimeStep -FPS=30`, isolated UserDir, autosave off). Neither session saves, and the editor quit itself.
  - Job 235: editor exit 0 after 758 s; 19,507 ticks.
  - Job 236: editor exit 0 after 378 s.
- **Pawn.** `BP_IBCharacter_Infantry_C` with the real movement:
  - capsule r 34, half-height 88;
  - walk 600 cm/s, jump 420 cm/s;
  - walkable angle 44.77 deg;
  - `drown_water_z` -35; LastSafeLocation readable.

  OnServerHit was bound at the start of each PIE session: once in job 235, and twice in job 236.
- **The PIE world had BS3 as planned:**
  - Rock_006 at (6305.7, 11635.3), yaw -1.46;
  - Rock_018 at (3667.5, -8707.0), yaw 40.08;
  - both with `[UNWALKABLE, 0.0, True]`;
  - Rock_025 at BS2's state.
- **Route method.** Every route started from clear land, verified first by the movement's own floor (walking on an RS1 land or coast piece) and by LastSafeLocation. The run was uninterrupted: no re-placement, only movement input and the jump. After 1.2 s in the air, or 3.5 s of walking, the input turned back toward the start. Any `Drown()` return was recorded with its target and the floor after it. Then came a walk back to the start (connected land).
- **Placement method.** Placements set the movement to falling before the teleport. A 2.5 s watch followed, then up to seven escapes from where the pawn was: walk, run-and-jump and jump at once toward land, each straight and at +-25 deg.

### 4.2 Left (`analysis/proof_eval.json`)

- **Stand stop.** The pawn was grounded on `IBGC_RS1_Coast_L06`, with the camera at (5968.3, 11783.4, 148.2).
  - Aimed shot: OnServerHit `IBGC_BS1_Rock_006`; replica trace on the stone at 439.9 cm.
  - The planned gap shot met `RS1_Rock_013` in front of its water point; see 4.5 for the clear-line shots.
  - Frame: `check/proof/frames/left_stand.png`.
- **13 uninterrupted routes,** including the moving-camera sequence.
  - Run-and-jumps at full speed, and at 65/70/75/90 % speed (chosen so the arc comes down on the stone).
  - Targets: the stone's centre, west end and east part, island 66's old point, left wedge 19's old point (the opened neck) and job 226's landing; plus two walk-ins.
  - 10 came back through `Drown()` to their take-off point on `Coast_L06` (9 routes and the sequence).
  - The two walk-ins went into shallow water (capsule centre down to -28.4) and walked back out.
  - The full-speed jump toward job 226's landing came down on `RS1_Rock_013`'s top. It walked there; LastSafeLocation was set on `RS1_Rock_013` six times. It went into the water, `Drown()` returned it onto `RS1_Rock_013` (6148.9, 11890.3), and the first escape (walk) reached `IBGC_RS1_Land_34`.
  - All 13 walked back to their start.
  - Walking ticks on the stone: 0. LastSafeLocation set on the stone: 0.
- **Moving camera:** 23 in-game frames along the full-speed jump toward the stone's centre: run, jump, water, `Drown()`, back on land facing the stone. See `analysis/sequence_left_contact.jpg` and 4.6.
- **Old placements** (regression controls). Island 66 and job 226's landing both went through `Drown()` onto land.
  - Left wedge 19's old point now lies under `RS1_Rock_013`'s collision top, so the pawn was placed on the surface points at and around it. Points 0, 1, 2 and 4 went through `Drown()` onto land.
  - Point 3, 30 cm north, **held** on `RS1_Rock_013`. The movement's own floor is walkable there: normal z 0.716, 44.3 deg, just inside the 44.77 deg limit. None of the seven escapes left the pocket.
- **Scan spots and grid.** The local scan's remaining stone flags (two self-notches and three hangs), and a 24-point grid over the stone's top: 29 of 29 went through `Drown()` onto land (home).
- **Coast and inlets** (4.7).

### 4.3 Right

- **Stand stop.** The pawn was grounded on `IBGC_RS1_Coast_R11`, with the camera at (3047.6, -8519.3, 148.2).
  - Aimed shot: OnServerHit `IBGC_BS1_Rock_018`; replica trace on the stone at 439.6 cm.
  - The planned gap shot met `RS1_Rock_025`; see 4.5.
- **7 uninterrupted routes,** including the moving-camera sequence.
  - Run-and-jumps toward the stone's centre, west end and north-east tip (full speed and 60 %), and toward the crevice's old point; plus one walk-in.
  - All 7 came back through `Drown()` to their take-off point on `Coast_R11` and walked back.
  - Walking ticks on the stone: 0. No LastSafeLocation change off land.
- **Moving camera:** 25 frames (`analysis/sequence_right_contact.jpg`).
- **Old placements.**
  - The crevice's old coordinate now lies under the stone's collision top. Its five surface points (at it, and 30 cm on each side) all went through `Drown()` onto land.
  - The right wedge 01 placement **held**, as on BS2: the pawn is falling against the outcrop's west face and the slab edge, at (3207.0, -8329.4, 47.8), the same position as on BS2.
- **Scan spots.** Five spots: the west-end slot and hang, the stone's self-notch hang, and the two places where the translation-only candidate kept its V. All five went through `Drown()` onto land.
- **Grid.** 23 points on the stone's top: all through `Drown()` onto land.
- **Control walk-in toward right wedge 01.** It entered the water and `Drown()` returned it onto `Coast_R10`. The hold is reachable by placement; this one walk-in did not catch.

### 4.4 BS2 controls: attribution (job 236 part B, `analysis/control_eval.json`)

These are the same placements and routes, on BS2 as saved:

| Probe | BS2 | BS3 | Verdict |
|---|---|---|---|
| Island 66 (positive control) | held on Rock_006 | `Drown()` onto land | fixed by BS3 |
| Left wedge 19, points 0, 1, 2, 4 | held on Rock_006 (4 of 4) | `Drown()` onto land | fixed by BS3 |
| Left wedge 19, point 3 | held on `RS1_Rock_013` at (6202.4, 12029.9, 136.7) | held there, same position | unchanged hold (not BS3's) |
| Full-speed jump toward job 226's landing | lands on Rock_006; `Drown()` back onto Rock_006 (6342.3, 12002.1); 7 escapes fail | ends on land | fixed by BS3 |
| Crevice placement (positive control) | held (falling at 3642.8, -8357.2, 32.2) | surface point 0 at the same x, y: `Drown()` onto land | fixed by BS3 |
| Right wedge 01 | held at (3207.0, -8329.4, 47.8) | held, same position | unchanged hold |
| Jump toward the crevice's old point | `Drown()` onto land | `Drown()` onto land | no hold on either |

The positive controls confirm that this probe code detects BS2's known holds. That rules out a probe-side reason for BS3's clean results.

### 4.5 Weapon and camera

- **Aimed shots.** In each area, one aimed shot with the pawn's own `UHitscanWeaponComponent.Fire()` hit the changed stone, both by OnServerHit and by the replica Pawn-profile trace. This happened in job 235 and again in job 236.
- **Water shots.** Job 235's planned gap shots met the neighbouring RS1 rock in front of their water points. So in job 236 each stand stop fired at two water points 30 cm from the stone, chosen so the line from the stand camera is clear of every rock in the static model:
  - left: (6280, 11910) and (6330, 12030);
  - right: (3410, -8480) and (3540, -8520).

  All four hit nothing: no OnServerHit and no replica trace hit within 1 km. No collision appeared beside the moved stones.
- **Camera.** The stand stops are 4.4 m from the stone faces. The moving-camera frames show the first-person camera over land and water, with the stone in view, and never inside rock.

### 4.6 Frames

The check tool named sequence frames after their route. The route name contains a colon, so on NTFS each frame was written as an alternate data stream of one file per area (`frames/<area>_sequence/<area>_moving_camera`). Job 237, without the engine, copied all 48 streams into ordinary PNGs (`frames/<area>_sequence/png/`; 1723 x 1280; PNG signature checked). The streams were left in place. The contact sheets show eight frames per area.

### 4.7 Coast paths and water-recovery inlets

- **Coast paths.** The revised coast paths from BS2's final spec, near each area, were walked in one attempt each: left 7 of 7 waypoints, right 6 of 6.
- **Right inlet.** The established drown walk on the right shoulder recovered onto `Coast_R11` and walked back.
- **Left inlets.**
  - The left shoulder drown spot 1 recovered onto `Coast_L02`.
  - The left rim band walk (arc 106 m) stopped before the water at (5895.9, 12096.7) on `Coast_L06`. That is exactly where BS2's job 228 stopped (same end point). It is unchanged and unrelated to the stone.

## 5. Appearance

`analysis/stills_board.jpg` holds the matched editor stills: BS2 then BS3, the same cameras, and the same load and settle times. There are four local views (left land and sea, right land and sea) and the approved overhead camera. `analysis/stills_diff.json` gives the changed-pixel shares.

- **Changed pixels.** The shares are 2.6-12.9 % (more than 24/255, 3 x 3 median). The changed regions are mainly the animated water, which differs in every pair of captures. Off the water, the changes are confined to the two stones.
- **Left stone.** It sits about 0.7 m further from `RS1_Rock_013`, and the opened neck shows as water.
- **Right stone.** It lies a little further along the outcrop's south face, and slightly more of it shows (visible share 1.11).
- **Overhead.** At the approved overhead camera neither change is visible. The irregular rocky rim is as in BS2 and as in the reference (`References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`, shown beside it on the board for eye comparison).

There was no BS2-BS2 control pair this time, so the shares are not calibrated against noise.

## 6. Preservation, processes, errors, frame rate

- **Preservation** (`analysis/bs3_preservation.py` -> `hashes/preservation-final.json`, `58A5E5EE...`): **PRESERVED.**
  - Codex's 2,447 records: 2,443 project files re-hashed now, all matching. The 4 engine files match through every stamp.
  - Codex's 12 BS2 artifact and evidence records: 12 of 12.
  - This task's 8 stamps (`shared-before-233` ... `shared-after-236`, 2,748 entries each) are all identical to the first. The 2,744 project files re-hash to it now.
  - Live map `FAFFD601...`; BS2 map `2D642903...`; BS2 receipt `F162F20B...`; four collision assets at their manifest hashes.
  - Every job: CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0. Only `CarrowGateGarrison_BoulderShore3.umap` was written, by jobs 233 and 234.
- **Processes** (`analysis/log_check.json`, `BAAB5211...`): 11 engine processes (9 commandlets and 2 GUI sessions), all logs closed normally.
  - Commandlets exit 1: the known GameFeatureData ensure before the script runs. The tool's own verdicts are in each step's `bs3_<step>.json`. GUI editors exit 0.
  - 0 access-violation or fatal lines. 0 compile, physics or static-mesh lines naming BS2 or BS3 assets or the editable rocks.
  - Error lines by kind, all pre-existing:
    - the GameFeatureData ensure block;
    - BP_Mech compile errors and CurrentVisualData lines (GUI);
    - the M_AI_Foam compile warning;
    - four Windows audio-device error lines of two kinds (GUI, job 235);
    - 38 BS3 refusal lines, which are the negative tests' intended refusals.
  - 11 crash-reporter folders, one per process, all `Ensure`.
- **Exit-time crashes:** none this time. Both GUI editors exited 0.
- **Dirty packages and autosave.**
  - No dirty package after any load, after PIE or at exit.
  - The isolated GUI UserDir holds one `Autosaves/PackageRestoreData.json` (96 bytes, `RestoreEnabled false`, no packages), written at editor exit, as in BS2's runs. No content was autosaved.
- **Frame rate** (`analysis/frame_timeline.json`, from job 235's own tick record): wall/game time per phase 0.95-1.22 (left 1.06, right 1.22). Median frame 0.016-0.031 s. The longest single tick in the PIE phases was 7.3 s (left) and 4.4 s (right). No severe slowdown; nothing was investigated or cut short.

## 7. What failed or was corrected

1. **Translation alone did not close the crevice** (static model). The plan added the +6 deg yaw (section 2.2). The tool accepts a recorded yaw change of at most 10 deg; z, pitch, roll and scale stay fixed. Negatives for the turn (yaw-back, yaw-only) were added and refused.
2. **Job 235's gap shots met the neighbouring rock.** The planned water points were behind `RS1_Rock_013` / `RS1_Rock_025` as seen from the stand. Job 236 repeated the stand stops on BS3 with clear-line water points (4.5).
3. **Moving-camera frames written as NTFS streams** (colon in the file name). They were recovered by job 237 without loss (4.6). The check tool used by job 235 is left as run.
4. **The full-speed jump toward job 226's landing** came down on `RS1_Rock_013`, not on the stone or the water as the ballistic estimate said. It is recorded as run.
5. **Attribution needed BS2 controls.** Job 236 part B was added after job 235 (4.4).

## 8. Limitations

- **Two areas only.** Other known holds (job 231's other wedges and pits, other rocks' tops) are untouched and remain queued, as the brief says.
- **Placement and probes are not exhaustive.**
  - 20 routes and 70 placements on BS3.
  - The scan is a heuristic: island 66 was a walkable top, not a wedge, and point 3 is a 44.3 deg pocket.
  - Walk-ins were few.
- **The two remaining holds are reachable.** Right wedge 01 is reachable by placement; this run's single walk-in did not catch. The `RS1_Rock_013` pocket is a placement; whether a player can walk or jump into it from `RS1_Rock_013`'s reachable top was not established.
- **Unwalkable stones change play there.** The two stones cannot be stood on: a player who jumps onto them slides into the water and returns to land. This is the brief's allowed override and a deliberate choice.
- **Stills differences are not noise-calibrated** (section 5).
- **Not checked:** no manual playtest, no multiplayer.

## 9. Files and hashes

**Outputs.**

| File | SHA256 |
|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3.umap` (applied) | `FDF8219D0C35A30EB778B92BDA76B55FBF2B6ABA4E3236C2AC56563E994BE132` |
| `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_BoulderShore3.json` | `656013F75938760239CF70A72F49F744EC71C52DA0D411937034522A09323683` |
| `run1/apply/ownership_manifest.json` | `3EA7FF78DD653A23A0EC5D54A3DC1A7422B2366CEF0047E1627472616CECB9DE` |

**Plans, tools, jobs** (evidence folder unless a path is given).

| File | SHA256 |
|---|---|
| `plan/bs3_plan.json` | `6523599CEC549C9BDA494917D12D3086857370A8742FAE43E2F7561AA84C8820` |
| `plan/bs3_proof_spec.json` | `CF9726BE244A24C9066CD110C13DF99124B40E0FC416285AD180553031E62E3A` |
| `plan/bs3_control_spec.json` | `BB97E30D4EE37AFC2BE5DFF68B23BCEB4FC8AEAA004A466F4B6A6DDC6CE7A484` |
| `tools/ib_garrison_shorerecovery.py` (copy + lifecycle) | `81B96E00370165A6C3FA20403B389A8FB612B940BCC41C65BF28F017A42B1282` |
| `tools/ib_garrison_shorerecovery_check.py` (job 235, as run) | `FC2767B5A2BF9D19F96BCC3848F04117127DEE46A4A5087E0E0C6C0405A45D37` |
| `tools/ib_garrison_shorerecovery_control.py` (job 236) | `4B68B1F843BFC89A0AABACE8CDC5FB82C05CFEFC03D2F1FCD8D4B508A2FC7D4A` |
| `Saved/zz_job/shorerecovery_lib.ps1` | `A37FF4897F0B24410DDAB5F43B0E6880C40E1AA393B670E7B826E3F54DB2F221` |
| jobs `233-bs3-prepare`, `234-bs3-lifecycle`, `235-bs3-proof`, `236-bs3-control`, `237-bs3-frames` | `92BDAB32...`, `C9BB52F1...`, `EF917595...`, `C0CB84D0...`, `BEC4CD05...` |

**Raw records and evaluations.**

| File | SHA256 |
|---|---|
| `run1/prepare/base_fingerprint.json` | `65115528CB4856964ABF4060A36BA274984830AE8091930BA6B5B281EF08323D` |
| `check/proof/bs3_proof.json` | `9CF2E3B1E89E767E83BCC687B89F29877EC15A57CE67C55746B35D2F67C13FD0` |
| `check/control/bs3_control.json` | `4886C7F173EC1DC7C21ED524352BBCAC1EB52149308413B7C4357A10FBFF1653` |
| `analysis/bs3_design.json` | `7EC1E2911F22CB62515364E5CA690F68BB03D479E8BAD416F7B7D51377962806` |
| `analysis/bs3_design_yaw.json` | `9593A5716B37E341CEDD63911C49139D1128DB5FB26BBF1CFACC8E7E74029DCF` |
| `analysis/proof_eval.json` | `2A0D2E420FD9AE6264142CA46D5025EC87CB80CD87CBE6DB5409BF1307B06384` |
| `analysis/control_eval.json` | `AAD95E03A2252359BF997665F5B7BEC4DBB6CD61CDB208C2E53C3BBE784D0157` |
| `analysis/stills_diff.json` / `stills_board.jpg` | `F333EA57...` / `0C3E2459...` |
| `analysis/frame_timeline.json` | `DDA8CABBB5A2FA4FCCF5EC6087F95FC07FC4A6E2BD647562CE0205D1CD3609F1` |
| `analysis/log_check.json` | `BAAB5211D9F9ADE4AA460E9FF2C430DEE2D9611A9001E4222B7052416DAEA125` |
| `hashes/preservation-final.json` | `58A5E5EE723C90CF5D619D0B195A003C20B4A6253C31D3CB4171B95B4A7012D6` |
| figures | `design_left.png`, `design_right.png`, `design_right_yaw.png`, `proof_spec_left/right.png`, `sequence_left/right_contact.jpg`, `frames/left_stand.png`, `frames/right_stand.png` |

The complete per-file list, with sizes and hashes, is `hashes/evidence-final.json`. It was written after this document, and its hash is in the status file.

**Rerun the offline analysis** from the project root. Set `BS2_WORK` to the BS2 evidence folder for the design scripts. The `bs3_design*.py`, `bs3_proof_spec.py` and `bs3_control_spec.py` scripts need numpy and scipy:

```
python3 Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/analysis/bs3_proof_eval.py <check/proof/bs3_proof.json> <plan/bs3_plan.json> <out>
python3 Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/analysis/bs3_control_eval.py <check/control/bs3_control.json> <check/proof/bs3_proof.json> <out>
python3 Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/analysis/bs3_preservation.py
python3 Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/analysis/bs3_log_check.py
```

## 10. Stop

The two-area proof is complete. Stopped for Codex review:

- No other rock, area or shore hold was touched.
- Nothing was promoted.
- The queue holds only `153-yellow-after.hold`.

Decisions for review:

- whether BS3's two fixes are accepted for continued disposable work;
- how to treat right wedge 01 (the outcrop) and the `RS1_Rock_013` pocket.
