# Garrison SP2 rock palette fix: result (2026-10-01)

**Brief:** `Docs/CLAUDE_GARRISON_ROCK_PALETTE_FIX_2026-10-01.md` (Codex, after its SP1 review: hashes checked 11:50:14 UTC, review recorded 11:52:36).
**Status:** DONE. Stopped for Codex's review. Disposable candidate only: no live promotion, no shared write, no Git.
**Evidence:** `Saved/GarrisonRestructure/20261001-claude-rockpalette/` (index in section 9).

**Summary.**

- **What SP2 changes.** One thing: slot 0 of `StaticMeshComponent0` on SP1's 54 recorded rocks (18 per mesh family) now uses one of three new instances, `MI_SP2_Rock_01` / `_02` / `_Eroded`, instead of SP1's `MI_SP1_Rock_01` / `_02` / `_Eroded`.
  - The three instances are duplicates of SP1's three rock instances: same parent (`M_SP1_Rock`), same textures, same roughness (0.9) and normal strength (1.0). Only gain, gamma and tint differ; desaturation stays SP1's 1.0 and was not set.
  - Everything else is SP1's. 3,489 of 3,543 actors are identical; the 54 rocks differ only in that slot's `materials` / `overrides`; 0 unexpected differences. The comparison now includes the relative location, rotation and scale of every in-game primitive and decal component (3,570; the 20 editor-only components are counted, not compared).
  - SP1, its seven materials, its receipt and its evidence are byte-identical. Connor's hangar reservation, the side bands and the approach are SP1's.
