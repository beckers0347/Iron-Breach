# Carrow Gate garrison, first layout pass — prepared (September 23, 2026)

Bounded preparation from `Docs/CLAUDE_GARRISON_REFERENCE_HANDOFF_2026-09-23.md`. Three new scripts
under `Scripts/`. No Unreal launched, no build, no process control, no live save, no git or lock
operation, no map or asset mutated, no apply mode run. **Nothing in this document has been executed.**

---

## Status, up front

The reference is confirmed and analysed, the layout is designed in real world coordinates, and the
tooling is written. **The apply pass cannot be completed yet, and the reason is specific:** the
existing audit (`Saved/GarrisonRestructure/20260923/audit-user/Saved/BastionPolish/audit.json`)
records class counts, lighting, water and materials — it contains no per-actor labels, transforms or
bounds for the 3,246 `StaticMeshActor`s. There is no evidence in this project that says which of
those are buildings, which are the deck, or where any of them sit.

So rather than guess selectors, §6 supplies the read-only inventory step that produces exactly that
evidence, and §7 says precisely what to hand back. The layout script is already written against that
inventory's shape, defaults to read-only, and refuses to run at all without it.

---

## 1. Reading the reference

`References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`, 1672 x 941, inspected
directly. It is one compound, not a scatter: a single spine with everything hung off it.

Back to front: the **hangar** closes the top of the site with a mech on a gantry in its open bay. In
front of it a **broad rear forecourt** carries two clusters of low service buildings, four or five on
the left including one with a small tower, three or four on the right, with real lanes between them
and between them and the road. A **broad central road** leaves the hangar mouth and runs straight out
through a **narrower neck** to a **chamfered landing platform** at the front with a circular marking
and an aircraft on it. A **secondary platform** projects to the left at about half depth, carrying a
round **watch tower** and a low **operations building**, joined to the spine by a short spur. A **long
narrow dock** runs parallel to the spine on the right with a **warship berthed outboard** of it.
Continuous seawall, yellow-painted edges, rails and bollards throughout; rocky wooded land behind
with a road entering from the back left.

### What I measured, and what I refuse to measure

I segmented the image into water and built surface and took lateral runs at matched depths:

| element | image width | ÷ rear platform |
|---|---|---|
| rear platform | ~870–940 px | 1.00 |
| front landing pad | ~390–430 px | 0.46 |
| left control platform | ~370 px | 0.41 |
| central causeway | ~260–280 px | 0.30 |
| dock | ~60–90 px | 0.08 |

**These are lateral ratios only, and even they are soft.** The image is an oblique aerial: the front
of the compound is nearer the camera and therefore drawn larger per metre than the back, so the pad's
true share is smaller than 0.46 and the rear platform's is larger than 1.00. Correcting roughly for
that puts the pad at 0.34–0.46 and the causeway at 0.25–0.30, which is the bracket the numbers in §3
sit inside.

**I have taken no depth measurements from the image at all.** Front-to-back pixel distance in an
oblique view is foreshortened non-linearly and is not recoverable without the camera. Every depth
figure below is functional instead: enough forecourt for two building rows and their lanes, a
causeway long enough to read as a route, a pad clear of it.

---

## 2. Putting it on this map

The reference's "down" is not world north, and nothing in the image says which way the compound
faces. One thing in the map does: the spawn the player walks out of.

`PS_Barracks_MissionStart` sits at `(7000, 7862.5, 489)` with yaw `-90`, which faces **−Y**, and
`IB_Harbor_Surface` sits at `(10000, -4000, -35)`. The player spawns inland and faces the water. So
**−Y is seaward — the reference's bottom — and +Y is landward, the hangar end.** The existing capture
cameras are consistent with that: `ib_capture_bastion.py`'s "player" shot looks from the spawn to
`(7000, -5000)`, straight down the axis this layout uses as its spine.

That is the whole of the orientation evidence, and the layout script derives the axis from the spawn
yaw at runtime rather than hard-coding −Y, so if the spawn is ever re-aimed the layout follows and
the report says which source it used.

**Scale is the part I do not have.** The compound's real width and depth come from the inventory's
deck bounds, not from me. The layout is therefore expressed in site-normalised coordinates and mapped
onto whatever the deck turns out to be:

- `u` — lateral, in units of the deck's width. 0 is the spine, negative is the reference's left.
  `|u| > 0.5` is off the platform, over water; only the berth uses it.
- `v` — 0 at the seaward tip, 1 at the landward edge, in units of the deck's depth.

Measuring against the **deck** rather than against everything with geometry matters, and a dry run
proved it: normalised against the full built extent — which includes the rocks and the perimeter —
the service rows landed *outside* the platform and buildings were assigned the Z of the tallest
tower. The inventory therefore reports the largest flat non-water cluster separately as the compound,
with its top surface as the deck height and its runners-up listed so the choice can be overruled.

---

