# Garrison SR2 service identity fix: result (2026-10-01)

**Brief:** `Docs/CLAUDE_GARRISON_SERVICE_IDENTITY_FIX_2026-10-01.md` (Codex, after reviewing SR1 at 07:06:56 UTC).
**Status:** DONE. Stopped for Codex's review. Disposable candidate only: no live promotion, no shared write, no Git.
**Evidence:** `Saved/GarrisonRestructure/20261001-claude-serviceidentity/` (index in section 10).

**Summary.**

- **Where the "03" is.** I measured the source data before building anything (jobs 194–195 plus offline analysis). The number is in three places:
  - the base colour (dark ink plus a baked shadow);
  - the normal map (embossed strokes);
  - **the mesh itself**: the glyphs stand 0.31 mesh units proud of the panel at the median and 0.41 at p95, which is 4.1 / 5.4 cm on the ×13 shells.

  Roughness and metallic carry no number. A colour-and-normal remap alone therefore leaves a raised, shaded "03" (job 198 probe; board PROBE band).
- **What SR2 changes.** One thing: slot 0 of `StaticMeshComponent0` on the two SR1 shells now uses `MI_SR2_Armory_NoNumber` instead of the Armory material. These stay identical to SR1:
  - the other 3,541 actors, including the real Armory;
  - every mesh, transform and tag;
  - every collision and visibility setting.
- **The material.** It is a duplicate of `M_Tripo_PBR_Master` with built-in nodes inserted. Its instance is a duplicate of `armory_3d_model_Mat`, re-parented to it, with the same four textures read-only.

  It acts only inside a rounded-box UV mask, which touches only the number's own UV chart. There it does three things:
  - takes base colour and normal detail from a plain area of the same texture, offset (−764.5, −33.5) texels, with a small colour correction;
  - flattens the normal to the panel;
  - lowers whatever stands above the panel back onto it with a world-position offset. The offset is at most 5.3 cm, and no vertex on the chart's seam moves.

  Roughness and metallic are untouched. In the whole mesh, 8,038 triangles carry any mask weight, all of them on the number's chart.
- **Result.** In the 12 paired views the "03" is gone from both shells. There is no rectangular patch, and the real Armory still shows its "03".

  At 2.6 m two faint marks remain. Both lie exactly on the number chart's own UV edge (located by a computed overlay, section 5.3):
  - the end of a panel groove that the "0" used to cover, now a short curl (about 20 cm);
  - a faint tone step (about 0.6 m) where the remapped colour meets the next chart.

  Neither is noticeable in the oblique, sea-face, walkway, coast or overall views. **Whether that is acceptable is Codex's call.** I am not calling the close-up clean.
