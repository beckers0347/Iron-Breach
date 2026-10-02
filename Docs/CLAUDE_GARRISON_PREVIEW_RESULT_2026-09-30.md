# Garrison preview result — 2026-09-30

Claude, 14:25 UTC. Answers `Docs/CLAUDE_GARRISON_APPLY_REVIEW_2026-09-30.md`.

**Scope held.**

- Only the disposable preview `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview3` and its receipt were written.
- The live `Content/LevelPrototyping/CarrowGateGarrison.umap` was `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC` before and after every job and step.
- None of the following happened: Git, locks, commits or pushes; live saves; messages to Shane; mech, menu, config or water-physics changes; a new inventory or build.

**This preview is not reference acceptance.** It is the current building-preserving plan made reviewable. Its reserve is still the shallow one in front of Command/Mess_Hall, and its control platform is still empty. Section 8 is the plan-only next proposal: a truly rear hangar reserve and a populated control platform. The real rear hangar is Connor's. Only its reservation appears.

## 1. At a glance

| Item | Result |
|---|---|
| Corrections 1–4 | Done in `Scripts/ib_layout_garrison.py`. The harness passes 38/38, including injected spawn, mesh, scale, piece rotation, prop rotation, destroy and save failures. |
| Preview copy | Made in two processes: copy and save, then a new process checks the copy against the source (2983 of 2983 actors match). The receipt records `created` = `733EE97A…`. |
| Lifecycle A (real engine) | apply+save → reload-verify → saved repeat. All passed. The repeat changed nothing and saved nothing. |
| Lifecycle B (real engine) | An outside edit is refused by apply, revert and verify. A byte restore verifies. A revert that would overwrite a later in-memory edit is refused with nothing changed. revert+save → reload-verify restores the exact clean state. An in-session round trip restores the level fingerprint exactly. Re-apply+save → verify. All passed. |
| Captures | 6 shots at 1920×1080 in `run3/shots2/`: a reference-framed overhead, a top-down view and four ground views. Captured in the GUI editor on the preview. The editor saved nothing, and the preview bytes are unchanged. |
| Play evidence | One scripted PIE drop into the channel. The pawn fell into the channel, and its capsule sank about 20 cm below where it would stand on the −35 waterline. It was back on its exact spine rest spot 1.29 s after the drop. This is consistent with the expected Drown snap-back. It is a single observation, not a play test. |
| Preservation | The live map was `FAFFD601…` at every step. 106 shared building/mesh/material files and the 4 live save files are identical in all 14 hash snapshots from 13:28 to the end. There were 0 content writes outside the preview folder and 0 owned processes left. |
| Manifest hash | Labelled; see 2.5. `3578AE17…` is the hash of the LF text and is now also the physical file. `70C8CD20…` is the same content with CRLF line endings. |

## 2. What changed

| `Scripts/` file | SHA256 (device = reviewed copy) | Change |
|---|---|---|
| `ib_layout_garrison.py` | `f429f498048abc039b669b5bec45f481d95e4e5cdaf07538b8fcb425109b4656` | Receipt lifecycle, verification of every operation, guarded exact revert, explicit target with identity remap, water collision resolved from the engine, outputs written as LF bytes |
| `ib_garrison_preview_copy.py` (new) | `652d31695c1ecf25bd05e28dcdc93ef151497cb5d9a6ccfecafed8c6e6e2d987` | Two-stage disposable copy that writes the `created` receipt |
| `ib_garrison_preview_tests.py` (new) | `e30c22ea915bad8aa48817098d4ddc88ada400a9a247739ee92f182155b0a707` | Focused real-engine tests: outside edit, in-memory revert conflict, in-session round trip |
| `ib_garrison_preview_capture.py` (new) | `92ad4f702344f4520731b51779b15446b111df361812798af5cf0b03492ac7ca` | GUI-editor shots, capsule sweeps and the PIE channel fall. Handles UE 5.8's camera signature, and one failed call no longer ends the run. Never saves. |
| `ib_garrison_rear_proposal.py` (new) | `8c24df95f6180b0211e0704fcdbc2934cc6db56f4261a13f5d0013f3191fef29` | Plan-only next proposal (section 8) |
| `ib_render_garrison_plan.py` | `d7882a4ef2764425047c2f499bcdad4e55946b62d8e815741d76a79b50ec4b84` | Adds the next-proposal panel; zone labels move clear of a relocated building |
| `ib_inventory_garrison.py` | `8ccf620ab74f0315dd3de0fdfcd5298938bc9a77ba16d7828927adb780161fd8` | Wording only: 0 simple shapes with `CTF_USE_DEFAULT` now reads "depends on the project default". Not re-run; `inventory-r3` remains the input. |

