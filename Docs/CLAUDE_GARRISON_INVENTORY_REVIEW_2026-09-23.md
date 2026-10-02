# Actual garrison inventory review — next implementation pass

Codex ran your inventory and plan scripts in Unreal, read-only, with separate absolute UserDirs and APPLY=0 / SAVE=0. The inventory completed on September 23 at 01:25:55 UTC, with 3,294 actors and 38 distinct placed static meshes. No apply or garrison capture was run. The current plan is not suitable for application.

## Actual evidence to read

All output is under `Saved/GarrisonRestructure/20260923-inventory/`:

- `inventory/actors.json` — full actor paths, labels, folders, transforms and world bounds. Read this locally; it is the evidence missing from the previous pass.
- `inventory/{clusters,meshes,anchors}.json`, `inventory/summary.txt`.
- `layout/plan.json`, `layout/report.txt` — actual read-only plan, with the incorrect frame and proposed moves; use it to diagnose, not apply.
- `inventory.log`, `plan.log` and map hashes.

### The main error is confirmed

The chosen deck is **1,042 m by 1,880 m**, centred at `(-35900, 0)` cm, with claimed top Z=2248. It includes 1,259 actors and 97% of the entire built footprint, including mainland ground and vegetation. It is not the garrison. Your 10 proposed moves relocate vegetation groups such as `Belt_013_01`, `Belt_036_02` and `Fringe_02_02`, plus mainland buildings, by hundreds of metres. The actual garrison structure group is excluded. There are 49 deferred groups, not 49 garrison building decisions to make.

The real existing platform is unambiguous in the inventory:

- Label `GarrisonPlatform_New`, folder `Carrowgate Garrison/Ground`.
- Mesh `/Game/LevelPrototyping/Garrison/Geometries/Body2.Body2`.
- World bounds centre `(6952.08, 1094.67, 10.0)` cm; half extents `(10452.08, 8897.97, 375.0)` cm.
- It is excluded from the deck heuristic because its half-height is 375, above TALL=240. Meanwhile low walls/roofs/foliage join the wrong deck group.
- Its bounding-box maximum Z is not proof that every point on its complex footprint has that surface height. Account for actual support/height at planned locations.

## Use existing authored groups and assets

The actor folders already identify coherent building assemblies: `Carrowgate Garrison/Barracks`, `Mess Hall`, `Armory`, `Command & Comms`, `Sensor Array`, `Watch Tower`, plus `/Lighting` subfolders. Those groups include walls, roofs, floors, furnishing and door actors. A tall-static-mesh-only proximity cluster is not a building: it leaves roofs, doors and lamps behind and can merge neighbouring buildings. Use the actual folders/actor paths and verify their contents and bounds.

There is already a ship: `Docks_Ship_Hull` in `Carrowgate Garrison/Docks / Harbor`, mesh `/Game/LevelPrototyping/AIModels/SM_Ship_Hull.SM_Ship_Hull`, bounds centre `(13199.31, -4000.77, 530)`, half extents `(1051.32, 234.56, 450)` cm. Existing dock cranes and `/Game/TripoModels/Seawall_Main/Seawall_Main.Seawall_Main` are also present. The mesh catalogue only inventories placed meshes, not every asset available in Content; don't equate an absent entry with a missing project asset.

The existing platform, engine cube/cylinder meshes, `SM_ChamferCube`, materials and these props provide useful starting points. You may author narrowly scoped platform geometry, road/landing markings and materials needed to match the reference; an exact pre-existing marking asset is not a prerequisite. Reuse suitable art and document genuine fidelity limits.

Act II–V previous-act references resolve in `anchors.json` to the existing preceding director actors. Other optional properties were omitted by the getter when None or an exception occurred, so omission does not distinguish an unset reference from failed extraction. Preserve that uncertainty until the inventory reports it explicitly.

## Corrections required before an apply pass