- **Lifecycle PASS** (job 199's verified copy, then job 201):
  - apply / save / reload;
  - a repeat apply on the saved state was a no-op: nothing to change, nothing saved, file byte-identical;
  - an exact restore to SR1: 3,543/3,543 actors identical, and the fingerprint digest equals SR1's own;
  - re-apply;
  - three ownership negatives.

  Job 199's first apply was correctly refused: an in-memory read effect, not a level change (section 4). A per-component collision read of all 3,558 static mesh components is identical to SR1's (job 202).
- **Exit.** The new visual check (job 203) exited **0 (0x00000000)**, after "Log file closed" at 08:57:55 UTC. SR1 job 193's exit-time `0xC0000005` stays an unresolved limitation. It was not investigated.
- **Disclosures.**
  - Editor autosave could not be switched off: the settings classes are not exposed to Python in UE 5.8. Autosave wrote 4 files, all inside this task's isolated UserDir (section 6).
  - Job 199 printed `LIFECYCLE_COMPLETE=True` despite its refusals. It also left misnamed backups: four map copies and four receipt copies that all hold the created state.
  - Job 196's after-stamp failed and printed a false "1357 changes". Job 197 rechecked: 0 changes.
  - The offset is visual only: the shells' per-polygon collision still contains the raised glyphs (up to about 5.6 cm).

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows2`<br>`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows2.umap`, 6,056,893 bytes<br>SHA256 `0267B9A353D1877D6DA6463798E6CF356976C183C0BF97812767EF3FF3713EC2` (SR2 applied)<br>Copied from SR1 `5C5ABD104B60BEB78CD65F7513771097A883A933687E10F29D8B344CBF8F5400`, which is unchanged. |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ServiceRows2.json`, 11,106 bytes<br>SHA256 `44AEE146EF33F12CA63CF0A771B11B2E900A3C030826F3BFE5561250C6540FF6`<br>History (UTC):<br>• created `819EC8D8…` 08:31:06<br>• applied `47A09DC1…` 08:41:45<br>• restored `D43DAC89…` 08:44:06<br>• applied `0267B9A3…` 08:45:41<br>Records: plan `7BA91A6F…`, material manifest `932C1CCD…`, SR1 base fingerprint `08FDFEA2…` and SR1's receipt `3479FC82…` (the shells' identities). |
| **New material assets** (only these, only in `/Game/_GarrisonPreview_Disposable/ServiceRows2_Materials/`) | `M_SR2_Armory_NumberRemap` (Material): 46,902 bytes, SHA256 `4026D14C24A2FE67FE5AE89215767C655C35839B5A55968CF5E5F4BC9424F4B9`. 89 expressions: the master's 6 plus 83 added.<br>`MI_SR2_Armory_NoNumber` (MaterialInstanceConstant): 5,237 bytes, SHA256 `A8EB671B11B3A877ED3F1FDD09603C316394B4A6F0BEBBEE6BEAF3E5E49C0E4A`.<br>Manifest: `run1/material/material_manifest.json`, `932C1CCD1BB336E9FEB2C7BD481002D5B3CBD67EAA7C9D4684B7C9CA738F900C`. |
| **Diff vs SR1** | 3,543 actors, as in SR1. **3,541 identical; 2 differ, only in slot 0's `materials`/`overrides`; 0 unexpected.**<br>The comparison covers each actor's:<br>• label, class, location, rotation, scale, hidden, actor collision, tags and folder;<br>• per component: class, visibility, collision profile, collision enabled, mesh, materials and overrides (3,570 components). |
| **Override diff** | Exact, from the receipt (section 4):<br>• `IBGC_SR1_Shell_RightBack` (`StaticMeshActor_1002`) and `IBGC_SR1_Shell_RightFront` (`StaticMeshActor_1003`), `StaticMeshComponent0`, slot 0.<br>• Before: materials `[…/Armory/armory_3d_model_Mat]`, overrides `[]`.<br>• After: materials = overrides = `[/Game/_GarrisonPreview_Disposable/ServiceRows2_Materials/MI_SR2_Armory_NoNumber.MI_SR2_Armory_NoNumber]`. |
| **Sources read-only** | Byte-identical before and after every job:<br>• `M_Tripo_PBR_Master` `E9F37CB1…`<br>• `armory_3d_model_Mat` `2034E7A6…`<br>• base colour `D4F2E03B…`, normal `05FDB871…`, roughness `C7A8B60A…`, metallic `86F585DF…`<br>• `Armory` mesh `C9167F0D…`, `Armory_Collision` `D0763C07…`<br>All 64 `TripoModels` files match. |
| **Lifecycle** | **PASS** (job 201, continuing from job 199's verified copy):<br>• apply → saved; reload verify: 3,541 identical + 2 planned slot changes, 0 unexpected;<br>• repeat apply on the saved state: no-op, nothing saved, byte-identical;<br>• **exact restore to SR1**: 3,543/3,543 identical, fingerprint digest `9B73E835…` = SR1's;<br>• re-apply and final verify as the first;<br>• 3 ownership negatives: nothing saved; map and receipt unchanged.<br>Collision body detail (job 202): 3,558 components, 0 differences. See section 4. |
| **Visual check** | Job 203, one GUI session: SR1, then SR2 loaded from disk. 12 cameras × 2 = 24 stills (1920×1080, 90° lens).<br>• Numbers absent on both shells.<br>• Real Armory unchanged.<br>• No rectangular patch.<br>• Close-range marks on the chart edge (section 5).<br>• After reload: shells' slot 0 = `MI_SR2_Armory_NoNumber`, parent, textures and scalars as recorded; 0 compile failures naming SR2 assets; 0 dirty packages at exit. |
| **Board** | `board/sr2-board.png` (3000×5651; JPG copy). Bands, kept apart:<br>• SOURCE: textures and mesh, not renders<br>• RENDER: the 12 pairs<br>• CLOSE-RANGE RESIDUE<br>• DIAGNOSTIC: computed outlines, labelled as not rendered<br>• PROBE: in-memory variants |
| **Preservation** | At 09:17 UTC:<br>• Codex's 1,423 records: **1,421/1,421 project files match**. The 2 engine BasicShapes are compared by the jobs' own stamps.<br>• All 1,558 project files of this task's first stamp: 0 changed.<br>• All 17 before/after stamps (jobs 194–203) byte-identical (`3B98AA31…`, 1,560 files each).<br>• Live map `FAFFD601…` unchanged.<br>• SR1's five reviewed artifacts, the approved picture and the four saves match Codex's records. |
| **Processes** | 35 engine processes, all owned, all exited; `OWNED_PROCESSES_LEFT=0` after every job.<br>• 31 commandlets: exit 1 = the known GameFeatureData ensure; exit −1 on job 199's refused stages; job 194's probe exit 3 (access violation).<br>• 4 GUI runs: exit 0.<br>Crash-reporter folders: 36. 35 are the GameFeatureData ensure at startup; 1 is job 194's access violation. |
| **Remaining** | • The close-range marks on the chart edge.<br>• The raised glyphs are still in collision (up to about 5.6 cm, invisible).<br>• Autosave was not suppressible.<br>• SR1's exit-time crash is unresolved.<br>See section 9. |

## 2. Where the number is: UV and channel evidence

### 2.1 Source facts (job 195; read-only commandlet; nothing saved)

- **Textures.** Four 2048×2048 `Texture2D`s with wrap addressing. Base colour is sRGB. The normal map uses the normal-map group and compression.
- **Material.** `armory_3d_model_Mat` is an instance of `M_Tripo_PBR_Master`, a 6-expression graph. Its four texture parameters are `BaseColorTex`, `NormalTex`, `RoughnessTex` and `MetallicTex`; all use UV0.
- **Mesh.** `Armory` is a Nanite mesh: 1 LOD, 1 section, 24,712 render triangles, 45,730 vertices. Its source geometry, exported for analysis (`probe2/mesh/armory_source_tris.f32`), has 1,897,800 triangles with UV0.
- **Exports.** The textures were exported to PNG outside `Content` (`probe2/source/`). Those PNGs feed only the offline analysis and the board's SOURCE band. The material samples the original texture assets.

### 2.2 Channel by channel

The "03" occupies its own UV chart: 13,852 texels of the 2048² atlas. The mask fitted to it is centred at texel (1267, 910) and turned −34°. "Ring" below means the plain panel just outside the mask. All figures come from `analysis/material_plan_checks.json` and `analysis/footprint_mask.json`.

| Channel | Number in it? | Measured |
|---|---|---|
| Base colour | **Yes**: dark ink plus a baked shadow | Mean linear luminance inside the mask core: 0.116, vs the ring's 0.218 ± 0.020. Ink: 2,713 texels. |
| Normal map | **Yes**: embossed strokes | Mean tilt (hypot of R−128 and G−128, 8-bit) 21.7 in the core vs 3.1 on the ring. Emboss: 2,585 texels. |
| Roughness | No | Glyph ink 201.4 vs plain core 202.5; ring 201.9 ± 3.6 |
| Metallic | No | Glyph ink 2.3 vs plain core 1.8; ring 2.1 ± 2.0 |
| **Mesh geometry** | **Yes: raised glyphs** | Height above the panel plane (fitted to 5,197 triangles), p5 / p50 / p95: **0.046 / 0.313 / 0.413** mesh units = 0.6 / 4.1 / 5.4 cm at ×13. Highest glyph vertex: 0.433 = 5.6 cm. The plain panel's own residual is −0.134…0.066. Relief: 3,030 texels. |

The union of ink, emboss and relief is 3,847 texels. All of it lies inside the mask at full weight (`footprint_all_full_weight`: true).

### 2.3 Why a colour remap alone is not enough

Jobs 197 and 198 rendered in-memory variants on the SR1 map, never saved (board PROBE band; `lookprobe3/grids/`):

| Variant | Close-up shows |
|---|---|
| Texture remap: base colour and normal both from the donor, no flattening (job 197, V1) | A light "03", still raised: the geometry |
| Donor base colour + flattened normal (job 198, V2) | The same raised "03", shaded by the real geometry |
| + relief offset, threshold τ 0.07 everywhere (V3a) | Thin stroke lines where the glyph sides stood |
| + relief offset, τ 0 (V3c) | Hairline cracks along the chart's UV seam: seam vertices moved apart |
| **+ relief offset, seam-safe τ ramp (V3b, used)** | No glyph, no stroke lines, no cracks; the groove curl and faint seam step of section 5.3 |

## 3. The material

### 3.1 How it works

All nodes are built-in; there is no custom HLSL. Spec: `plan/sr2_material_spec.json` (`9226057D…`). Builder: `tools/ib_garrison_serviceidentity_material.py` (`37B6FA7F…`).

- **Mask w** (rounded box in UV, smoothstep feather). Centre UV (0.61865, 0.44434), half-size 34.97 × 41.93 texels, corner radius 30, angle −34°, feather 10 texels.
  - Clearances: 15.0 texels to the facet's other details; 24.9 texels to any other chart (more than the feather).
  - Times `SR2_Weight` (1).
- **Base colour:** `lerp(original, donor + correction, w)`.
  - **Donor:** the same texture at UV + (−0.373291, −0.016357), that is (−764.5, −33.5) texels.
  - It was chosen from 1,879 candidate positions as the closest match to the ring. Score 7.7; the next was 118.7.
  - Its texture-only statistics: grain 0.074 (ring 0.074); roughness 196.9 (ring 201.9); 0 marking texels; entirely inside a chart interior.
  - **Correction:** a small planar linear-colour term, about +0.02 at the mask centre. It brings the donor's level and gradient to the ring's.
- **Normal:** `lerp(original, lerp(donor, whiteout(facet normal, donor), SR2_NormalFlatten), w)`.
  - The facet normal is the fitted panel normal, transformed local → tangent. The donor keeps fine panel grain; the glyph strokes go.
- **World-position offset:** `Local→World( −n · max(h − τ, 0) · w · SR2_WPOFlatten )`.
  - `h = (LocalPosition − p0)·n`, using the pre-offset local position.
  - Panel plane: p0 = (28.27, 33.80, 27.33), n = (−0.0019, 0.9469, 0.3217) in mesh space.
  - **τ is 0.025 mesh units (0.33 cm) away from the seam and 0.07 (0.91 cm) at the chart's seam line, ramping over 2–6 texels.** Every seam vertex therefore stays where it is.
  - Only what stands above the panel moves, and only toward it.
  - `max_world_position_offset_displacement` = 8 cm. Every other material flag is the master's (the asset is a duplicate).
- **Untouched:** roughness and metallic (same samplers and outputs as the master).
- **Instance:** parent `M_SR2_Armory_NumberRemap`; the same four texture values as `armory_3d_model_Mat`; `SR2_Weight` = `SR2_NormalFlatten` = `SR2_WPOFlatten` = 1. The τ values are the parent's defaults.

### 3.2 Exact checks on the design (offline)

| Check | Result |
|---|---|
| Triangles in the whole mesh with any mask weight | **8,038, all on the number's chart.** Nothing else on the building can change. |
| Seam corners (positions shared with another chart) | 409 positions; 1,317 corners on the number chart, 209 of them with weight.<br>Highest weighted seam corner: 0.067 < τ_seam 0.07, so **0 seam corners move**. |
| Relief left after the offset (10,034 relief vertices at full weight) | p50 0.025, p99 0.07 mesh units = 0.33 / 0.91 cm. Largest offset: 0.408 mesh units = **5.3 cm**. |
| Expected colour (from the textures) | Core luminance after: 0.2145 ± 0.0133, vs the ring's 0.2178 ± 0.0203 (before: 0.116) |
| Expected normal | Core tilt after: 1.18, vs the ring's 3.11 (before: 21.7) |

Sources: `analysis/seam_check.json`, `analysis/material_plan_checks.json`, `analysis/donor_candidates2.json`.

### 3.3 Verified in the engine

- **Job 199, `material` stage.** Duplicated the master and the instance, inserted the nodes and saved **only** the two new packages. Before the save, the dirty list was exactly those two.
- **Job 199, `material-verify` stage (new process).** Both assets reloaded; nothing dirty after load. Checked: graph (89 expressions), outputs (base colour, metallic, roughness, normal, world-position offset), parent, the four textures, the scalars and the file bytes, all as recorded.
- **Job 203 (GUI).** After loading SR2 from disk, both shells' slot 0 = the instance, with the recorded parent, textures and scalars. Compile failures naming SR2 assets: **0**. The only "Failed to compile" line is the pre-existing `M_AI_Foam` (also in SR1's runs).

