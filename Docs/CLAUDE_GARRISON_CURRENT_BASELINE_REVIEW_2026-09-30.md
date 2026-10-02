# Current garrison baseline — review and next Claude task

Prepared by Codex, September 30, 2026, 05:48 UTC. **Delivered through Claude desktop Project status update during the11:33 UTC check; submitted message and working state verified. No layout apply authorized by this document.** The user authorized the garrison restructuring; this bounded task prepares an implementation for review while preserving the new map work.

## Verified evidence

- Map: `Content/LevelPrototyping/CarrowGateGarrison.umap`, SHA256 `FAFFD601EE4165A6FF76760BA264665D38631240D1DFC72C9322DD7A0B51EFEC`. Before/after hashes match after both read-only runs. September23 D4A722DD-based manifests are obsolete.
- Fresh survey: `Saved/GarrisonRestructure/20260930-current-inventory/inventory/`. It enumerated 2,983 actors, 78 placed mesh types, and five authored garrison folder groups. `actors.json` contains the actual actor paths, transforms, bounds and materials. The inventory script reached COMPLETE, but the overall commandlet reported Failure (23 errors, four warnings) from the GameFeatureData class-loading ensure; this is not a clean engine pass. Log: `inventory-commandlet.log` in the parent evidence directory. Process 27340 has exited.
- Ground mesh sampling works: support status `ok`, mode `mesh`, 1,274 of 2,385 cells have heights, 204 Body2 triangles, no support-specific errors. This verifies geometry extraction only, not collision or navigation.
- Platform world bounds remain centre `(6952.08,1094.67,10)`, half extents `(10452.08,8897.97,375)`. Actor location `(5500,20000,-365)` alone does not establish a displaced site. This corrects the prior manager note's suggestion that the probe points necessarily missed because of a platform shift.
- Probe: `Saved/GarrisonRestructure/20260930-probe/probe/support-probe.json`. All traces returned None; collision_enabled/profile/object_type editor-property reads failed. Hardcoded named-building sample points are not tied to current buildings. The cause of trace misses is unproven; do not report absent physics or broken collision as established.

## Current map does not match the old assembly rules

Five new service-building meshes have **no folder**, while their five doors share `Carrowgate Garrison/Doors`. Grouping by old building folders omits the buildings and combines unrelated doors. Current `ib_layout_garrison.py` still requires the old roles and a `Main Gate` folder to establish orientation; do not run its apply mode.

All paths below have prefix `/Game/LevelPrototyping/CarrowGateGarrison.CarrowGateGarrison:PersistentLevel.`. Use full paths from actors.json as identities, not just names or these suffixes.

| Building | Actor suffix | Door suffix | Current building location |
| --- | --- | --- | --- |
| Medical | StaticMeshActor_1 | BP_DoorFrame_C_0 | 9397.59,6241.17,380 |
| Barracks | StaticMeshActor_54 | BP_DoorFrame_C_1 | 3310,-1604,380 |
| Armory | StaticMeshActor_56 | BP_DoorFrame_C_2 | 6893,8733,380 |
| Command | StaticMeshActor_58 | BP_DoorFrame_C_3 | 518,5770,380 |
| Mess_Hall | StaticMeshActor_60 | BP_DoorFrame_C_4 | 318,2854,380 |
| SM_MainGate_Tripo | StaticMeshActor_280 | BP_DoorFrame_C_6 (BP_MainGateDoor) | -49,-250,376 |

These are candidate explicit associations grounded in labels/mesh identities, not permission to move them without inspecting attachments and current door behavior. MainGate is in the root `Carrowgate Garrison` folder. The platform Ground folder also contains a very large separate ground actor; never use combined Ground bounds as the site frame. BP_WeaponRack is ungrouped at `(7836,7587,390)` and PlayerStart at `(4690,4024,539)`. Preserve spawn, interaction, missions and deployment paths. Do not assume old Watch Tower/Sensor/Vehicle Bay roles still exist.

## Next bounded task for Claude

1. Reconcile inventory and layout tools with this new baseline using explicit actor identities, building-door associations, attachment/component ownership and current collision/interior/road work. Identify unresolved associations rather than guessing from proximity or grouping every door together. Preserve Shane's new work and resolve ownership before map edits; do not contact Shane or anyone else without user authorization.
2. Produce a revised dry-run manifest and concise structural plan against the approved image `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`. Show rear service forecourt, central spine, forward chamfered pad, left control platform and separate right berth/water gaps. Reserve the rear hangar for the user. Explain how existing new buildings fit those roles without deleting or replacing them.
3. Keep support heights, full-footprint checks, source validation, preflight failures, repeatability and stale-map guards from the previous review. Avoid leaving an invisible collidable platform across proposed water gaps; distinguish proposed appearance from verified walkability. No apply or package save in this preparation task.
4. Correct the small probe limitations if needed for verification: current known ground points, supported collision getter methods, explicit errors and cautious conclusions. Diagnose the GameFeatureData commandlet ensure only enough to separate tool results from engine failure; do not expand into unrelated asset restoration.
5. Write `Docs/CLAUDE_GARRISON_CURRENT_BASELINE_RESULT_2026-09-30.md` with changed tool files, dry-run evidence, unresolved decisions and review instructions. Codex will review before a backed-up layout apply and focused visual/gameplay checks.

Accepted menus remain unchanged. No Git/locks/commit/push operations, live-save modifications, BP_Mech restoration or rear-hangar construction. The historical GARRISON_PLAYTEST_PUNCHLIST is background, not a fresh audit or an instruction to broaden this task into animation/texture work.