## 3. The layout

| zone | u | v | notes |
|---|---|---|---|
| `hangar_reserve` | −0.22 … 0.22 | 0.86 … 1.00 | **kept clear** — yours to build |
| `rear_forecourt` | −0.50 … 0.50 | 0.56 … 0.86 | the broad rear platform |
| `service_left` | −0.50 … −0.12 | 0.58 … 0.84 | two rows of buildings, lanes between |
| `service_right` | 0.12 … 0.50 | 0.58 … 0.84 | two rows |
| `central_road` | −0.11 … 0.11 | 0.05 … 0.86 | the spine, hangar mouth to pad |
| `neck` | −0.14 … 0.14 | 0.18 … 0.40 | narrower joint into the pad |
| `control_platform` | −0.46 … −0.12 | 0.30 … 0.56 | left projection, tower + operations |
| `front_pad` | −0.24 … 0.20 | 0.00 … 0.20 | chamfered pad, slightly left of the spine as in the reference |
| `dock` | 0.30 … 0.40 | 0.06 … 0.56 | long narrow pier, parallel to the spine |
| `berth` | 0.42 … 0.56 | 0.10 … 0.52 | ship alongside, outboard, over water |

Eight building slots (two rows each side) plus a tower slot and an operations slot on the left
platform. The road at 0.22 of the deck width is the conservative end of the measured bracket — broad
enough to read as the reference's parade route, not so broad it swallows the yard.

On a dry run against a synthetic 10,800 x 16,000 cm deck every zone landed inside the platform, the
forecourt exactly on its edges, and the berth correctly outboard over water.

**The hangar reserve is a hole in the plan, not a building in it.** Pass 1 keeps it clear, keeps the
forecourt in front of it usable as an approach, and the apply step aborts if any slot resolves inside
it.

---

## 4. New files

| File | What it does | Writes? |
|---|---|---|
| `Scripts/ib_inventory_garrison.py` | Read-only inventory: every actor's label, class, path, transform, bounds, mesh, materials, tags; derived structure and deck clusters; distinct meshes with unit bounds; gameplay anchors **with their mission-director reference values**. | Never. Loads the map, saves nothing. |
| `Scripts/ib_layout_garrison.py` | Projects the layout above onto the real site and writes a plan plus a validation report. Applies it only when explicitly told to. | Read-only by default. |
| `Scripts/ib_capture_garrison.py` | One aerial framed like the reference plus four ground views, all derived from the site frame so before/after line up. | Never saves the level. |

Nothing existing was modified. No C++, no menu, network or progression code was touched.

---

## 5. Exact invocations

Run from the project root with the editor **not** already open on this map.