### 3.4 What the offset does not change

The world-position offset moves rendered positions only:

- **Collision.** Unchanged, as the brief requires. Pawns still collide with `Armory_Collision`, which keeps the raised glyphs: up to about 5.6 cm proud of the visible wall, on the sea face. That figure is the highest glyph vertex of the render mesh; the collision mesh itself was not measured.
- **Distance fields and other precomputed data.** Built from the unmoved mesh. No glyph shadow is visible in the stills.
- **Packaged builds.** Nanite with an offset is not checked in a cooked or packaged build.

## 4. Lifecycle and ownership

Tool: `tools/ib_garrison_serviceidentity.py` (`97FFD495…`; r1 in `tools/superseded/`). It is derived from SR1's tool, which is unchanged. Each stage ran in its own commandlet process with the isolated UserDir.

| Job (UTC) | Steps | Result | Map after |
|---|---|---|---|
| 194 (07:19–07:20) | Material probe, first version | Access violation (exit 3) inside a material query (callstack: PythonScriptPlugin → MaterialEditor), before its report. Only its log was written. | — |
| 195 (07:23–07:26) | Probe, second version (statistics query dropped) | Textures, graph and mesh exported; exit 1 (ensure) | — |
| 196–198 (07:54–08:23) | GUI look probes on SR1, in memory, never saved | Job 196 stopped at creating the dynamic instance (wrong API name). Jobs 197 and 198 rendered the variants of section 2.3. SR1 hash unchanged in each. | — |
| 199 (08:27–08:39) | material; material-verify; SR1 fingerprint; copy; copy-verify; apply; repeat; verify; restore; verify; re-apply; verify; 3 negatives; verify-final | Material authored and verified. Copy verified: **3,543/3,543 identical**.<br>**Apply REFUSED, not saved** (below). Every later stage then refused or verified the unchanged copy. | `819EC8D8…` |
| 201 (08:40–08:50) | apply; repeat; verify; restore; verify; re-apply; verify; 3 negatives; verify-final | **PASS** (table below) | `47A09DC1…` → `D43DAC89…` → `0267B9A3…` |
| 202 (08:50–08:52) | Collision body detail, SR1 and SR2, each read first in a fresh process | 3,558 components each; **0 differences**; neither file changed by the read | `0267B9A3…` |
| 203 (08:52–08:58) | GUI paired visual check (never saves) | Section 5 | `0267B9A3…` |