- **The values** (old → new; each family's new set is exactly the rendered candidate C2):

  | Family (18 rocks each) | Gain | Gamma | Tint (R, G, B) |
  |---|---|---|---|
  | 01 (`SM_Mountain_01`) | 0.22 → 0.21 | 1.30 → 0.65 | (1.00, 0.95, 0.93) → (0.86, 0.93, 1.00) |
  | 02 (`SM_Iceland_Mountain_02`) | 0.22 → 0.21 | 1.30 → 0.65 | (1.00, 0.95, 0.93) → (0.86, 0.93, 1.00) |
  | Eroded (`SM_Iceland_Eroded_Mountain`) | 0.22 → 0.60 | 1.30 → 0.65 | (1.00, 0.95, 0.93) → (0.86, 0.93, 1.00) |

  `M_SP1_Rock` computes base colour = lerp(c, lum(c), desaturation) × lum(c)^(gamma − 1) × gain × tint (SP1 result section 3.1 gives it at SP1's values; the general form is in `plan/rp2_candidates.json`). With desaturation 1.0 that is lum^gamma × gain × tint. Gamma 0.65 lifts the mid-tones that cover most of each rock; gain 0.21 keeps the albedo of the former snow tops of 01/02 grey rather than white; gain 0.60 lifts the dark eroded texture; the tint makes the albedo slightly cool.
- **How it was chosen.** One rendered comparison before anything was saved (job 209: SP1, C1 = the brief's suggested starting point, C2). C2 was chosen for all three families. The plan step refuses any value that differs from what job 209 read back from the rendered C2 instances, so the saved values are the rendered ones.
- **Result** (job 211: one GUI session, SP1 then SP2 loaded from disk, same cameras; both maps shot on the same tick schedule, so the clouds match: sky patches within 0–2 levels).
  - **Eroded: no longer crushed.** Rock median sRGB (45, 33, 22) → (92, 73, 51); rock/grass luminance ratio 0.44 → 0.94; pixels below luminance 25: 21.5 % → 8.8 %. The surface and crevices read.
  - **Shade: neutral grey.** The 02 wall rock in the rear strip's shade (037) went from (30, 28, 30), brown beside the cool wall, to slate grey (31, 32, 36), the wall's own cool cast; pixels below 25: 31.6 % → 15.2 %. The same family reads sand-beige in direct sun (below).
  - **From the air:** the near-black eroded rocks along the right coast rim are now mid taupe-grey; they are still darker and browner than the 01/02 rocks beside them.
  - **01:** lighter, cooler stone; the sunlit quarter's R/B 1.71 → 1.51; pixels below 25: 17.2 % → 11.4 %.
  - **02 in direct low sun: still sand-beige**: (144, 113, 81) → (141, 118, 89); sunlit R/B 1.76 → 1.56.
  - No white tops: no measured rock pixel above luminance 215, before or after.
- **Not called finished.** Every sunlit rock face is still beige-warm (R/B about 1.5–1.7). The rock albedo is now slightly cool, so that warmth is the map's low sun; a cooler tint would turn the shaded rocks blue. Section 8.
- **Lifecycle PASS** (job 210, six batched commandlet processes): instances authored and reload-verified; copy identical to SP1 (3,543/3,543); apply → saved → fresh-process verify (only the 54 planned slots); saved-state no-op (nothing saved, file and receipt unchanged); exact restore to SP1 (3,543/3,543 identical, fingerprint digest = SP1's `67BE42A2…`); re-apply (digest = the first applied state's `F0509F98…`); final verify.
- **Exits and preservation.**
  - Job 209's editor exited 0. Job 210's six commandlets exited 1 (the known GameFeatureData ensure). Job 211's editor wrote all 14 stills and its records, closed its log at 12:42:55 UTC, then exited 0xC0000005: the known exit crash, not investigated (section 6).
  - At 12:56:47 UTC all 1,976 project files of Codex's 1,980 records match, as do SP1's 12 reviewed artifacts; the 4 engine files (on A:) are unchanged between this task's first and last job stamps. All six job stamps (2,129 files) are byte-identical. The live map `FAFFD601…`, every earlier preview map, the picture and the four saves are unchanged.
  - 0 compile errors name an SP1 or SP2 asset; no package dirty at any GUI exit; autosave read back off in both GUI sessions.
- **Disclosures.**
  - Job 209's three variants were shot about a minute apart in one world while the clouds moved, so its numbers mix material and light; the same-light pair (job 211) shows a smaller warmth change for 02 than job 209 suggested (section 2).
  - The shade region measures one rock (037, family 02); the other two wall rocks are partly behind a tree. I first labelled it "wall rocks 035-037" and corrected the labels after projecting the recorded rock positions; the measurement files and board were rebuilt with the same regions and numbers.
  - The new step batching has no engine refusal test in this pass (the guard itself is SP1's, unchanged; section 4).
  - Job 211's log carries one 98 KB line: it printed the isolated per-user settings file, which the editor had rewritten in full (autosave still False).

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette2`<br>`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette2.umap`, 6,064,918 bytes<br>SHA256 `68CA73DEFE016766F89850847A4E6D72F3323CAA641D73CA1EE3A37F573C8B72` (SP2 applied)<br>Copied from SP1 `333A3A4463B0A1A1F4CD00C804637BE2F5CA2DB101FCB9AD6AEC648306B01C20`, which is unchanged. |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette2.json`, 46,766 bytes<br>SHA256 `9224A409BD5E21781D767C2758868A9F5143CF142A6B9318E677621092B59705`<br>History (UTC): created `D3ACFE7F…` 12:35:44; applied `76C1CB63…` 12:35:47; restored `2BDCFE58…` 12:36:40; applied `68CA73DE…` 12:37:31.<br>It records the plan `32ACD2FD…`, the material manifest `F37A8920…`, the base fingerprint file `30FFF3A8…`, the copy fingerprint (digest `67BE42A2…`, the same as SP1's), SP1's receipt `F6BA8E00…`, the 54 identities with their family, and the exact override diff. |
| **New assets** (only these, only in `/Game/_GarrisonPreview_Disposable/ShorePalette2_Materials/`) | `MI_SP2_Rock_01`: 7,010 bytes, `53458EC277EFC690E0D18F71B477BA5E2F44ADF972DCC995F60D0C782473D753`<br>`MI_SP2_Rock_02`: 7,010 bytes, `9C38F7DA18FE19D3C93E950BF09D2CE79A80221B77ED220902E06A34B535130C`<br>`MI_SP2_Rock_Eroded`: 7,044 bytes, `3FBD455067D848471E2CE39A0B94024ABB8CD3AFBF1EFFD45D703A5EEDA0605F`<br>Each is an `EditorAssetLibrary.duplicate_asset` of the matching `MI_SP1_Rock_*`, with only `SP1_RockGain`, `SP1_RockGamma` and `SP1_RockTint` set. Parent `M_SP1_Rock`; textures the mesh's own baked maps (`T_Mountain_01`, `T_Mountain_02`, `T_Iceland_Eroded`), read-only. Manifest `run1/prepare/material_manifest.json` `F37A8920…`. |
| **Diff vs SP1** | 3,543 actors, as in SP1. **3,489 identical; 54 differ, only in `StaticMeshComponent0.materials` / `.overrides`; 0 unexpected.**<br>Compared per actor: label, class, location, rotation, scale, hidden, actor collision, tags, folder; per in-game primitive or decal component (3,570): class, **relative location / rotation / scale (read on all 3,570)**, visibility, collision profile, collision enabled, mesh, materials and overrides; decal material and size. 20 editor-only components are counted, not compared. |
| **Override diff** | Exact, from the receipt (both "applied" entries), slot 0 of `StaticMeshComponent0`, materials = overrides = the one instance:<br>• 01, 18 rocks: `MI_SP1_Rock_01` → `MI_SP2_Rock_01`<br>• 02, 18 rocks: `MI_SP1_Rock_02` → `MI_SP2_Rock_02`<br>• Eroded, 18 rocks: `MI_SP1_Rock_Eroded` → `MI_SP2_Rock_Eroded`<br>Restored entry: each family back to its `MI_SP1_Rock_*`. |
| **Not touched** | The other 3,489 actors (trees, CityGround, background peaks, water, buildings, markings, pier, pad, ship, gameplay, the hangar reservation), SP1's 82 other terrain pieces (still on `MI_SP1_Ground_Land` / `_Coast` in both maps, job 211), SP1's seven materials (byte-identical). Light and post-process properties are not in the fingerprint; the tool's only level write is `set_material(0, …)` on the 54 rock components, and job 211's unchanged sky and reference patches match within 0–2 levels. |
| **Lifecycle** | **PASS** (job 210; section 4) |
| **Paired renders** | Job 211, one GUI session: SP1, then SP2 from disk; 7 cameras × 2 = 14 stills (12 at 1920×1080, the reference-fit eye at 7680×4320). After reload: SP1 54/54 rocks on `MI_SP1_Rock_*`, SP2 54/54 on `MI_SP2_Rock_*`; 82/82 other terrain pieces on SP1's ground instances in both; the three instances' parent, parameters and textures as saved. |
| **Board** | `board/rp2-board.png` (3000×6576; JPG copy `rp2-board.jpg`). Bands: the top band sets the SOURCE picture (scaled to fit, labelled SOURCE) beside the two RENDER framing panels; then RENDER (6 pairs), DETAIL (1:1 crops, 729 px wide), PROBE (job 209's in-memory comparison) and DIAGNOSTIC (regions and median colours, labelled as not rendered). |
| **Preservation** | At 12:56:47 UTC: Codex's 1,980 records: all 1,976 project files match (the 4 engine files on A: are compared between this task's first and last job stamps, unchanged); SP1's 12 reviewed artifacts match; all 2,125 project files of this task's first stamp unchanged; six job stamps byte-identical (`9F5E0714…`); 17 named files (picture, live map, 11 earlier preview maps, 4 saves) match Codex's records. |
| **Processes** | 8 engine processes, all owned, all exited; `OWNED_PROCESSES_LEFT=0` after every job. Crash-reporter folders: 8, all the GameFeatureData ensure at startup (6 in `user/`, 2 in `user-gui/`). |

## 2. Base, identities and the rendered comparison

**Base.** SP1 `333A3A44…` with its receipt `F6BA8E00…` ending "applied" at those bytes (checked by every lifecycle step).

**Identities** (`plan/rp2_identity.json` `CAFAF6E2…`, written by `analysis/rp2_make_plan.py identity` before any engine run): exactly SP1's 54 planned rocks, 18 per mesh family, 0 problems. Each rock's object name, label, class and mesh equals both SP1's receipt (last "applied" identities) and RS1's receipt, RS1's recorded role is "rock", and SP1's planned slot 0 is the family's `MI_SP1_Rock_*`. Shared tags alone select nothing. In the level the tool also requires `IB_GarrisonRearShore` and the expected slot state (SP1's guard, unchanged), and `read_plan` re-checks the 54 identities against SP1's receipt bytes in every process.

**Which rocks the views show** (the recorded rock positions projected into each camera): the close-ups centre on `IBGC_RS1_Rock_050` (01), `_049` (02) and `_051` (Eroded). The rear-strip camera looks along the wall at `_035` (01), `_036` (Eroded) and `_037` (02); 035 and 036 are partly behind a tree, so the shade measurement is of 037 alone (the choice file calls it "wall rocks").

**The comparison** (job 209, 12:04–12:09 UTC; one GUI session on SP1; never saved; editor exit 0). `tools/ib_garrison_rockpalette_lookprobe.py` (`4F443E4C…`) selected the 54 rocks by key, label, tag and slot (54 selected, 0 refused, 18 per family), put dynamic instances parented to SP1's own three rock instances on them, and set only the colour parameters (`plan/rp2_candidates.json` `832CBBF6…`):

| Set | 01 and 02 | Eroded | Tint (all) |
|---|---|---|---|
| V0 = SP1 | gain 0.22, gamma 1.3 | gain 0.22, gamma 1.3 | (1.00, 0.95, 0.93) |
| C1 (the brief's starting point) | gain 0.22, gamma 1.3 | gain 0.60, gamma 1.0 | (0.96, 0.97, 1.00) |
| C2 | gain 0.21, gamma 0.65 | gain 0.60, gamma 0.65 | (0.86, 0.93, 1.00) |

Desaturation 1.0, roughness 0.9 and normal strength 1.0 in every set (C1 and C2 read back exactly from the dynamic instances; V0 is SP1's own instances, whose values are in SP1's manifest). Six cameras each (18 stills): the three families close up in low sun with cast tree shadows, the rear-strip wall rocks in the wall's shade, the backlit left rim, and the right coast from the air. Every rock got its SP1 instance back before quitting (54/54 verified identical); nothing was dirty at exit.

**Measurement** (`analysis/rp2_measure.py`, `analysis/rp2_measure_look.json` `4BA1BDCB…`). Fixed rectangles traced inside each rock (and a nearby grass or concrete-wall patch as an unchanged reference), the same for every variant of a camera. A difference mask was tried first and discarded, its output overwritten: the clouds and exposure moved between shots, so most of each frame registered as changed. Because the light drifted (the sky patches in job 209 differ by up to 123 levels between variants), the rock is compared with the reference patch in the same frame:

| View | V0 = SP1 | C1 | C2 |
|---|---|---|---|
| Eroded: rock/grass luminance ratio; pixels below 25 | 0.45; 20.5 % | 0.51; 18.2 % | **0.67; 10.7 %** |
| 01: ratio; pixels below 25 | 0.53; 17.0 % | 0.67; 13.5 % | **0.75; 8.7 %** |
| 02 in sun: rock R−B minus grass R−B | +23 | +11 | **+7** |
| Wall rock 037 (02) in shade: rock R−B minus wall R−B | +5 | +1 | −1 |
| Pixels above luminance 215 (any view) | 0 | 0 | 0 |

**Choice: C2 for all three families** (`plan/rp2_choice.json` `EB6D5720…`). By eye and by these numbers C1 left the eroded rocks dark brown and SP1's crushed lows on 01; C2 lifted the mid-tones, kept the crevices dark and did not bring back white tops. No third set was rendered (the brief allows two).

**The saved setting is the rendered one.** `rp2_make_plan.py plan` wrote `plan/rp2_material_spec.json` (`63D12EC5…`) and `plan/rp2_plan.json` (`32ACD2FD…`). For each family it compares SP1's parameters plus the choice with what job 209 read back from the rendered C2 instance (all six parameters, to 1e-6), checks that instance's parent was the family's `MI_SP1_Rock_*` (so the textures were SP1's) and that it was on all 18 rocks; any difference refuses the plan. It sets only the parameters that change (gain, gamma, tint).

**Caveat found later.** In job 211's same-light pair (section 5) the 02 change is smaller than job 209 suggested (rock R−B minus grass R−B +22 → +12, not +23 → +7), and the eroded change larger (ratio 0.44 → 0.94, not 0.45 → 0.67): job 209's numbers mix the material change with the moving clouds. Job 211 rendered only the chosen set, so it confirms C2 against SP1, not against C1; the C2-over-C1 ranking rests on job 209's comparison above.

## 3. The three instances (job 210, processes "prepare" and "copy")

- **prepare / material** (12:34:07 UTC): duplicated `MI_SP1_Rock_01` / `_02` / `_Eroded` (each first checked at its recorded bytes) into `ShorePalette2_Materials/`, set gain, gamma and tint from the spec, checked parent and all parameters against SP1's values plus the spec, saved only the three packages.
  - Dirty packages before the save: exactly the three new instances.
  - SP1's map, receipt and seven materials re-hashed after the save: unchanged. The folder holds exactly the three files.
- **copy / material-verify** (new process, 12:34:49): the three reload with parent `M_SP1_Rock`, the spec's values, SP1's roughness, normal strength and textures, and their recorded bytes; 0 issues; nothing dirty after load.
- **Job 211** read them again in the GUI after loading SP2: the same parent, parameters and textures. The shared parent `M_SP1_Rock` (unchanged): 25 nodes; 217 pixel-shader instructions, 2 pixel texture samples, 3 samplers.
- 0 compile or material error lines name an SP1 or SP2 asset in any process.

## 4. Lifecycle (job 210)

Tool: `tools/ib_garrison_rockpalette.py` (`12DA0125…`), derived from SP1's lifecycle tool (unchanged; nothing imported from SP1's folder). Steps are batched: six commandlet processes, each starting with its own fresh first read of the map it checks; a failed step stops the rest of its process. Each process used the isolated UserDir `user/`, ran 47–53 s and exited 1 (the known ensure). Job: 12:33:12–12:38:49 UTC.

| Process | Steps and result |
|---|---|
| prepare | **basefp**: SP1 loaded first in the process: 3,543 actors, 3,570 components, relative transforms read on 3,570; 20 editor-only skipped; digest `67BE42A2…`. **material**: section 3. |
| copy | **material-verify**: 0 issues. **copy**: SP1 duplicated to SP2 `D3ACFE7F…`; SP1 and the live map unchanged. |
| apply | **copy-verify**: the process's first read of SP2 = SP1's fingerprint, **3,543/3,543 identical**; receipt "created". **apply**: source check = that first read (0 unexpected); preflight 0 conflicts; slot 0 set on the 54; whole-state check against a settled second read: 108 changed values (54 × materials/overrides), **0 unexpected**; saved `76C1CB63…`; receipt "applied". |
| restore | **verify**: fresh first read: 3,489 identical, 54 differ (all planned, only the two slot fields), **0 unexpected**; nothing dirty. **repeat** (apply's own branch for an already-applied map, run directly): **a no-op**: "already applied and verified", nothing saved, map and receipt unchanged, nothing dirty. **restore**: preflight 0 conflicts; SP1's exact instance back on exactly the 54 (108 values, 0 unexpected); saved `2BDCFE58…`; receipt "restored". |
| reapply | **verify**: restored state **3,543/3,543 identical to SP1; fingerprint digest = SP1's `67BE42A2…`**. **apply**: as before; saved `68CA73DE…` (final); receipt "applied". The ownership manifest (`50EB1A92…`) is identical to the first apply's. |
| final | **verify**: 3,489 identical, 54 differ (only the two slot fields), 0 unexpected; digest `F0509F98…`, the same as the first applied state's. |

**Bytes.** The restored file differs in bytes from the created copy, and the re-applied file from the first applied one; a save re-serialises the package (as in SP1, job 207). The equality checks are the fingerprint comparisons and digests above.

**Read settling.** The same single in-memory value SP1 and SR2 documented: `IB_Harbor_Surface`'s collision profile reads `Custom` first and `BlockAll` afterwards. Every fresh process compares its first read (which reads `Custom` in the base fingerprint too); in-process transition checks use the settled second read.

**Ownership.** The identity guard is SP1's (`pieces_of` / `preflight`, unchanged), so the engine refusal tests were not repeated. The new batching (first-read reuse, stop on failure) has no engine refusal test in this pass; before job 210 I tried it only offline against a stand-in for the editor API, which is not kept as evidence.

## 5. Final paired session (job 211)

**Setup.** `tools/ib_garrison_rockpalette_check.py` (`B51CF6A8…`), 12:38:52–12:43:07 UTC. One GUI editor session (`-UseFixedTimeStep -FPS=30`, isolated `user-gui/` UserDir, autosave read back False for all three settings, background CPU throttle off for the session only, in memory). It loaded SP1 from disk, took 7 stills, loaded SP2 from disk, took the same 7. Nothing was spawned, moved or saved; no package dirty after either load or at exit.

**Same light.** Job 209 showed the sun does not move but the clouds do. Job 211 therefore schedules by ticks, not seconds: each load starts a new world clock, and both maps follow the same schedule. The engine's own frame numbers in its log put both maps' screenshots at identical offsets after their map load (1,325, 1,585, … 2,885 frames). (The script's own counter, which misses the frames spent on each screenshot, recorded 1,325–2,855 and 1,320–2,850.) Measured result: sky patches agree within 0–2 levels in all six views; the unchanged grass and wall reference patches within 0–1.4 levels of luminance.

**Cameras.** The three families close up (Rock_050 01, Rock_049 02, Rock_051 Eroded), the rear strip in the wall's shade (wall rocks 035–037; 037 unobstructed), the backlit left rim, the right coast from the air, and the reference-fit eye (7680×4320, reprojected into the picture's framing on the board).

**Measurements** (`analysis/rp2_measure_final.json` `E70F89D6…`; same regions as job 209; diagnostics of the stills, not renders):

| View | Median sRGB SP1 → SP2 | Rock / reference luminance | Pixels below 25 | Sunlit quarter R/B | Shaded quarter |
|---|---|---|---|---|---|
| Eroded close (Rock_051) | (45, 33, 22) → (92, 73, 51) | 0.44 → 0.94 | 21.5 % → 8.8 % | 2.07 → 1.68 | (21, 16, 12) → (43, 35, 27) |
| 01 close (Rock_050) | (48, 45, 44) → (48, 49, 52) | 0.52 → 0.57 | 17.2 % → 11.4 % | 1.71 → 1.51 | (20, 19, 20) → (25, 26, 30) |
| 02 close (Rock_049) | (144, 113, 81) → (141, 118, 89) | 1.61 → 1.69 | 0.7 % → 0.1 % | 1.76 → 1.56 | (116, 88, 62) → (119, 98, 73) |
| Wall rock 037 (02) in shade | (30, 28, 30) → (31, 32, 36) | 0.73 → 0.82 | 31.6 % → 15.2 % | 1.03 → 0.89 (wall patch median 0.90) | (20, 18, 20) → (23, 24, 27) |
| Backlit rim | (21, 20, 20) → (22, 22, 24) | – | 92.3 % → 72.5 % | – | – |

Pixels above luminance 215: 0 in every region, before and after. The 01 region is mostly in a tree's cast shadow, so its median is a shaded value.

**What the pairs show.**

- **Eroded:** from crushed black-brown to a medium grey-brown stone with visible strata, light edges and dark crevices.
- **01:** lighter, cooler taupe-grey; more detail inside the cast shadows.
- **02:** in direct low sun still sand-beige; slightly lighter and less saturated than SP1. The smooth former-snow faces dominate this mesh.
- **Shade:** wall rock 037 changes from brown to the slate grey of the wall beside it; still dark, like everything in that shade. Where they show between the leaves, 035 (01) goes from beige to grey and 036 (Eroded) from near-black to dark grey (seen in brightened crops; not measured).
- **Backlit rim:** silhouettes; almost no visible change.
- **Right coast from the air:** the near-black eroded rocks along the rim are now mid taupe-grey, still darker and browner than the 01/02 rocks beside them; the rim no longer has black gaps.
- **Reference framing:** at that scale the rocks are a few pixels each; the scattered terrace rocks and the right rim turn from brown to grey.

**Board.** `board/rp2-board.png` (3000×6576, `2976CCA8…`; JPG `CEC5E95F…`), built by `analysis/rp2_board.py` from the original stills in `check-sp2/editor/` (14 PNGs, kept). The only non-render image is the approved picture, labelled SOURCE and scaled to fit, in the top band beside the two RENDER framing panels; every other panel is labelled RENDER, DETAIL, PROBE or DIAGNOSTIC.

## 6. Preservation, processes, logs and autosave

**Preservation.** `hashes/preservation-final.json` (`265E6240…`, 12:56:47 UTC, recorded after the last evidence write, from `analysis/rp2_preservation.py`):

- **Codex's 1,980 records** (`20261001-codex-shorepalette-review/protected-current.json`, checked 11:50:14): 1,976/1,976 project files match. The four engine files on A: (BasicShapes Cube and Cylinder, WorldAlignedTexture, WorldAlignedNormal) are not reachable from the desktop check; they are compared between this task's first and last Windows-side job stamps (12:04 and 12:43 UTC) and are unchanged.
- **SP1's 12 reviewed artifacts** (`artifacts-current.json`): map, receipt, checks, board, material manifest, seven materials: all match.
- **This task's first stamp** (job 209, before any SP2 engine run; 2,129 files: the 1,980, which include the four engine files, plus SP1's map, receipt, seven materials and completed evidence without its engine UserDirs, and Codex's SP1 review folder): all 2,125 project files unchanged.
- **All six stamps** `hashes/shared-{before,after}-{209,210,211}.json` are byte-identical (`9F5E0714…`). Every job printed `SHARED_ASSET_OR_SAVE_CHANGES=0` and `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`; only job 210 wrote preview files (the SP2 map and the three instances).
- **Named files:** the picture, the live map `FAFFD601…`, the 11 earlier preview maps and the four saves match Codex's records.

**Processes and logs.** `analysis/log_check.json` (`AC80D40A…`):

- 8 engine processes, all owned: job 209 GUI (exit 0); job 210's six commandlets (exit 1, the known ensure); job 211 GUI (exit 0xC0000005).
- **Job 211's exit.** The session finished (14/14 stills, 0 errors, records saved), the log ends "Log file closed" at 12:42:55 UTC, and the process then returned 0xC0000005 with no crash-reporter folder. This is the exit-time crash already seen after closed logs in SR1 job 193, PF1 job 146 and FF1 job 163; per the brief it was not investigated. Both maps and every protected file were re-hashed after it: unchanged.
- All 8 logs end with "Log file closed"; 0 access-violation, critical or fatal lines; 0 Python errors; 0 SP2 refusals.
- Error lines are the pre-existing kinds only: the GameFeatureData ensure block in every process, and 7 BP_Mech compile errors in each GUI run.
- Compile lines: 2, both the pre-existing `M_AI_Foam` warning (one per GUI run); 0 name an SP1 or SP2 asset.
- Crash-reporter folders: 8, all "Ensure condition failed: AssetBaseClassLoaded" at startup (6 in `user/`, 2 in `user-gui/`).

**Autosave.** The isolated per-user settings in `user-gui/` set all three autosave flags False (still False after the editor rewrote that file); both GUI sessions read them back False with the C++ property names. The only file in `user-gui/Saved/Autosaves/` is the editor's `PackageRestoreData.json` (96 bytes, rewritten at each GUI exit); no package was autosaved.

## 7. Every write

**Content** (preview only): `_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette2.umap` and the three instances in `_GarrisonPreview_Disposable/ShorePalette2_Materials/`.

**Saved:**

- The receipt `GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette2.json`.
- The job runner: `zz_job/rockpalette_lib.ps1` (`227D6F8D…`); jobs 209–211 (now in `zz_job/running/`, each `.exit` = 0: the job scripts, not the engine exits); their logs and empty `.err.log` files in `zz_job/logs/`; the runner's own `current.txt`.
- The evidence folder `GarrisonRestructure/20261001-claude-rockpalette/`: 89 files, 238 MB, not counting `hashes/preservation-final.json` and the engine UserDirs: `tools/`, `analysis/`, `plan/`, `lookprobe/` (18 stills), `run1/` (step reports, fingerprints, manifests, logs), `check-sp2/` (14 stills, 124 MB, `rp2_checks.json` `FF5BD6BA…`), `board/`, `hashes/`, `protected-1980.json`. No Python bytecode cache.
- The isolated UserDirs `user/` and `user-gui/`: engine scratch, the ensure reports, settings and the restore file above.

**Docs:** this file. **Claude outputs:** `CLAUDE_STATUS.md` (updated; backup in my desktop scratch).

Nothing else: no write under `Content/` outside the preview folder (scanned by every job), no SP1 file, no texture, mesh or shared material (all hashed), no Git. Project configuration is not in the stamps; the tools write none, and an mtime scan at 13:20 UTC found no file under `Config/` or `Saved/Config/` and no `.uproject` change since 12:00 UTC.

## 8. Remaining visible limitations

1. **Sunlit rock still reads warm.** In the map's low sun every lit rock face is beige: R/B about 1.5–1.7 (SP1: 1.7–2.1); 02, whose large smooth faces dominate, still reads sand-coloured. The albedo itself is now slightly cool (a fully desaturated texture times (0.86, 0.93, 1.00)), so the remaining warmth is the light, which this pass may not change. A cooler tint would push the shaded rocks blue: they already sit at the concrete wall's own cool cast.
2. **Shade is dark.** Wall rock 037 is lighter and neutral but still dark (median luminance 32, the wall 39), like everything in that shade. No eroded rock was measured in shade (036 is partly behind a tree).
3. **The 01/02 meshes keep their texture's character.** The former snow faces are smooth and fairly uniform; the eroded mesh has the most surface detail.
4. **Backlit views** show silhouettes; the palette change is not visible there.
5. **Rock form, shoreline, surf, sea and forest are unchanged** (outside this brief): small spiky rocks, straight slab edges, flat grey-teal sea and sparse broadleaf trees remain the larger differences from the picture.

## 9. Evidence index

Paths relative to `Saved/GarrisonRestructure/20261001-claude-rockpalette/`.

| File | SHA256 (first 16) |
|---|---|
| `plan/rp2_identity.json` | `CAFAF6E2DCF39309` |
| `plan/rp2_candidates.json` | `832CBBF64B28855E` |
| `plan/rp2_choice.json` | `EB6D5720C549BC20` |
| `plan/rp2_material_spec.json` | `63D12EC54B26EB4F` |
| `plan/rp2_plan.json` | `32ACD2FD440230FE` |
| `lookprobe/rp2_lookprobe.json` (job 209) | `1B2DFC3032554153` |
| `analysis/rp2_measure_look.json` / `rp2_masks_look.png` | `4BA1BDCB024BF162` / `A8D88DD7975A8643` |
| `run1/prepare/base_fingerprint.json` | `30FFF3A84B3EBE18` |
| `run1/prepare/material_manifest.json` | `F37A892055EF9A8B` |
| `run1/apply/copy_fingerprint.json` | `2ECA6ED541B505A2` |
| `run1/reapply/ownership_manifest.json` (= `run1/apply/…`) | `50EB1A9270A18DD2` |
| `run1/final/rp_verify.json` | `6768D8CA96C1092E` |
| `check-sp2/rp2_checks.json` (job 211) | `FF5BD6BA1A317C30` |
| `analysis/rp2_measure_final.json` / `rp2_masks_final.png` | `E70F89D6E876A170` / `F8D6BF91ECBE6820` |
| `analysis/framing/rp2-reference-framing-before-SP1.png` / `-after-SP2.png` | `FCCD540293EA874B` / `AFD2A42537E31381` |
| `board/rp2-board.png` / `.jpg` | `2976CCA89E40C6A8` / `CEC5E95FCA636178` |
| `analysis/log_check.json` | `AC80D40AEAEDB25A` |
| `hashes/preservation-final.json` | `265E624055FB6B97` |
| `tools/ib_garrison_rockpalette.py` / `_check.py` / `_lookprobe.py` | `12DA012573F82F98` / `B51CF6A8D4550100` / `4F443E4CF4F42179` |
| `analysis/rp2_make_plan.py` / `rp2_measure.py` / `rp2_board.py` / `rp2_log_check.py` / `rp2_preservation.py` | `BCF39627E3ACC2DD` / `7D58A7AF73B6FD66` / `48761645A39A4772` / `4215D30F8B8A1B63` / `447403FBCF98DE95` |
| `Saved/zz_job/running/209-rp-lookprobe.ps1` / `210-rp-lifecycle.ps1` / `211-rp-check.ps1` | `B4C1E3FA63227F50` / `5337FA5A237ADF45` / `71714E78BABB1535` |
| `Saved/zz_job/logs/209-…log` / `210-…log` / `211-…log` | `981CBBD407D89B12` / `F009EDC73463539F` / `CB0C071C85A04911` |
