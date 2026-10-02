# Garrison current baseline: result

Prepared by Claude, 2026-09-30 12:45 UTC, for Codex's review. Brief: `Docs/CLAUDE_GARRISON_CURRENT_BASELINE_REVIEW_2026-09-30.md`. Preparation only. **Nothing was applied, nothing was saved.**

> **Erratum (2026-09-30 14:25 UTC, after Codex's review).**
>
> 1. `3578AE17…` below is the SHA256 of the manifest's LF text. The physical `manifest.csv` files this run wrote are CRLF and hash `70C8CD20…`; the content is the same.
> 2. "Cannot hold a walking pawn … not complex-as-simple" overstated the evidence. The mesh's own flag is `CTF_USE_DEFAULT`, which inherits the project default (`CTF_USE_SIMPLE_AND_COMPLEX`). Pawn sweeps are therefore *expected* to pass through it, and Drown snap-back is expected, not established. One scripted PIE drop on the disposable preview later matched that expectation.
>
> See `Docs/CLAUDE_GARRISON_PREVIEW_RESULT_2026-09-30.md` §2.4, §2.5 and §6.3.

## Outcome

- The inventory and layout tools now use explicit actor identities. All folder-based building and door logic is gone.
- The structural plan fits the approved reference around Shane's new buildings **without moving, deleting or replacing any of them**:
  - the rear service forecourt;
  - a reserved hangar site (outline only);
  - the central spine;
  - a forward octagonal pad;
  - a left control platform;
  - a right pier with the ship berthed outboard;
  - real water gaps between them.
- The engine dry run is clean:
  - 0 blocking problems, and the read-only apply preflight is CLEAN.
  - The plan is repeatable: two runs produced byte-identical manifests (SHA256 `3578AE17…`).
  - The map hash stayed `FAFFD601…` from before to after, and no package was written during the jobs.
- **New fact about water.** The harbor surface cannot hold a walking pawn. Its mesh has 0 simple collision shapes and is not complex-as-simple, so the BlockAll profile does nothing for movement. A player who steps into a gap falls through the water plane, and Shane's `Drown()` snaps them back to dry ground. The gaps therefore behave like the rest of the harbor. This comes from collision data, not play, so it needs a PIE check.

![plan](../Saved/GarrisonRestructure/20260930-claude-baseline/layout-replace/plan.png)

`Saved/GarrisonRestructure/20260930-claude-baseline/layout-replace/plan.png` has three panels: the reference, the site now, and the plan. The site panels use the reference's framing: land at the top, the docks side (-Y) on the right.

## Changed tool files (all in `Scripts/`)

| File | State | SHA256 (first 12) | What changed |
|---|---|---|---|
| `ib_inventory_garrison.py` | revised (rev 2) | `71079d137358` | See the note below. |
| `ib_layout_garrison.py` | rewritten | `52f88db3b16b` | No folder roles, no `Main Gate` folder frame. It is described in the next section. |
| `ib_probe_garrison_support.py` | revised | `c564dcb94c2a` | See the note below. |
| `ib_classify_commandlet_log.py` | new | `d45130e1c570` | Plain Python. It splits a commandlet log at script start, so engine errors are separated from tool results. |
| `ib_render_garrison_plan.py` | new | `9d51d39b7cae` | Plain Python with matplotlib. It draws the reference, the site now and the plan. |

**Inventory (rev 2):**

- Buildings are resolved by label and mesh to one full actor path. Each door is resolved by its own label.
- It records attachment, BP components and collision through getter methods, plus the map SHA256 before and after.
- It records the platform's upward faces and an explicit list of unresolved items.
- Rev 2 fixes water detection. Class is now checked before name, so `Seawall_*`, `Act4DeepWaterDirector` and the guard tower are no longer called water.
- Rev 2 records local bounds and pawn-blocking collision geometry for each prop, water and platform mesh, read from the mesh's BodySetup.

**Probe:**

- Its points come from the current doors, gate, ramp and apron.
- It reads collision through getter methods and adds must-hit and must-miss controls.
- Its verdicts are cautious.

Pre-change copies are in `Saved/GarrisonRestructure/20260930-claude-baseline/tools-before/` (layout `dcb29630…`, inventory `89f92b93…`, probe `f115356e…`, capture `e2c6f246…`).

`ib_capture_garrison.py` is unchanged. It reads the plan.json `frame` keys, which the new plan writes. Its fallback without a plan still looks for the old `Main Gate` folder, so run it after a plan exists.

### What the new layout tool does

- **Reads, never guesses:**
  - Building and door identities come from `elements.json`.
  - The ground is derived from the platform mesh's own triangles and checked against the geometry the plan was designed on. The upper outline must match within 5 cm, and the land ramp must be planar and in place. If either fails, the tool refuses.
  - The frame comes from the land ramp and gate (land is -X) and from the docks (image-right is -Y). A mirrored or turned site refuses.
- **Stale guards:**
  - The map SHA256 from the inventory must equal the file on disk.
  - The package hash of every relied-on mesh is recorded: Body2, the six building meshes and the four re-homed prop meshes. Apply refuses on any difference.
- **Preservation checks:**
  - Every preserved footprint is sampled on a 50 cm grid, corners included. Old ground (platform triangles) is compared with new ground (deck pieces).
  - 15 gameplay paths are sampled every 50 cm.
  - Prop targets must be fully on deck, or fully in water for the ship.
  - Gaps must hold no deck and no standing actor.
  - Seawalls keep at least 15 m clearance.
- **No coplanar overlap.** Each deck shape becomes disjoint axis-aligned boxes plus one rotated filler per chamfer. Fillers sit 1 cm under the deck, so nothing z-fights. The pieces tile the design exactly: 0 uncovered samples and 0 outside it.
- **Apply safety** (not run):
  - A complete read-only preflight checks the map hash, package hashes, each move's class, label and source transform, the platform state and asset loads.
  - Pieces are reconciled by label under the run tag `IB_GarrisonCB1`, so a second run changes nothing.
  - Props move after the decks are verified. The old platform is treated last.
  - Any failed operation stops the run before a save. A save happens only with `IB_GARRISON_SAVE=1`.
  - `IB_GARRISON_REVERT=1` undoes everything.
- **Tested before the device run.** A mocked `unreal` API exercised these paths:
  - plan;
  - apply (72 pieces, 7 moves, platform treated last);
  - a repeat apply (0 created, 72 updated);
  - revert (7 returned, 72 removed, platform restored);
  - refusals with nothing changed for a displaced actor and for a missing asset;
  - save only on request.

## Dry-run evidence

All paths are under `Saved/GarrisonRestructure/20260930-claude-baseline/`.

| Run (UTC) | Output | Result |
|---|---|---|
| Job 100, 11:52: inventory r1 and probe | `inventory/`, `probe/support-probe.json` | Inventory complete, 0 tool errors. Probe: collision getters read with 0 errors. All 30 traces in 3 forms returned no hit, **including the city-ground control that must hit**. A commandlet world answers no scene queries, so no collision conclusion is drawn from traces. |
| Job 110, 12:29: inventory r2 and layouts | `inventory-r2/`, `logs/layout-*-commandlet.log` | **Superseded.** r2's simple-collision counts were `-1`, the StaticMeshEditorSubsystem's error code in a commandlet. The layout runs hit a bug in the engine-only path (`UnboundLocalError`), now fixed. The logs are kept. |
| Job 111, 12:36: inventory r3 | `inventory-r3/` | **Authoritative.** Complete, 0 tool errors. Counts are read from each BodySetup. As a sanity check, the Engine Cube shows its 1 box. |
| Job 111: layout, replace mode | `layout-replace/` (plan.json, report.txt, manifest.csv, tool_status.json, plan.png) | 0 problems, 0 tool errors. Assets load 3 of 3. The deck mesh has 1 simple box, so decks block pawns. The read-only apply preflight is **CLEAN**, with 7 moves to do. |
| Job 111: layout, replace repeat | `layout-replace-repeat/` | Manifest identical: `3578AE173915127B…` |
| Job 111: layout, keep mode | `layout-keep/` | 0 problems. It builds only the reserve outline. |
| Map hashes | `map-before/after-hash-110.json`, `…-111.json` | `FAFFD601EE41…` before and after every run. |
| Job summary lines | `Saved/zz_job/logs/111-garrison-plan.log` | `CONTENT_PACKAGES_WRITTEN_DURING_JOB=0`, `OWNED_PROCESSES_LEFT=0` |
| Log classification | `logs/*-111.classified.json`, `logs/inventory-r3-commandlet.classified.json` | See below. |

**Log classification.** Every commandlet ends "Failure - 23 error(s)". All 23 are logged before the script starts: the GameFeatureData handled-ensure block. None are logged while the tools run, and each tool reports success. The inventory's 40 script-time warnings are Python deprecation notices from scanning actor properties, plus the known Body2 "Allow CPU Access" notice.

**GameFeatureData cause:** `Config/DefaultGame.ini` (fed25b7) scans a GameFeatureData primary asset type while the GameFeatures plugin is not enabled. It was left unchanged. Enabling the plugin or dropping the row is an engine-config decision.

## The structural plan (replace mode, world cm, deck top z 385)

| Reference element | Plan | How the existing work fits |
|---|---|---|
| Rear hangar, top centre | **Reserved, not built.** x 1822–4390, y 750–6750: 60 m wide × 25.7 m deep, mouth +X on the spine axis (y 3750). Outline markings only. | Command and Mess_Hall already hold the rear edge, so the reserve sits directly in front of them. The reserve is the rearmost clear site the checked search found. |
| Rear service forecourt with service buildings | Body2's upper deck at its own height (z 385), rebuilt in place. Its diagonal seaward edge is squared off at x 10182, where the old 11° terrace slope becomes deck. | Service buildings: Barracks (image-right), Armory and Medical (image-left), Command and Mess_Hall (rear). Also SM_MainGate_Tripo (land gate), PlayerStart and BP_WeaponRack. **All transforms unchanged.** |
| Land road beside the hangar | The land ramp is rebuilt at its exact slope (z 10 to 385, 9.5°). | The city ramp leads to the gate. It enters at the hangar's image-right; the reference draws it at image-left. The gate is Shane's, so it stays. |
| Central spine | x 10182–14532, y 1825–5675: 38.5 m wide (0.31 of the forecourt width, as in the reference) × 43.5 m. | The gate road runs along it (dashed centre line from the reserve's mouth to the pad). |
| Forward chamfered pad | Regular octagon, centre (17232, 4525), 54 m across flats. It sits 7.75 m image-left of the axis, as in the reference, so its image-right flat continues the channel wall. | The Helicopter is re-homed onto it. |
| Left control platform (tower and low block) | x 11082–14532, y 5675–10275, outer seaward corner chamfered. 9 m of open water separates it from the forecourt. | Built empty. Command is the site's tower but stays in the forecourt. |
| Right pier, ship berthed outboard | x 10182–18600, y −1275 to 925 (22 m wide), with a 9 m channel to the spine and pad. | Docks_Ship_Hull is berthed outboard. Docks_Crane_01 and the four trucks are re-homed onto the pier. |

**Totals:**

- 12 deck or ramp boxes, 9 chamfer fillers and 51 no-collision markings: reserve outline, spine dashes and pad ring. That is 72 generated actors, tag `IB_GarrisonCB1`, folder `Carrowgate Garrison/Structure CB1`, label prefix `IBGC_`.
- Material: `Concrete_Mat`, the platform's own world-aligned material, so scaled cubes don't stretch and the look carries over. Markings use `MI_Landmass_HelipadMarking`.
- New decks cover 20,658 m². The old platform had an upper deck of 11,267 m² (z 385) and an apron of 7,571 m² (z 85). Everything inside the old outline that isn't rebuilt becomes open water.

**One level.** All new decks share the forecourt's height. The old z-85 apron and its slope go, so no new ramps are invented. The pier stands 4.2 m above the water.

## Preservation evidence (from `layout-replace/report.txt`)

- **24 preserved footprints:**
  - 6 buildings, 6 doors, 7 door approaches (6 m out; both sides of the gate), PlayerStart, BP_WeaponRack, and Cube, Cube2 and Cube3.
  - All keep **100 %** of their deck samples at the same height. The largest difference is 1.0 cm, where the gate's corner overlaps a ramp-head chamfer filler; tolerance is 2 cm.
  - Medical gains flat support on 5 corner samples that overhung the old slope.
- **15 paths, no gap at any 50 cm sample:**
  - city road to ramp to gate (9.5° ramp, as today);
  - gate to forecourt to spine to pad;
  - hangar mouth to spine;
  - PlayerStart to spine;
  - spine to control platform;
  - forecourt to pier end;
  - forecourt to every door approach and anchor.
  - All are flat at 385 except the ramp.
- **Untouched:**
  - Shane's carved doorway collision: each building's complex-as-simple `*_Collision` mesh.
  - All `BP_DoorFrame_C` doors, and the gate's `BP_MainGateDoor`.
  - The mission directors. Act1 to Act5 reference only each other (`previous_act_director`, chain 2→1, 3→2, 4→3, 5→4 complete) and an optional `GarrisonMech` soft pointer. No director code uses world positions, so the layout can't break mission logic.
  - PlayerStart, so the Carrow Gate arrival path is unchanged.
- **Not verified:** walking in play. Deck walkability rests on geometry and the Cube's collision setup. A commandlet cannot trace, so PIE is required after apply.

## Water gaps: proposed appearance vs verified behaviour

- **Appearance.** Two named gaps: the channel between spine or pad and the pier, and the gap between forecourt and control platform, both 9 m. There are also V-notches where the spine meets the pad, and open water wherever the old apron is not rebuilt.
- **No invisible collidable platform.** In replace mode the old `GarrisonPlatform_New` (StaticMeshActor_167) is:
  - hidden, with the component invisible and hidden in game;
  - set to no collision on the component and off on the actor.
  - Its prior state is recorded. It is applied last, only after every new deck exists and is verified, and `IB_GARRISON_REVERT=1` restores it.
  - Gap checks found 0 deck samples in either gap, and no non-hidden actor above the waterline in them.
- **Behaviour, from collision data:**
  - `IB_Harbor_Surface` (SM_Bastion_Harbor) has 0 simple collision shapes and `CTF_USE_DEFAULT`. Pawn movement therefore passes through it despite its BlockAll profile.
  - A player who steps off a deck falls. Once the capsule centre is below `DrownWaterZ` (−35), `Drown()` teleports them to their last grounded location.
  - This is how the harbor already behaves at every existing quay edge.
  - `Water_Placeholder` is hidden and overlap-only.
  - Visibility traces that use complex collision can still hit the water plane.
- **Correction.** Earlier in this session I assumed from the BlockAll profile that the water was walkable. The mesh data shows it isn't. That assumption was never written into the shared docs.

## Moves (replace mode only; nothing of Shane's buildings, doors or anchors)

These stood on the old apron (z 85), which becomes water. Each is keyed by full actor path, with absolute source and target.

| Actor | From → to (loc, yaw) | Why |
|---|---|---|
| Docks_Ship_Hull (StaticMeshActor_137) | (11757, −3352, 80) yaw −45 → (15111, −2218, −335) yaw 0 | Its local box is 57.8 × 12.9 m (long axis local X). It is berthed parallel to the pier, 3 m off its outboard edge. The hull bottom is 3 m under the waterline, which is a visual call. It had been sitting on the concrete apron 1.15 m above the water. |
| Docks_Crane_01 (StaticMeshActor_138) | (11190, −5073, 80) yaw −135 → (15112, −173, 380) yaw −90 | On the pier, abreast of the ship. It turns +45° with the dock line, so it stays square to the berth. Its 20 m box fits the 22 m pier. |
| SM_Truck_Cargo, 2, 3, 4 (StaticMeshActor_62/64/66/68) | z 85 → z 385, yaw 0 kept | A row on the pier's inboard half, in their original x order, kept 3 m clear of the crane. |
| Helicopter (StaticMeshActor_372) | (14429, 4570, −292) → (16907, 4533, 8) | Centred on the pad and raised 300 cm with its deck, rotation kept. See the unresolved list. |

## Unresolved associations and ownership (owner decisions; none guessed)

1. **Map owner.** CarrowGateGarrison.umap is Shane's rebuild (fed25b7). Hiding his platform and re-homing his props needs one agreed owner before any apply. Not contacted, per instructions.
2. **Cube, Cube2, Cube3** (StaticMeshActor_69/70/71) are inside Barracks' footprint, but no label, folder or attachment ties them to it. They are held in place; the plan neither adopts nor moves them. They may be Shane's interior blockers.
3. **BP_WeaponRack_C_2** is 265 cm outside Armory's footprint and has no association. It is held in place and stays on deck.
4. **Doors.** All six are associated by their own labels. None is attached to its building, so any future building move must move its door explicitly.
5. **Broken placeholders, held and rendering nothing:**
   - `concrete_bunker_3d_model` (StaticMeshActor_293, no mesh, at 9000, −3000);
   - `harbor guard tower 3d model` (Actor_1, no bounds);
   - `2026-09-04-10-03-41-983` (Actor_0, empty, scale 1000 at the origin).
   - Delete or repair is the owner's call.
6. **Helicopter pose.** Roll −17.3°, with its pivot 377 cm below the apron it stood on, so part of it sits inside the old platform. It could be a deliberately downed prop or a misplaced import. The plan keeps its pose relative to the deck.
7. **Ship and crane.** Draft (3 m) and crane orientation are visual calls to confirm after apply.
8. **Navigation.** The level has no NavMeshBoundsVolume or RecastNavMesh, before or after. Adding one is a separate decision.
9. **Old foam strips.** 28 `Surf_*` actors in `Foam` are hidden at z −430. They are untouched and trace the old outline, so delete them if they are no longer wanted.
10. **GameFeatureData ensure.** Engine config (above). Unchanged.

## Decisions for Connor

- **Hangar reserve:** 60 × 25.7 m. It is limited at the rear by Command (6 m clearance) and at the front by PlayerStart (3 m). Moving PlayerStart forward would open a ~61 m-deep site (x 1822–7955).
- **Land road side:** it enters at the hangar's image-right, not image-left as drawn.
- **Control platform:** built empty. Moving Command there would match the reference's tower more closely, but Command is Shane's building and outside this pass.
- **Single level:** the old apron level goes, and the pier is a 4.2 m quay.
- **Keep mode instead:** it leaves the platform untouched and only marks the reserve. It cannot produce the reference's gaps.

## Review instructions for Codex

1. **Look:** `layout-replace/plan.png`, `report.txt` and `manifest.csv`. The manifest has one row per operation: create, move, hide+no-collision and hold, each with full paths and from/to transforms.
2. **Re-run read-only.** It changes nothing and saves nothing. With the editor closed, run each script as `UnrealEditor-Cmd.exe "<proj>" -run=pythonscript -script="<Root>/Scripts/<script>" -unattended -NoSteam -SCCProvider=None -NullRHI -UserDir=<sandbox> -abslog=<log>`. Leave `IB_GARRISON_APPLY`, `IB_GARRISON_SAVE` and `IB_GARRISON_REVERT` unset.
   - **Inventory** (`ib_inventory_garrison.py`): set `IB_GARRISON_OUT=<inv>`.
   - **Layout** (`ib_layout_garrison.py`): set `IB_GARRISON_INVENTORY=<inv>` and `IB_GARRISON_OUT=<dir>`. Set `IB_GARRISON_PLATFORM_MODE=keep` for the alternative.
   - **Geometry only, no engine:** `python Scripts/ib_layout_garrison.py --inventory <inv> --out <dir>`. UE's bundled Python works.
   - **Figure:** `python Scripts/ib_render_garrison_plan.py --plan <dir>/plan.json --inventory <inv> --reference References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`. This needs matplotlib.
   - **Logs:** `python Scripts/ib_classify_commandlet_log.py <log>`.
3. **When an apply is authorized** (not part of this task):
   1. Close the editor and back up `Content/LevelPrototyping/CarrowGateGarrison.umap`.
   2. Confirm the map hash is still `FAFFD601…`.
   3. Run the layout with `IB_GARRISON_PLAN=<reviewed plan.json>` and `IB_GARRISON_APPLY=1`, without save, and confirm the preflight passes and all operations report success.
   4. Repeat with `IB_GARRISON_SAVE=1`.
   5. Capture with `ib_capture_garrison.py`.
   6. PIE checks: spawn at PlayerStart; walk gate to forecourt to every door; walk the spine to the pad, the control platform and the pier; step into the channel and confirm the Drown snap-back; open the doors; run the Carrow Gate arrival check.
   7. To undo, run `IB_GARRISON_APPLY=1 IB_GARRISON_REVERT=1` (plus save) or restore the backup.

## Not done, by instruction

No apply or package save, no live-save changes, no Git, locks, commit or push, and no messages to Shane. No BP_Mech work and no hangar construction. The accepted menus are unchanged.