**Job 201 in detail.**

| Stage | Result |
|---|---|
| apply | Source check vs SR1: 0 unexpected.<br>In process, the only changes vs the settled level are the 4 planned values (two shells × materials/overrides).<br>Saved. Receipt "applied". |
| apply-repeat | Already applied and verified: **a no-op**. Nothing to change and nothing saved (`saved: false`); map byte-identical; receipt still 2 entries. |
| verify-applied (new process) | 3,541 of 3,543 identical, 2 differ (planned), **0 unexpected**; digest `B211C5AD…`; nothing dirty after load |
| restore | The level was exactly the applied state at the recorded identities. Overrides set back to SR1's (none) on exactly those two components; the only changes are the 4 values back. Saved. |
| verify-restored | **3,543 of 3,543 identical, 0 differ, 0 unexpected.** Fingerprint digest `9B73E835AB61DD11…` = SR1's own base fingerprint digest = the created copy's. |
| reapply / verify-reapplied / verify-final | As apply / verify-applied; digest `B211C5AD…` again |

**Byte-level note.** The restored file (`D43DAC89…`, 6,056,604 bytes) is not byte-identical to the created copy (`819EC8D8…`, 6,056,571 bytes). Likewise the re-applied file (`0267B9A3…`) differs in bytes from the first applied one (`47A09DC1…`). A save re-serialises the package, as in SR1. The check is the fingerprint comparison above.

**Why job 199's apply was refused.** In a commandlet, the first read of a component's materials completes an asynchronous mesh build. The engine then re-applies that mesh's default collision profile to components that use it.

- `IB_Harbor_Surface` (`StaticMeshActor_133`, which uses its mesh's default collision) reads `Custom` first and `BlockAll` after that, in memory only.
- r1 of the tool compared a second, post-read state against the first-read baseline. It saw that as a third difference and refused to save, correctly by its rule.
- r2 checks the first read against SR1's baseline, then compares in-process changes against a second, settled read. In job 201 the stages that take that settled read logged exactly this one read-settling value (`read_settling` in their reports): apply, restore, re-apply and the CB1 negative. The repeat and the other two negatives stop before it.
- Every fresh-process verify reads `Custom` again. Job 202 read the full collision body detail first in a fresh process, for SR1 and SR2: profile, enabled, object type, the 8 standard channel responses and the default-collision flag. **0 differences.** The harbor surface is `Custom` with all eight channels Block in both.

**Two job-199 defects, disclosed.**

- Its summary printed `LIFECYCLE_COMPLETE=True` although apply, repeat, restore, re-apply and the negatives had refused.
- Its backup step wrote `backup/ServiceRows2-{created,applied,restored,reapplied,final}.umap`. All five are the created copy (`819EC8D8…`). The five receipts `backup/ServiceRows2-receipt-*.json` are all the 'created' receipt (`DFB486CC…`).
- The correct backups are the job 201 files `backup/ServiceRows2-run2-*`. Nothing outside the evidence folder was affected.

**Ownership.**

- A shell is SR2-edited only if its object name, label, class and mesh equal SR1's recorded identity (from SR1's receipt) **and** it carries `IB_GarrisonServiceRows`.
- `IB_GarrisonCB1` alone never selects anything.
- The ownership manifest is `run2/apply/ownership_manifest.json` (`DA3F04E2…`), identical after the re-apply.

| Ambiguity added in memory (saving blocked) | Outcome (job 201) |
|---|---|
| An extra Armory-mesh actor with only the shared `IB_GarrisonCB1` tag and the SR2 instance on slot 0 | Not selected; left untouched (slot still the SR2 instance). The level then differed from base + recorded overrides in 1 way, so the restore did not verify and nothing was saved. |
| One recorded shell with its `IB_GarrisonServiceRows` tag removed | RESTORE REFUSED: 1 conflict; nothing changed |
| An extra Armory-mesh actor with both tags, an unrecorded label and the SR2 instance | RESTORE REFUSED: 1 conflict ("carries IB_GarrisonServiceRows but is not a recorded shell"); nothing changed |