1. **Explicit scope and frame.** Derive the garrison frame from the verified platform/site actors, not the largest scene cluster. Exclude unrelated mainland, town, mountain and vegetation folders from move candidates. Keep the reference's left control platform and right ship dock correct in the comparison camera. The current `side = (-sea.y, sea.x)` is player-facing-seaward right, whereas the aerial looks landward; verify image handedness to avoid mirroring it. Record numeric yaw/pitch/roll rather than parsing a guessed `Y=` string; the actual run fell back to -Y.
2. **Whole assemblies and gameplay.** Plan coherent groups with their doors, roofs, lighting and relevant furniture. Preserve actor identity and reference wiring. Spatial restructuring may deliberately relocate a door, rack or player start with its associated building, provided every such change is explicit in the manifest and preserves safe spawn/approach and mission function; don't leave gameplay objects detached from relocated architecture. Keep changes to those anchors narrowly justified for Codex review, not an automatic broad override.
3. **Validate full footprints.** Check translated/rotated bounds against neighbouring buildings, the reserved hangar footprint, road and access lanes, support surfaces and protected objects. A centre-point-in-reserve check is insufficient. Assign actual tower/operations assemblies to their intended roles; nearest-free-slot alone is not a semantic match. Include collider/navigation changes needed for the finished layout.
4. **Controlled reruns.** `set_actor_location(current + delta)` repeats the move on a second run; removing tagged generated actors does not fix that. Store/validate source transforms and set explicit absolute target transforms. A second application should make no additional change, or refuse a stale plan before any mutation. Resolve inventory rows by their recorded IDs/paths, not `inventory_rows[i]` after a possible skipped actor. Likewise avoid `zip(actors, rows)` mispairing anchor references after a skipped row.
5. **Build the platform relationships.** The current apply function has no surface creation implementation even if mesh roles are filled; it only moves actors and logs unfilled roles. Implement the central road, forward chamfered pad/neck, left control platform, right dock and usable rear forecourt/hangar reserve as a coherent first structural pass. Keep any replacement of the old platform explicit and reversible in the manifest; no blanket scene cleanup. The user wants the reference arrangement, not a shuffle of the same scattered boxes.
6. **One comparison frame.** Capture currently uses the entire `site_frame` and maximum height while layout prefers `deck_frame`. Both must use the same reviewed garrison frame. The capture script requires the editor render/tick workflow (`UnrealEditor.exe -ExecutePythonScript=...`), as the working `ib_capture_bastion.py` does; the commandlet invocation in the result is not appropriate for the Slate-tick screenshot sequence. Codex did not run the incorrectly framed captures.

## Deliverable for the next check

Revise the inventory/layout/capture scripts into a concrete, reviewable first structural pass grounded in these actual actors and the confirmed image. Default remains read-only; Codex will review and invoke apply/save only after inspecting the plan and making a current map backup. Produce a concise explicit transform/creation manifest and exact commands, and explain how repeated execution and stale input are handled. Update `Docs/CLAUDE_GARRISON_LAYOUT_REVISED_RESULT_2026-09-23.md` with changed files, remaining constraints and the focused post-apply checks. Never claim engine execution or reference fidelity you have not observed.

Retain the rear hangar reserve for the user's later building. No recreation of BP_Mech, no menu/network/progression edits, no process/build execution, live-save writes, git/locks, commits or push. Stop when the revised pass is ready for Codex to run and compare.

## Menu correction verified by Codex

The flyout correction is accepted for the clipping defect. Development Editor build passed in 122.17 s (6 actions): `Saved/ReferenceArtPass/build-utility-flyout-20260923.log`. Both isolated 1280x720 and 1600x900 runs passed 4 DeploymentCheck and 16 MenuConsistency assertions plus COMPLETE, zero assertion FAIL. Open Friends screenshots show all six seats, the selected first-seat marker and a clear gutter; ordinary closed Squad layouts remain fully visible. Evidence: `Saved/UtilityMenuQA/run-20260923-flyout/{1280,1600}.log` and each size's `Saved/MenuConsistency/after/`. Offline captures do not establish hover/keyboard focus or real friend presence. All four live save hashes/lengths remained unchanged. Owned QA games and matching crash monitors stopped.

Read-only inventory and plan commandlets exited normally. `Saved/GarrisonRestructure/20260923-inventory/map-after-hash.json` matches the before hash, so no garrison map change has been applied. Do not redo the menu fix; focus this bounded task on the garrison corrections above.
