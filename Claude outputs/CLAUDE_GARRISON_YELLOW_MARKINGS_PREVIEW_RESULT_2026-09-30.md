# Garrison yellow markings preview (YM1) result — 2026-09-30

Claude, 19:35 UTC. This answers `Docs/CLAUDE_GARRISON_YELLOW_MARKINGS_PREVIEW_2026-09-30.md`. Engine jobs 150–156 ran from 18:24 to 18:54 UTC; the job logs print local time (UTC−7).

**Candidate, left saved and applied for review:**
`/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1`
(`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1.umap`, SHA256 `AF25734AB4E78445A40A971D6F2B60DEAEE89A7A30683CAAB4A3BB6F26418855`, the last `applied` entry in its new correction receipt).

**New material instance:**
`/Game/_GarrisonPreview_Disposable/YellowMarkings1_Materials/MI_YM1_DeckPaintYellow`
(file SHA256 `B9E3E18F8DCDBB77B065A73B3F704727EB4420F4DBAF033FCE939E8ECEBF20C8`). No test process is running, and the job queue holds only the inert `153-yellow-after.hold` (section 8).

**Scope held.**

- Written in Content: only the new candidate map and the new material instance (plus the candidate's new receipt in Saved).
- The base PF1 (`C904EF8C…`) and its receipt (`4470B368…`) are byte-identical before and after every job, and so are the 106 files of PF1's evidence folder (engine scratch UserDirs excluded).
- Also byte-identical before and after every job:
  - the live map `FAFFD601…`;
  - P3Candidate1 and Preview3 with their receipts, CB1Preview and CB1Preview2;
  - the shared `MI_Landmass_*` family and `M_FlatCol`;
  - the live saves.
- The layout receipts were not touched.
- Nothing was deleted. There was no Git, no locks, no commit or push, no message to anyone, no live-map promotion and no hangar work.

## 1. At a glance

| Item | Result |
|---|---|
| New candidate | Made from the final PF1 state with the engine's asset duplication. It was verified actor for actor and component for component against a fingerprint of PF1: 3131 actors and 3158 in-game primitive components, all identical. It has its own receipt, which records PF1's package, bytes and receipt as provenance. Layout, crane/truck transforms, the 6 m pier corridor, quay geometry and gameplay assemblies are unchanged. |
| Material instance | Lives in a subfolder of the disposable folder. Parent is `M_FlatCol`, which is not edited. The only override is the exposed vector **`Base Color` = (0.95, 0.82, 0.15, 1.0)** (linear); the nonexistent `Color` parameter is not set. Metallic 0 and Roughness 1 are inherited from the parent, so the surface is matte. M_FlatCol is DefaultLit and opaque with no emissive input (PF1's probe), so the paint is non-emissive. After save and reload, the engine reports the effective Base Color as (0.95, 0.82, 0.15, 1.0). |
| Assignments | **91 generated, candidate-owned markings**, each on slot 0 of its `StaticMeshComponent0`, from `MI_Landmass_HelipadMarking` to the new instance. Each assignment is identified by actor object path, label, run tag, component, slot, mesh and original override list. The 91 are P3's pad ring (32), spine dashes (15) and rear-reservation outline (8), plus all 36 PF1 markings. Paint stays NoCollision. The three inherited live-map actors that use the shared instance (`Helipad_North_H_L`, `_R`, `_Bar`) were deliberately left untouched. |
| Lifecycle (real engine, job 155) | verify clean → apply+save → reload-verify → saved repeat (no-op, bytes unchanged) → revert+save (every original restored) → reload-verify → re-apply+save → verify-final. **All passed.** |
| Candidate vs PF1 | Actor for actor and component for component after reload: **91 expected slot changes, 0 unexpected**. All other 3040 actors are identical; after the revert there were 0 differences. |
| Engine material readout | In the loaded editor world **and in the PIE world**, all 91 markings carry `MI_YM1_DeckPaintYellow`. Before (PF1): all 91 carried `MI_Landmass_HelipadMarking`. |
| Visual result | The markings now read as yellow deck paint overhead and at the player's eye height, pad ring included. On the same cameras before and after, the paint's mean hue moved to 44–53° in every view, and its saturation rose by 0.25–0.52. Before, it was bluish grey in shade or grey-brown in low sun. Section 5 also compares it with the reference's amber paint. |
| Paint geometry | **Unchanged.** Section 6 explains why no overlap fix was needed. |
| Movement | One representative scripted PIE walk (forecourt → pier end along the lane) **reached** in 16.0 s. The lane scan (788 cm corridor) and all 15 capsule sweeps are identical to PF1's r2 check. |
| Preservation | 224 protected files are identical in all 14 snapshots (before-150 … after-156): the brief's 116, the PF1 map and receipt, and 106 PF1 evidence files. Content writes outside the disposable folder: 0. Owned processes left: 0. |
| Engine health | **Not a clean engine run.** All 19 engine processes logged the pre-existing GameFeatureData ensure; the GUI runs also logged the known BP_Mech errors. None logged an access violation, and all 19 logs close normally. Section 9. |

## 2. The material instance

It was created by `Scripts/ib_garrison_paint_correction.py` in its `material` stage, which never overwrites an existing package. The stage built the instance in memory, checked it, and only then saved that one package. The parent file's hash was checked before and after.

The engine readout after reload is the same in all four verify reports (`y-verify-created`, `-applied`, `-reverted`, `-final`) and in the apply, repeat, revert and re-apply reports:

- parent `/Game/LevelPrototyping/Materials/M_FlatCol.M_FlatCol`;
- vector overrides `[Base Color (0.95, 0.82, 0.15, 1.0)]`; no scalar or texture overrides;
- base-property overrides (shading model, blend mode, two-sided) all off;
- effective `Base Color` (0.95, 0.82, 0.15, 1.0), `Metallic` 0.0, `Roughness` 1.0.

The tool's check asserts the parent, the single `Base Color` override, the effective Base Color and the absence of scalar and texture overrides. Metallic, Roughness and the base-property overrides are recorded in every report, but they are not asserted.

The instance is recorded in the candidate's receipt under `material`. The record holds the package, file, SHA256, parent, parent-file SHA256, value and `owned_by` (the candidate).

Colour choice: I kept the brief's starting value. How it compares with the reference's paint is in section 5. The tool can retint the candidate's own instance in place and record the history, if a more amber value is wanted. The retint is covered by the offline harness only; it was not run on the engine.

Engine note: `MaterialEditingLibrary.set_material_instance_vector_parameter_value` returned `False` although the value was applied. It happened both in the rehearsal's in-memory instance (`paint_smoke.json`) and in the real stage (`paint_material.json`). The tool therefore judges only the effective values it reads back.

## 3. The assignment list

The full list is in `Saved/GarrisonRestructure/20260930-claude-yellowmarkings/run1/plan/assignments.json` (SHA256 `C1A18F4A0F33774CEE92F861AFDD9339773F0DED856376C3C5B70488FF349240`).

The plan stage derived it read-only from PF1's layout plan (`plan2/plan.json`, `20F26D60…`). A piece qualified only if it was one of that plan's generated pieces on the shared marking instance and carries the run tag `IB_GarrisonCB1`.

Each row records:

- actor object path and label;
- class and tags;
- component `StaticMeshComponent0`, slot 0 of 1;
- mesh `/Engine/BasicShapes/Cube.Cube`;
- collision profile `NoCollision`;
- `from` = `MI_Landmass_HelipadMarking`, and `from_overrides` = the exact original override list (used for the revert);
- `to` = the new instance;
- zone, kind and origin (P3 or PF1).

| Origin | Zone / kind | Count |
|---|---|---|
| P3 | pad ring segments | 32 |
| P3 | spine centre dashes | 15 |
| P3 | rear reservation outline (edge + inner) | 8 |
| PF1 | edge lines: pad 7, spine 4, control 4, pier 3 | 18 |
| PF1 | lane lines: pier 2, spine 2 | 4 |
| PF1 | control-apron route dashes | 12 |
| PF1 | door bars | 2 |
| **Total** | | **91** |

Nothing else was assigned. The following keep their materials:

- the decks (`Concrete_Mat`), coping and fascia (`M_Bastion_Concrete`) and buildings;
- the three inherited live-map users of the shared instance (`Helipad_North_H_L`, `Helipad_North_H_R`, `Helipad_North_H_Bar`). These are still grey in the candidate, as they are in the live map.

## 4. Lifecycle and reversibility (real engine)

Every step ran in its own commandlet process with the isolated UserDir `…/20260930-claude-yellowmarkings/user`. As in earlier tasks, each commandlet exits 1 because the pre-existing GameFeatureData ensure block logs 23 error lines before the script starts. The one exception is job 152's refused copy-verify, which exited −1. The tool's own status is `complete` on every step except that refusal.

| Job / step | Result | Candidate after |
|---|---|---|
| 150 smoke (rehearsal, read-only, tool v1) | Loaded PF1 and fingerprinted 3131 actors. Read 91 markings on the shared instance. Built the instance **in memory only** and assigned it to a transient component, then restored the component. Nothing on disk. | — |
| 152 copy (tool v1) | `duplicate_asset` of PF1 to the new name; saved only the target | 962B7C39004C |
| 152 copy-verify (tool v1) | **Refused**, with no receipt written: 13 differences in a comparison that loaded PF1 and then the copy **in one process**. Exit −1. The 12 error lines during the script are the tool's refusal message, its 10-line traceback and the commandlet's "Python script executed with errors". The log ends normally. | 962B7C39004C |
| 154 load-order probe (read-only) | YM1, PF1, the live map, YM1 and PF1 were loaded in turn in one process (load, read, garbage-collect, the same sequence as v1). Every load read the water profile `Custom` and the checked door frame's editor sprite as `BillboardComponent_0`. **The effect did not reproduce.** | unchanged |
| 155 base-fingerprint (tool v2) | PF1 alone, first map in its process. 3131 actors and 3158 in-game components; 18 editor-only components counted and skipped | — |
| 155 copy-verify | Target loaded alone and compared with the base fingerprint: 3131 of 3131 identical. Receipt `created` | 962B7C39004C |
| 155 material, plan | Instance created (`B9E3E18F…`); 91 assignments, 0 problems | 962B7C39004C |
| 155 verify (clean) | 0 differences | 962B7C39004C |
| 155 apply + save → reload-verify | applied-verified → verified: 91 expected, 0 unexpected | 43FDAF88A3D5 |
| 155 saved repeat | already-applied-verified, not saved, bytes unchanged | 43FDAF88A3D5 |
| 155 revert + save → reload-verify | reverted-verified (91 originals restored, override lists included) → verified: 0 differences from PF1 | 030736EF10C5 |
| 155 re-apply + save → verify-final | applied-verified → verified: 91 expected, 0 unexpected | **AF25734AB4E7** |

**Job 152's refused copy-verify.** The 13 differences were:

- 12 in the six door frames' editor-only sprite components: `BillboardComponent_0` on the first map loaded, `_1` on the second;
- 1 in the harbor water's collision profile: `Custom` on the first map, `BlockAll` on the second (collision enabled `QUERY_AND_PHYSICS` in both).

They did not come from the copy's content:

- The copy was never changed; it stayed `962B7C39…` from job 152 through job 155.
- The probe read the same values from the copy and from PF1.
- Tool v2 fingerprints each map alone, and with it the copy compared identical.

**The mechanism is not identified.** The probe repeated v1's sequence with five loads in one process and did not reproduce the effect. Tool v2 avoids the situation in two ways: it fingerprints each map as the first map loaded in its own process, and it counts editor-only components without comparing them. Every v2 comparison matched expectations (table above).

**Revert.** Exact restoration is judged by the fingerprint, which records:

- for each actor: class, label, transform, hidden and collision flags, tags and folder;
- for each in-game primitive component: visibility, collision profile and state, mesh, per-slot materials and override list.

After the revert there were 0 differences from PF1. The bytes are a different matter: saved packages are not byte-reproducible here. The two applied saves (`43FDAF88…`, `AF25734A…`) have the same verified content but different bytes, and the reverted file (`030736EF…`) differs from the first copy (`962B7C39…`) the same way.

**Receipt.** `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_YellowMarkings1.json` (SHA256 `C2A52B76…`). Its kind is `YM1 paint correction candidate`. Its history is created → applied → reverted → applied. Each applied and reverted entry records the assignments' SHA256 and the instance's SHA256.

- The layout tool refuses this candidate, because its source is PF1 rather than the live map. So no layout receipt claims these material assignments.
- PF1's own receipt is untouched.

**Refusal tests.** These are the offline harness only (`drive_ym1.py`, 27/27, re-run at 19:21 UTC against my local copy of the final v2 tool, which has the same SHA256 as the one on the machine); they do not run on the engine. Each case below was refused:

- a base at the wrong bytes;
- a base whose receipt does not end `applied`;
- a copy onto an existing target;
- a base fingerprint of other bytes;
- an instance outside a subfolder;
- a Base Color that does not take (nothing saved);
- an assignment that does not take (not saved);
- an outside edit to the target (STALE TARGET in apply, revert and verify);
- an unexpected actor change under a forged receipt (caught by the comparison);
- revert on the reverted state.

The harness also covers the exact revert, the saved repeat and an in-place retint.

**Backups (not used for restore):** `backup/YellowMarkings1-created.umap` and `backup/YellowMarkings1-applied.umap`.

## 5. Captures and measured colour (before and after)

- **Before:** job 152z on PF1, read-only (`before2/shots/`).
- **After:** job 156 on YM1 (`after/shots/`).

Both runs used `ib_garrison_yellow_check.py` at `44C60C75…`. The file was last written at 18:31:10 UTC, before job 152z started at 18:31:43, and has not changed since. They used the same cameras (the PF1 r2 set plus a pad-ring view), the same capture timing and the isolated UserDir. World lighting was not touched, and no lighting or post-process asset was changed. The PIE captures come from the player's own camera.

Job 151's before set (made with the earlier `E3FFE4B6…` version of the script) is kept but superseded. Its PIE pad view had the ring under the subtitle bar, and I moved that camera.

**Exposure** was left at the project's settings, which do not turn automatic exposure off; it was not locked for the captures.

- A post-run image check (`board/ym1_post_checks.py` → `board/ym1-post-checks.json`) compares each pair over the pixels that did not change.
- Mean luma differs by under 1 level (of 255) in 9 of the 12 pairs.
- It differs by 2.8–4.8 levels in `pad-ring`, `spine-control-join` and `pie-control-apron-to-command`, where the after frame is uniformly slightly darker (under 1 % of pixels identical).
- All 12 after frames are darker outside the paint, by 0.01–4.84 levels.
- The cause was not investigated. Automatic exposure responding to the brighter paint is one possible explanation, but the shift does not track the paint's share of the frame.
- Either way, the shift darkens the after frames, so it works against the new paint rather than flattering it.

**Board:** `board/ym1-before-after-board.png`, with 10 matched pairs plus an overhead crop and a data footer. Statistics are in `board/ym1-colour-stats.json`.

**Measurement method:** "Paint" means pixels that changed by more than 24 levels and whose after-colour is yellow-hued (hue 25–70°, saturation at least 0.25). The means below are over those pixels, sampling every second pixel.

| View | Kind | Paint px | Before mean sRGB (hue°, sat) | After mean sRGB (hue°, sat) |
|---|---|---|---|---|
| overhead-reference | EDITOR | 0.30 % | (117,107,104) (14, 0.11) | (170,160,108) (50, 0.37) |
| pier-lane-ground | EDITOR | 2.74 % | (51,48,52) (285, 0.08) | (124,115,51) (53, 0.59) |
| pier-lane-eye | EDITOR, eye height | 3.64 % | (40,40,46) (240, 0.13) | (113,104,45) (52, 0.60) |
| control-pad-edge | EDITOR | 1.81 % | (94,78,66) (26, 0.30) | (173,149,67) (46, 0.61) |
| pad-ring | EDITOR | 2.63 % | (54,53,60) (249, 0.12) | (132,122,58) (52, 0.56) |
| spine-control-join | EDITOR | 2.31 % | (84,72,65) (22, 0.23) | (176,150,63) (46, 0.64) |
| pie-pier-lane-from-forecourt | **GAMEPLAY** | 1.22 % | (62,52,45) (25, 0.27) | (119,100,46) (44, 0.61) |
| pie-pier-lane-from-pier-end | **GAMEPLAY** | 3.39 % | (44,43,47) (255, 0.09) | (118,108,47) (52, 0.60) |
| pie-control-apron-to-command | **GAMEPLAY** | 3.55 % | (101,82,64) (29, 0.37) | (188,155,60) (45, 0.68) |
| pie-pad-ring | **GAMEPLAY**, eye height across the ring | 2.15 % | (55,53,57) (270, 0.07) | (135,124,58) (51, 0.57) |

In every view, the paint's saturation rose by 0.25–0.52 and its brightness (HSV value) rose by 0.21–0.36.

- **Before:** bluish grey in shade (hue 240–285°, saturation 0.07–0.13), or grey-brown where the low sun warms it (hue 14–29°, saturation 0.11–0.37).
- **After:** yellow (hue 44–53°, saturation 0.37–0.68).

In shade, under the ship's and crane's shadows and at eye height, the paint reads as a darker mustard yellow; in sun it reads golden.

Changed pixels outside the paint gate are at most 0.19 % of the frame in the ten board views, and 0.21 % in `overhead-topdown`. They are a mix of two things:

- anti-aliased paint edges below the saturation gate;
- things that move between runs: water, clouds, the helicopter's rotor and the PIE subtitle.

Two other shots, `overhead-topdown` and `pier-channel-quay`, are in both sets and not on the board.

**Against the reference.** The approved reference's deck paint is amber rather than lemon.

- `board/ym1_post_checks.py` samples five deck boxes of the reference (pad, spine, control platform, main deck, pier) with the same hue gate (25–70°) at two saturation gates.
- Broad gate (saturation at least 0.25): mean sRGB (160,129,97), hue 30.5°, saturation 0.39.
- Strict gate (saturation and value at least 0.45): (185,141,90), hue 32.2°, saturation 0.51.
- The same gates on the paint pixels of the after `overhead-reference` give (169,159,108), hue 50.2°, saturation 0.36, and (191,175,99), hue 49.6°, saturation 0.48.

So brightness and saturation are close, and the new paint's hue is 17–20° yellower than the reference's amber.

## 6. Paint overlaps and geometry

No paint geometry was changed: same pieces, transforms, widths, heights and collision. So the route widths, platform silhouettes and clearances are exactly PF1's.

- **The 40 pre-existing coplanar overlaps** are P3's own: 32 pad-ring joints and 8 reservation-outline corners. In each pair, both pieces now carry the same new instance and the same upward-facing surface. Whichever wins the depth test therefore shades identically.
- **Zoomed crops:** in zoomed crops of the after pad-ring view and the overhead, I saw no dark intersections or seams at the ring joints or reservation corners.
- **No colour-mixing overlaps remain.** Where PF1's markings overlapped one another or P3's markings, PF1 had already raised them in 0.3 cm steps (its plan check found 0 coplanar overlaps among new pieces). No marking top is coplanar with a deck.
- **Limit of the check:** there is no temporal (video) capture, so flicker is argued from the identical materials rather than observed over time.
- **Visible at eye height:** the ring's 32 straight facets. This is P3's geometry and was left as is.

## 7. Movement and collision (collision and geometry unchanged, so a single walk)

Job 156 checks:

- **Scripted PIE walk:** `BP_IBCharacter_Infantry_C` along the pier lane, forecourt → pier end. Reached 3 of 3 waypoints in 16.0 s over 96.5 m, capsule z 475.2 throughout, drift 47.8 cm including the stop at the goal.
- **Engine lane scan** (not movement): pawn-centre band y −274.3…446.0 (720 cm), obstacle-free corridor 788 cm between the crane and truck 4. This is identical to PF1's r2 check (job 146).
- **Capsule sweeps:** 15 of 15 clear. Floors are 384–385 on the decks and 385–393.4 on the coping curb, identical to PF1's r2 check.
- **Props and assemblies:** all at their plan transforms.
- **Before set:** the before run (152z) ran no walk, sweeps or lane scan. The movement comparison is with PF1's own r2 check.
- **No full lifecycle, movement or build suite was rerun,** as the brief allows.

## 8. Preservation and files changed

Protected set: 224 files, hashed in all 14 snapshots `hashes/shared-before-150.json` … `shared-after-156.json`, with **0 differences, 0 missing and 0 new**. They are:

- the brief's 116: 105 shared assets (including `MI_Landmass_HelipadMarking` `047D3AA8…` and `M_FlatCol` `41DBBDA4…`), the live map, 4 earlier preview maps, 2 receipts and 4 live saves;
- the PF1 map and PF1 receipt;
- 106 files of PF1's evidence (engine scratch UserDirs excluded).

Every job logged `SHARED_ASSET_OR_SAVE_CHANGES=0`, `LIVE_MAP_SHA256=FAFFD601…`, `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0` and `OWNED_PROCESSES_LEFT=0`. The GUI runs' PIE sessions saved game data only inside their isolated UserDir.

**Files created or changed by this task:**

| File | SHA256 |
|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1.umap` (new, applied) | `AF25734AB4E78445A40A971D6F2B60DEAEE89A7A30683CAAB4A3BB6F26418855` |
| `Content/_GarrisonPreview_Disposable/YellowMarkings1_Materials/MI_YM1_DeckPaintYellow.uasset` (new) | `B9E3E18F8DCDBB77B065A73B3F704727EB4420F4DBAF033FCE939E8ECEBF20C8` |
| `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_YellowMarkings1.json` (new) | `C2A52B7698F5C0C701A431E3472929601CA00D39545010E66C73CD6D9900CEB1` |
| `Scripts/ib_garrison_paint_correction.py` (new, v2, used from job 155) | `FCD658A20516C47CEFADF7D4BCA850AFBD429A60A7656B26E8F86EC0804428E0` |
| the same file as v1, used by jobs 150 and 152, overwritten by v2 (both job logs record `96A85D202A7EE04C`; the full hash is of my copy of v1) | `96A85D202A7EE04C76AFF73506C481F2677E310778589B0E2AE5B9B36512FC7C` |
| `Scripts/ib_garrison_yellow_check.py` (new, used by 152z and 156; `ib_garrison_pierfinish_check.py` is unchanged) | `44C60C75F43671DA0438C12D87E5025134959FF627952B4A63C8E1186D22C1AA` |
| the same file's earlier version, used by job 151 (the job-150 log records its first 16 hex digits) | `E3FFE4B6018A1B57…` |
| `Scripts/ib_garrison_yellow_board.py` (new) | `70F2DF94E945B66A514DBC139D55C245F88B3D0779F62E9D6563F63A474A20AC` |
| `Saved/GarrisonRestructure/20260930-claude-yellowmarkings/` (new evidence folder; `run1/evidence.json` lists every hash, step, snapshot and shot) | evidence.json `00A7653389DFA2A901100CC5F3EA56E1D3845D709C4E71EE13CE7880BA0A1CA1` |
| in it, added after the jobs (read-only checks): `run1/ym1_log_check.py` → `run1/log_check.json` | `FDEABB68…` → `6304CD6F…` |
| … `board/ym1_post_checks.py` → `board/ym1-post-checks.json` | `326085FE…` → `6AD8CF75…` |
| … `probe/ym1_load_order_probe.py` | `F61377FC…` |
| `Saved/zz_job/yellow_lib.ps1` | `D0E90ADF…` |
| job files, left by the runner with their `.exit` files (all 0) in `Saved/zz_job/running/`: 150 `EDD1C607…`, 151 `2E77B6E7…`, 152 `C15AEE8E…`, 152z `36A5CDFF…`, 154 `71534526…`, 155 `BC3CADE3…`, 156 `ADD00E03…`; logs `Saved/zz_job/logs/15*-yellow-*.log` | as listed |
| `Saved/zz_job/queue/153-yellow-after.hold` (inert; see below) | `13802049…` |
| this document and `Claude outputs/CLAUDE_STATUS.md` | reported in the status file and the handoff |

`Scripts/ib_layout_garrison.py` (`C0DB217B…`) was not changed.

`153-yellow-after.hold` is an inert copy of the after-capture job. It was renamed before it could run against a candidate without a receipt, and it never ran; the runner ignores `.hold` files.

## 9. Limitations and remaining items

1. **The shared family is still wrong.** PF1 found (from the byte name tables of all 16 `MI_Landmass_*` instances) that they set `Color` while their parent has `Base Color`. The live map's own helipad "H" pieces and landmass pieces still render grey. Per the brief this is not fixed here; it is Connor's call.
2. **Hue versus the reference.** The new paint is golden yellow (hue about 50° overhead); the reference's deck paint is amber (about 31–32°). The paint in the ship's and crane's shadows reads darker mustard. Both are retint questions for the candidate's own instance (section 5).
3. **Exposure was not locked.** Three pairs differ by 2.8–4.8 luma levels outside the paint, in the direction that darkens the after frames (section 5).
4. **Overlap flicker is argued, not filmed** (section 6). The ring's facets are P3 geometry.
5. **Engine health: not a clean run.** `run1/log_check.json` covers all 19 engine processes: 15 commandlet steps, the probe and 3 GUI runs.
   - **Startup ensure:** every process logged the pre-existing GameFeatureData ensure (`AssetBaseClassLoaded`, AssetManagerTypes.cpp line 82). That is 23 error lines before the script in each commandlet log (the 15 steps and the probe) and 26 in each GUI log.
   - **Crash-reporter folders:** each process also wrote one unattended crash-reporter folder for that ensure in its isolated UserDir. The 19 folders are under `user/` and `user-gui/Saved/Crashes`; all are `CrashType Ensure` at startup, and none is a crash.
   - **GUI-only errors:** the GUI logs also show the `BP_Mech` "Update Mech Proximity" compile errors (7 lines) and one `CurrentVisualData is NULL` line.
   - **Shutdown:** all 19 logs end with the engine's normal "Log file closed" line, and none contains an access-violation, unhandled-exception, critical or fatal line. The three GUI editors exited 0.
   - **Earlier crashes:** the two PF1 shutdown access violations remain unresolved and were not investigated further.
6. **v1 comparison artifact.** Job 152's copy-verify refusal came from the tool's two-map comparison, not from the copy. Its mechanism is not identified (section 4), and v2 avoids it. The refused attempt's report is kept (`run1/copy/paint_copy-verify.attempt1-job152.json`).
7. **Carried unchanged:**
   - the door interiors (pre-existing);
   - the forecourt edges, helicopter pose and ship draft;
   - the rear hangar, reserved for Connor and not built.

## 10. Paths

- **Evidence:** `Saved/GarrisonRestructure/20260930-claude-yellowmarkings/`
  - `run1/`: steps, logs, `basefp/`, `copy/`, `plan/assignments.json`, `evidence.json`, `log_check.json`;
  - `before2/` and `after/`: matched shots and `yellow_checks.json`;
  - `before/`: superseded job 151 set;
  - `probe/`: load-order probe;
  - `board/`: board, colour statistics, `ym1-post-checks.json`;
  - `backup/`, `hashes/`;
  - `user/`, `user-gui/`: isolated engine UserDirs.
- **Job logs:** `Saved/zz_job/logs/150…156-yellow-*.log`.
- **Candidate:** `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1`.
- **Material instance:** `/Game/_GarrisonPreview_Disposable/YellowMarkings1_Materials/MI_YM1_DeckPaintYellow`.
- **Base (unchanged):** `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_PierFinish1` (`C904EF8C…`).
