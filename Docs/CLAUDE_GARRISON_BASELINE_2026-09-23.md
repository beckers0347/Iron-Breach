# Garrison restructuring: baseline and reference gate

Prepared by Codex on September 23, 2026 UTC while Claude finishes the utility menus. The user explicitly approved parallel garrison preparation and reiterated that the result should match the earlier picture. This is preparation, not a claim that the layout has been changed or the reference recovered.

## Reference recovered after this baseline

The user subsequently supplied the requested concept in this conversation. Exact unchanged copy: `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`. Reference identity is now confirmed; the historical recovery notes below no longer block layout work. Current implementation brief: `Docs/CLAUDE_GARRISON_REFERENCE_HANDOFF_2026-09-23.md`.

### Historical recovery notes

The original ChatGPT conversation is **Layout Feedback Writing**, ID `6aad7a7b-fc88-83e8-86dc-19ff8762e7dd`. The September 18 sequence requested correctly scaled buildings and a mech hangar, then an overhead view, then rebuilding the existing level to match that generated picture.

- Overhead assistant message: `528fd400-9fc5-5b1a-98c9-45b72b7e43e0`.
- Earlier oblique assistant message: `5eea4af1-fc70-5c08-a0d9-c61644401a68`.
- The user's later instruction was to leave construction of the hangar itself for them, reserve its place, and develop the surroundings.
- Conversation text discusses a rear hangar reserve, forward landing pad and right-side dock. These words do not establish dimensions, orientation or exact placement.
- The task reader returned conversation text but no generated concept image. The existing-layout attachment `IMG_6423.jpeg` is not a confirmed substitute.
- Browser recovery also failed: Chrome unavailable; in-app navigation/focus timed out. Project/reference and scoped image filename searches found no verified copy.

**Do not move buildings from these text notes alone.** Inspect the exact generated overhead/oblique reference once supplied. Record its durable project path and which view controls placement. Do not substitute current screenshots, menu art, separate building concepts or a newly generated design.

## Fresh map audit

Map: `/Game/LevelPrototyping/CarrowGateGarrison`.

Codex ran the existing read-only `Scripts/ib_audit_bastion.py` in an isolated commandlet. It loaded the actual map and exited successfully with code 0. The script does not save levels or assets.

Evidence under `Saved/GarrisonRestructure/20260923/`:

- `audit.log`
- `audit-user/Saved/BastionPolish/audit.json`
- `map-before.json`, `map-before-hash.json`
- Baseline screenshots from the existing non-saving `Scripts/ib_capture_bastion.py`: `baseline-shots/`; capture completion is recorded separately in `capture.log`.

Map baseline: 5,620,631 bytes; SHA256 `D4A722DD20DDE3A16143ED0E853FB377307D75A4EFE669D670DDE6F51E8477F6`. Both post-audit and post-capture hashes matched; final evidence is `map-after-hash.json`. Capture finished at 00:45:54 UTC with `BASTION CAPTURE COMPLETE; no level saved`; the owned editor exited normally and no owned editor/crash reporter remained. All four 1280x720 screenshots were inspected.

| Existing item | Observed baseline | Preserve during restructuring |
|---|---|---|
| Player start | One `PS_Barracks_MissionStart`, XYZ `(7000, 7862.5, 489)` cm, yaw `-90` | A safe spawn and a clear exit; deliberately revalidate any repositioning |
| Mission directors | One each of Act I through Act V | Actor identity, configured references and event chain |
| Kaiju spawner | One `BP_M1_KaijuSpawner_C` | Mission references and viable spawn area |
| Weapon rack | One `BP_WeaponRack_C` | Existing stock, interaction and approach space |
| Door frames | Six `BP_DoorFrame_C` | Functional openings and collision clearance |
| Navigation | Two `NavMeshBoundsVolume`, one `RecastNavMesh` | Coverage for changed routes; counts alone do not prove walkability |
| Geometry | 3,246 `StaticMeshActor` objects | Use/reposition existing work selectively; avoid blanket replacement |
| Visible harbor surface | `IB_Harbor_Surface`, XYZ `(10000, -4000, -35)` cm, scale 1 | Existing visual waterline and waterfront relationship |

The visible water uses `SM_Bastion_Harbor` and `M_Bastion_Harbor` under `/Game/IronBreach/Environment/Bastion`. Older water placeholder/shallows/deep/surf actors remain hidden. Do not delete them merely because they are hidden: prior environment documentation records retained collision.

## Fresh visual observations

Codex inspected the new `fortress.png` and `yard.png` views. The current layout has simple concrete building masses with sparse openings, broad unmarked open ground, a circular waterfront platform, and an unfinished approach through a large rectangular gateway. The detailed perimeter fortification and water are already present. The central buildings and circulation areas remain much less developed visually.

These observations support prioritizing the overall building arrangement, route definition and transitions into the landing/waterfront areas before small decoration. The exact changes, proportions and style still depend on the confirmed reference. Camera names come from the existing capture script and are not assertions about building function.

## Gameplay dependencies reviewed

The Act II–V C++ directors expose `PreviousActDirector` soft references and bind completion events from the preceding act. Optional references include Act I `SquadNPCs`, Act II `DistrictNPCs`, Act III `ClassDSpawner` and `GarrisonMech`, and Acts IV/V `PalawanActor` and `GarrisonMech`. The audit confirms director presence, not the values of those map-instance references. Inventory those values before moving/replacing related actors.

`IBWeaponRack` owns its interaction sphere and stock. Maintain room to approach and interact, not just a visually plausible mesh location. `IBKitZone` is a combat ability field, not evidence of a garrison kit station.

Deployment already passed four checks in `Saved/ReferenceArtPass/crewqa-host-20260922-2348.log` at 23:51:55 UTC: listen Watch, garrison arrival, return, redeploy. These are recent travel results, not a fresh walking/navigation test. Keep the `carrow_gate` destination and map asset identity stable.

The configured real `BP_Mech` package is currently missing (see manager status/crew fixture result). Do not invent a replacement mech or confuse that separate blocker with permission to build the reserved hangar.

## Next implementation handoff, after the exact image is available

1. Compare the reference directly against these baseline views. Identify the hangar reserve, buildings, landing pad, waterfront/dock, routes and relative scale actually visible in the image. Resolve uncertain image identity before implementation.
2. Claude owns heavy layout work. Begin with coherent building placement, open spaces and routes using existing assets, keeping the hangar footprint reserved. Preserve unrelated and Caryatid edits and existing gameplay anchors.
3. Review the overall arrangement in Unreal before adding detailed dressing/material work. Add detail where it supports the confirmed reference, without filling required access routes.
4. Codex compares fresh screenshots to the reference and checks spawn clearance, walking/access to the rack and relevant mission areas, navigation/collision affected by moves, and Watch deployment/return. Review mission reference continuity before calling the restructuring complete.

The audit/captures are a baseline only. No complete actor-reference inventory, walking test, navigation rebuild or new layout has been performed. No source/assets were edited by Codex for this preparation, and no commit/push/pull/rebase or lock mutation is authorized.
