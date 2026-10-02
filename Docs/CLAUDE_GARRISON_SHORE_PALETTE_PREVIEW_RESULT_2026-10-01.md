# Garrison SP1 shore palette preview: result (2026-10-01)

**Brief:** `Docs/CLAUDE_GARRISON_SHORE_PALETTE_PREVIEW_2026-10-01.md` (Codex, after accepting SR2 at 09:51:12 UTC).
**Status:** DONE. Stopped for Codex's review. Disposable candidate only: no live promotion, no shared write, no Git.
**Evidence:** `Saved/GarrisonRestructure/20261001-claude-shorepalette/` (index in section 10).

**Summary.**

- **What SP1 changes.** One thing: slot 0 of `StaticMeshComponent0` on the 136 RS1 natural-terrain pieces now uses one of five new preview-local material instances instead of the four shared `M_AI_Mountain*` masters:
  - 43 land + 9 terrace: `MI_SP1_Ground_Land`;
  - 30 coast (28 coast bands and the 2 wall bands): `MI_SP1_Ground_Coast`;
  - 54 rocks: `MI_SP1_Rock_01` / `_02` / `_Eroded`, chosen by each rock's RS1-recorded mesh (18 each).

  Everything else is identical to SR2: 3,407 of 3,543 actors are identical, and the 136 differ only in that slot's `materials` / `overrides`. There are 0 unexpected differences. No actor transform, mesh, collision setting, visibility, tag or folder changed. The fingerprint compares actor transforms; component-relative transforms are not in it, but the tool's only write is `set_material` on slot 0. So Connor's hangar reservation, the side bands and the approach are exactly SR2's.
- **Why new masters.** The four current terrain masters have no parameters at all (job 204: 0 scalar, vector and texture parameters each), so an instance of them cannot change anything.

  The other terrain-like materials in the project do not fit either (offline name-table scan, section 2.3):
  - the Iceland mountain master is a snow-line material driven by runtime virtual textures;
  - the auto-landscape master works only on Landscape actors;
  - the AI landmass instances are flat single colours.

  So I duplicated the two current masters into `ShorePalette1_Materials/` and replaced their graphs with built-in nodes. Every texture is an existing Iceland-environment texture, referenced read-only.
- **The ground** (`M_SP1_Ground`).
  - **Mapping.** The mapping is world-aligned, so nothing is stretched across the huge slab faces and the texture runs on across neighbouring slabs. The mapping moves no surface.
  - **Layers.** Grass and forest floor are mixed by a large-scale mottle (30 m) taken from the Iceland plateau texture. Desaturated mossy creek stone covers steep faces, and on the coast instance it also fills the darker mottles.
  - **Detail.** Normals and roughness come from the same layers.
- **The rocks** (`M_SP1_Rock`). Each rock keeps its own mesh's baked colour and normal maps. The snow-white baked colour becomes desaturated, darker grey, and the crevices stay dark.
- **Result** (job 208: one GUI session, SR2 then SP1 from disk, 13 identical cameras).
  - **Ground: clearly closer to the picture.** The stretched gold streaks are gone. At foot level the ground shows grass and forest-floor detail with mottling, and grey stones along the coast band. No slab seam shows as a texture break.

    In the picture's own framing, the median colour of the changed ground pixels moved from SR2 (156, 128, 72) to SP1 (91, 90, 60). The picture's inland olive is (87, 86, 61).
  - **Rocks: improved but not yet the picture's light grey rock.** They are no longer snow-white. The two mountain meshes read as warm taupe-grey stone with dark crevices.

    In the picture's framing, the formerly white rock pixels went from (201, 185, 167) to (138, 117, 96); the picture's grey shore band is (129, 123, 124). That is similar brightness but warmer, under the map's low warm sun.

    The 18 eroded-mesh rocks render darker than in SR2: their baked texture is already dark, and the shared darkening made it darker still. In shade and from the air the rocks now read dark and low-contrast. Section 9 gives the exact per-instance correction; I did not run it, because the brief allows one final render session.
- **Lifecycle PASS** (job 207, 15 processes):
  - material authoring, then reload verify;
  - copy (3,543/3,543 identical), apply and save;
  - a repeat apply on the saved state was a no-op (nothing saved, byte-identical);
  - fresh-process verify (only the 136 planned slots differ);
  - exact restore to SR2: 3,543/3,543 identical, and the fingerprint digest equals SR2's own (`B211C5AD…`);
  - re-apply, three ownership negatives, final verify.

  The negatives were re-run because the identity guard is new. It uses RS1's recorded identities and tag, not SR2's shells.
- **Exits and preservation.**
  - Job 208's editor exited **0 (0x00000000)**; the log closed at 10:56:35 UTC.
  - The 10 job stamps of 1,980 protected files are byte-identical, and the live map `FAFFD601…` is unchanged.
  - At 11:35 UTC Codex's 1,560 records match (1,558/1,558 project files), and so do SR2's six reviewed artifacts, the picture and the four saves.
  - 0 compile errors name an SP1 asset.
  - Autosave was read back **off** in jobs 206 and 208: enable flag in 206, all three flags in 208. Job 205's read-back failed. In every GUI run, no package was autosaved (section 7).
