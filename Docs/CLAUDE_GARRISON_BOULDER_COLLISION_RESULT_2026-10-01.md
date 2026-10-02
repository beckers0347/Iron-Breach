# Garrison BS2 boulder collision: result (2026-10-01)

Claude, 2026-10-01 23:28 UTC. Answers `Docs/CLAUDE_GARRISON_BOULDER_COLLISION_2026-10-01.md` (brief SHA256 `2145054629A626178C08733EC743615C57D7EBC600FD223CAAB9AB79C3B81F1E`). Evidence: `Saved/GarrisonRestructure/20261001-claude-bouldercollision/` (paths below are relative to it unless they start with `Content/`, `Docs/` or `Saved/`).

**Scope held.**

- One new disposable candidate, `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore2`, copied from BS1 (`49154B4E…`) and applied. Apart from the map and its receipt, this task wrote only four preview-local collision assets in `/Game/_GarrisonPreview_Disposable/BoulderShore2_Collision/` (every job: `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`).
- Changed: exactly BS1's 61 rocks (35 edited RS1 rim rocks, 26 BS1 rocks), resolved from BS1's receipt and ownership manifest (`E1D6E9AF…`). Two fields changed on each:
  - the static mesh: BS1's source mesh → the BS2 duplicate of that same mesh at the rock's burial depth;
  - the collision profile: `NoCollision` → `BlockAll`.
- Unchanged on the 61: relative location, rotation and scale, slot-0 material, walkability, step-up, tags, labels and folders. **No rock was moved:** no route was blocked without a valid way around (section 6).
- Every other actor is BS1's. Fresh reload: 3,508 of 3,569 actors identical, the 61 exactly as planned, 0 unexpected, 3,596 of 3,596 components with relative transforms (section 4).
- **Connor's hangar reservation is untouched:** no actor near it changed, and the nearest of the 61 (`BS1_Rock_012`) has its collision 37.5 m outside the reservation including its 6 m side bands and the straight approach (x −500…10,182, y 1,219.4…6,280.6; the right-rim rocks end at y −2,526, the left-rim rocks start at y 10,029).
- Unchanged: `SM_Mountain_05`, `SM_Mountain_Plateu_01`, every material and texture, BS1's map, receipt and evidence, Codex's review records, the live map, earlier previews and saves (section 12).
- No surf, water, forest or lighting change. No plugin, download, new art asset, shared code or project-setting change. No live promotion, Git or cleanup. The queue again holds only `153-yellow-after.hold`.

**Outcome.**

- **The collision itself is credible.** Convex pieces fitted to the visible rock above the sea surface (section 2) stop the real pawn at the visible faces, keep the camera out and take the weapon's trace there; nothing is added below the sea surface, in gaps or over open water (sections 3, 5, 7, 8). Lifecycle, ownership and negatives pass (section 4). Routes keep their connectivity with revised coast walks, the four drowns recover onto land, and no deck-end climb bypasses the wall (section 6). The rocks look the same as in BS1 (section 10), and no frame cost was measured (section 11).
- **BS2 is not gameplay-acceptable yet: recovery is not preserved (section 9).** With solid rocks the pawn can now be held on the rock band where its recovery cannot act. `Drown()` fires only when the capsule centre drops below z −35, and the safe point it returns to is the last walkable floor of any kind, rocks included. Scripted PIE with the real pawn found **11 places that hold it** (no scripted attempt reached land): 2 of 11 candidates in job 230 and 9 of 34 wedge pits found by an offline scan in job 231, plus job 230's crevice again as a control. Nine of the 11 are at the waterline: the capsule hangs between steep faces with its feet between 21 cm below and 12 cm above the sea surface, and its centre above −35.
- **A tested remedy does not close it.** Making the 61 rocks unwalkable (in memory only, job 230) stopped the pawn standing on rock tops, but the waterline crevice still held it, and still counted as a floor.
- **A decision is needed** before BS2 can go further (section 9.6): a change to the pawn's recovery code (outside this brief: no gameplay-system rewrites), or a bounded per-place geometry pass. BS2 stays applied, unchanged since job 227, as the evidence for that decision. Nothing was promoted.

## 1. At a glance