### 2.1 Saved repeat (correction 1)

The receipt is `Saved/GarrisonRestructure/receipts/<package, "/"→"__">.json`. It holds the history of verified states:

- `created`, written by the copy tool;
- `applied`, with `plan_sha256` and the engine-captured `platform_before`;
- `reverted`.

A run is accepted only when the target file's SHA256 equals the **last** entry. An `applied` entry must also carry this plan's hash. So:

- **Saved apply, then a new process.** The run is accepted. If the level matches the applied plan exactly, the result is `already-applied-verified` and nothing is changed or saved.
- **Any edit saved outside the tool** (the real test nudges one actor by 1 cm). Every mode reports `STALE TARGET` and refuses, and nothing is written. A file equal to an *older* recorded state is refused as well; nothing is assumed about it.
- **No receipt.** Refused. The two receipt-less copies left by the failed first attempts (jobs 120 and 121) are refused this way.

### 2.2 Every operation verified before the platform is retired or anything is saved (correction 2)

The apply runs in this order:

1. **Read-only preflight.** It checks all of the following:
   - the 7 props are at their source transforms;
   - the platform's five flags equal the before-state captured by the engine;
   - there are no generated actors, and no untagged actor already uses a planned label;
   - all meshes and materials load;
   - the plan has 0 problems.
2. **Spawn the 72 pieces.** Each is read back for label, run tag, mesh, material, location, rotation, scale, visibility, collision profile and collision-enabled. Setter return values are not trusted.
3. **Move the 7 props.** Each is read back for location, **rotation** and scale.
4. **Retire the old platform.** Only now is it hidden, with component collision off and actor collision off, and then read back.
5. **Check the full applied state.** Exactly one actor must exist per planned label, with no extra generated actors.
6. **Save the target, then append the receipt.**

Any failure stops before step 4 and before the save.

Apply never destroys anything: the old platform is retired reversibly. Destruction happens only in revert, where a failed removal is injected (harness check 31).

### 2.3 Guarded, exact revert (correction 3)

**Validation comes first and is read-only.**

- The target must be at its last verified state.
- The level must match the applied plan exactly: every piece, every moved prop at its planned transform, and the platform in its retired state.
- Any difference gives `REVERT REFUSED: n conflict(s)`. Nothing is changed, so later edits are never overwritten.

**Only then does it restore.**

1. The props return to their exact source transforms.
2. The generated actors are removed.
3. The platform's flags are restored from the before-state in the receipt. The order is profile, collision-enabled, actor collision, visibility, then hidden. Nothing is hardcoded.
4. The full clean-state check runs, including all five platform flags.
5. Only then are the save and the `reverted` receipt written.

There is no hash bypass.

### 2.4 Collision wording (correction 4)

The engine reports `PhysicsSettings.default_shape_complexity = CTF_USE_SIMPLE_AND_COMPLEX`. `IB_Harbor_Surface` has its own flag set to `CTF_USE_DEFAULT` and has 0 simple shapes. Under this project's default, pawn sweeps (which use simple collision) are therefore **expected** to pass through it.

The plan report now reads:

> EXPECTED REAL WATER … Expected from code and collision data; not yet observed in play.

Drown snap-back is treated as expected behaviour, not established gameplay. Section 6.3 holds the one PIE observation. No water physics or config was changed.

### 2.5 Manifest hash (Codex "Verified" item)

`3578AE173915127B6C0FBD85D88AB657FB8A6D0D5CD7018D2D81F2D16183F7A2` is the SHA256 of the manifest text with LF newlines. The old tool wrote through Windows text mode, so the physical files got CRLF and hash `70C8CD207F7B4944BF3969DABD2961C37DC3EBF287CF12D9072726CDDF951D5C`.

The fixed tool writes bytes and reports the hash of those bytes:

- `Saved/GarrisonRestructure/20260930-claude-preview/plan/manifest.csv` hashes `3578AE17…`, and its `tool_status.json` reports the same value.
- `20260930-codex-review/offline-plan/manifest.csv` and `20260930-claude-baseline/layout-replace*/manifest.csv` (`70C8CD20…`) are byte-identical to it after CRLF→LF (checked with `cmp`).

So the engine plan used here equals Codex's independent offline plan.

## 3. The disposable preview

| What | Path |
|---|---|
| Package | `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview3` |
| File | `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview3.umap` |
| Receipt | `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_CB1Preview3.json` |
| Plan (engine, read-only on the live map, 0 problems) | `Saved/GarrisonRestructure/20260930-claude-preview/plan/plan.json` (`40B7F78B368941F208C3E1B2BF72D2D3E5DFE871138004DAB7F1A512C48ED69F`) |
| Step outputs | `Saved/GarrisonRestructure/20260930-claude-preview/run3/<step>/`, logs in `run3/logs/`, shots in `run3/shots2/` (`run3/shots/` holds the failed first attempt's record), collected evidence in `run3/evidence.json` |
| Byte backups (for the restore test) | `Saved/GarrisonRestructure/20260930-claude-preview/backup/CB1Preview3-created.umap`, `…-applied.umap` |
| Job logs | `Saved/zz_job/logs/124-preview-lifecycle-a3.log`, `125-…-b3.log`, `126-preview-capture3.log` (failed capture), `127-preview-refusals3.log`, `128-preview-capture3b.log`. All five jobs exited 0. |
| Isolated UserDirs | `…/20260930-claude-preview/user` (commandlets), `…/user-gui` (GUI capture) |

**Targeting and identity.**

- Every mode except plan requires an explicit `IB_GARRISON_TARGET_LEVEL`.
- The source map is refused by name (`LIVE_WRITE_ENABLED = False`) and again at save time.
- A save is refused unless the loaded world *is* the target.
- Each planned identity is a source-map actor path, remapped deliberately by prefix: `/Game/LevelPrototyping/CarrowGateGarrison.CarrowGateGarrison:PersistentLevel.X` → `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview3.CarrowGateGarrison_CB1Preview3:PersistentLevel.X`. An identity outside the source prefix is an error.
- Before its receipt existed, the copy was checked actor for actor against the source by object name, label, class, location and rotation (2983 of 2983).
- The copy tool refuses:
  - targets outside `/Game/_GarrisonPreview_Disposable/`;
  - existing targets;
  - the source;
  - a receipt without its map.

**Why the copy takes two processes.** Jobs 120 and 121 duplicated the map and then loaded maps in the same process. The editor aborted with "World Memory Leaks" because the duplicated world was still alive.

- The copy stage now only duplicates and saves; it loads no map.
- A fresh process then loads the source and the copy, compares them and writes the receipt.
- Job 121 had also run a stale copy script, because a device commit reused an earlier upload. Every script's device hash was checked against the reviewed copy before job 124.

## 4. Lifecycle on the real engine (engine operation evidence)

Every commandlet step exits with process code 1. That code comes from the 23 GameFeatureData errors logged *before* the Python script starts, which happens in every commandlet on this project. The tool's own verdict is in each step's `lifecycle_<mode>.json` or `test_<name>.json`. The log classification is in `run3/evidence.json`.

"Process" is the commandlet exit code: `1` means the script finished and only the pre-script errors were logged; `-1` means the script raised, which is the expected refusal. Each step runs in a new editor process that loads the preview from disk, so every step after a save is also a reload. Hashes are the preview file's SHA256 after the step.

**Lifecycle A — job 124**

| Step | What | Process | Tool verdict | Saved | Preview after |
|---|---|---|---|---|---|
| `a-copy` | Copy stage: duplicate + save; loads no map | 1 | `copied` | preview created | `733EE97A` |
| `a-copy-verify` | New process: load source, then copy; compare | 1 | `complete`: 2983/2983 actors, 0 missing/extra/differing → receipt `created` | – | `733EE97A` |
| `a-verify-created` | Verify | 1 | `verified`: clean layout, platform flags = engine before-state | no | `733EE97A` |
| `a-apply-save` | Apply + save | 1 | `applied-verified`: 80 operations (72 pieces, 7 moves, platform) | **yes** | `E076D168` |
| `a-verify-applied` | Reload + verify | 1 | `verified`: 0 differences | no | `E076D168` |
| `a-repeat-apply-save` | The same apply + save again, new process | 1 | `already-applied-verified`: nothing changed | no (bytes unchanged) | `E076D168` |

**Lifecycle B — job 125**

| Step | What | Process | Tool verdict | Saved | Preview after |
|---|---|---|---|---|---|
| `b-external-edit` | Test: move `Water_Placeholder` z +1 cm and save it outside the layout tool | 1 | test pass | yes (the outside edit) | `BB73A959` |
| `b-after-edit-apply` | Apply + save | −1 | refused: `STALE TARGET` (file ≠ last verified `applied`) | no | `BB73A959` |
| `b-after-edit-revert` | Revert + save | −1 | refused: `STALE TARGET` | no | `BB73A959` |
| `b-after-edit-verify` | Verify | −1 | refused: `STALE TARGET` | no | `BB73A959` |
| (job) | Byte copy of `backup/CB1Preview3-applied.umap` back | – | – | – | `E076D168` |
| `b-verify-restored` | Verify | 1 | `verified`: `applied`, 0 differences | no | `E076D168` |
| `b-revert-conflict` | Test: move `SM_Truck_Cargo3` x +1000 cm in memory, then revert | 1 | `REVERT REFUSED: 1 conflict(s)`. Level fingerprint `53D3EAE1…` unchanged, 3055 actors before and after. Test pass. | no | `E076D168` |
| `b-revert-save` | Revert + save | 1 | `reverted-verified` | **yes** | `5CDF59AB` |
| `b-verify-reverted` | Reload + verify | 1 | `verified`: exact clean layout, including all five platform flags from the receipt | no | `5CDF59AB` |
| `b-session-roundtrip` | Test: apply → revert → verify in one session, no save | 1 | Fingerprint `234AD687…` → `F44A4D13…` → `234AD687…`, actors 2983 → 3055 → 2983. Test pass. | no | `5CDF59AB` |
| `b-reapply-save` | Apply + save | 1 | `applied-verified` | **yes** | `8FCD23B9` |
| `b-verify-final` | Reload + verify | 1 | `verified` | no | `8FCD23B9` |

The fingerprint is the SHA256 of every actor's path, label, location, rotation and scale. For static-mesh actors it also includes visibility, collision-enabled and actor collision.

**Refusal probes — job 127, real engine.** Each probe refused before loading or writing anything. The preview bytes, receipt, live map and shared files were unchanged.

| Step | Probe | Process | Refusal |
|---|---|---|---|
| `r-apply-source-target` | Layout apply+save with `IB_GARRISON_TARGET_LEVEL=/Game/LevelPrototyping/CarrowGateGarrison` | −1 | `the target is the source map …; this build never writes it (preview copies only)` |
| `r-apply-no-target` | Layout apply+save with no target | −1 | `set IB_GARRISON_TARGET_LEVEL …; this tool never guesses its target` |
| `r-copy-source-target` | Copy tool with the source as target | −1 | `the target must be a new package under /Game/_GarrisonPreview_Disposable/` |
| `r-copy-existing` | Copy tool onto the existing preview | −1 | `… already exists; pick a new name (disposable previews are never overwritten)` |

Jobs 120 and 121 also showed, on the real engine, that a copy without a receipt is refused by verify, apply and repeat.

Receipt history at the end (`Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_CB1Preview3.json`):

| State | SHA256 |
|---|---|
| `created` | `733EE97AA4ECB303CE3E591AF9883ACD60DBCD35F32BD0AED2F908E3E525CC10` |
| `applied` | `E076D168F0E45B2DAFDE61874FE6A6C58CD17C24E6778C352FA58F281A5A6CD6` |
| `reverted` | `5CDF59AB67FBAF5F8FD989C94BAC912D12A8417079A89FB37CABAA0C0BF135C1` |
| `applied` | `8FCD23B9B51906A786AF0A117FC3B8A27B0B1AB3869071AFE6B62ABF6096C585` |

The preview is left in its verified `applied` state for review.

## 5. Captures (visual evidence)

Job 128 ran the GUI editor with an isolated UserDir, loaded the preview and set the camera through the viewport; no camera actors were spawned. It took 1920×1080 high-res shots from 14:12 to 14:15 UTC.

- There were no capture errors and no dirty packages at exit, and nothing was saved.
- The preview hash was `8FCD23B9…` before and after.
- All 72 generated actors were present.

| Shot (`run3/shots2/`) | SHA256 | What it shows |
|---|---|---|
| `overhead-reference.png` | `205D8904…` | Framed like the approved reference: land and rear at the top, sea at the bottom, docks at the right. It shows the forecourt with its six buildings and the gate; the spine to the chamfered pad with the helicopter; the separated pier with the crane and trucks, with the ship berthed on its outside edge; the empty left control platform; and both water channels. The hangar-reserve markings are too thin to read at this distance. |
| `overhead-topdown.png` | `84D57FB2…` | The same from straight above. The reserve outline is faint in front of Command/Mess_Hall. |
| `ground-spine-to-pad.png` | `689E8CBF…` | Deck level from the spine towards the pad: continuous deck, the centreline marking, the helicopter on the pad, the seawall behind. |
| `ground-pad-to-hangar-reserve.png` | `A4FCF7C8…` | From the pad back to the forecourt and the rear. The buildings are unchanged. The reserve is only line markings on the deck, and no hangar exists. |
| `ground-pier-and-berth.png` | `02A4C522…` | Along the pier: trucks, the crane, and the ship hull alongside at the planned draft. |
| `ground-channel.png` | `D4552CF4…` | Down the 9 m channel between the pier (left) and the spine/pad (right). Both deck edges are clean, with water between. |

The first GUI attempt (job 126) stopped at its first camera move. On UE 5.8, `LevelEditorSubsystem.set_level_viewport_camera_info` requires a `viewport_config_key`. The capture tool now passes the active key and falls back to older signatures, and a failed call skips only its own shot. That attempt also saved nothing, and the preview was unchanged.

The capture state machine was dry-run in a stub before each GUI run, covering the 5.8 signature, the older signature and no camera API at all.

## 6. Evidence, kept separate

### 6.1 Geometric (plan, computed from inventory-r3; no engine)

- **Paths.** 15 walk paths are sampled along their polylines on the planned support. Each has 0 ground-less samples and a maximum step of 0 cm, except the city road/land ramp at 8.5 cm, which is the same as today. The approaches to the Armory, Barracks, Command, Medical and Mess_Hall doors, both gate-door approaches, PlayerStart and BP_WeaponRack all stay on deck at z = 385.
- **Footprints.** 24 footprints are checked: buildings, doors, door approaches, the PlayerStart and BP_WeaponRack anchors, and the unresolved Cube/Cube2/Cube3. All keep 100% of their support, with max Δz 1 cm and 0 lost samples.
- **Gaps.** Both 8.98 m water gaps have 0 new-deck samples. The channel between spine/pad and pier is covered today by 264 samples of the old platform, which the plan retires. The control gap has no actors standing in it.
- **Pieces and seawalls.** Seawall clearances are ≥ 31 m. The pieces have 0 tier-0 overlaps and 0 design samples uncovered.

### 6.2 Engine: editor world, not play

In the preview in the GUI editor (job 128), a standing-pawn capsule (r 34, half-height 88) was swept straight down against WorldStatic and WorldDynamic objects using simple collision. These are editor-world facts, not play.

- **Paths.** The 15 plan paths gave 1190 samples, with 0 without ground. Every non-deck hit is an object standing on or over a path: `BP_MainGateDoor` inside the gate (22), the `Helicopter` at the pad centre (17), `Docks_Crane_01` over the pier (5), and `BP_WeaponRack` at its own approach (3). None is a floor gap.
- **New deck seams.** Samples were taken 2 cm either side of each seam: forecourt|spine, spine|pad, forecourt|pier and spine|control. 16 of 16 hit decks at z 385.0 (384.9–385.0 at spine|pad).
- **Gaps.**
  - All 10 channel and control-gap probes, and 2 of the 3 old-apron probes, report `Water_Placeholder` at −35. The third old-apron probe (15500, 4800) lies on the new pad and hits `IBGC_Pad_Deck_00` at 385.
  - Read these water hits carefully. `Water_Placeholder` is a hidden 30 cm Cube slab with its top at −35. It is `QUERY_ONLY`, `OverlapAllDynamic` and WorldDynamic, and it **overlaps** pawns. An object-type sweep reports it regardless of channel response, so these hits show geometry at the waterline, not a floor for pawns.
  - No probe hit `IB_Harbor_Surface` (0 simple shapes), as the plan expects.

### 6.3 Play (PIE)

In job 128, the editor's own Play-In-Editor spawned the game's pawn, `BP_IBCharacter_Infantry_C`.

1. The pawn was set down on the spine at (12000, 2075). It came to rest at z 475.2, which puts its capsule centre about 90 cm above the deck.
2. It was then placed over the channel at (12000, 1375, 535).

| t (s) | x, y | capsule centre z |
|---|---|---|
| 15.74 | dropped over the channel | 535 |
| 15.99 | 12000, 1375 | 510.3 |
| 16.25 | 12000, 1375 | 408.7 |
| 16.50 | 12000, 1375 | 261.8 |
| 16.77 | 12000, 1375 | **34.4** |
| 17.03 | **12000, 2075** | **475.2** (its exact spine rest spot) |

At 34.4 cm the capsule was about 20 cm below where it would stand on a −35 surface, so it was passing through the waterline, not standing on it. 1.29 s after the drop it was back at its last standing spot.

This matches the expected Drown snap-back. However, the probe records positions, not which code moved the pawn, and it is one drop at one spot. It is not a play test by a person, and the control gap and other channel positions were not dropped into.

The PIE session logged one pre-existing error line, `BP_IBCharacter_Infantry_C_0: CurrentVisualData is NULL! Check Blueprint Class Defaults`. It was not investigated because it is outside this task.

## 7. Source-map and asset preservation

| Check | Result |
|---|---|
| Live map `Content/LevelPrototyping/CarrowGateGarrison.umap` | `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC` after every one of the 21 steps and at the end of jobs 124, 125, 126, 127 and 128. Each step's job stops if it changes. |
| Shared assets and live saves | 106 files: the Tripo building folders (Medical, Barracks, Armory, Command, Mess_Hall, MainGate, Helicopter), the garrison Geometries, Bastion, Generated_Materials, the ship/crane/truck meshes, the helipad marking MI, `M_FlatCol`, the live map, and the 4 `Saved/SaveGames/*.sav`. All **14 snapshots** (`…/hashes/shared-before-120.json` at 13:28 UTC through `shared-after-128.json`) are identical: 0 differ, 0 new. |
| Content writes outside the preview folder | 0 in every job (any `Content/` file with a newer write time outside `_GarrisonPreview_Disposable`). The preview folder holds only the three `.umap` files. |
| Owned processes left | 0 in every job |
| UserDir | Commandlets used `…/20260930-claude-preview/user`; the GUI editor used `…/user-gui`. `-UserDir` redirects engine-side Saved data there (logs, config, any PIE saves), and the live `Saved/SaveGames` files are unchanged. |
| Commandlet noise | Every step logs exactly the same 23 pre-script GameFeatureData ensure lines. Script-time errors appear only in the refusal steps, where the refusal is the expected result. |
| GUI editor noise (`run3/logs/capture-editor-2.log`, 34 error lines) | 26 are the same GameFeatureData ensure block. 7 are `BP_Mech` compile errors: an "Update Mech Proximity" node calls `UpdateMechProximity`, which `BP_IBCharacter_Infantry_C` no longer has. 1 is the Infantry `CurrentVisualData` line. All are pre-existing and none are from the tools. The BP_Mech errors are reported for Connor and were not touched (no mech work in this task). |

Job 120's log line `SHARED_ASSET_OR_SAVE_CHANGES=106` is wrong and should be ignored. The job helper returned a log line together with the hash table, so every file was reported as "NEW". The hash files that job itself wrote are identical, 0 differences. The helper was fixed before job 121, which reports 0.

## 8. Next proposal (plan only; nothing applied)

Files:

- `Saved/GarrisonRestructure/20260930-claude-preview/proposal/proposal.json`
- `…/proposal/plan-and-proposal.png`, with four panels: the reference, the site now, the current plan and the next proposal.

It was computed by `Scripts/ib_garrison_rear_proposal.py` from the engine plan above (`40B7F78B…`) and inventory-r3. It has 0 problems.

**P1, recommended.**

- **Truly rear hangar reserve.** The reserve sits on the rear edge (x = −500, the forecourt's rear edge), centred on the spine axis (y = 3750): x [−500, 4390] × y [1819.4, 5680.6], which is **48.9 m deep × 38.6 m wide**. It is 100% on deck.
  - Its width is limited by the main gate (+6 m clearance: the gate holds the rear edge up to y = 1219).
  - Its depth is limited by PlayerStart (+3 m).
  - The current baseline reserve is 25.7 × 60 m and sits in front of Command/Mess_Hall.
  - Only the reservation is drawn. No hangar is built.
- **Populated left control platform.** `Command` moves with its `Command_DoorFrame` as one complete assembly.
  - It goes to (12803.5, 7959.1, 380), turned −90° so that its door faces the spine.
  - Its footprint is 100% on deck and its door approach is on deck.
  - Its nearest building is Medical, 14.5 m away.
- **Rear-left.** `Mess_Hall` moves with its `Mess_Hall_DoorFrame` to (728.3, 7507.4, 380), unrotated. It is 100% on deck with its door approach on deck, 6 m from the reserve.
- **Completeness.** Both assemblies are complete: the only things inside or attached to either building are their own door frames.
- **Unchanged.** Every other building, door and anchor stays where it is: Armory, Barracks, Medical, the gate, PlayerStart and BP_WeaponRack.

**Alternatives, for Connor.**

- **P2.** A ~59 m wide rear hangar is possible only off the spine axis (y 1819–7683, centre 4751), or by moving the spine axis about +10 m. The second option puts Medical at the spine's mouth.
- **P3.** Command *and* Mess_Hall both go on the control platform, as the reference's tower and low block. They fit stacked, with a 7 m walkway between them, and the rear-left stays open.

**Unresolved; untouched in every option.**

- `Cube`, `Cube2` and `Cube3` inside Barracks have unknown ownership, so Barracks does not move.
- `BP_WeaponRack` has no association and stays.
- The three empty placeholders are untouched.
- No live-map object moved.

P1 still moves two of Shane's buildings. It is a layout proposal for Connor's decision, not an applied change.

## 9. Remaining layout decisions

All are for Connor, and for Shane where his buildings are involved. Nothing below was changed in the live map.

1. **Structure.** Is the preview's spine, separated pier, 9 m water channels and chamfered pad acceptable as the structural base? This is the building-preserving baseline, not reference acceptance.
2. **Rear hangar and control platform.** P1, P2 or P3 (section 8). P1 and P3 move Shane's Command and Mess_Hall as complete assemblies. The hangar width is 38.6 m on the axis (P1) or about 59 m off the axis or with a shifted spine (P2).
3. **PlayerStart.** It limits the reserve's depth. Moving it forward would allow a deeper reserve in any option.
4. **Unresolved associations.** Who owns `Cube`/`Cube2`/`Cube3` inside Barracks, whether `BP_WeaponRack` belongs to anything, and what the three empty placeholders are. All are untouched and none are guessed.
5. **Props.** The helicopter is at roll −17.3° with its pivot 377 cm below its apron: a deliberately downed prop or a misplaced import? The ship's draft is set with the hull bottom 300 cm under the waterline because the mesh's real waterline is unknown. Judge both on the captures.
6. **Water gaps.** Falling into a gap is expected to snap the player back via Drown (6.3 has the one observation). Whether to add rails, a drown volume or harbour collision is a gameplay decision; it was not changed here.
7. **Land road side.** The road enters at the hangar's image-right, where the gate is today; the reference draws it at image-left. It is kept because the gate is Shane's.
8. **Before any live integration.** The map owner and lock need to be settled, Codex's review and test of this candidate completed, and an explicit decision taken to enable a live write. That needs a reviewed change to `LIVE_WRITE_ENABLED`; this build cannot write the live map.

## 10. Cleanup after review

Disposable and not for commit. Delete after review:

- `Content/_GarrisonPreview_Disposable/`: three files.
  - `CarrowGateGarrison_CB1Preview3.umap` is this preview.
  - `CarrowGateGarrison_CB1Preview.umap` and `…_CB1Preview2.umap` are orphans from the crashed jobs 120 and 121. They have no receipt, so the tools refuse them.
- `Saved/GarrisonRestructure/receipts/`
- `Saved/GarrisonRestructure/20260930-claude-preview/backup/`
- `Saved/GarrisonRestructure/20260930-claude-preview/user*` (the isolated UserDirs)

Keep the plan, `run3/` evidence and the proposal for review. The preview folder holds no external-actor packages, so no `__ExternalActors__` entries were created. I did not delete anything: this session cannot delete files in the project, and deleting them is Connor's or Codex's call.
