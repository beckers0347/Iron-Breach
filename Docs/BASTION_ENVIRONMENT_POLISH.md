# Bastion environment and harbor pass

Target: `/Game/LevelPrototyping/CarrowGateGarrison`. This is the existing playable fortress;
the separate `Lvl_Bastion` city described in the design document is not present in this project.

## Changes

- Replaced the flat water placeholder's visible surface with a 3 km harbor mesh at the same
  waterline, Z = -35 cm. The mesh has 66,049 vertices and 131,072 triangles, with denser geometry
  near the fortress. Three long waves displace it; eight wave scales supply animated normals.
  Fine ripples fade with distance to reduce shimmer.
- Added a Single Layer Water material with absorption, scattering, reflections and a narrow
  distance-field foam band. These are visual waves, not a new buoyancy or swimming system.
- Hid the old overlapping water/foam slabs. Their collision settings remain unchanged; the
  new visible water mesh has no collision. The old actors are retained for inspection/recovery.
- Applied world-scale concrete to 249 material slots, including structural checkerboard
  placeholders. Six ground slots use courtyard paving. Fixed the visible bark on 1,233
  surrounding trunk meshes with a replacement material that matches the source texture's
  color space. Original shared materials are retained.
- Neutralized the heavily orange sunlight and grade, reduced duplicate fog, softened bloom
  and grain, and retained the existing practical lamps, geometry, mission actors and spawns.

Assets are under `Content/IronBreach/Environment/Bastion/`. The editor's source control
provider automatically staged the first concrete material and harbor mesh during creation;
no commit or push was made.

## Rebuild and review

`Scripts/ib_polish_bastion.py` creates/updates the new assets and saves the fortress map.
Run with UnrealEditor-Cmd, the project path, `-run=pythonscript`,
`-script="D:/Unreal Games/IronBreach/Scripts/ib_polish_bastion.py"`, `-unattended`,
`-NoSteam`, `-SCCProvider=None`, and `-AllowCommandletRendering`.
It is safe to rerun without duplicating the water actor or material assignments.

`Scripts/ib_audit_bastion.py` reads the environment into `Saved/BastionPolish/audit.json`.
`Scripts/ib_capture_bastion.py`, run with `-ExecutePythonScript`, captures settled views of
the fortress, yard, water and player approach, then exits without saving the level.

The original map is backed up at `Saved/BastionPolish/before/CarrowGateGarrison.umap`.
Restore that file only if later map edits do not need to be preserved. It predates this pass.
Initial assignment counts are recorded in `Saved/BastionPolish/initial-changes.json`;
subsequent runs correctly report zero additional assignments.

## Scope

This pass improves the current fortress's materials, lighting and water. Its buildings still
use the existing blockout geometry. It does not build the planned walkable hub city or add
new mission logic. The deployment fix is documented separately in `WATCH_WIRING.md`.

## Visual validation

The final assets were reloaded in a fresh editor and reviewed from four settled cameras
at 1280×720: fortress approach, courtyard, waterline and player approach. The new materials
compiled successfully. Captures: `Saved/BastionPolish/after/`; log:
`Saved/BastionPolish/capture-final.log`. Earlier noisier water is retained under `first-pass/`
for comparison. The retired shared `M_AI_Foam` asset still logs its existing broken-clamp
warning while loading hidden legacy actors; the new water does not use it.

This is visual validation, not a measured performance benchmark. Existing player graphics
preferences were retained.

On 2026-09-10, the updated map passed the complete Steam deployment check at 1600×900:
operative DEPLOY → live Watch → Carrow Gate → return to Watch → Carrow Gate again.
Both arrivals remained stable with a possessed infantry pawn. No network failures or
new-material compilation failures were logged. See `Saved/BastionPolish/game-final.log`;
the final in-game view is `Saved/BastionPolish/after/in-game.png`.