In every negative test the save was never reached, and the map and receipt were unchanged.

**Exact override diff** (receipt, both 'applied' entries):

```
IBGC_SR1_Shell_RightBack  (StaticMeshActor_1002, StaticMeshActor, /Game/TripoModels/Armory/Armory.Armory)
IBGC_SR1_Shell_RightFront (StaticMeshActor_1003, StaticMeshActor, /Game/TripoModels/Armory/Armory.Armory)
  component StaticMeshComponent0, slot 0
  before: materials [/Game/TripoModels/Armory/armory_3d_model_Mat.armory_3d_model_Mat]  overrides []
  after:  materials [/Game/_GarrisonPreview_Disposable/ServiceRows2_Materials/MI_SR2_Armory_NoNumber.MI_SR2_Armory_NoNumber]
          overrides [/Game/_GarrisonPreview_Disposable/ServiceRows2_Materials/MI_SR2_Armory_NoNumber.MI_SR2_Armory_NoNumber]
restored entry: slot0_overrides [] on both (recorded identity AND tag IB_GarrisonServiceRows)
```

## 5. Paired visual check (job 203)

### 5.1 Setup

- GUI editor (`-ExecutePythonScript`, `-UseFixedTimeStep -FPS=30`), isolated UserDir, never saves.
- SR1 was loaded first, then SR2 from disk, in **one session**: the same map lighting actors (identical inherited actors) and the same cameras.
- Stills: 1920×1080, editor game view, 90° lens, taken after `finish_loading_before_screenshot`. Tool: `tools/ib_garrison_serviceidentity_check.py` (`A9B7DEAE…`); record: `check-sr2/sr2_checks.json` (`447DFB9F…`).
- `rear-walkway-eye`, `right-coast-eye` and `right-flank-oblique` use exactly SR1 job 193's cameras. `cross-road-south-eye` is new: SR1 named that viewpoint but had no still for it. The close, oblique, sea-face and Armory cameras are new.
- The editor's background-throttle and autosave settings could not be set from Python in UE 5.8 (`EditorPerformanceSettings` and `EditorLoadingSavingSettings` are not exposed).
- The sky's clouds move between stills, so exposure varies a little. Pixel differences are not used as evidence.

### 5.2 What the pairs show

| Camera | BEFORE (SR1) | AFTER (SR2) |
|---|---|---|
| `rb-number-close`, `rf-number-close` (2.6 m from each number) | Raised dark "03" with its shadow | **No number.** Plain panel; bolts, panel lines, the plates above and the "II" marks below unchanged. At the former "0"'s lower left: the groove curl and a faint tone step along the chart edge (5.3). |
| `rb-number-oblique`, `rf-number-oblique` | "03" | **No number, no patch outline.** The curl shows only as a small mark at the panel's lower left. |
| `rb-sea-face`, `rf-sea-face` (whole face, roof equipment and door) | "03" on the shell in view; in `rb-sea-face`, also the other shell's, at the frame edge | **No number on either shell**; roof, door, chevrons and panels unchanged |
| `armory-number-close`, `armory-face` (real Armory, `StaticMeshActor_56`) | "03" | **"03" unchanged.** Its slot 0 still `armory_3d_model_Mat`, no override (recorded at load). |
| `rear-walkway-eye`, `cross-road-south-eye` | Shell faces along the walkway | No number; no other visible change |
| `right-coast-eye` | "03" over the deck edge | **No number** |
| `right-flank-oblique` (overall row) | Row of three | Unchanged at this scale (the number is a few pixels in SR1) |

### 5.3 The close-range marks, located

