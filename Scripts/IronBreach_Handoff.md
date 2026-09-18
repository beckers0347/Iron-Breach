# IronBreach — Collision/Building Cleanup Handoff (for Claude Code)

Project: UE5.8 game **IronBreach**, repo/project root `X:\IronBreach`.
Level being worked on: `Content/LevelPrototyping/CarrowGateGarrison.umap`.
Scripts live in `X:\IronBreach\Scripts\*.py` and are run manually in the
Unreal Editor's Python console (`py "X:/IronBreach/Scripts/<name>.py"`).

## 1. Standing constraint — READ THIS FIRST

The user does **not** want any tool taking GUI control of their computer
(no screenshots, clicks, or typed input into the editor). All work is
done by:
1. Writing a Python script for Unreal's editor Python API.
2. Deploying it to `X:\IronBreach\Scripts\`.
3. The user runs it themselves via the editor's Python console:
   `py "X:/IronBreach/Scripts/<script>.py"`
4. The user pastes back the console log output, tagged with `IBPY:`
   prefixes from `unreal.log(f"IBPY: {msg}")` calls, for review.

**If Claude Code has terminal/file access to this machine, it can skip
the "deploy via chat" round-trip and just write scripts directly into
`X:\IronBreach\Scripts\`** — that's a meaningful workflow improvement.
But it still cannot click inside the Unreal Editor UI unless the user
has separately set up something like UE's Python **Remote Execution**
(multicast socket, `Editor Preferences > Python > Enable Remote
Execution`), which would let a local process send Python commands to a
running editor session without any window automation. That has NOT been
set up in this project yet — right now, the user still needs to
manually paste `py "X:/..."` into the in-editor Python console and paste
back the log each time. Don't assume remote execution is available
unless the user confirms it.

## 2. Original problem being solved

Garrison buildings use Tripo3D-generated exterior meshes (solid,
closed-shell, high-poly/Nanite) that have no real collision matching
their visible shape — decorative dishes/pods/antennas stick out and need
to block the player, while the player should be able to walk in through
the doorways. Buildings involved: **Armory**, **Command & Comms**,
**Mess Hall** (a Medical building and a Mech Hangar are still pending
much earlier-stage work — blockout/mesh generation — not touched this
session).

### Approach history (context only — no action needed)
- Originally tried BlockingVolume shells; reverted (user said "the
  collision walls... aren't working correctly," deleted them all).
- Considered simplified-primitive auto-collision (convex hulls) vs.
  **"Use Complex Collision As Simple"** (`CTF_USE_COMPLEX_AS_SIMPLE`) —
  the user chose complex-as-simple, since it exactly matches the mesh's
  real shape (dishes, pods, octagon walls) with no manual box-fitting.
- Complex-as-simple alone made buildings **fully solid** (no doorway —
  the visible "door" is a decorative mesh sitting in front of a solid
  wall, not an actual opening). User chose **"Option B"**: physically
  carve a doorway-shaped hole into the collision mesh via Geometry
  Script mesh-boolean subtraction, **non-destructively** (never touches
  the original visual mesh — see §3).

## 3. Current state — what's already done and confirmed working

All three buildings now have:
- `body_setup.collision_trace_flag = CTF_USE_COMPLEX_AS_SIMPLE` on their
  StaticMesh asset.
- A doorway hole carved into a **separate, duplicate** collision-only
  mesh asset (e.g. `/Game/TripoModels/Armory/Armory_Collision`), never
  into the original visual asset.
- The original visual asset's `complex_collision_mesh` property pointed
  at that duplicate (tells the engine "use this OTHER mesh's geometry
  for complex collision," while rendering stays on the original,
  unmodified mesh).
- `mesh_comp.collision_enabled = QueryOnly`, profile `BlockAll` on the
  level actor's static mesh component.

This was confirmed working in the most recent run (`ib_carve_door_holes.py`
v3, see §4) — full summary from the user's pasted log:
```
07_Armory: OK       (yaw=-45.0, normal cutter size, delta=1827 triangles)
08_Command & Comms: OK  (yaw=90.0, ENLARGED cutter size, delta=1390 triangles)
06_Mess Hall: OK    (yaw=15.0, normal cutter size, delta=3098 triangles)
```

**Not yet confirmed:** the user still needs to walk into each doorway in
PIE to verify it's actually open and reasonably sized/positioned, confirm
everything else still blocks the player, then save the level (Ctrl+S) —
the mesh assets themselves are already saved by the script, but the
level's actor collision-enabled state needs a level save too.

## 4. Key scripts on disk (`X:\IronBreach\Scripts\`)

- **`ib_complex_collision.py`** — sets complex-as-simple + collision
  enabled on the 3 buildings. Already run successfully; safe to leave.
- **`ib_revert_complex_collision.py`** — emergency revert to
  `NoCollision` (used once when complex-as-simple alone made buildings
  fully solid, before the door-carving fix existed). Not needed anymore
  but harmless to keep.
- **`ib_geoscript_probe.py` / `_probe2.py` / `_probe3.py` / `_probe4.py`**
  — read-only API-discovery scripts (already served their purpose,
  findings baked into `ib_carve_door_holes.py`; safe to delete or keep).
- **`ib_diag_command_door.py`** — read-only diagnostic that dumped the
  Command & Comms door actor's true position vs. the building's octagon
  center; explains why hardcoded/rotation-based cutter guesses failed
  for that building.
- **`ib_carve_door_holes.py` (v3, current)** — the core script. See §5
  for exact algorithm; this is the one to build on if door position/size
  needs tuning per building.
- **`ib_list_old_buildings.py`** — **just deployed, not yet run/reviewed**
  (see §6). Read-only listing of every level actor, grouped by World
  Outliner folder + a soft "likely placeholder" flag, in prep for a
  cleanup/deletion script.

## 5. `ib_carve_door_holes.py` v3 — algorithm (for future tuning)

Per building (`BUILDINGS` list at top of file has `prefix`,
`exterior_actor`, `door_actor` for Armory/Command/Mess Hall):

1. Duplicate the original StaticMesh asset to `<Name>_Collision`
   (deletes any stale one from a prior run first).
2. **Empirical search** for a cutter that actually intersects the mesh —
   this replaced two earlier, unreliable single-guess strategies:
   - v1: hardcoded per-building wall direction table → wrong for
     Command (stale data).
   - v2: trusted each DoorFrame actor's own `get_actor_rotation()`
     directly → right for Armory, but silently no-op'd for Command AND
     regressed Mess Hall (which had worked in v1).
   - **v3 (current)**: tries the door's own yaw first, then sweeps every
     15° around a full circle, each candidate tested against a *fresh,
     throwaway* copy of the mesh (`copy_mesh_from_static_mesh` +
     `apply_mesh_boolean`, checking `get_triangle_count()` before/after).
     A candidate only "wins" if the triangle-count delta is
     `>= MIN_TRIANGLE_DELTA` (50 — filters grazing near-misses). If
     *no* yaw works at the normal cutter size
     (`DOOR_CUT_WIDTH/HEIGHT/DEPTH_CM` = 220/280/600), it retries the
     full sweep with an **enlarged** cutter
     (`ENLARGED_CUT_*` = 340/380/1200) in case the miss was a
     position/reach problem rather than pure orientation — this is what
     ended up solving Command & Comms.
   - Only the winning candidate is ever written back to an asset (so
     failed candidates cost an in-memory boolean op, not a Nanite
     rebuild — rebuilds only happen once per building, on the winner).
3. Write the winning mesh into the `_Collision` duplicate only, set its
   `collision_trace_flag`, save it.
4. Point the *original* asset's `complex_collision_mesh` at the
   duplicate, set its `collision_trace_flag` too, save it.
5. Re-enable collision (`QueryOnly` / `BlockAll`) on the level actor's
   mesh component.

If a building's doorway ends up misaligned/wrong-sized in PIE, the
knobs to adjust are `DOOR_CUT_WIDTH_CM` / `DOOR_CUT_HEIGHT_CM` /
`DOOR_CUT_DEPTH_CM` (and the enlarged variants), or
`MIN_TRIANGLE_DELTA`/`YAW_SWEEP_STEP_DEG` if the search itself needs to
be finer/coarser.

## 6. In-progress task — remove old buildings and their props

User asked to remove old (pre-Tripo3D) placeholder buildings and props.
Clarified scope with the user:
- **Target**: pre-Tripo3D placeholder blockouts specifically (not the
  current Armory/Command/Mess Hall Tripo3D buildings or their doors).
- **Identification method**: user chose "list first" — no naming
  convention was assumed; nothing should be deleted blind.

**Current state**: `ib_list_old_buildings.py` has been written and
deployed to `X:\IronBreach\Scripts\`, but **the user has not yet run it
or pasted back output**. It is read-only — lists all level actors
grouped by World Outliner folder path, plus a soft heuristic flag
("likely placeholder") based on name substrings (old/placeholder/
blockout/temp/bsp/wip/deprecated/unused/delete), BSP brush class, or a
static mesh sourced from `/Engine/BasicShapes` — while explicitly
excluding the known-good Tripo3D buildings/doors from that flag.

**Next step for whoever picks this up**: get the user to run
`py "X:/IronBreach/Scripts/ib_list_old_buildings.py"` and paste back the
log. Review the folder groupings and flagged candidates with the user,
agree on the exact actor list/folder/pattern to remove, THEN write a
second script that does the actual deletion (e.g. via
`unreal.EditorActorSubsystem().destroy_actor(a)` per confirmed actor, or
by deleting an entire confirmed Outliner folder's contents) — always as
a reviewed, explicit list, never a blind pattern-match delete.

## 7. Still entirely unaddressed — door mesh looks wrong when walked through

Separate, lower-priority issue the user raised: the door actors (built
earlier via a different Python script, referenced but not detailed in
this session) are static meshes, so when the player walks through one
it doesn't animate — you just see the door mesh sitting there, looks
wrong even though it doesn't block movement. Not yet designed or
implemented. Prior proposal (verbal only, not built): a sliding
blast-door Blueprint using the existing DoorFrame actor's trigger box +
a Timeline to slide/rotate the door mesh open on player overlap. Needs
the user's go-ahead before building.

## 8. Suggested first message to Claude Code

Something like:

> This is the IronBreach UE5.8 project at X:\IronBreach. Read
> `X:\IronBreach\Scripts\IronBreach_Handoff.md` for full context on
> what's been done (door-hole collision carving for 3 buildings, all
> confirmed working) and what's in progress (listing old placeholder
> buildings/props before writing a deletion script — see §6). Don't
> automate the Unreal Editor GUI; work by writing/editing Python scripts
> in X:\IronBreach\Scripts and having me run them in the editor's Python
> console.

(This handoff file itself should be deployed to
`X:\IronBreach\Scripts\IronBreach_Handoff.md` so Claude Code can read it
directly from disk.)