**Step 1 — inventory (read-only, required first):**

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -run=pythonscript -script="D:\Unreal Games\IronBreach\Scripts\ib_inventory_garrison.py" -unattended -nosplash -abslog="D:\Unreal Games\IronBreach\Saved\GarrisonRestructure\inventory.log"
```

Writes `Saved/GarrisonRestructure/inventory/` — `actors.json` (large), `clusters.json`,
`meshes.json`, `anchors.json`, `summary.txt`. Tuning: `IB_GARRISON_GAP` (cluster merge distance, cm,
default 900) and `IB_GARRISON_TALL` (structure-vs-deck half-height, cm, default 240).

**Step 2 — plan (read-only):** same command with `ib_layout_garrison.py`. Writes
`Saved/GarrisonRestructure/layout/plan.json` and `report.txt` and changes nothing. Read the report
before anything else happens.

**Step 3 — capture the "before":** same command with `ib_capture_garrison.py`. Writes
`Saved/GarrisonRestructure/shots/`. Copy that folder aside before the apply run.

**Step 4 — apply, only after reviewing the plan:** set `IB_GARRISON_APPLY=1` and run
`ib_layout_garrison.py`. It performs the plan and **does not save**. Add `IB_GARRISON_SAVE=1` to
save; that flag is the only path in any of these scripts that writes the level. To execute an edited
plan instead of a recomputed one, point `IB_GARRISON_PLAN` at it.

Take a map backup before the first apply, as you planned. Re-run step 3 afterwards for the "after".

---

## 6. Guards

- Read-only unless `IB_GARRISON_APPLY=1`; unsaved unless `IB_GARRISON_SAVE=1` as well.
- Refuses to run without the inventory, naming the script to run.
- Resolves every target **by actor path name**, not by list position — `get_all_level_actors()` does
  not promise a stable order. Any target that cannot be resolved, or that comes back with a different
  class or label than the inventory recorded, aborts the whole run before anything moves.
- Never touches `PlayerStart`, `BP_WeaponRack_C`, `BP_M1_KaijuSpawner_C`, `BP_DoorFrame_C`, nav
  volumes, the five act directors, lighting, post-process, the Datasmith scene or the skeletal mesh
  actor. Aborts rather than moving one.
- Never touches anything whose label or material mentions water, harbour, sea, foam, surf or
  shallows. **Hidden water actors carry collision and are not scenery to tidy away** — the inventory
  records them, the clustering keeps them out of the "which slab is the compound" question, and the
  apply step refuses them.
- Deletes nothing. Its own created actors carry the tag `IB_GarrisonPass1` and labels beginning
  `IBG1_`, and an apply run removes **only** tagged actors before rebuilding, so repeated runs
  converge instead of stacking. No level is ever cleared.
- Moves are **lateral only**. No building's height changes: the deck under it has not moved, and a
  vertical guess either floats it or buries it.
- Groups on the site edge, oversized masses (terrain, perimeter) and anything containing a protected
  anchor are excluded from the pass and listed with the reason.
- A move longer than 45% of the compound's larger dimension is **deferred, not performed** — once the
  near slots fill, nearest-free-slot will happily teleport a building across the site, and that is a
  judgement call rather than an arrangement. The cap is `IB_GARRISON_MAX_MOVE`.

---

## 7. What I need back before an apply pass can be finished

From `Saved/GarrisonRestructure/inventory/`, the four small files — `clusters.json`, `meshes.json`,
`anchors.json`, `summary.txt`. Not `actors.json`; the scripts read it locally. Specifically:

1. **`deck_frame` in `clusters.json`** — is the largest flat cluster really the compound platform?
   Its size, centre and `top_z`, and whether a runner-up is the better choice. Everything in §3 is
   normalised against this, so if it is wrong every placement is wrong.
2. **The structure-group list** — how many building-sized masses there actually are, where they sit,
   and how many of the ten slots they can fill. If the map has three buildings rather than ten, the
   pass is mostly about the route and the pad, not about rearranging.
3. **`meshes.json`** — this is the one that decides how much of the reference is reachable at all.
   I need to know whether meshes exist for: a road/deck slab, painted road markings, a circular
   landing marking, a chamfered pad edge, a seawall or quay run, bollards and rails, and a ship. The
   `SURFACE_ROLES` table in the layout script is deliberately empty of mesh paths and every role
   currently reports "unfilled": I will not substitute a guess for a missing asset, and the pass will
   report a role as unmet rather than dressing the site with the wrong thing.
4. **`anchors.json` reference values** — the act directors' `previous_act_director`, `squad_npcs`,
   `district_npcs`, `class_d_spawner`, `garrison_mech` and `palawan_actor`. The baseline confirmed
   those directors exist but not what they point at, and moving a referenced actor without knowing is
   how a mission chain breaks quietly. Note `garrison_mech` is likely unset or dangling given
   `BP_Mech` is missing — that is the separate blocker, not a licence to build the hangar.
5. **The plan's `deferred` and `slots_unused` lists from step 2**, so we can settle the leftovers
   deliberately rather than by cap.

---

## 8. Preserved

Same map, same asset path, same `carrow_gate` destination. Spawn, weapon rack and its approach, the
kaiju spawner, the six door frames, both nav volumes and the recast mesh, all five act directors and
their configured references, the harbour surface and the hidden water. Existing travel and
deployment/return behaviour. Caryatid and other unrelated work — no C++ was touched for this task. No
old whole-map backup is restored by anything here.

---

## 9. Limitations and unresolved art

- **Nothing ran.** No script in this document has been executed against Unreal. The plan logic was
  dry-run in isolation against a synthetic inventory with the engine stubbed out, which proves the
  arithmetic and the guards execute — it proves nothing about the real map.
- The Unreal Python calls follow `ib_audit_bastion.py`, `ib_capture_bastion.py` and
  `ib_polish_bastion.py`, which are known to run in this project. `get_folder_path`, `tags` and
  `get_actor_bounds` unpacking are each wrapped in try/except because they are not proven here.
- Scale is unknown until step 1. Every absolute figure in a report is derived, not asserted.
- The aerial camera is framed at roughly 48° down from about half the site's depth out to sea, which
  is about how the reference sits. It is an approximation of an illustration, not a solved camera.
- **Exact-art gaps, honestly:** there is no confirmed asset in this project for painted road or pad
  markings, a chamfered pad edge, bollards or rails, or a berthed ship. The reference's mech sits in
  the hangar we are not building, and `BP_Mech` is missing anyway. Until `meshes.json` says
  otherwise, treat the markings, the dock furniture and the ship as unmet.
- This pass is arrangement, not dressing: routes, platform relationships and building placement
  first, so the overall shape is reviewable before anyone spends time on detail.

## 10. Next focused checks, after the first apply

Aerial against the reference; walk the spine from the pad to the forecourt; spawn clearance and a
clear exit; the weapon rack still approachable and interactable; collision and navigation over every
moved footprint — a rebuilt navmesh, not a volume count; mission-director references intact; and a
Watch deployment and return. The garrison is not done until those pass.

Stopping here for your review.