| Item | Result |
|---|---|
| **Candidate** | `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore2.umap`, SHA256 `2D642903764302EF08899122100D1A0ED77AA786701A18CCD7EF3195410FF189` (applied) |
| **Receipt** | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_BoulderShore2.json`, SHA256 `F162F20B92937172D181714811EC9A405999BC96A8A8964D78B18DB9AC7973EE`.<br>History: created `24403971` → applied `667C1F69` → restored `4F65311F` → applied `2D642903`. |
| **Collision assets** (preview-local duplicates of the two used meshes; only their simple collision differs) | `SM_BS2_Mountain_05_Outcrop` `B82152AF…` (629 convex pieces, 15 rocks), `SM_BS2_Mountain_05_Stone` `58AD5684…` (96, 9), `SM_BS2_Mountain_Plateu_01_Outcrop` `3FDDA823…` (1,079, 28), `SM_BS2_Mountain_Plateu_01_Stone` `1E0AF25B…` (90, 9). All `CTF_USE_SIMPLE_AS_COMPLEX`; nothing below the sea surface. 41,321 pieces / 1.34 million hull triangles in the level. |
| **Fidelity** | Offline, every rock, 2 cm samples: the collision surface lies within 4.1 cm outside / 5.8 cm inside the visible rock at worst (p99 ≤ 2.6 / 1.6 cm), and at most 4.1 cm out over open water. In the engine (all 61, five channels, 5,705 rays each): every rock hit lies 0.04–2.66 cm from the visible rock (median 0.67). No pass-through, no hit below the sea surface, in a gap or over open water, and no invisible collider on BS1's 894-point coast grid (section 5). |
| **Small proof first** | One outcrop (`RS1_Rock_013`) and one stone (`BS1_Rock_006`), in memory, never saved. Real pawn stopped 0.0–1.1 cm from the visible faces; camera ≥ 47.9 cm from the rock; 15/15 weapon shots `OnServerHit` on the face; negatives clean (section 3). |
| **Lifecycle** | **PASS** (section 4): copy = BS1; guarded apply and save; fresh reload shows only the planned changes; repeat is a no-op (nothing saved, receipt unchanged); ownership negatives: every conflict refused (9 in the applied state, 7 in the clean state) and the shared-tag decoy correctly not selected (once in each); restore = BS1 actor for actor, with the same digest as BS1's; re-apply; final fresh verify. |
| **Routes** (scripted PIE, real pawn) | 4/4 drowns recovered onto land; band walks: 3 stopped at a rock, 3 fell in and were returned onto rock tops, all 6 walked back; revised coast walks 39/39 and 36/36 (BS1's left waypoints now stop at a solid rock, as they should); both rim ends; rear-wall drop and ramp/gate return identical to BS1; six deck-end climbs at the full 10 s, **0 bypasses** (section 6). |
| **Camera** | No collision avoidance exists (first-person camera on the capsule axis, no spring arm, near clip 5 cm); the capsule keeps it out. Moving frame sequences at BS1's traversal frames 014 / 019: camera ≥ 52 cm from visible rock, 0 frames inside rock (section 7). |
| **Weapon** | `UHitscanWeaponComponent`, `ECC_Pawn` line trace, simple = complex on the 61. 24/24 aimed PIE shots at the two outcrops `OnServerHit` on the aimed face; 3 aimed at a Plateu stone hit the outcrop in front of it; engine traces on all 61 agree on all five channels except at two unchanged RS1 wall rocks (sections 5, 8). |
| **Recovery** | **Not preserved (the blocker).** 11 places hold the pawn on the rocks with no scripted way back to land (2 of 11 candidates in job 230, 9 of 34 wedge pits in job 231; job 230's crevice held again as a control). 9 of the 11 are at the waterline, the capsule centre above the −35 drown line. How play reaches each one was not shown; shown were falls returned onto rocks, entry jumps onto islands and a walk-off into the crevice from a placed stone top. In-memory unwalkable rocks did not close the crevice (section 9). |
| **Appearance** | Whole frames: BS2 − BS1 below a BS1-to-BS1 control (water animation). Inside the rocks' outline the comparison is mixed (more large differences on the left camera, a higher mean on the right), in short streaks at a few sunlit rock edges and the waterline; the rocks look the same (section 10). |
| **Frame rate** | No cost from the collision in a BS1/BS2/BS1/BS2 A/B (job 229). Some GUI sessions slowed to about 1 fps for a reason outside the map (section 11). |
| **Preservation** | **PRESERVED** (`hashes/preservation-final.json`, `56DE0B60…`): Codex's 2,228 records (2,224 project files re-hashed, 4 engine files through the stamps) and six BS1 artifacts match; all 16 job stamps (2,447 files) equal the first; live map `FAFFD601…`, BS1 map `49154B4E…` (section 12). |
| **Processes** | 16 engine processes, every log closed normally: 11 commandlets exit 1 (the pre-existing GameFeatureData ensure; every step complete); GUI jobs 226, 230, 231 exit 0, jobs 228 and 229 returned `0xC0000005` after "Log file closed" (the known exit-time crash, no crash report). 0 access-violation, fatal or critical lines; 16 crash-reporter folders, all the startup ensure. Map packages dirty at exit: none; content: only the four collision assets in job 230 (its in-memory test; never saved, bytes unchanged). Autosave flags False in every GUI session; 0 owned processes left (section 12). |

## 2. Method: collision that follows the visible rock

### 2.1 Why the meshes needed their own collision

`SM_Mountain_05` and `SM_Mountain_Plateu_01` are terrain tiles: a 513 × 513 vertex heightfield on a 2 cm local grid (524,288 triangles, Nanite, fallback 100 %), whose only simple collision is one convex hull over the whole tile. BS1 cuts each tile deep at the sea surface, so that hull stands metres above and around the visible rock (BS1 §2.1). With it switched off (BS1), players, the camera and weapon traces passed through all 61.

Two whole-tile options were rejected before anything was built:

- **The tile hull** (SP2's state) gives invisible walls and underwater floors.
- **The render mesh as collision** (complex-as-simple over all 524,288 triangles) would make the buried part of each tile solid. That part continues metres below the sea surface (BS1's pale skirts), so it would become exactly the artificial seabed and the land bridges between rocks that the brief forbids.

The collision therefore covers only the rock above the sea surface.

### 2.2 Probe (job 224, read-only)

- The two meshes' LOD0 render geometry, exported from the engine (vertex grid; both possible triangle diagonals of every quad kept, since the triangle export failed and the grid's diagonal could not be read).
- Each BS1 rock's exact state. Every rock has yaw only and a uniform horizontal scale; its burial level (the local height that lands on the sea surface, world z −35) is one of four values: outcrop and stone depth on each mesh (`SM_Mountain_05` 295.498 / 378.1 local cm, `SM_Mountain_Plateu_01` 268.462 / 317.699).
- Engine facts: `GeometryScript_Collision.set_simple_collision_of_static_mesh` writes convex simple collision into a mesh in a commandlet (a text import into the body setup did not cook in-process; `StaticMeshEditorSubsystem` is unavailable there).

### 2.3 The four collision assets (job 225)

- `EditorAssetLibrary.duplicate_asset` of each used mesh, twice (outcrop and stone burial depth), into `BoulderShore2_Collision/`. **The only change in each duplicate is its simple collision**, set to `CTF_USE_SIMPLE_AS_COMPLEX`. The reload check found the render facts identical to the source mesh: bounds, material slot and default material, Nanite settings, LOD count, and the LOD0 source vertex positions (hashed).
- The simple collision is a set of convex "prism" pieces fitted offline to the visible surface above that variant's burial level (`analysis/bs2_fit.py`): a 64 cm local quadtree, refined until each piece is within 3 cm of the visible surface (world, inside and outside) or a cell reaches one 2 cm quad, then merged; at most 48 vertices per piece. A few minimum-size cells keep a larger fit-time estimate (up to 5.4 cm on `SM_Mountain_05` outcrops, 6.3 cm on Plateu outcrops, `analysis/fit_report.json`); the 3D measurement below is the actual result. **Nothing lies below the burial level**, so no piece reaches under the sea surface or over open water beyond the visible rock.

| Variant (asset) | Pieces | Vertices | Hull triangles | Rocks using it |
|---|---|---|---|---|
| `SM_BS2_Mountain_05_Outcrop` | 629 | 11,299 | 20,082 | 15 |
| `SM_BS2_Mountain_05_Stone` | 96 | 1,883 | 3,382 | 9 |
| `SM_BS2_Mountain_Plateu_01_Outcrop` | 1,079 | 19,641 | 34,960 | 28 |
| `SM_BS2_Mountain_Plateu_01_Stone` | 90 | 1,979 | 3,598 | 9 |

In the level: 41,321 convex pieces over the 61 rocks (1.34 million hull triangles), against 61 single tile-wide hulls (SP2's 35 rim rocks) or none (BS1).

**Fidelity, offline, every rock** (`analysis/fidelity3d.json`): the visible render surface and the collision's exterior surface sampled at 2 cm in world space.

| Variant | Rocks | Visible surface inside or within tolerance of collision (min over rocks) | Visible rock outside collision, max (p99) | Collision outside visible rock, max (p99) | Over open water, max |
|---|---|---|---|---|---|
| Mountain_05 outcrop | 15 | 97.2 % | 4.6 cm (1.3) | 3.4 cm (2.5) | 3.1 cm |
| Mountain_05 stone | 9 | 92.0 % | 3.6 cm (1.6) | 2.9 cm (2.2) | 2.7 cm |
| Plateu_01 outcrop | 28 | 97.4 % | 5.6 cm (1.2) | 4.1 cm (2.6) | 4.1 cm |
| Plateu_01 stone | 9 | 93.7 % | 5.8 cm (1.5) | 2.9 cm (2.4) | 2.9 cm |

So the collision surface lies within a few centimetres of the render surface everywhere above the sea, mostly just outside it.

## 3. Small proof first: one large outcrop, one stone (jobs 225–226)

Before any of the 61 changed on disk, only `IBGC_RS1_Rock_013` (a `SM_Mountain_05` outcrop, the rock in BS1's traversal frame 014) and `IBGC_BS1_Rock_006` (a `SM_Mountain_05` stone) took their planned state **in memory** on the clean BS2 map; nothing was saved (map and receipt hashed unchanged).

### 3.1 Engine traces (job 225, `run1/verify-proof/proof_traces.json`, evaluated in `analysis/proof_eval.json`)

Five channels on every ray: the hitscan weapon's own query (`ECC_Pawn`, default params, simple), the same complex, Visibility simple and complex, Camera simple.

| | Outcrop `RS1_Rock_013` | Stone `BS1_Rock_006` |
|---|---|---|
| Before (BS1 state): hits on the rock, any ray | 0 | 0 |
| Vertical rays: hits; hit − planned collision | 191; median 0.0, max 0.41 cm | 21; median 0.0, max 0.10 cm |
| Horizontal rays at fixed heights: hits; visible-face entry − hit | 127; median 0.78, max 5.0 cm (min −0.22) | 46; median 0.84, max 2.4 cm (min −1.2) |
| Eye-level aim lines from the band: hits; visible entry − hit | 56/56; median 0.87, max 4.6 cm | 15; median 1.0, max 4.1 cm |
| Channels at the same point as the weapon's query | all | all (2 complex-only hits on a neighbour) |
| Rays below the sea surface, open water, gaps | 0 rock hits (24 + 51, 12, 6) | 0 (24 + 6, 12, 6; the 4 gap hits are the neighbouring outcrop, then clear) |
| Pawn-profile capsule sweeps (r 34, hh 88) from the band | 14/14 stop at the rock; clearance to the visible rock −0.30 … +0.60 cm | its 6 sweeps from the band meet the neighbouring outcrop first |

### 3.2 Scripted PIE with the real infantry pawn (job 226, `check/pie-proof/bs2_proof.json`, evaluated in `analysis/pie_proof_eval.json`)

`BP_IBCharacter_Infantry_C`: capsule 34 / 88, walk 600 cm/s, step 45 cm, walkable 44.77°, jump 420 cm/s. The camera is `FirstPersonCamera` on the capsule axis at +64 cm, with **no spring arm and no camera collision test**; only the capsule keeps it out of geometry (near clip plane 5 cm, `DefaultEngine.ini`). The weapon is `UHitscanWeaponComponent`: one `LineTraceSingleByChannel(ECC_Pawn)` per shot, simple collision, the shooter ignored; `OnServerHit` reports the hit actor.

- **Five approaches into the outcrop's faces** from the coast band (movement input, 3 s): 5/5 stopped by `RS1_Rock_013` after 155–219 cm. Capsule clearance to the visible rock at the stop **0.0–1.1 cm**, and never below 0.0 over 225 recorded positions (every second tick). First-person camera **48–76 cm** from the visible rock at the stops, never inside it. One in-game frame at each stop (`check/pie-proof/frames/`).
- **Fifteen aimed shots** of the pawn's own weapon at those faces (sights raised, spread 0.35°): `OnServerHit` = `RS1_Rock_013` 15/15; a replica of the trace hits **0.06–5.4 cm in front of the visible face** (median 1.3); impact points 0.3–1.9 cm from the visible surface.
- **Three negative shots** (directions offline-clear of every rock collision): no rock hit (the far city wall, an apartment block, the forecourt deck).
- **Stone:** a running jump landed on `BS1_Rock_006` and stood on it (capsule 1.5 cm from the visible rock); walking on, it fell into the sea and `Drown()` returned it **onto the stone** (its last grounded spot). A shot down at the stone from on top hit it 1.4 cm in front of the visible surface. A second jump flew 17 cm clear over the stone's crest without touching it (no invisible collider); the third was a planned face jump that came down in the water short of the stone (the run-up was set behind its start; recovered onto the band).

**Verdict:** credible collision: it stops the real pawn, keeps the camera out and takes the weapon's trace at the visible faces, and adds nothing below the sea surface or in gaps. The method then went to all 61 unchanged.

## 4. Lifecycle and ownership on all 61 (job 227)

Six commandlet processes, each its own `UnrealEditor-Cmd` run with the isolated `user/` UserDir and its own fresh first read (`run1/<process>/bc_<step>.json`, logs `run1/logs/`). Times UTC.

| Process | Steps | Result | Map after |
|---|---|---|---|
| apply (19:13–19:14) | verify + apply | clean copy = BS1 (3,569/3,569 identical); exactly the 61 recorded rocks given their variant + `BlockAll`; in-process check: 0 changes besides the plan (one read-settling value, see below); saved | `667C1F69` |
| applied (19:14–19:15) | verify + apply again + negatives | fresh read 3,508/3,569 identical, 61 changed as planned, 0 unexpected; the repeat apply is a **no-op** (`already-applied-verified`, nothing saved, map and receipt unchanged, 0 BS2-tagged actors); 10/10 applied-state negatives refused (below) | `667C1F69` |
| restore (19:15–19:16) | verify + restore | the 61 back to BS1's exact state; pre-save comparison with BS1: 3,569/3,569 identical, 0 unexpected; saved | `4F65311F` |
| restored (19:16–19:17) | verify + negatives | fresh read **= BS1 actor for actor, field for field** (3,569/3,569), digest `29A020B3` = BS1's own; 8/8 clean-state negatives refused | `4F65311F` |
| reapply (19:17–19:18) | verify + apply | re-applied; ownership manifest identical to the first apply (`0EDBBDD2…`) | `2D642903` |
| final (19:18–19:19) | verify + coverage | fresh read 3,508/3,569 identical, 61 as planned, 0 unexpected, 3,596/3,596 components with relative transforms; read-only coverage (section 5) | `2D642903` |

**Receipt** `…BoulderShore2.json` (`F162F20B…`): created `24403971` → applied `667C1F69` → restored `4F65311F` → applied `2D642903`.

**Exact inherited state.** The expected record of each of the 61 is BS1's record with only `mesh`, `profile` and `collision` (`NO_COLLISION` → `QUERY_AND_PHYSICS`) replaced; every other field, the materials list and the component-relative transform included, must be identical, and every other actor must be identical to BS1's. The plan carries no translation, so no transform changed.

**Ownership rule.**

- A rock is BS2-changed only if its object name, label, class, tags and component equal BS1's recorded identity (BS1's receipt and ownership manifest, which must agree) **and** its exact state equals the plan's before (apply) or after (restore) state. Exact state: mesh, full-precision relative transform (0.01 cm, 0.001°, 1e-7), slot-0 override, profile, walkability, step-up.
- BS2 adds no actor: any actor carrying `IB_GarrisonBoulderShore2`, or using a planned rock's label at another object name, is a conflict. `IB_GarrisonCB1` alone never selects anything.
- The four collision assets must be at their manifest bytes (`asset_manifest.json`, `F240972A…`) and load with exactly the planned piece counts and `CTF_USE_SIMPLE_AS_COMPLEX`.
- Any conflict refuses before a change.

**Negatives** (in memory, saving blocked; map, receipt and asset files hashed unchanged after each run; every undo returned to "no refusal"):

- *Applied state (10):* the other burial variant on one rock; its BS1 source mesh (the tile hull) while `BlockAll`; profile back to `NoCollision`; moved 10 cm; identity tag removed; an extra BS2-tagged actor; an untagged actor using a planned label; a shared-tag-only decoy (**not selected**); a collision asset not at its manifest bytes (a manifest copy recording another hash); a rock deleted. All refused or not selected.
- *Clean state (8):* the planned variant while `NoCollision` (a partial apply); `BlockAll` on the source mesh; move; untag; BS2-tagged extra; label decoy; shared-tag decoy (not selected); asset bytes. All refused or not selected.

**Read settling and signed zero.** `IB_Harbor_Surface`'s profile name reads `Custom` on a process's first read and `BlockAll` afterwards, as in BS1 (BS1 §5.3). Apply and restore logged it as read settling, and the restore carried it over to the base before its pre-save comparison. BS1's signed-zero difference did not recur: the restored map's raw digest equals BS1's (`29A020B3`), and with every −0.0 written as 0.0 both are `BB9661FD`. The applied map's digest is `A0F8F41F` (normalized `6F824237`): the 61 differ by design.

**No failed step.** Every process completed; the only refusals in the logs are the intended negative-test refusals.

## 5. Coverage on all 61 (job 227 final, read-only; `analysis/coverage_eval.json`)

**Bindings and settings, all 61:**

- Profile `BlockAll`, collision `QUERY_AND_PHYSICS`, object type WorldStatic, **Block** on Pawn, Visibility, Camera, WorldStatic, WorldDynamic, PhysicsBody, Vehicle, Destructible.
- Each rock's mesh is its planned variant (15 / 9 / 28 / 9 rocks), carrying the planned piece count (629 / 96 / 1,079 / 90), `CTF_USE_SIMPLE_AS_COMPLEX` and no other simple shape.
- Walkability `default`, step-up `ECB_YES`; not hidden; actor collision on.

**Trace coverage** (5,705 rays per channel; the weapon's query, the same complex, Visibility simple and complex, Camera):

| Set | Rays | Result |
|---|---|---|
| Vertical, on 40 random visible points per rock | 2,440 | 2,343 rock hits (2,122 on the rock itself, 221 on an overlapping neighbour of the 61); 97 first hits on the land band where the rock's visible surface lies under the band top, or on the unchanged `RS1_Rock_043`. Hit − planned collision: median 0.00, p99 0.21, max 1.41 cm |
| Gap: vertical, 15–25 cm outside each visible footprint, no planned collision below | 663 | **0 rock hits** (195 band or mainland ground, 2 `RS1_Rock_043`, 468 nothing) |
| Horizontal at mid height, 16 directions per rock | 976 | 653 rock hits (158 rays starting inside a neighbouring rock or the band excluded) |
| Below the sea surface (z −45, and vertical from −36) | 732 | **0 hits on the 61** |
| BS1's 894-point coast grid | 894 | 254 rock hits, **all within 2.5 cm of visible rock** (median 0.7); **0 invisible** (SP2: 238), **0 over open water** (SP2: 67); 0 points with visible rock above and no hit |

- **Every rock hit lies at the visible rock:** 2,996 hits, 3D distance from the hit to that rock's visible surface median 0.67, p95 1.65, p99 2.0, **max 2.66 cm**.
- **No pass-through:** no ray went 3 cm or more into visible rock before its first hit, and none crossed visible rock without one.
- **Channels agree:** of 3,005 rays with a rock hit on any channel, 2,996 have the identical hit on all five. The 9 others first meet the unchanged RS1 wall rocks `RS1_Rock_043` (8) and `RS1_Rock_042` (1), whose tile-wide simple hulls differ from their complex surface (pre-existing, outside the 61).

## 6. Routes on BS2 against BS1 (job 228, one GUI session; job 230 for the full-length climbs)

Scripted PIE with the real pawn, one attempt per route, never resumed after a stall and never teleported (the only moves of more than 150 cm in one tick are the pawn's own `Drown()` returns, listed). Raw: `check/final/bs2_final.json` (`3932CB54…`); evaluated against the visible rock in `analysis/final_eval.json` (`56EEE81A…`); figure `analysis/final_routes.png`. BS1 = job 223 (`20261001-claude-bouldershore/check/bs1_checks.json`, `6E0E97C3…`).

| Route | BS1 (job 223) | BS2 (job 228) |
|---|---|---|
| Four coast drowns (RS1's inlets) | 4/4 recovered onto land | **4/4 recovered onto land**, same floors (`Coast_L02` ×2, `Coast_R07`, `Coast_R11`); each then walked back to its start |
| Six band walks (out through the rock band to the sea) | 6/6 recovered onto land | 3 stopped by a rock before the water (`BS1_Rock_003`, `RS1_Rock_013`, `RS1_Rock_024`); 3 fell in and `Drown()` returned the pawn **onto a rock top**, its last grounded spot (`RS1_Rock_003` at the waterline, `RS1_Rock_020`, `RS1_Rock_030`). All 6 then walked back to the band. Ending on a rock top is the recovery change of section 9 |
| Left coast walk, BS1's 47 waypoints | completed | **stalled** at waypoint 7 after 6.0 s, against `RS1_Rock_003` (as required, not resumed). The engine's capsule sweep along BS1's waypoints meets rocks on 10 of 47 segments (`RS1_Rock_002`, `003`, `006`, `011`, `015`) |
| Left coast walk, **revised around the solid rocks** (39 waypoints) | — | **reached 39/39** in 19.9 s; no rock floor; capsule never closer than 20.4 cm to visible rock; sweep: 0 of 39 segments blocked |
| Right coast walk, BS1's 53 waypoints | completed | **reached 53/53** in 22.1 s (closest 9.2 cm; the sweep meets rocks on 4 segments, the pawn slid past) |
| Right coast walk, revised (36 waypoints) | — | reached 36/36 in 21.9 s, closest 22.1 cm, sweep 0 blocked |
| Six deck-end jump-climbs | 10 s each, 10–12 jumps, 0 bypasses | **0 bypasses at the full 10 s** (job 230). Left: 12 / 12 / 12 jumps, highest capsule centre 178 / 174 / 175 cm, all on the band. Right: 11 / 9 / 10 jumps, highest 214 / 364 / 317 cm; the pawn climbed onto `RS1_Rock_016` and `BS1_Rock_012` and fell back, and its 1 / 5 / 3 falls into the sea were returned by `Drown()` onto the band once and otherwise onto those rock tops (the 364 cm is a jump from the top of `BS1_Rock_012`, as in job 228). Job 228 had already found 0 bypasses, but my script's wall-clock cap ended its climbs after 5.5–6.2 s of game time (section 13) |
| Both rim ends onto the mainland | reached in 2.2 s | reached in 2.2 s (`CityGround_00`) |
| Rear-wall drop, ramp and gate return | 8/8 in 19.27 s, onto `RS1_Land_06`, back on the forecourt | **identical**: 8/8 in 19.27 s, onto `RS1_Land_06`, back on `IBGC_Forecourt_Deck_02` |

- **Revised coast waypoints** (`plan/bs2_final_spec.json`, `coast_paths[].revised_waypoints`, from `analysis/bs2_routes.py`) follow the land around each now-solid rock, keeping BS1's path wherever it is already clear; the pawn's actual tracks are `coast_paths[].trajectory` in the raw record. Nothing walks through rock and nothing was resumed.
- **No rock was translated.** No route was blocked without a valid path around, so the brief's minimum-translation rule was never triggered.
- **No wall or gate bypass.** No climb reached the deck. Standing spots on rock near the deck walls: the highest within 6 m of the forecourt edge is 207 cm (left, `BS1_Rock_009`) and 185 cm (right, `BS1_Rock_012`), so the pawn's jump apex (90 cm) stays at least 88 cm below the deck top at 385 cm (`analysis/recovery_reach.json`). In job 228 the right-end climb #2 jumped from a top on `BS1_Rock_012` to a capsule centre of 363.9 cm (feet 276 cm) and fell back.

## 7. Camera: the traversal positions 014 / 019 (job 228)

The pawn's `FirstPersonCamera` sits on the capsule axis at +64 cm, attached to the capsule. There is **no spring arm and no camera collision test**; the capsule (radius 34) is the only thing keeping the camera out of geometry. Near clip plane: 5 cm (`DefaultEngine.ini`). No camera system was changed.

Two ordered in-game frame sequences, 22 frames each, 7.5 s of game time, the pawn driven by movement input (`check/final/frames/traversal_014/`, `…/traversal_019/`; board `analysis/final_traversal_board.jpg`). Every frame records pawn, camera, floor, speed, movement mode and phase. The capsule and camera distances to the visible rock are evaluated per frame.

| Sequence | What happens | Capsule to visible rock | Camera to visible rock | Frames with the camera inside rock |
|---|---|---|---|---|
| 014 (`RS1_Rock_013`, BS1's problem frame) | approach; **stopped by `RS1_Rock_013`** at t 0.8 s (capsule 0.05 cm from the visible face); slides south along it; stopped again by `RS1_Rock_014`; moves on around onto the band | min −0.07 cm | min 52.1 cm | **0** |
| 019 (`RS1_Rock_014`) | the approach walks **up and over** the low, walkable `RS1_Rock_014` (feet up to 68 cm), down its far side to the waterline. There the pawn stands wedged at the rock's foot (MOVE_WALKING at t 2.7 s, capsule bottom below the sea surface) before walking back over the rock | min −0.42 cm | min 72.3 cm | **0** |

In BS1 the same approach at 014 walked into `RS1_Rock_013` and the camera entered the rock. In BS2 the face stops it. The waterline wedge in 019 was probed again in job 230: the pawn left it for land on the first attempt (section 9.2).

## 8. Weapon traces

The weapon is `UHitscanWeaponComponent`: `LineTraceSingleByChannel(ECC_Pawn)`, default query params (simple collision), shooter ignored; `OnServerHit` reports the actor. Simple and complex give the same hit on the 61, because the duplicates use `CTF_USE_SIMPLE_AS_COMPLEX` (section 5).

- **Outcrop `RS1_Rock_013` (`SM_Mountain_05`, job 226):** 15/15 aimed shots `OnServerHit` = the rock, 0.06–5.4 cm in front of the visible face.
- **Outcrop `RS1_Rock_014` (`SM_Mountain_Plateu_01`, job 228):** three approaches from the band, each stopped by the rock (end capsule clearance 0.25 / 1.93 / 0.30 cm; camera 71.5 / 153.9 / 75.1 cm from it), and **9/9 aimed shots `OnServerHit` = `RS1_Rock_014`**. Replica impacts 0.20–1.29 cm from the visible surface; visible entry − hit 0.06–1.76 cm.
- **Stone faces:** the three face shots planned at the `SM_Mountain_Plateu_01` stone `BS1_Rock_004` all hit the outcrop `RS1_Rock_010` in front of it along those lines (0.56–0.79 cm from its visible surface). So the Plateu stone asset was not shot in PIE. Its trace behaviour rests on job 227's coverage rays, which cover all five channels on all 9 Plateu stones. One shot down at the stone `BS1_Rock_006` (job 226) hit it 1.4 cm in front of its visible surface.
- **Negatives:** 3 shots offline-clear of every rock hit no rock (job 226). Coverage (section 5): no ray below the sea surface, through a gap or over open water hits any of the 61.
- All 12 `OnServerHit` events in job 228 are the intended rocks (`RS1_Rock_014` ×9, `RS1_Rock_010` ×3).
- **Job 230, in-memory unwalkable test (section 9.4):** two more face approaches (`RS1_Rock_013`, `RS1_Rock_014`) stopped 0.84 and 0.25 cm from the visible face, and the replica of each aimed shot hit that rock. `OnServerHit` was not recorded there: my script binds it once per session and did not bind it again after restarting PIE.

## 9. Recovery with solid rocks: the pawn can be held (the blocker)

### 9.1 How recovery works, and why solid rocks change it

- `AIBCharacter_Infantry::Tick` stores `LastSafeLocation = GetActorLocation()` on every tick where `GetCharacterMovement()->IsMovingOnGround()` is true (`Source/IronBreach/Infantry/IBCharacter_Infantry.cpp` lines 1172–1177). The code comment calls this the "last dry ground", but **any walkable floor counts**.
- `Drown()` teleports the pawn there once its actor location (the capsule centre) is **below z −35** (`DrownWaterZ`; lines 1184–1186, 1498–1522). With the capsule half-height of 88 cm, the pawn's feet can hang up to 88 cm into the sea before this fires.
- In BS1 the rocks had no collision, so the only floors near the sea were land, and nothing could hold the pawn above the water. In BS2 the 61 rocks are solid and walkable (walkability `default`, kept from BS1 as the brief requires). Two new outcomes follow:
  - **a fall into the sea returns the pawn to the last rock it stood on** (job 226's stone landing, three of job 228's band walks and two of job 230's deck-end climbs; section 6);
  - **the pawn can come to rest on rock without reaching land or the drown line**: on a rock top it cannot leave toward land, or hanging in a crevice between steep faces with its centre above −35. If such a place also counts as a floor, every later fall returns the pawn to it.
- The probes below put the pawn on such places (placement), then try to leave toward land. A place is **HELD** when no attempt ends on land. That shows the hold exists; it does not show how often play reaches it (section 9.5).

### 9.2 Hold candidates in PIE, BS2 as saved (job 230 part 1; `analysis/trap_eval.json`)

Eleven candidates: islands that the second offline recovery model (`analysis/bs2_recovery2.py`, `recovery_reach2.json`) finds reachable from land without a robust jump back, three places where the pawn ended up off the land in jobs 226 and 228, and two tiny perches (1 and 2 raster cells) as controls. For five of them an entry jump from the band was run first: four landed on the intended rock (`RS1_Rock_010`, `RS1_Rock_005`, `RS1_Rock_034` twice), the fifth (toward `BS1_Rock_006`'s top) came down in the sea and was returned to its take-off point on the coast. Then the pawn was placed on each candidate and given up to 24 escape attempts (walk, run 0.25 s and jump, jump at once; eight directions around the bearing to land).

- **9 escaped** (1–5 attempts each).
- **2 HELD:**
  - **`BS1_Rock_006`, island 66** (a 0.035 m² standing area on the stone's top, `(6296.9, 11961.4)`): 23 of the 24 attempts fell into the sea, and `Drown()` returned the pawn onto `BS1_Rock_006` every time: to wherever on the stone it had last stood (top or flank, up to 1.3 m from the placement), never to land.
  - **The waterline crevice between `BS1_Rock_018` and `RS1_Rock_025`** `(3642.85, −8357.18)`, where job 228's return probe had ended: capsule centre at z 32.2 (above −35), capsule bottom at z −55.8 (21 cm under the sea surface), held between two steep faces (74–82°). The pawn alternated between walking and falling; jumps fired only on its walking ticks (8 of 24) and none got it out.

### 9.3 Wedge scan and probes (`analysis/bs2_pits.py` → `pits.json`, `pits.png`; job 231)

**Offline scan.** The crevice is a kind of place the recovery models did not look for. `bs2_pits.py` scans for it on the planned collision of all 61 rocks:

- On a 5 cm raster per rim, it computes the resting height of the capsule lowered at each point, over the rocks, the land and the other solid pieces (water is not solid).
- It floods that height field from the outlets (open water, a resting centre below −35, land) to find the basins a sliding pawn ends up in.
- A basin whose lowest point is held by steep faces only, with the capsule centre above −35, is a **wedge pit**.

Result: **34 wedge pits** (20 left rim, 14 right), 4 of them with the capsule bottom below the sea surface. One lies 17.8 cm from the job 230 crevice.

**PIE probes (job 231, `check/pits/bs2_traps.json`).** For each of the 34, plus job 230's exact crevice placement as a control:

1. The pawn was grounded on clear land for 0.6 s, so that a `Drown()` return goes to land unless the pit itself counts as a floor.
2. It was placed in the pit and watched for 2 s.
3. If it was neither back on land nor returned by `Drown()`, it got up to 7 escape attempts: walk toward land; run 0.25 s then jump, and jump at once, each toward land and ±25°. It was grounded on land again before each attempt.

The character movement's own floor result was recorded at each pit.

| Outcome | Count | Places |
|---|---|---|
| Left by itself within 2 s (4 drowned back to land; at 2 the placement already stood on land at the land's edge) | 6 | left 11, 16, 17, 18; right 02 (the static pit next to the crevice), 05 |
| Escaped to land | 19 | mostly on the first or second attempt |
| **HELD** (7 attempts, none on land) | **9** | **left** `RS1_Rock_002`/`003` crevice (feet 21 cm under the sea surface), `RS1_Rock_011`, `RS1_Rock_010`/`011`, `BS1_Rock_006` (a second hold on that stone, 1 m from island 66), `RS1_Rock_013` (high on the outcrop, centre at z 251); **right** `RS1_Rock_025` beside the land edge (feet 2 cm under the sea surface, clear land 36 cm away), `RS1_Rock_026`, `BS1_Rock_019`, `BS1_Rock_019`/`RS1_Rock_026` |
| Control: job 230's crevice placement | HELD again | the same position to 0.1 cm |

**What the movement component reports at the 10 held places:**

- **4 count as walkable floor** (`RS1_Rock_002`/`003`, `BS1_Rock_006`, `RS1_Rock_013`, `BS1_Rock_019`/`RS1_Rock_026`). The floor sweep's normal at a crevice can be walkable, e.g. 43° on `RS1_Rock_002`, although the faces are steeper. So these places become the pawn's `LastSafeLocation`.
- **5 alternate between walking and falling** (`RS1_Rock_011`, `RS1_Rock_010`/`011`, `RS1_Rock_026`, `BS1_Rock_019`, the control; grounded on 26–30 of 60 ticks). Jumps fire only on the walking ticks. Where they fired, the pawn rose about 90 cm and came down on rock again, not on land.
- **1 is pure falling** (`RS1_Rock_025` beside the land edge: 1 grounded tick of 60). The pawn cannot jump there, and it does not reach the drown line.

The board `analysis/trap_board.jpg` shows the pawn's view at every held place.

**Together: 11 places hold the pawn** (job 230: 2; job 231: 9 more). The crevice held in all three runs: as saved in jobs 230 and 231, and with unwalkable rocks. Six are on the left rim and five on the right. By the scan's labels they involve 10 of the 61 rocks; at one of them the PIE floor was a further rock, `BS1_Rock_020`. The scan is a heuristic. Island 66 is a walkable top, not a wedge, so holds of other shapes exist, and the list is not complete.

### 9.4 Tested remedy, in memory only: unwalkable rocks (job 230 part 2)

**Method.** The four collision assets' body-setup `WalkableSlopeOverride` was set to `Unwalkable` in memory (never saved; reverted before exit; their files hashed unchanged), and PIE restarted. Then the same eleven placements, the four drowns, six band walks, both revised coast walks, two face approaches with a shot each and the six climbs were run. The 61 components carry no walkable-slope override of their own (instance flag False on all 61 in `run1/copyverify/probe_data.json`; walkability `default` and unchanged by the plan in the final verify), so the asset setting is the one the movement reads.

| Probe | Result with unwalkable rocks |
|---|---|
| Eleven placements | **8 no longer stand on rock**: 5 fell in and were returned to land, 3 slid onto land. `RS1_Rock_010` island 105 stayed put without moving, because the movement did not re-test its floor after the scripted placement; its first walk reached land. **The `BS1_Rock_018` / `RS1_Rock_025` crevice still held** the pawn (8 walk attempts), still alternating walking and falling. |
| Crevice as a floor | Its walking ticks still made it the pawn's `LastSafeLocation`. The next placement, `RS1_Rock_014`'s waterline shelf 196 m away, fell into the sea, and `Drown()` returned the pawn **into the crevice**. (In part 2 the grounding on land failed at 6 of the 11 placements, at 5 distinct land points of my spec that were not chosen clear of the rocks; at this one no floor was found at all. Where a `Drown()` return followed, it went to the last floor of an earlier probe: land twice, and for this placement the crevice. It shows the crevice counts as safe ground.) |
| Four drowns | 4/4 recovered onto land |
| Six band walks | The rocks became walls: 0 walking samples on rock, 206 on land at the rock faces. Five stopped at a rock face; the sixth pushed against `RS1_Rock_029` for its full 15 s, alternating walking and falling at land height. All six ended on land and walked back. |
| Coast walks, approaches | 39/39 and 36/36. Approaches stopped 0.84 and 0.25 cm from the visible faces, camera 48 and 72 cm away (section 8). |
| Six climbs | 0 bypasses (highest capsule centre 197 cm) |

**Conclusion.** Unwalkable rocks remove the rock-top holds and climbing, and they change how the shore plays (no standing on rocks). They **do not** remove the crevice holds. Not applied.

A check I first relied on was wrong: my "flat rock top" probe was in fact the coast beside `RS1_Rock_013` (job 229's spot). The pawn stood on `IBGC_RS1_Coast_L06`, and my probe's 34 cm floor sweep touched the rock's flank. I first read it as "the asset override has no effect". The placements show that it does (section 13).

### 9.5 What this means for the brief

The brief requires "Preserve recovery and prevent a new wall/gate bypass".

- **Wall and gate: met.** 0 bypasses in the six full-length climbs (job 230) as in job 228's shortened ones, and the rear-wall drop and the gate return are unchanged.
- **Recovery: not met.** BS2 adds places on the rock band where the pawn stays without recovery.
- **Reachability:**
  - Shown in play: falls returning the pawn onto rock tops (jobs 226, 228, 230), an entry jump from the band onto four islands on three rocks (job 230), and a walk-off from a stone top into the crevice (job 228, starting from a placed position).
  - Not shown: an unbroken path from the band into each held place.

### 9.6 Options (decision needed)

1. **Change recovery in the pawn's code** (outside this brief, which forbids gameplay-system rewrites). For example:
   - store `LastSafeLocation` only on land, coast and terrace pieces (or surfaces tagged as safe);
   - treat a pawn that stays near the water without a safe floor and without making progress for a few seconds as drowned.

   This handles every hold of every shape, keeps BS2's collision as it is, and would also cover future shore art.
2. **A bounded geometry pass on BS2:** close or open each held crevice (owned collision proxies fitted to the visible rock, or minimal translation of a stone), make the small stones unwalkable, then re-scan and re-probe. This stays inside the preview, but every fix needs its own proof, and the scan cannot promise that nothing is missed (island 66 is not a wedge).
3. **Keep BS1's no-collision rocks for play** until recovery can handle solid shore rocks; BS2 stays as the fitted-collision reference.

My recommendation is option 1, because it removes the cause rather than the instances. It needs Connor's or Codex's decision, since it is a gameplay change.

## 10. Appearance: matched BS1 / BS2 stills (job 228)

BS1 and then BS2 were loaded from disk in one session and shot through BS1's two coast-oblique editor cameras on the same tick schedule (`check/final/editor/`; board `analysis/final_stills_board.jpg`). BS2 changes no transform or material, and each duplicate mesh keeps its source's render facts (bounds, material slot, Nanite settings, LOD count, LOD0 vertex positions; section 2.3). Each pair is compared with a **control**: BS1 against BS1, job 223's still against job 228's. The control shows how much the same map differs between two renders, mostly through the animated water.

| Camera | Whole frame, BS2 − BS1: mean / pixels > 32 | Whole frame, control: mean / pixels > 32 | Inside the rocks' projected outline, BS2 − BS1: mean / pixels > 32 / max (control) |
|---|---|---|---|
| coast-left-oblique | 4.47 / 27,389 | 5.40 / 32,196 | 3.69 / 103 / 102 (4.02 / 25 / 51) of 21,346 px |
| coast-right-oblique | 6.61 / 41,357 | 7.83 / 53,486 | 4.99 / 27 / 66 (3.48 / 10 / 47) of 19,409 px |

- **Whole frames:** BS2 differs from BS1 less than BS1 differs from itself. The large differences sit in the water: waves and reflections.
- **Inside the rocks' outline** (a thin band at the waterline in these distant views; `analysis/final_still_mask_*.jpg`), the comparison is mixed:
  - left: lower mean, but more pixels above 32;
  - right: higher mean.
- In the board's difference panel these pixels sit at the waterline and in short streaks along a few sunlit rock edges. The rocks look the same in both stills. I have not traced those edge pixels further.

## 11. Frame rate

- **No collision cost (job 229, A/B in one session;** `check/perf/bs2_perf.json`, `analysis/perf_eval.json`). BS1, BS2, BS1, BS2 were loaded from disk in turn. PIE ran at six fixed spots (against a rock, facing away, pushing into it, walking past rocks, and on the forecourt about 50 m from every rock), 60 ticks each, early and late.
  - Mean wall time per tick: BS1 30.7 ms, BS2 50.5, BS1 49.1, BS2 50.1. **The slowdown after the first round hit BS1 just as much**, so it belongs to the session, not the map.
  - The adjacent pair in round 2 differs by +1.1 ms on average (−6.2 to +3.7 ms per spot, the forecourt spot far from every rock included).
  - Editor-world queries over the rock band, where BS2's queries do hit the rocks, cost the same on both maps: capsule sweeps and line traces ≤ 0.08 ms each, sphere overlaps (r 300 cm) 0.15–0.16 ms.
  - **No frame cost attributable to the collision was measured.** The session clock's 15.6 ms step limits single-tick values, so means over 60 ticks are used.
- **Slow sessions, not caused by the map** (`analysis/frame_timeline.json`, frames counted from each engine log). In jobs 223, 226, 228, 230 and 231, about 50.5 s after PIE start, Windows switched its default communications audio device to the MSI monitor's audio (job 229 saw no switch). What followed varied:

  | Session | PIE frame rate | Slow stretch |
  |---|---|---|
  | BS1 job 223 (BS1's own checks) | 6.8 and 8.4 fps | 15:50–15:52 |
  | job 226 | 22.6 fps | none |
  | job 228 | 2.2 fps | about 1 fps from 19:52 to 20:56 UTC, then about 27 fps |
  | job 229 | 26.8, then 14.2–15.4 fps | none (the drop is the A/B above) |
  | job 230 | 5.4 fps in part 1, 22.1 fps in part 2 | about 1 fps from 21:36 to 22:03 |
  | job 231 | 28.8 fps | one slower minute at the switch (22:42, about 10 fps) |

  Job 228's six climbs were cut short by that slowdown (section 13). Every job 230 and 231 probe ran on game time (fixed 30 Hz step), so the slow stretches lengthened the wall time only.

## 12. Preservation, processes and errors

**Hashes** (`analysis/bs2_preservation.py` → `hashes/preservation-final.json`, `56DE0B60…`, 22:56 UTC after the last job): **PRESERVED**.

- **Codex's 2,228 BS1-review records** (`20261001-codex-bouldershore-review/protected-current.json`, `248314E0…`): 2,224 project files re-hashed now, 2,224 match, 0 missing. The 4 engine files (`A:`) were compared through the job stamps, and their first-stamp hashes equal Codex's.
- **Codex's six BS1 artifacts:** 6/6 match. These are BS1's map `49154B4E…`, receipt `8DB374D1…`, plan `9881238C…`, ownership manifest `E1D6E9AF…`, checks `6E0E97C3…` and board `AD393265…`.
- **This task's protected set**, 2,447 files: the 2,228 plus BS1's map and receipt, BS1's completed evidence, its helper library and job scripts, and Codex's BS1 review folder.
  - All 16 stamps (`hashes/shared-{before,after}-{224…231}.json`) are identical to the first.
  - All 2,443 project files of the first stamp re-hash to it now.
  - Every job printed `SHARED_ASSET_OR_SAVE_CHANGES=0` and `CONTENT_FILES_WRITTEN_OUTSIDE_PREVIEW=0`.
- **Named:** live map `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC`, BS1 map `49154B4E…`, BS1 receipt `8DB374D1…`.
- **This task's outputs, final:** BS2 map `2D642903…`, receipt `F162F20B…`, the four collision assets `B82152AF…` / `58AD5684…` / `3FDDA823…` / `1E0AF25B…`.
  - Only jobs 224 (the copy), 225 (the four assets) and 227 (the lifecycle saves) wrote preview files.
  - Job 226 (before the lifecycle) left the clean copy (`24403971…`), its receipt and the assets unchanged. Jobs 228–231 left the map, receipt and assets at the bytes above. Each job re-hashed them.
- **Evidence manifest:** `hashes/evidence-final.json` (`32590AA3…`) hashes every file of the evidence folder (256 files, 449.8 MB, the engine user directories excepted), the outputs above and the job scripts and logs 224–231.

**Processes** (`analysis/bs2_log_check.py` → `analysis/log_check.json`, `0311F7A9…`):

| Process | Exit | Log |
|---|---|---|
| 11 commandlets (job 224: prepare, copy, copyverify; job 225: assets, verify-proof; job 227: apply, applied, restore, restored, reapply, final) | 1 each: the pre-existing GameFeatureData ensure; every step's own report is complete | closed normally |
| GUI job 226 (small proof) | 0, after 209 s | closed normally |
| GUI job 228 (final checks) | `0xC0000005` after 4,248 s, **after** its log closed and its record was complete; no crash report | closed normally |
| GUI job 229 (frame-time A/B) | `0xC0000005` after 722 s, the same way | closed normally |
| GUI job 230 (hold probes, in-memory test) | 0, after 2,541 s | closed normally |
| GUI job 231 (wedge probes) | 0, after 646 s | closed normally |

The `0xC0000005` after a closed log is the exit-time fault already seen in SR1 job 193, PF1 job 146, FF1 job 163 and SP2 job 211. It was not investigated, as before.

Every job's wrapper `.exit` is 0, and every job ended with `OWNED_PROCESSES_LEFT=0`.

**Errors, by kind:**

| Kind | Count | New? |
|---|---|---|
| GameFeatureData ensure block (`AssetBaseClassLoaded`) | 45 error lines per commandlet, 26 per GUI run | Pre-existing |
| `BP_Mech` Blueprint compile errors | 7 per GUI run | Pre-existing |
| `CurrentVisualData is NULL` | 1–4 per GUI run | Pre-existing kind |
| BS2 negative-test refusals | 32 `LogPython: Error` lines: 18 in job 227 "applied", 14 in "restored" | **New and intended** (section 4) |
| Audio-device errors (`LogAudioMixer` … `null device swap result`, `AUDCLNT_E_DEVICE_INVALIDATED`) | 4 lines, job 231 only, at the audio-device switch (section 11) | Outside the project |
| `M_AI_Foam` compile warning | 1 per GUI run; 0 compile lines name a BS2 asset or the two meshes | Pre-existing |
| Physics / static-mesh errors naming BS2 or the two meshes | 0 | — |
| Access violation, fatal or critical lines | 0 | — |
| "Failed to load" lines | 6 per process: the GameFeatureData class and optional profiler DLLs | Pre-existing |

**Crash-reporter folders:** 16 (11 in `user/`, 5 in `user-gui/`), one per process, all `CrashType Ensure`: the startup GameFeatureData ensure (`SecondsSinceStart` 0). None is a crash.

**Dirty packages and autosave.**

- Map packages dirty at exit: none in any GUI session.
- Content packages dirty at exit: none, except job 230's four collision assets. Those were dirtied in memory by its walkable-slope test; nothing was saved, and their files are byte-identical before and after.
- Every GUI session read the isolated per-user autosave flags back as False (`autosave_bAutoSaveEnable`, `…Maps`, `…Content`).
- The only file in `user-gui/Saved/Autosaves/` is the editor's 96-byte `PackageRestoreData.json`, rewritten at each GUI exit. No package was autosaved.
- The project's `Saved/Autosaves` and `DerivedDataCache` gained or changed no file during this task (only the `DerivedDataCache/VT` folder's own timestamp moved, at job 231's start).

## 13. What failed or was corrected

- **Job 224, probe:** the engine's triangle export of the two meshes failed. The vertex grid exported fine, so the offline work keeps **both** triangle diagonals of every quad: the higher one when checking whether rock lies outside the collision, the lower one when checking whether collision lies outside the rock.
- **Job 225, asset writing:** a text import of the convex elements into the body setup did not cook inside the commandlet, so the pieces are written with `GeometryScript_Collision.set_simple_collision_of_static_mesh`. The reload check confirms the piece counts, the trace flag and unchanged render facts.
- **Job 228, deck-end climbs:** my script's wall-clock cap (6 × the game-time limit + 60 s) ended all six climbs after 5.5–6.2 s of game time, because the session ran at about 1.5 fps. No bypass occurred. Job 230 repeated them at BS1's full 10 s, with 0 bypasses.
- **Job 228, stone return probes:** the scripted jump fired once the pawn had passed the take-off point. On a stone's edge it had often walked off first, so it never jumped. The probes also relied on the first recovery model, which ignores rocks in a jump's path; one return was blocked in flight by a neighbouring rock. Corrected in job 230 (jump one frame before the take-off point, only while grounded) and by the second model (section 9.2).
- **Job 228, the Plateu stone's face shots** (`BS1_Rock_004`) met the outcrop `RS1_Rock_010` in front of it. They are valid hits on visible rock, but not a PIE shot at the Plateu stone asset (section 8).
- **Job 229, timing resolution:** the session clock (`time.monotonic`) steps in about 15.6 ms on Windows. Per-tick medians are therefore quantised, and the evaluation uses each spot's 60-tick wall time.
- **Job 230:**
  - **Wrong reading, corrected.** My "flat rock top" probe stood on the coast beside `RS1_Rock_013`, not on the rock. My probes name the floor from a 34 cm sphere swept down from the capsule centre, and beside a rock that sweep touches the rock's flank. From that probe I first concluded that the asset-level unwalkable override had no effect, and I prepared a per-component variant for a further job. The placements show that the override did work, so that variant was never run. `analysis/bs2_trap_eval.py` now counts a grounded sample as on a rock only when the capsule bottom is not at the land top under the pawn.
  - **Part 2 restarted PIE without binding `OnServerHit` again**, so its two shots have replica traces only (section 8).
  - **My spec's land points were not chosen clear of the rocks.** In part 2, with unwalkable rocks, grounding on land failed at 6 of the 11 placements (5 distinct points; at the `RS1_Rock_014` shelf's point no floor was found at all), so those placements' `Drown()` returns went to the last floor of an earlier probe (section 9.4). Job 231 picks land points at least 60 cm from any rock or obstacle, and every grounding succeeded.
  - **`RS1_Rock_010` island 105 in part 2** stayed on the unwalkable rock because the movement did not re-test its floor after my scripted placement; its first walk reached land.
- **Job 231:** the placements use the static pits' positions. One pit, 17.8 cm from the crevice where the pawn was held, drained to land by itself; the control at job 230's exact position held again.
- **Offline analysis fixes** before any engine use of their results:
  - The coverage evaluation first flagged grazing hits as misses; it now measures the 3D distance to the visible surface and counts a ray as passing through only when it goes 3 cm or more into visible rock.
  - The route planner first treated the harbour water as an obstacle.
  - A raster slope estimate turned every piece boundary into a false step. Walkability now uses the pieces' own plane normals (`bs2_walk.py`).
  - My first pit scan counted the harbour water surface (`IB_Harbor_Surface`, a plane at z −35) as solid; `bs2_pits.py` leaves it out.
- **Image hashes:** the device copies of PNG/JPEG evidence images differ in bytes from the cloud copies they were written from (the transfer re-encodes them). Section 15 and `hashes/evidence-final.json` give the device hashes; JSON and scripts are byte-identical.

## 14. Limitations

- **Verification:** scripted PIE with the real pawn and movement input, at a fixed 30 Hz game step. This is not manual play, a packaged build or multiplayer.
  - Sprinting (900 cm/s) is not reachable from the scripts. It lengthens jumps from the band and so can only add reachable rock spots.
  - No AI navigation exists in the level (no nav mesh), so none was tested.
- **Holds:** placement shows that a hold exists, not how often play reaches it. The pit scan is a heuristic, and island 66 shows that holds of other shapes exist. The 11 places are a lower bound, not an inventory.
- **Unwalkable rocks** were tested in memory through the assets' body setup only (never saved). The deck-end climbs and coast walks were run with them; the full route matrix was not.
- **Camera:** it has no collision avoidance. Only the capsule keeps it out of rock: the camera is on the capsule axis, at least about 34 cm from any wall the capsule touches. A near clip of 5 cm remains.
- **Fit:** the collision follows the visible rock within a few centimetres (section 2.3). Thin slivers of visible rock up to 5.8 cm deep can lie outside the collision, mostly at tiny overhangs. No engine ray went 3 cm or more into visible rock before a hit.
- **Two unchanged RS1 wall rocks**, `RS1_Rock_042` and `RS1_Rock_043`, keep their tile-wide simple hulls, whose simple and complex surfaces differ. This is pre-existing, outside the 61 and the brief, and is the only source of channel disagreement in the coverage.
- **Cost:** 41,321 convex pieces in the level. No frame or query cost was measurable in this scene (section 11). Not measured with many pawns, projectiles or physics bodies.
- **Unchanged visual gaps** (out of scope by the brief): pale submerged skirts under the single-layer water, no surf or wet band, warm sunlit colour, `IBGC_BS1_Rock_023` hidden by its neighbours.
- **Not claimed:** manual or packaged acceptance; gameplay acceptance of BS2 (section 9); acceptance of anything beyond this preview.

## 15. Files and hashes

All SHA256 values are the bytes on the device; `hashes/evidence-final.json` (`32590AA36F4704A2687D11262B72FA27D3A99EA282ABB79B8182C2B01696A6B3`) lists every evidence file in full.

**Outputs.**

| File | SHA256 |
|---|---|
| `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore2.umap` | `2D642903764302EF08899122100D1A0ED77AA786701A18CCD7EF3195410FF189` |
| `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_BoulderShore2.json` | `F162F20B92937172D181714811EC9A405999BC96A8A8964D78B18DB9AC7973EE` |
| `Content/_GarrisonPreview_Disposable/BoulderShore2_Collision/SM_BS2_Mountain_05_Outcrop.uasset` | `B82152AFE29CDE0B4A44FA37073509A2375D3B3196C68AC5FDF931D14570AAC7` |
| `…/SM_BS2_Mountain_05_Stone.uasset` | `58AD5684BEB6C32C9D7673E4BF4ED36283F07A56561387150ABED632769CDB01` |
| `…/SM_BS2_Mountain_Plateu_01_Outcrop.uasset` | `3FDDA823BF86404A45A6FC56757A13A3CDC43836C0D227E9924290FD8FD27F35` |
| `…/SM_BS2_Mountain_Plateu_01_Stone.uasset` | `1E0AF25BF7F8FF8AE5B55F23841E498019E38F2FE93EC7C41329000907DA531B` |
| `Docs/CLAUDE_GARRISON_BOULDER_COLLISION_RESULT_2026-10-01.md` | this document (reported in the status file) |

**Tools and jobs.**

| File | SHA256 (first 8) |
|---|---|
| `tools/ib_garrison_bouldercollision.py` (lifecycle, jobs 224–227) | `14036A06` |
| `tools/ib_garrison_bouldercollision_check.py` (GUI checks, as run in job 231) | `3D747EBC` |
| As-run copies `tools/job224-as-run/` … `job230-as-run/` | `7756E5E6`, `793DE4EE`, `60B776AE` (226), `3218B9AB` (228), `BBEA263F` (229), `D9DEC4F4` (230) |
| `Saved/zz_job/bouldercollision_lib.ps1` | `E86736A1` |
| Jobs `Saved/zz_job/running/224-bc-prepare.ps1` … `231-bc-pits.ps1` (each `.exit` 0; logs in `Saved/zz_job/logs/`) | `F66D11C9`, `9F2F5691`, `0973D786`, `63CB279C`, `B5D47A4D`, `4BE24D0D`, `D386A314`, `5F2A6CEF` |

**Plans and raw records.**

| File | SHA256 (first 8) |
|---|---|
| `plan/bs2_plan.json` (the 61, before / after) | `8DE1D85E` |
| `plan/bs2_hulls.json` (the fitted pieces) | `9DAB4A93` |
| `run1/assets/asset_manifest.json`; `run1/apply/ownership_manifest.json` (= `run1/reapply/`) | `F240972A`; `0EDBBDD2` |
| `run1/verify-proof/proof_traces.json` (job 225) | `5DCA5502` |
| `check/pie-proof/bs2_proof.json` (job 226) | `30F66FA0` |
| `run1/final/bc_verify.json`, `run1/final/bc_coverage.json` (job 227) | `9989C1A3`, `EE175A1D` |
| `check/final/bs2_final.json` (job 228) | `3932CB54` |
| `check/perf/bs2_perf.json` (job 229) | `49341AE4` |
| `check/traps/bs2_traps.json` (job 230); `plan/bs2_trap_spec.json` | `BE575C21`; `5CA4B57C` |
| `check/pits/bs2_traps.json` (job 231); `plan/bs2_pit_spec.json` | `2DAA9A1D`; `41E94E14` |

**Evaluations** (offline unless noted "device").

| File | SHA256 (first 8) |
|---|---|
| `analysis/fit_report.json`, `analysis/fidelity3d.json` | `996A3E0D`, `BB1E9B1F` |
| `analysis/proof_eval.json`, `analysis/pie_proof_eval.json` | `1A4B67F5`, `798D870E` |
| `analysis/coverage_eval.json` (+ `.png` `47368947`) | `290A885F` |
| `analysis/final_eval.json`; `final_routes.png`, `final_stills_board.jpg`, `final_traversal_board.jpg` | `56EEE81A`; `770BBFCD`, `7A6C9ECE`, `F245AAB2` |
| `analysis/perf_eval.json` | `789159F6` |
| `analysis/recovery_reach.json`, `analysis/recovery_reach2.json` (+ `.png` `D22FCD36`) | `9EA33576`, `C1572413` |
| `analysis/pits.json` (+ `pits.png` `C1BC5E43`) | `C16CFFE7` |
| `analysis/trap_eval.json` (+ `trap_board.jpg` `6F974C66`) | `423454FB` |
| `analysis/frame_timeline.json` (device) | `D91079E6` |
| `analysis/log_check.json` (device) | `0311F7A9` |
| `hashes/preservation-final.json` (device) | `56DE0B60` |

Scripts: `analysis/bs2_*.py` (hashes in the manifest). The device runs the pure-Python ones: `bs2_preservation.py`, `bs2_log_check.py`, `bs2_frame_timeline.py`, `bs2_evidence_manifest.py`. The others need numpy / scipy and ran in the cloud workspace on staged copies. None imports from an earlier evidence folder.