- **Disclosures.**
  - Job 205's look comparison stopped at the material build. In UE 5.8, `delete_all_material_expressions` removes only every other node per call (65 → 32 left). Job 206 repeated the comparison with a clear that loops until none is left.
  - The rock setting was not part of the look comparison. It was derived from V2's measured render and first rendered in job 208.
  - Both duplicated masters had their graphs rebuilt completely, not adjusted. The selection numbers and the candidate scan were recorded after authoring (section 4).
  - Python wrote `tools/__pycache__/` (UE's interpreter and my plan script on the desktop).

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette1`<br>`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette1.umap`, 6,064,936 bytes<br>SHA256 `333A3A4463B0A1A1F4CD00C804637BE2F5CA2DB101FCB9AD6AEC648306B01C20` (SP1 applied)<br>Copied from SR2 `0267B9A353D1877D6DA6463798E6CF356976C183C0BF97812767EF3FF3713EC2`, which is unchanged. |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette1.json`, 93,946 bytes<br>SHA256 `F6BA8E00CEBEEA1FC8732D64B3356FF4F08B8C40C3AA4BA47B75CFEA2E1C68D9`<br>History (UTC):<br>• created `A4C6762E…` 10:41:08<br>• applied `868FADCF…` 10:41:59<br>• restored `105C1514…` 10:44:26<br>• applied `333A3A44…` 10:46:02<br>It records the plan `DA89E3E3…`, the material manifest `C4CA8E44…`, the SR2 base fingerprint file `A3F65197…`, the copy fingerprint `2DBB0C51…` (digest `B211C5AD…`, the same as the base's), SR2's receipt `44AEE146…`, the 136 identities and the exact override diff. |
| **New material assets** (only these, only in `/Game/_GarrisonPreview_Disposable/ShorePalette1_Materials/`) | `M_SP1_Ground` (Material; duplicate of `M_AI_MountainGround`, graph replaced, 108 built-in nodes): 58,705 bytes, `B0B9D79B739293A08E5958E141F80445E5B79C9BE7DA078FE8548E00A31F08E0`<br>`M_SP1_Rock` (Material; duplicate of `M_AI_MountainRock_01`, graph replaced, 25 nodes): 17,884 bytes, `058459D5581A4EB24142565F3E5D579CE14A7591F31CC89592717A7E5C6A66B0`<br>`MI_SP1_Ground_Land`: 10,877 bytes, `464356901A7BA16005256A47FC0E009BBE0413DD8191524406A261617EA9029B`<br>`MI_SP1_Ground_Coast`: 10,882 bytes, `0B30C52BE149241401B822913EEB0AAE8713B23654D5E9B16145D6C645317384`<br>`MI_SP1_Rock_01`: 7,010 bytes, `CB33D04E594CEECB490FAEE042B13BC1C7D5BE2C1F3051D02EEB86133DE0C3BB`<br>`MI_SP1_Rock_02`: 7,010 bytes, `7AC46A68BF4A0748117310E3A441C256064C913171B88FF8EFA0CF7C7DEDC93F`<br>`MI_SP1_Rock_Eroded`: 7,044 bytes, `8DF309E3B265586F293A4E87DE9D8263F1D878A279BDC79E30D5E6923ED8FF83`<br>Manifest `run1/material/material_manifest.json` `C4CA8E44BA7D2867021603B26C584758AF6A6ED4C342BACDC220014944D4E456`. Both parents keep their source master's domain, blend mode, shading model, two-sided, tangent-space normal, usage and world-position-offset settings (identical flags recorded). |
| **Diff vs SR2** | 3,543 actors, as in SR2. **3,407 identical; 136 differ, only in `StaticMeshComponent0.materials` / `.overrides`; 0 unexpected.**<br>The comparison covers each actor's:<br>• label, class, location, rotation, scale, hidden, actor collision, tags and folder;<br>• per component: class, visibility, collision profile, collision enabled, mesh, materials and overrides (3,570 components). |
| **Override diff** | Exact, from the receipt (section 5). Slot 0 of `StaticMeshComponent0`:<br>• land 43 + terrace 9: `M_AI_MountainGround` → `MI_SP1_Ground_Land`<br>• coast 30: `M_AI_MountainGround` → `MI_SP1_Ground_Coast`<br>• rock 18: `M_AI_MountainRock_01` → `MI_SP1_Rock_01`<br>• rock 18: `M_AI_MountainRock_02` → `MI_SP1_Rock_02`<br>• rock 18: `M_AI_MountainRock_Eroded` → `MI_SP1_Rock_Eroded`<br>In every case materials = overrides = the one listed instance. |
| **Not touched** | Every other user of the four shared masters stays on them: `M_AI_MountainGround` 45 (`CityGround_00`–`43` and `MountainGroundPad`); `_Rock_01` 42, `_Rock_02` 55 and `_Rock_Eroded` 47 (the background `Peak` actors). Job 208 checked this in SR2 and in SP1.<br>Source materials, textures and meshes are byte-identical before and after every job. They are part of the 1,980-file stamp: the whole `AITextures` and `IcelandEnviroment` folders plus the engine shapes and functions. |
| **Lifecycle** | **PASS** (job 207; section 5) |
| **Paired renders** | Job 208, one GUI session: SR2, then SP1 from disk.<br>• 13 cameras × 2 = 26 stills: 24 at 1920×1080, plus the reference-fit eye at 7680×4320.<br>• After reload: 136/136 slots at the SP1 instances; parents, outputs, parameters and textures as recorded.<br>• Shader statistics: ground 313 PS instructions / 11 samplers; rock 217 / 3.<br>• 0 compile errors naming SP1; 0 dirty packages at exit. |
| **Board** | `board/sp1-board.png` (3000×6791; JPG copy `sp1-board.jpg`). Bands, kept apart:<br>• SOURCE: the picture, scaled to fit<br>• RENDER: the reference framing and 12 pairs<br>• DETAIL: exact 1:1 crops, 729 px wide<br>• PROBE: the in-memory comparison<br>• DIAGNOSTIC: masks and median colours, labelled as not rendered |
| **Preservation** | At 11:35 UTC:<br>• Codex's 1,560 records: **1,558/1,558 project files match**. The 2 engine BasicShapes are compared by the jobs' own stamps.<br>• All 1,976 project files of this task's first stamp: 0 changed.<br>• All 10 before/after stamps (jobs 204–208) byte-identical (`421BEC92…`, 1,980 files each).<br>• Live map `FAFFD601…` unchanged.<br>• SR2's six reviewed artifacts, the approved picture and the four saves match Codex's records. |
| **Processes** | 19 engine processes, all owned, all exited; `OWNED_PROCESSES_LEFT=0` after every job.<br>• 16 commandlets: exit 1 = the known GameFeatureData ensure.<br>• 3 GUI runs: exit 0.<br>Crash-reporter folders: 19, all the GameFeatureData ensure at startup. |
| **Remaining** | • Rocks warmer and, for the eroded mesh, darker than the picture's light grey.<br>• Small, spiky, sparse rock meshes.<br>• Physical slab edges.<br>• The khaki non-RS1 ground beyond RS1.<br>See section 9. |

## 2. Eligible identities and material choice

### 2.1 Identities (job 204; read-only commandlet; nothing saved)

The probe loaded only SR2 and confirmed every eligible piece against RS1's own records:

- RS1's receipt (file `0033AAD5…`): its last `applied` entry (map `882F9D20…`), 284 identities;
- RS1's engine plan r2: `9711DEBA…`, the roles.

**136 eligible: land 43, coast 30 (28 coast bands + 2 wall bands), rock 54, terrace 9.** Each one was checked as follows:

- label, class, mesh and object name equal RS1's record;
- it carries `IB_GarrisonRearShore`;
- it has a single component `StaticMeshComponent0` with one slot, overridden to the RS1 material.

Problems: 0. Actors carrying the RS1 tag but not recorded by RS1: 0. RS1-tagged actors: 284; the other 148 are RS1's 74 tree trunks and 74 canopies (RS1 plan r2 roles), which SP1 does not touch.

Rock meshes: `SM_Mountain_01`, `SM_Iceland_Mountain_02` and `SM_Iceland_Eroded_Mountain`, 18 of each.

Plan: `plan/sp1_plan.json` (`DA89E3E3…`, generated by `analysis/sp1_make_plan.py`). It holds each piece's exact before/after slot state, plus the other users of the four masters, which must stay unchanged.

### 2.2 Why the current look is wrong

- `M_AI_MountainGround` (65 nodes) samples the khaki grass texture with UV0. On RS1's cube slabs, which are up to 146 m long, UV0 stretches it into the flat gold, streaked ground of SR2.
- `M_AI_MountainRock_*` (35 nodes each) shows each mountain mesh's baked texture. That texture is snow-covered, hence the icy white rocks.
- None of the four has a parameter.
- All four are shared with the CityGround slabs, `MountainGroundPad` and the background peaks, so they must not be edited.

### 2.3 Existing materials considered

`analysis/existing_material_candidates.json` (`31E82831…`, from `analysis/sp1_candidate_scan.py`) is a read-only scan of each asset's name table; no engine was run.

| Candidate | What it is | Why not instanced |
|---|---|---|
| `M_AI_MountainGround`, `M_AI_MountainRock_01` (scanned); `_02`, `_Eroded` (job 204's probe only) | the current RS1 materials | no parameters (job 204, all four) |
| `M_Iceland_Mountains` and `MI_Iceland_Mountains_01` (its siblings `_02`–`_06` not scanned) | snow-line mountain master: `Snow`, `Snow_Line`, `SnowSlopeAngle`; samples runtime virtual textures `RVT_Blend` / `RVT_Height` | snow look; depends on RVT volumes not in this level |
| `M_AutoLandscape` and `MI_Landscape_Mountain` (`MI_Landscape_Arctic` not scanned) | landscape layer-blend material (`/Script/Landscape`, grass types) | Landscape actors only; RS1's terrain is static-mesh cubes |
| `MI_Landmass_Beach / Mountain / MountainFar` | instances of `M_FlatCol` (one `Color` parameter) | a uniform flat tint, which the brief rules out |

## 3. The materials

### 3.1 How they work

Both graphs are built by `tools/ib_garrison_shorepalette_material.py` (`B5FC2611…`) from built-in nodes only. The brief allowed duplicating a master and adjusting native nodes. I replaced each duplicate's graph completely, because the source graphs sample by stretched UV0 and expose no parameters. Only base colour, roughness and normal are driven. There is no world-position offset, displacement, opacity or emissive; the builder checks this, and each output is fed by a node it created.

**M_SP1_Ground** (108 nodes):

- **Projection.** World-aligned, in cm. Faces with |normal.z| < `SP1_SteepZ` (0.6) use world XZ or YZ, whichever plane they face. All other faces use world XY. One sample per texture.
  - Tiles: grass 4 m, forest floor 3 m, stone 2.5 m, macro mottle 30 m.
  - It moves no surface. Adjoining slabs at the same height continue the same texture.
- **Colour.**
  - Grass: `T_Iceland_Grass_BaseColor`, tinted (0.36, 0.56, 0.70).
  - Forest floor: `T_ForestGround_A`, tinted (0.85, 1.45, 1.80).
  - The two are mixed by a mottle mask m = sat((lum(macro) − 0.074) × 16 + 0.5). The macro is `T_Iceland_Plateu_Base_Color` at 30 m; it also adds 30 % of its own colour variation.
  - Stone: `T_MossyCreekStones_A`, 80 % desaturated and tinted (0.75, 0.78, 0.85). It covers steep faces (`SP1_BankStone` 1). On the coast instance it also covers mottles darker than `SP1_StoneAmount` 0.45 (edge 4); on the land instance this amount is 0.
- **Roughness.** The layers' roughness (`T_ForestGround_R`, `T_Iceland_Grass_ORM`.G, `T_MossyCreekStones_R`) blended the same way, + 0.35, saturated.
- **Normal.** The layers' normal maps blended the same way, x/y × 0.8, rebuilt in the projection frame around the vertex normal, then World → Tangent.

**M_SP1_Rock** (25 nodes):

- **Textures.** The mesh's own baked base colour and normal: texture parameters `SP1_RockBC` / `SP1_RockN`, UV0, sampled as the source rock materials do. Each instance sets its mesh's pair:
  - `T_Mountain_01_*`
  - `T_Mountain_02_*`
  - `T_Iceland_Eroded_BaseColor` + `Iceland_Eroded_Normal`
- **Base colour.** lerp(c, lum(c), 1.0) × lum(c)^0.3 × 0.22 × (1.0, 0.95, 0.93).
- **Roughness** 0.9.
- **Normal** x/y × 1.0.

### 3.2 Verified in the engine

- **Material stage** (job 207, commandlet). It saved exactly the seven packages; the dirty set before saving was exactly those seven. Every instance parameter was read back equal to the spec (`plan/sp1_material_spec.json`, `8D26F0B5…`). The source masters and textures were byte-identical afterwards.

  The clear needed 6 delete calls for the ground and 5 for the rock (expression count after each):
  - ground: 65 → 32 → 15 → 7 → 3 → 1 → 0;
  - rock: 35 → 17 → 8 → 3 → 1 → 0.

  After the clear no output was left connected.
- **material-verify** (new process). After reload, the graphs, flags, parents, parameters and file bytes equal the manifest. 0 issues; nothing was dirty after load.
- **Job 208** (GUI, SP1 loaded from disk).

  | Parent | Pixel-shader instructions | Vertex-shader instructions | Pixel texture samples | Samplers |
  |---|---|---|---|---|
  | `M_SP1_Ground` | 313 | 148 | 13 | 11 |
  | `M_SP1_Rock` | 217 | 153 | 2 | 3 |

  All five instances have the right parent, parameters and textures. 0 "Failed to compile" or material-error lines name an SP1 asset. The one compile line in each GUI run is the pre-existing `M_AI_Foam` warning.

  The commandlet stages ran with -NullRHI, so their statistics read 0. They are recorded but not meaningful.

## 4. Look comparison and the chosen setting

**The comparison.** It is one small comparison, run in memory and never saved, on SR2's 136 pieces (`tools/ib_garrison_shorepalette_lookprobe.py`, `plan/sp1_look_variants.json` `63E3FB7D…`).

- **Job 205** (10:15–10:19 UTC; editor exit 0) took the V0 stills.
  - It then stopped at the material build: "32 expressions survived the clear", the UE 5.8 behaviour described in the summary.
  - Its tools as run are kept in `tools/job205-as-run/` (`F27CFDBD…`, `4622B35E…`).
- **Job 206** (10:25–10:30 UTC; editor exit 0) used the fixed clear and took V0 and V1–V3.
  - Five cameras each, 20 stills in all.
  - Restored all 136 overrides (136/136 verified identical) and quit without saving.
  - The probe-only package path was never written to disk.

| Variant | Ground (land; coast) | Rock | Overhead ground median (sRGB) |
|---|---|---|---|
| V0 = SR2 | (as is) | (as is) | (154, 127, 71) |
| V1 olive A | contrast 12; coast = land | desat 0.85, gamma 1.15, gain 0.60 | (100, 96, 60) |
| **V2 olive B** | contrast 16, darker tints; coast stone 0.45 | desat 0.92, gamma 1.25, gain 0.52 | **(86, 89, 64)** |
| V3 olive C | contrast 10, yellower; coast stone 0.30 | desat 0.75, gamma 1.10, gain 0.65 | (81, 83, 67) |

Picture's inland olive: (87, 86, 61). Numbers from `analysis/look_selection.json` (`7C582019…`); method in `analysis/sp1_look_selection.py`.

**The ground: V2.** It is the closest to the picture overhead and at foot level, and its stone mottling along the coast band gives a mottled, not straight-edged, transition to the shore.

**The rocks** in all three variants stayed light (V2's former snow tops: (203, 184, 165)). I therefore kept V2's rock graph and set:

- desaturation 1.0;
- gamma 1.30;
- gain 0.22;
- warm-grey tint (1.0, 0.95, 0.93).

In scene-linear terms that is about 0.42× V2's albedo. In display values the drop is smaller, because the tonemapper compresses highlights. Job 208's overhead, measured on the same band and pixels:

- former snow tops: (230, 217, 199) → (184, 156, 125);
- ground: (155, 128, 71) → (97, 96, 59).

This rock setting is the one value not seen before the final render.

**When the numbers were recorded.** I chose the setting between 10:31 and 10:36 UTC from job 206's stills: by viewing them, and with the same overhead measurement run without saving. `analysis/look_selection.json` (written 11:03) and the candidate scan (10:51) were recorded during the write-up, after the materials were authored at 10:37. The look-selection file reproduces the selection numbers from the same stills.

## 5. Lifecycle and ownership (job 207)

Tool: `tools/ib_garrison_shorepalette.py` (`317F6C82…`). It is derived from SR2's tool, which is unchanged.

- Each stage ran in its own commandlet process with the isolated UserDir.
- The job took 10:37–10:49 UTC.
- All 15 stages exited 1, the known ensure.

| Stage | Result |
|---|---|
| material / material-verify | Seven assets authored and saved; reload verified (section 3.2) |
| base-fingerprint | SR2 loaded first in the process: 3,543 actors, 3,570 components (20 editor-only skipped); digest `B211C5AD…` (SR2's own applied digest) |
| copy / copy-verify | Copy `A4C6762E…`: **3,543/3,543 identical** to SR2; receipt "created" |
| apply | Source check vs SR2: 0 unexpected.<br>In process: 272 changed values (136 × materials/overrides), 0 unexpected.<br>Saved `868FADCF…`; receipt "applied". |
| apply-repeat | Already applied and verified: **a no-op**. Nothing to change and nothing saved (`saved: false`); map byte-identical; receipt still 2 entries. |
| verify-applied (new process) | 3,407 identical, 136 differ (all planned, only the two slot fields), **0 unexpected**; digest `354AB40C…`; nothing dirty after load |
| restore | The level was exactly the applied state at the recorded identities. SR2's exact overrides were put back on exactly those 136 components (272 values back). Saved `105C1514…`. |
| verify-restored | **3,543/3,543 identical, 0 unexpected; digest `B211C5AD…` = SR2's base fingerprint = the created copy's** |
| reapply | As apply; saved `333A3A44…` (final); the ownership manifest (`13BFA10B…`) is identical to the first apply's |
| 3 negatives (table below) | All passed; nothing saved; map and receipt unchanged |
| verify-final | As verify-applied; digest `354AB40C…` again |

**Byte-level note.** The restored file (`105C1514…`) differs in bytes from the created copy (`A4C6762E…`), and the re-applied file from the first applied one. A save re-serialises the package, as in SR1 and SR2. The check is the fingerprint comparison.

**Read settling.** It is the same single value SR2 documented. `IB_Harbor_Surface` reads `Custom` first and `BlockAll` after the first material read, in memory only. Apply, restore, re-apply and the CB1 negative logged it. In-process checks use the settled read; fresh-process verifies read `Custom` again.

**Ownership.**

- A piece is SP1-edited only if all of these hold:
  - its object name, label, class and mesh equal RS1's recorded identity (RS1's receipt);
  - its RS1 role is land, coast, rock or terrace;
  - it carries `IB_GarrisonRearShore`.
- `IB_GarrisonCB1` alone never selects anything.
- An actor carrying `IB_GarrisonRearShore` that RS1 never recorded is a conflict.
- Manifest: `run1/apply/ownership_manifest.json` (`13BFA10B…`).
- This guard is new for SP1, so the negatives were run again.

| Ambiguity added in memory (saving blocked) | Outcome |
|---|---|
| An extra cube with only `IB_GarrisonCB1` and the SP1 land instance on slot 0 | Not selected; left untouched (slot still the SP1 instance). The level then differed from base + recorded overrides in 1 way, so the restore did not verify and nothing was saved. |
| `IBGC_RS1_Land_00` with its `IB_GarrisonRearShore` tag removed | RESTORE REFUSED: 1 conflict; nothing changed |
| An extra cube with both tags and an unrecorded label | RESTORE REFUSED: 1 conflict ("carries IB_GarrisonRearShore but is not one of RS1's recorded identities"); nothing changed |

**Exact override diff** (receipt, both "applied" entries; per piece in `plan/sp1_plan.json`):

```
component StaticMeshComponent0, slot 0 (materials = overrides, one entry)
land 43, terrace 9 : /Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround.M_AI_MountainGround
                  -> /Game/_GarrisonPreview_Disposable/ShorePalette1_Materials/MI_SP1_Ground_Land.MI_SP1_Ground_Land
coast 30           : .../M_AI_MountainGround.M_AI_MountainGround -> .../MI_SP1_Ground_Coast.MI_SP1_Ground_Coast
rock 18 (SM_Mountain_01)              : .../M_AI_MountainRock_01.M_AI_MountainRock_01 -> .../MI_SP1_Rock_01.MI_SP1_Rock_01
rock 18 (SM_Iceland_Mountain_02)      : .../M_AI_MountainRock_02.M_AI_MountainRock_02 -> .../MI_SP1_Rock_02.MI_SP1_Rock_02
rock 18 (SM_Iceland_Eroded_Mountain)  : .../M_AI_MountainRock_Eroded.M_AI_MountainRock_Eroded -> .../MI_SP1_Rock_Eroded.MI_SP1_Rock_Eroded
restored entry: each role back to its RS1 material (selection: RS1 recorded identity AND tag IB_GarrisonRearShore)
```

## 6. Paired render session (job 208)

### 6.1 Setup

**The run.**

- One GUI editor session, 10:50–10:56 UTC, with `-UseFixedTimeStep -FPS=30` and the isolated UserDir. It never saves.
- It loaded SR2, then SP1 from disk, and took the same 13 cameras with the same map lighting. The sky's clouds and the sea move between stills.
- After each load it flushed loading and shaders before any still.

**Cameras.**

| Camera | What it shows |
|---|---|
| overhead (RS1's camera) | the whole garrison from above |
| reference-fit eye, 7680×4320 | the picture's own view: the fitted camera F = 4000 of the reference-fit packet, rendered with the viewport's 90° lens from the same eye, then reprojected exactly into the picture's 1672×941 framing |
| left coast, right coast | both coasts, oblique |
| rear terrace, terrace edge | the rear terrace and its land edge |
| rear land strip | foot level |
| gate approach | the road into the gate |
| shore | foot level |
| two rock close-ups | on the rear terrace: `IBGC_RS1_Rock_050` (SM_Mountain_01) and `_051` (eroded mesh) |
| across adjoining land slabs | low view on the right flank |
| service shells / Armory row | in context, from the right flank |

**Read back after loading.**

- SR2: 136/136 slots at SR2's overrides.
- SP1: 136/136 at the SP1 instances, all 136 still tagged.
- In both maps, every other user of the four masters still uses it.
- 0 dirty packages after either load and at exit.

### 6.2 What the pairs show

| View | SR2 → SP1 |
|---|---|
| Reference framing, overhead | The gold land becomes mottled olive-green on both RS1 flanks. White rock blobs become small brown-grey rocks at the rim. The deck, the trees and everything else are unchanged. |
| Coasts | The RS1 land reads green with a stony rim. The khaki ground beyond RS1 (not RS1-owned) now contrasts with it. |
| Foot level (terrace edge, rear strip, shore, slab seams) | Stretched gold streaks are replaced by grass/forest-floor detail with darker mottles and sticks. The coast band carries grey stones that mix into the grass. No slab seam is visible as a texture break.<br>Median of the same lower-frame boxes:<br>• terrace edge (116, 94, 47) → (78, 76, 40)<br>• slab seams (106, 87, 47) → (58, 59, 34) |
| Rock close-up, SM_Mountain_01 | Snow-white becomes weathered taupe-grey stone with dark crevices and the mesh's normal detail. |
| Rock close-up, eroded mesh | Dark brown with yellow highlights becomes a darker brown-grey: lower contrast, details muted. |
| Wall rocks in shade, coast rim from the air | Visibly rock rather than snow, but dark and low-contrast. SR2's white rocks stood out more. |
| Service shells / Armory row | Unchanged; only the RS1 ground and rim rocks in the frame changed |

### 6.3 Measurements

All from `analysis/palette_measure.json` (`E990EEB3…`), in the picture's own framing. These are diagnostics, not renders.

| | Ground | Rock |
|---|---|---|
| Picture | inland olive (87, 86, 61) | shore-band grey (129, 123, 124); includes surf |
| SR2 (changed pixels) | (156, 128, 72) | (201, 185, 167) |
| SP1 (same pixels) | **(91, 90, 60)** | **(138, 117, 96)** |

- The picture's framing contains 20,813 land pixels that stay khaki in both renders, (121, 99, 75). These are non-RS1 ground at the top edge.
- **Shore band and sea** (one rule for all three images; grey = saturation < 0.18 and 0.25 < value < 0.9, so it counts rock, surf, grey water and concrete alike):

  | | Shore band grey | Sea median |
  |---|---|---|
  | Picture | 36 % | (20, 60, 81) |
  | SR2 | 21 % | (55, 64, 69) |
  | SP1 | 7 % | (53, 64, 70) |
- Masks (`analysis/palette_masks.png`):
  - picture: land above its traced waterlines and outside its deck outline; shore band ≤ 45 px from a waterline; inland ≥ 80 px;
  - renders: land pixels changed by more than 30 levels and not water-like, split by SR2's colour.

### 6.4 Board

`board/sp1-board.png` (3000×6791, `154FEE71…`; JPG `100A2357…`). From `analysis/sp1_board.py`. Its bands are kept apart:

- **SOURCE + RENDER framing:** the picture (scaled to fit, otherwise unchanged), then SR2 and SP1 reprojected.
- **RENDER:** 12 before/after pairs.
- **DETAIL:** exact 1:1 crops of the same stills (729 px wide): both rock close-ups, shore band, slab seams, wall rocks, coast rim.
- **PROBE:** job 206's V0–V3 at the shore.
- **DIAGNOSTIC:** the masks with colour swatches.

## 7. Preservation, processes, logs and autosave

**Preservation.** `hashes/preservation-final.json` (`73579D4A…`, recorded at 11:35 UTC, after the last evidence write; from `analysis/sp1_preservation.py`):

- **Codex's 1,560 records:** 1,558/1,558 project files match. The two engine BasicShapes are compared by the jobs' Windows-side stamps.
- **The first stamp** (job 204, before any SP1 engine run, 1,980 files): every one of its 1,976 project files is unchanged. It covers:
  - Codex's 1,560;
  - SR2's map and receipt, and its evidence folder excluding its engine UserDirs (`user/`, `user-gui/`);
  - Codex's SR2 review folder;
  - RS1's receipt and plan;
  - the `AITextures` and `IcelandEnviroment` folders and SR2's two materials.

  The four engine files in it (BasicShapes Cube and Cylinder, WorldAlignedTexture and WorldAlignedNormal) are compared by the jobs' stamps.
- **All ten stamps** `hashes/shared-{before,after}-{204..208}.json` are byte-identical (`421BEC92…`). Every job printed `SHARED_ASSET_OR_SAVE_CHANGES=0` and `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`.
- **SR2's six reviewed artifacts** match Codex's `artifacts-current.json`: map `0267B9A3…`, both materials, receipt `44AEE146…`, checks `447DFB9F…`, board `D6D6F874…`. So do the approved picture and the four saves.
- **The live map** is `FAFFD601…` throughout.

**Processes and logs.** `analysis/log_check.json` (`98866864…`):

- 19 engine processes, all owned: 16 commandlets (exit 1, the known ensure) and 3 GUI runs (exit 0).
- All 19 logs end with "Log file closed". 0 access violations, 0 critical or fatal lines.
- **Error lines** are the pre-existing kinds plus this task's expected ones:
  - pre-existing: the GameFeatureData ensure block in every process, and BP_Mech compile errors in the GUI runs (21);
  - expected: the 6 lines of the three negative tests (2 each; two are the CB1 test's "not base + the recorded overrides" verification failure, four are the other two tests' refusals);
  - job 205's "32 expressions survived the clear".
- **Compile lines:** 3, all the pre-existing `M_AI_Foam` warning; 0 name SP1.
- **Crash-reporter folders:** 19, all "Ensure condition failed: AssetBaseClassLoaded … GameFeatureData" at startup. 16 are in `user/`, 3 in `user-gui/`.

**Autosave.**

- The isolated GUI UserDir's per-user settings set `bAutoSaveEnable / bAutoSaveMaps / bAutoSaveContent = False`. That file lives only in `user-gui/`.
- **Read-back in each GUI run:**
  - job 205: failed; 5.8 does not find the Python spelling `auto_save_enable`;
  - job 206: `bAutoSaveEnable` = **False**, read with the C++ property name, which 5.8 accepts;
  - job 208: `bAutoSaveEnable`, `bAutoSaveMaps` and `bAutoSaveContent` all **False**.
- The same runs switched the editor's background CPU throttle off for the session only, in memory; it was not saved.
- The only file in `user-gui/Saved/Autosaves/` is `PackageRestoreData.json` (96 bytes, `"RestoreEnabled": false, "Packages": []`). It is rewritten at each GUI exit and is not an autosave of any package.
- No autosaved package exists.

## 8. Every write

**Content** (preview only):

- `_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette1.umap`;
- the seven assets in `_GarrisonPreview_Disposable/ShorePalette1_Materials/`.

The in-memory probe package path `ShorePalette1_LookProbeUnsaved` was never written.

**Saved:**

- **The receipt:** `GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette1.json`.
- **The job runner:**
  - `zz_job/shorepalette_lib.ps1` (`0B377DC4…`);
  - jobs 204–208 (now in `zz_job/running/`, each with its `.exit` = 0);
  - their logs in `zz_job/logs/`.
- **The evidence folder** `GarrisonRestructure/20261001-claude-shorepalette/`: 137 files and 293 MB, counting `hashes/preservation-final.json` and excluding the engine UserDirs:
  - `tools/`, `analysis/`, `plan/`, `probe/`;
  - `lookprobe/` (job 205, 5 stills) and `lookprobe2/` (job 206, 20 stills);
  - `run1/` (stage reports, fingerprints, manifests, logs);
  - `check-sp1/` (26 stills, 156 MB, plus `sp1_checks.json` `8EDD678C…`);
  - `board/`, `hashes/`, `protected-1560.json`, `source/`.
- **The isolated UserDirs** `user/` and `user-gui/`: engine scratch, the ensure reports and the restore file above.
- **`tools/__pycache__/`:** `ib_garrison_shorepalette_material.cpython-311.pyc` written by UE's Python, and `.cpython-310.pyc` written when I ran `sp1_make_plan.py` on the desktop. The later analysis runs used `PYTHONDONTWRITEBYTECODE`.

**Docs:** this file. **Claude outputs:** `CLAUDE_STATUS.md` (updated; backup in my desktop scratch).

The job runner also kept its own bookkeeping: `zz_job/current.txt`, and each job's `.exit` and empty `.err.log` files. Jobs 205 and 206 exited with their in-memory probe material packages still dirty; they were never saved.

Nothing else was written. There was no write under `Content/` outside the preview folder, and no project or engine configuration change.

## 9. Remaining limitations and the next largest reference mismatch

1. **Rock colour.**
   - **Warm cast.** The two mountain-mesh rocks render as warm taupe-grey, not the picture's neutral light grey. The albedo is neutral-warm, and the map's low sun is warm.
   - **The eroded mesh** (18 rocks) renders darker than before. Its baked texture is already dark, so the shared darkening pushed it further.
   - **Shade and distance.** In shade and from the air, the rocks are dark and low-contrast.
   - **Bounded correction, not run.** It touches instance values only; no geometry, graph or new asset:
     - `MI_SP1_Rock_Eroded`: gain about 0.6 and gamma 1.0;
     - all three rock instances: a slightly cool tint, about (0.96, 0.97, 1.0).

     It needs one more apply/verify/render round, which this pass did not have.
2. **Rock form** (geometry, not material).
   - The rocks are RS1's scaled-down mountain meshes (about 1/100–1/250 scale; mesh bounds from job 204), set about 1.5 m into the ground.
   - What shows is a cluster of narrow, spiky peaks about 1–4 m high, centred about 7.8 m apart along each rim.
   - They read as separate crystal-like specks, not as the picture's continuous field of large, rounded boulders.
3. **Physical slab edges.** A material cannot fix these:
   - the land slab tops (z −5 cm) sit 1 cm above the coast bands (−6 cm);
   - the coast bands end in straight edges in the water (visible near the shore-eye rock);
   - the terrace is a box with vertical faces. Stone covers them, but the form stays rectilinear.
4. **Non-RS1 ground.** The 44 CityGround slabs, `MountainGroundPad` and the background peaks keep the shared khaki/snow masters by design. In the coast obliques, the green RS1 land now meets a hard khaki boundary.
5. **Look-comparison scope.** The rock setting was chosen from measurement, not previewed. Variants were compared in 5 views only.

**Next largest reference mismatch: the shoreline itself.**

- **The difference.** In the picture's framing, the land band within 45 px of its waterlines is **36 % grey** (rock and surf). One class rule, `analysis/palette_measure.json` → `shore_and_sea`, gives in the same band:
  - SR2: 21 % (white rocks, plus grey water and concrete edges);
  - SP1: **7 %**. Its rocks are now brown-grey, so on this measure SP1 moved away from the picture.

  The picture's coast is a continuous band of large grey boulders with white surf. Ours is a straight slab edge with separate small peaked rocks.
- **What it needs.** Shoreline geometry (rounded boulder meshes placed along both waterlines) and surf. That is beyond a palette pass.
- **The next two.**
  - The sea: the picture's sea median is (20, 60, 81), deep blue. The renders' is (55, 64, 69) / (53, 64, 70), grey-teal and flat.
  - The forest: the picture has a dense conifer canopy over most of the land; ours has sparse broadleaf trees showing the ground.

  Both are larger in area than the rocks, but they are separate systems: the shared sea, and the RS1 trees, which are fixed by this brief.

## 10. Evidence index

All paths are relative to `Saved/GarrisonRestructure/20261001-claude-shorepalette/`.

**Plan and probe.**

| File | SHA256 |
|---|---|
| `probe/sp1_probe.json` (job 204) | `45CF84FA…` |
| `plan/sp1_plan.json` | `DA89E3E3…` |
| `plan/sp1_material_spec.json` | `8D26F0B5…` |
| `plan/sp1_look_variants.json` | `63E3FB7D…` |

**Tools.**

| File | SHA256 |
|---|---|
| `tools/ib_garrison_shorepalette.py` (lifecycle) | `317F6C82…` |
| `tools/ib_garrison_shorepalette_material.py` | `B5FC2611…` |
| `tools/ib_garrison_shorepalette_lookprobe.py` | `E10932C7…` |
| `tools/ib_garrison_shorepalette_check.py` | `587FA72F…` |
| `tools/ib_garrison_shorepalette_probe.py` | `FEE4FD3B…` |
| `tools/job205-as-run/*` | as run in job 205 |

**Lifecycle.**

| File | SHA256 |
|---|---|
| `run1/<step>/sp_<stage>.json`, one report per step (e.g. `run1/apply-repeat/sp_apply.json`; material-verify in `run1/material/`, copy-verify in `run1/copy/`) | — |
| `run1/material/material_manifest.json` | `C4CA8E44…` |
| `run1/basefp/base_fingerprint.json` | `A3F65197…` |
| `run1/copy/copy_fingerprint.json` | `2DBB0C51…` |
| `run1/apply/ownership_manifest.json` | `13BFA10B…` |
| `run1/logs/*.log` | — |

**Renders.**

| File | SHA256 |
|---|---|
| `lookprobe/` (job 205) and `lookprobe2/` (job 206): stills and `sp1_lookprobe.json` | `AD2EB81D…` and `97F686E2…` |
| `check-sp1/editor/*.png` (26 stills) | — |
| `check-sp1/sp1_checks.json` | `8EDD678C…` |
| `check-sp1/logs/check-editor.log` | `286373CC…` |

**Analysis.**

| File | SHA256 |
|---|---|
| `analysis/framing/sp1-reference-framing-{before-SR2,after-SP1}.png` | `A160DA86…`, `45730C1F…` |
| `analysis/palette_measure.json` | `E990EEB3…` |
| `analysis/palette_masks.png` | `3A6A7A6F…` |
| `analysis/look_selection.json` | `7C582019…` |
| `analysis/existing_material_candidates.json` | `31E82831…` |
| `analysis/log_check.json` | `98866864…` |
| `analysis/sp1_*.py` (board, palette measure, look selection, candidate scan, log check, preservation, make plan) | — |

**Board and hashes.**

| File | SHA256 |
|---|---|
| `board/sp1-board.png` | `154FEE71…` |
| `board/sp1-board.jpg` | `100A2357…` |
| `hashes/shared-{before,after}-{204..208}.json` | — |
| `hashes/preservation-final.json` | `73579D4A…` |
| `protected-1560.json` | `5B972F7B…` |

**Job runner** (in `Saved/zz_job/running/`).

| File | SHA256 |
|---|---|
| `204-sp-probe.ps1` | `60A860A5…` |
| `205-sp-lookprobe.ps1` | `0BA8A710…` |
| `206-sp-lookprobe2.ps1` | `D55C3F2C…` |
| `207-sp-lifecycle.ps1` | `3405FA10…` |
| `208-sp-check.ps1` | `368C18B9…` |