`analysis/sr2_residue_overlay.py` places the Armory's source triangles near the number with each shell's transform (SR1's engine plan: ×13, yaw 180). It projects them with job 203's recorded camera. It evaluates the mask per triangle corner exactly as the material does, then draws three computed outlines over the unmodified stills:

- **yellow:** the full-strength core;
- **cyan:** the outer edge of the feather;
- **red:** the number chart's own UV edge.

The outlines match the panel lines in the stills.

![Close-range residue with computed outlines](../Saved/GarrisonRestructure/20261001-claude-serviceidentity/analysis/residue_overlay/rb-number-close_residue_zoom.png)

What the overlay shows (`analysis/residue_overlay/`, RightBack and RightFront alike):

- **The number's chart edge runs along the panel groove** that comes down from the upper left. It curls under the former "0" and then runs along the number's bottom. The mask's full-strength core reaches that edge along the lower left and bottom.
- **The curl is on the edge.** It is the end of the groove, which the "0" used to cover. The material keeps the edge's vertices still and keeps up to 0.07 mesh units (0.9 cm) of relief within 2–6 texels of it, so that no crack can open (V3c). The curl is about 20 cm long at ×13.
- **The faint tone step is on the edge.** It sits where the remapped colour (inside the chart) meets the next chart's original texture, along about 0.6 m of the bottom edge. It is not at the feather: outside the cyan line the material is the original.
- **No rectangular patch.** The mask is a rounded box in UV, cut by the chart. Outside the number's chart no triangle has any weight.

### 5.4 Board

`board/sr2-board.png` (`D6D6F874…`; 3000×5651) and `board/sr2-board.jpg` (`0C8334CB…`). Script: `analysis/sr2_board.py` (`EE57682E…`). Bands, top to bottom:

1. **SOURCE**: the Armory's own four textures and the mesh relief around the number, cropped, with the mask core, the feather and the chart edge drawn on. Also the donor area. Not renders.
2. **RENDER**: the 12 job-203 pairs (BEFORE SR1 | AFTER SR2).
3. **CLOSE-RANGE RESIDUE**: the two close pairs, zoomed ×2 at the former number's lower edge.
4. **DIAGNOSTIC**: the computed outlines over the RightBack close pair, plus the ×2 zoom. Labelled as not rendered.
5. **PROBE**: job 198's in-memory variants (SR1 as is; remap + flat normal; τ 0.07; the τ ramp used).

![SR2 board](../Saved/GarrisonRestructure/20261001-claude-serviceidentity/board/sr2-board.jpg)

## 6. Preservation, processes and errors

**Isolation.**

- Every engine process used an isolated UserDir under the evidence folder: `user/` for commandlets, `user-gui/` for GUI runs.
- Every job hashed the live map after every step, and SR1's map and receipt around its steps. The job would stop on any change; none occurred.
- `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0` in every job.
- `PREVIEW_FILES_WRITTEN` was 3 in job 199 (the SR2 map and the two material assets) and 1 in job 201 (the SR2 map); 0 elsewhere.

**Stamps.** Each job stamped 1,560 files before and after (17 stamps; job 196's after-stamp is missing, see below). The stamp covers:

- Codex's 1,423 records;
- SR1's map, receipt and evidence folder (outside its UserDirs);
- Codex's SR1 review folder;
- all 64 `TripoModels` files;
- the engine BasicShapes.

**All 17 are byte-identical** (`3B98AA3123A05C4C…`), and every job reported `SHARED_ASSET_OR_SAVE_CHANGES=0`, except job 196.

**Job 196's stamp defect.** A PowerShell loop variable (`$e`) shadowed the evidence-folder variable (`$E`); PowerShell names are case-insensitive. Its after-stamp therefore could not be written, and it printed `SHARED_ASSET_OR_SAVE_CHANGES=1357 (of 203 protected files)`, which is false. Job 197 compared before-196 with before-197 (1,560 files): **`SINCE_BEFORE_196_CHANGES=0`**. The variable was renamed from job 197 on.

**`hashes/preservation-final.json`** (`22B3866F…`, 09:17:23 UTC; `analysis/sr2_preservation.py`):

- Codex's 1,423 records: 1,421/1,421 project files match; the 2 engine BasicShapes on A: are compared by the jobs' stamps. The records include the live map, the approved picture and every Tripo source.
- First stamp (before job 194): 1,558 project files, **0 changed**.
- SR1's five reviewed artifacts (map `5C5ABD10…`, receipt `3479FC82…`, engine plan `6CEB8D57…`, `sr1_checks.json` `F67B4995…`, `sr1-board.png` `BF044791…`): all match.
- The approved picture and the four save files (`IBCharacters`, `IronBreach_Ledger`, `IronBreach_Vault`, `IronBreach_XP`) match Codex's bytes.
- `TripoModels`: 64/64 match.
- Every project file changed after 07:07:00 UTC, outside the evidence folder and this task's job scripts and logs:
  - the three SR2 content files, the SR2 receipt and `Saved/zz_job/serviceidentity_lib.ps1` (this task);
  - the runner's own `current.txt` and `runner.alive`;
  - Codex's brief and `review-summary.json`;
  - `Docs/CLAUDE_MANAGER_STATUS.md` (changed at 09:04 and 09:34 UTC), which this task did not write.

  The project `DerivedDataCache` and `Saved/Autosaves` received no new files.
- The queue holds only the inert `153-yellow-after.hold` (unchanged since 2026-09-30).

**Autosave (disclosed).** Autosave could not be disabled (5.1), and it fired in the GUI look probes:

- `ServiceRows2_LookProbeUnsaved/M_SR2_LookProbe_Auto1.uasset` (08:03, job 197) and `…/M_SR2_LookProbe3_Auto1.uasset` (08:17, job 198): the in-memory probe materials;
- `CarrowGateGarrison_ServiceRows1_Auto2.umap` (08:19) and `_Auto3.umap` (08:21), job 198: the SR1 map dirtied in memory by the probe's temporary overrides.

All four are in `user-gui/Saved/Autosaves/Game/_GarrisonPreview_Disposable/` inside the evidence folder. The project's `Saved/Autosaves` and `Content` were not touched by autosave, and SR1's map hash never changed. `user-gui/Saved/Autosaves/PackageRestoreData.json` (written at job 203's exit) reads `RestoreEnabled: false`, no packages. The job descriptions of jobs 196 and 197 say "autosave off". That is inaccurate: the setting could not be changed.

**Logs** (`analysis/log_check.json`, `232D6D85…`; 35 processes):

| Kind | Count | New? |
|---|---|---|
| GameFeatureData ensure block | 45 error lines per commandlet (23 in job 194's, which crashed before its closing summary); 26 per GUI run | Pre-existing (RS1/SR1 baseline) |
| `BP_Mech` compile errors (`UpdateMechProximity`) | 7 lines per GUI run | Pre-existing |
| "Failed to compile" | 1 per GUI run: `M_AI_Foam` | Pre-existing (SR1's runs too) |
| Other error lines (none of the known kinds) | 233 in all:<br>• 204 are refusals: job 199's seven refused stages (198) and job 201's three negatives (6). 176 of these are `LogPython: Error` lines.<br>• 28 are job 194's crash block.<br>• 1 is job 196's script error, `unreal.KismetMaterialLibrary` (the API is `unreal.MaterialLibrary`).<br>Job 199's refusal texts: apply, repeat and re-apply "1 check(s) did not verify; NOT saved"; restore "nothing to restore"; negatives "needs the applied target". | Refusals intended; the crash and the script error are mine |
| Access violation | 1: job 194 (`EXCEPTION_ACCESS_VIOLATION reading address 0x0`; callstack PythonScriptPlugin → MaterialEditor) | **Mine**; probe dropped the call in job 195 |
| Logs closed normally | 34 of 35 (all but job 194) | — |
| Crash-reporter folders | 36: 35 are the `AssetBaseClassLoaded` (GameFeatureData) ensure at startup (`SecondsSinceStart` 0); 1 is job 194's access violation (`UECC-Windows-64ECF0E4…_0001`) | Ensures pre-existing |

## 7. Exit codes and the exit-time limitation

| Process | Exit | Log ending |
|---|---|---|
| **Job 203 GUI visual check (this brief's check)** | **0 (0x00000000)** after 345 s | Results written at 08:57:52 UTC, then:<br>`[2026.10.01-08.57.55:237][857]LogExit: Exiting.`<br>`[2026.10.01-08.57.55:249][857]Log file closed, 10/01/26 01:57:55` (local time = 08:57:55 UTC)<br>Dirty map/content packages at exit: none. |
| Jobs 196, 197, 198 GUI look probes | 0 | Log file closed normally |
| Commandlets (jobs 195, 199, 201, 202) | 1 (GameFeatureData ensure) with complete reports; −1 for job 199's refused stages (Python exception) | Log file closed normally |
| Job 194 probe | 3 (access violation) | Ended at `Engine exit requested`, no closing line |

**SR1 job 193** returned `0xC0000005` after writing its results. That remains an **unresolved exit-time limitation**, not a clean exit. Nothing here investigated it, and no successful test was re-run for its exit code. Job 203 happened to exit 0; that says nothing about the cause.

## 8. Every write

| Path | What |
|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows2.umap` | The SR2 candidate (`0267B9A3…`) |
| `Content/_GarrisonPreview_Disposable/ServiceRows2_Materials/M_SR2_Armory_NumberRemap.uasset` | New material (`4026D14C…`) |
| `Content/_GarrisonPreview_Disposable/ServiceRows2_Materials/MI_SR2_Armory_NoNumber.uasset` | New instance (`A8EB671B…`) |
| `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ServiceRows2.json` | Receipt (`44AEE146…`) |
| `Saved/GarrisonRestructure/20261001-claude-serviceidentity/` | Evidence. Outside the two UserDirs: 264 files, 485.7 MB at 09:17 UTC.<br>Engine output in the UserDirs: `user/` 30.8 MB (180 files), `user-gui/` 184.8 MB (47 files). That is crash-reporter folders and logs, the 4 autosaves, and the editor's intermediate caches (asset registry, shader autogen).<br>Also a Python bytecode cache, `tools/__pycache__/`. |
| `Saved/zz_job/serviceidentity_lib.ps1` | Job helper library (`0EDABA9E…`) |
| `Saved/zz_job/running/{194…199,201…203}-si-*.ps1` + `.exit` | 9 job scripts (all exit files 0). Number 200 was not used. |
| `Saved/zz_job/logs/{194…199,201…203}-si-*.log` + `.err.log` | Job logs (job 196's `.err.log` holds the stamp error) |
| `Docs/CLAUDE_GARRISON_SERVICE_IDENTITY_FIX_RESULT_2026-10-01.md` | This result |
| `Claude outputs/CLAUDE_STATUS.md` | Status (backed up outside the project first) |

Not written:

- the live map; SR1's map, receipt and evidence; any earlier preview or receipt;
- any Tripo source or other Content outside the preview folder;
- project configuration, engine content, plugins, C++;
- the project's `Saved/Autosaves` and `DerivedDataCache`;
- Git: no locks, commit or push.

The in-memory probe material path `/Game/_GarrisonPreview_Disposable/ServiceRows2_LookProbeUnsaved/` was never saved to `Content`; only its autosave copies exist, in `user-gui/`.

## 9. Remaining limitations and options

| Item | Detail | Option (not done; needs Codex's go) |
|---|---|---|
| **Close-range marks on the chart edge** | The groove curl (about 20 cm) and a faint tone step (about 0.6 m) at the former number's lower edge.<br>Seen in the 2.6 m stills; not noticeable in the oblique, face, walkway, coast or row views. | Accept as is.<br>Or a material-only follow-up: a correction field that fades from the chart edge inward, to match the neighbouring chart's colour along the step. It would not change the curl, which is geometry kept on purpose so the seam cannot crack.<br>A fully clean close-up needs edited assets, which this brief excludes: a preview-local copy of the base colour/normal chart with the number painted out, and a mesh copy with the glyph relief removed (and its collision copy). |
| Collision keeps the glyphs | `Armory_Collision` is unchanged, as required, so an invisible relief of up to about 5.6 cm remains on the sea face | Only a collision-mesh copy would change it; excluded |
| Autosave | Could not be disabled from Python; 4 autosave files inside `user-gui/` | An editor-settings change, a project-config write, is outside this brief |
| SR1 job 193 exit-time `0xC0000005` | Unresolved; not investigated | Separate task if wanted |
| Not covered | Manual play, PIE (no geometry or gameplay changed), packaged/cooked builds (Nanite + offset), performance | — |

**Brief items.**

- **SR2 from SR1, SR1 intact:** met.
- **Only the two shells' material overrides change:** met (section 4).
- **New assets only in a named ServiceRows2 subfolder; sources read-only:** met.
- **"Check whether the number is encoded in more than base colour; avoid leaving a shiny or embossed ghost":**
  - Checked: it is also in the normal map and in the mesh geometry; not in roughness or metallic, so no shiny ghost.
  - The emboss and relief are removed by the flat normal and the offset. Up to 0.9 cm of relief stays along the chart edge.
- **"No visible rectangular patch, new seam or damaged nearby markings/details":**
  - No rectangular patch.
  - No new seam was created, but the number chart's **existing** UV edge is faintly visible at close range where it used to run under the number.
  - No nearby marking or detail changed, but the groove's covered end is now visible as a curl.
  - Reported for review, not called finished.
- **Verification 1–4:** met, with the disclosures above. The rear-walkway, right-coast and row views reuse SR1's job 193 cameras.

## 10. Evidence index

`Saved/GarrisonRestructure/20261001-claude-serviceidentity/` (SHA256, first 16 hex digits):

| File | SHA256 | What |
|---|---|---|
| `plan/sr2_material_spec.json` | `9226057DF1AFD9F3` | Mask, donor, colour correction, panel plane, τ, seam line; source PNG and mesh hashes (r1 in `plan/superseded/`) |
| `plan/sr2_plan.json` | `7BA91A6FC203EDDE` | The two shells' before/after slot states, material paths, real Armory key |
| `tools/ib_garrison_serviceidentity.py` | `97FFD4959A207E5C` | Lifecycle tool r2 (r1 `8C318491…` in `tools/superseded/`) |
| `tools/ib_garrison_serviceidentity_material.py` | `37B6FA7F9CD886E5` | Material builder (r1 in `tools/superseded/`) |
| `tools/ib_garrison_serviceidentity_probe.py` / `_probe2.py` | `EA8DC274C5B49E3A` / `DC1B8842F7B82862` | Source probes (jobs 194 / 195) |
| `tools/ib_garrison_serviceidentity_lookprobe.py` / `2` / `3` | `6887189F07BF14D0` / `CEECE12BDA48026B` / `A9C0684FEB25920B` | In-memory GUI look probes (jobs 196–198) |
| `tools/ib_garrison_serviceidentity_check.py` | `A9B7DEAEA053F44D` | GUI paired check (job 203) |
| `tools/ib_garrison_serviceidentity_bodydetail.py` | `2F8250DED27EB69A` | Collision body detail (job 202) |
| `probe2/sr2_probe.json` | `4E514B8997F30716` | Source record: textures, graph, mesh; exports in `probe2/source/`, `probe2/mesh/` |
| `analysis/footprint_mask.json`, `material_plan_checks.json`, `donor_candidates2.json`, `seam_check.json`, `uv_window.json` | `79CE6BA341C4D4A1`, `7A9A6F08445F87CC`, `9365798B26DB518D`, `43A16638B46D29FF`, `E029283036F59BD6` | Channel, mask, donor and seam evidence (scripts `sr2_footprint_mask.py` `5AA3D802…`, `sr2_material_plan.py` `76F5589D…`, `sr2_donor_search2.py` `FE4B3250…`, `sr2_seam_check.py` `39E7D5A2…`, `sr2_uv_window.py` `C88E4331…`) |
| `lookprobe3/sr2_lookprobe.json` | `CB1F28BC253F46B3` | Job 198 variants; stills in `lookprobe3/shots/`, grids in `lookprobe3/grids/` |
| `run1/material/material_manifest.json` | `932C1CCD1BB336E9` | Material manifest (graph, flags, outputs, source hashes) |
| `run1/material-verify/si_material-verify.json` | `13143BCBA25F2AAA` | Reload verification of both assets |
| `run1/basefp/base_fingerprint.json` / `run1/copy/copy_fingerprint.json` | `08FDFEA2AB36DB9D` / `DD958EA6845FBA21` | SR1 fingerprint and the copy's (both digest `9B73E835…`) |
| `run2/apply/si_apply.json` | `56668A3F1EF9225F` | Apply report (source check, read settling, transition check) |
| `run2/apply/` and `run2/reapply/ownership_manifest.json` | both `DA3F04E2C15F6C9D` | Ownership manifest |
| `run2/verify-applied/`, `verify-restored/`, `verify-final/si_verify.json` | `B2F327714506E1A6`, `9B2A8F1D097E02E5`, `10063346DBDA13E5` | Fresh-process verify reports |
| `bodydetail/body_detail_CarrowGateGarrison_ServiceRows{1,2}.json`, `analysis/bodydetail_compare.json` | `26ACF8ACE38999CA`, `D3B81756D83FB0C0`, `5D32C396D4003DB4` | Collision body detail, 0 differences |
| `check-sr2/sr2_checks.json` | `447DFB9F54EDB897` | Job 203 record; stills in `check-sr2/editor/` (`<camera>__before-SR1.png`, `__after-SR2.png`) |
| `analysis/residue_overlay/` | `rb-number-close_overlay.png` `22F46A4B…`, `_residue_zoom.png` `2FACFCEC…`; `rf-…` `E26953DF…`, `CF64F6D1…`; `residue_overlay.json` `4DD01AEC…` | Computed outlines (`analysis/sr2_residue_overlay.py`, `6308F181…`) |
| `board/sr2-board.png` / `.jpg` | `D6D6F874013E0D03` / `0C8334CBEF9302CF` | The board (`analysis/sr2_board.py`, `EE57682E…`) |
| `analysis/log_check.json` | `232D6D85F2DF7944` | Logs and crash folders (`analysis/sr2_log_check.py`, `89DDA4A9…`) |
| `hashes/preservation-final.json` | `22B3866F91975D3A` | Preservation (`analysis/sr2_preservation.py`, `11813F11…`) |
| `hashes/shared-{before,after}-{194…203}.json` | all `3B98AA3123A05C4C` | The 17 stamps (1,560 files each; no after-196) |
| `protected-1423.json` | `A0AB1701E078D8DF` | Copy of Codex's 1,423-file list used by the stamps |
| `backup/ServiceRows2-run2-{applied,restored,reapplied,final}.umap` | `47A09DC1…`, `D43DAC89…`, `0267B9A3…`, `0267B9A3…` | Job 201 backups (correct); the receipts beside them `955BE56C…`, `2C8B945C…`, `44AEE146…` |
| `backup/ServiceRows2-{created,applied,restored,reapplied,final}.umap` | all `819EC8D8…` | Job 199 backups: all the created copy (misnamed, section 4) |

**Job scripts** (`Saved/zz_job/running/`, all exit files 0):

- 194 `A545CBD2…`, 195 `E899C464…`, 196 `E831E22E…`;
- 197 `BFBD3EF7…`, 198 `8F05D851…`, 199 `CF41EDA4…`;
- 201 `F6B05EDA…`, 202 `A0BC262F…`, 203 `5F9AFAC4…`.

They use `Saved/zz_job/serviceidentity_lib.ps1` (`0EDABA9E…`). Step logs are in `run1/logs/`, `run2/logs/`, `bodydetail/logs/`, `probe*/logs/`, `lookprobe*/logs/` and `check-sr2/logs/`.

**Provenance.** The SR2 tools are derived from SR1's, which are unchanged. They live in the evidence folder, not in `Scripts/`. There was no engine, project-setting, plugin or C++ change, and no build.
