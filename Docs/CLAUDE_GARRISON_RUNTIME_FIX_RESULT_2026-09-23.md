# Garrison runtime fixes — support, assemblies, geometry, preflight (September 23, 2026)

From `Docs/CLAUDE_GARRISON_RUNTIME_REVIEW_2026-09-23.md`. One new script, three revised, all in
`Scripts/`. No Unreal launched, no build, no apply, no save, no live save, no git or lock operation,
no menu, network or progression change. **Nothing has been executed against the engine.**

---

## 1. Run the probe first

`Scripts/ib_probe_garrison_support.py` is new, small and read-only. Everything else is blocked behind
it, because the layout pass now refuses to plan a placement without ground data.

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -run=pythonscript -script="D:\Unreal Games\IronBreach\Scripts\ib_probe_garrison_support.py" -unattended -nosplash -abslog="D:\Unreal Games\IronBreach\Saved\GarrisonRestructure\probe-commandlet.log"
```

and, for the comparison that matters most, the same script in the **editor**:

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -ExecutePythonScript="D:\Unreal Games\IronBreach\Scripts\ib_probe_garrison_support.py"
```

It writes `Saved/GarrisonRestructure/probe/support-probe.json` and prints one VERDICT line. It reports
which editor world it got, the platform component's collision settings and whether its mesh even has a
`body_setup`, what `line_trace_single` actually returns here (type, tuple length, and whether
`GameplayStatics.break_hit_result` decodes it), six probes onto known ground under existing buildings
across every available trace channel, and whether the platform's triangles can be read instead. **No
exception is caught without being printed**, and the first full traceback is kept verbatim.

### What your log already tells us

The failure is not an exception. Line 228 was reached — the `TRACE_TYPE_QUERY1` deprecation warning
fired — and 2,385 traces completed in 442 ms, returning no hit every time. So the decode path was
never reached and the old `except: z = None` never fired. Something returned "nothing there" 2,385
times, quickly. The likeliest cause is that a `-run=pythonscript` commandlet world has no physics
scene to query; a mesh with no collision geometry would look identical. The probe separates those,
which is why it checks `body_setup` and offers the editor comparison.

### And a route that cannot fail the same way

The inventory's default support mode is now **`mesh`**, not `trace`. It reads the platform's triangles
through `ProceduralMeshLibrary.get_section_from_static_mesh`, transforms them into world space and
rasterises the highest surface into the grid. No physics, no collision, no trace channel — so it works
in a commandlet regardless of what the probe finds. `IB_GARRISON_SUPPORT_MODE=trace` or `both` are
there for when the probe says traces work.

**Ground is an allowlist, not a filter.** `IB_GARRISON_SUPPORT_ACTORS` names the actors that *are* the
ground (default `GarrisonPlatform_New`). A roof, a crate or a foliage card cannot become load-bearing
by accident, because nothing else is ever sampled. In trace mode the same list is applied to the hit
actor, and every cell records which source supplied it.

**Zero usable samples is now `no-data`, never `ok`.** The summary prints a block telling you to run the
probe, and the layout refuses.

---

## 2. Measuring the right ground

- **Out-of-grid cells count as unsupported.** They were being clamped away, which silently shrank each
  footprint to the part inside the grid and then reported full coverage of that. A footprint half off
  the platform now reports its real coverage and the count of cells that were off it.
- **Source support is rejected too.** If a building's *current* ground is invalid, its height cannot be
  trusted, and that is a blocking problem rather than a silent `dz` of zero.
- Footprint edges and corners are included, because the box is walked from `floor(min)` to
  `floor(max)` inclusive rather than clamped inward.

---

## 3. The nineteen lights

Assemblies are now one per **building**, including every descendant folder. `Carrowgate
Garrison/Barracks/Lighting` is part of the Barracks. Paths are deduplicated, and the explicit
`BP_WeaponRack` adoption is retained.

Verified against your inventory: Armory 3, Barracks 4, Command & Comms 3, Mess Hall 5, Sensor Array 1,
Watch Tower 3 — **19 lights, all now carried**. Transform count rises from 279 to 298.

`Carrowgate Garrison/Lighting` (5 site-wide lights) stays a separate held assembly; it is not a
building's lighting.

**Placement bounds come from structural geometry only** — `StaticMeshActor` and `BP_DoorFrame_C`,
never lights. A point light's bounds are its influence radius, and a 50 m radius is not a building
footprint. Each assembly reports `bounds_from`, its structural and lighting counts, and its subfolders.

---

## 4. One finished level, which is what reconciles entrances with slabs

The site has terraces 3 m apart (rear buildings based at z 378, seaward ones at z 78). The reference is
one flat compound. Rather than reconcile every entrance against a different slab, **every new deck
shares one finished top**, and each is thick enough to reach its own ground.

- `finish_z` = the highest ground any zone stands on, plus 20 cm. Overridable with
  `IB_GARRISON_FINISH_Z`.
- Each slab's top is `finish_z`; its underside reaches its zone's lowest ground, so nothing floats and
  nothing is a step.
- **Every building's base becomes `finish_z`.** There is one deck height, so every door threshold lands
  on the same surface. No ramps are invented that nobody has walked.
- The report prints each zone's existing ground range, its coverage and the fill needed. A zone needing
  more than 9 m of fill is a blocking problem rather than a silent tower of slab.

## 5. Water gaps, and an explicit way back

Thin rectangles laid over the old broad platform cannot make the gaps the reference shows beside the
spine and the pier. So the new decks are the ground and `GarrisonPlatform_New` is **hidden — never
deleted, never hidden as a class, never part of a blanket sweep**. Exactly that one actor, by path,
via its mesh component's visibility, which is a saved property rather than an editor-only flag.

- `IB_GARRISON_PLATFORM_MODE=hide` (default) — visibility off, **collision left on**. Nothing can fall
  through; the gaps are visual until a later pass deals with collision. The report says this plainly.
- `hide+nocollision` — also disables collision; navigation must be rebuilt.
- `keep` — leave it alone.
- `IB_GARRISON_REVERT=1` with APPLY restores the platform, returns every moved actor to its recorded
  source and removes every generated actor.

No water actor is touched by any mode.

---

## 6. The small geometry, corrected

| was | now |
|---|---|
| bollards on `dock max Y`, the **inboard** edge | outboard edge derived from the sign of the frame's lateral vector. Verified: dock zone spans Y −6024…−4244, image-right is −Y, bollards land at **−5964** |
| road dash count from the across-road dimension | from the spine dimension |
| ring segments a fixed 80 cm at a ~13.5 m radius, so large gaps | half-length from the circumference: 32 segments, half-length **164 cm** against a 132 cm half-chord, a 24% overlap, so the ring closes |
| pad top `deck_z+18`, marking top `deck_z+16` — buried | markings sit `finish_z + 6` with the deck top at `finish_z`. Verified: pad deck top **405**, marking top **415** |
| unit extents assumed to be 50 | read from `meshes.json` per mesh; a mesh with no recorded bounds is a blocking problem, not a silent 50 |
| `unreal.Rotator(a, b, c)` positionally — which sets **pitch**, not yaw | `Rotator(roll=, pitch=, yaw=)` by keyword |

That last one was a live bug: every ring segment was being pitched instead of turned.

---

## 7. Preflight, and reruns that really are no-ops

Nothing mutates until every check passes. Location **and rotation and scale** are the source
transform; each is compared against the inventory. Every mesh and material is loaded up front. The
plan's own problems, an unusable support survey, a protected class, a water-like label, a missing nav
volume or a nav volume that still would not cover the platform all stop the run **before the first
move**. Every move and every surface placement is read back and verified, and if any operation did not
take effect the level is **not saved**.

Surfaces are **reconciled by label**: matched actors are updated in place, missing ones created, and
only labels the plan no longer contains are destroyed. The previous version destroyed and recreated
all fifty every run while calling it a no-op.

Simulated against the real plan: first apply moves 298 and leaves 0; second moves 0 and finds 298
already in place; rotating one actor, rescaling one, or moving one refuses the whole run naming that
actor. 63 surface labels, all unique.

**Navigation:** the actual volume is half extent (12000, 9750, 2250), already larger than the platform's
(10452, 8898). Recentring on the platform centre covers it — the plan computes that and reports
`covers_platform_after_move: True`, so **no brush resize is needed**. If a future frame made that
false it becomes a blocking problem. Rebuild navigation after applying.

---

## 8. Commands

1. **Probe** — §1, both forms. Read the VERDICT.
2. **Inventory** — `-run=pythonscript -script=".../ib_inventory_garrison.py"`. Writes `actors.json`,
   `assemblies.json`, `meshes.json`, `anchors.json`, `support.json`, `summary.txt`. Check the SUPPORT
   GRID block says `ok` with a nonzero cell count before going on.
3. **Plan (read-only)** — same form with `ib_layout_garrison.py`. Writes `layout/plan.json` and
   `report.txt`.
4. **Captures (editor, not a commandlet)** —
   `UnrealEditor.exe <project> -ExecutePythonScript=".../ib_capture_garrison.py"`.
5. **Apply** — after your backup: `IB_GARRISON_APPLY=1`, plus `IB_GARRISON_SAVE=1` to save,
   `IB_GARRISON_NAV=1` for the nav recentre. `IB_GARRISON_REVERT=1` undoes it.

## 9. Changed tools

| File | Change |
|---|---|
| `Scripts/ib_probe_garrison_support.py` | **New.** Read-only support diagnostic with an explicit verdict. |
| `Scripts/ib_inventory_garrison.py` | Mesh-geometry support by default with an allowlisted ground source; trace mode with `break_hit_result` decoding and hit identity; `no-data` never reported as `ok`; errors recorded, not swallowed; assemblies include all descendant folders, deduplicated; structural-only placement bounds. |
| `Scripts/ib_layout_garrison.py` | One finished deck level; out-of-grid unsupported; source support rejected; reversible platform treatment; corrected bollard edge, road length, ring chord, marking height, mesh bounds and Rotator keywords; full preflight including rotation and scale; verified operations; label-keyed surface reconciliation; revert mode; nav coverage validated. |
| `Scripts/ib_capture_garrison.py` | Unchanged this pass — it already shares the plan's frame and documents the editor invocation. |

---

## 10. Unverified limits

- **Nothing ran.** The plan logic was exercised with `unreal` stubbed, against your real
  `actors.json`, `assemblies` and `meshes.json`. The support grid in that exercise was **modelled**
  from where the existing buildings' bases sit — it is a way to drive the code, **not** measured
  terrain, and none of its numbers are offered as evidence. `finish_z = 405` in my run is an artefact
  of that model; the real value comes from the real survey.
- The dry run did find four live defects that only real data exposes: missing imports after the header
  rewrite, the `Docks / Harbor` folder splitting on its own name, the tolerant folder matcher
  preferring the site root over the docks, and the `Rotator` argument order. All fixed and re-verified.
- `ProceduralMeshLibrary.get_section_from_static_mesh` and `StaticMesh.get_num_sections` are the
  documented editor route to mesh data but are **unproven in this project**. If they fail, the
  inventory records the traceback and reports `no-data`, and the probe's geometry section says so
  first. That is the single most important thing for the probe to confirm.
- Rasterising at 400 cm resolves terraces well and platform **edges** only to ~4 m. Slab extents are
  zone rectangles, so a deck may overhang the real rim by a couple of metres; worth a finer step for
  the pad and pier once the survey works.
- Hiding the old platform leaves its collision, so pass 1's water gaps are **visual only**. Walking out
  over a gap will not drop you. That is deliberate and reversible, not an oversight.
- The new decks are axis-aligned rectangles. The reference's chamfered pad outline is approximated by
  a chamfered-cube slab, not a true octagon, and the pier is a rectangle, not a tapered mole.
- Markings are prototype cubes wearing `MI_Landmass_HelipadMarking`. They read as paint from the air,
  not close up. No kerb, rail or seawall-cap asset is used; `Seawall_Main` is untouched.
- Building yaws are unchanged, so doors face where they faced. Whether each still opens sensibly onto
  the new lanes is a judgement for the captures.

## 11. Focused checks after the first apply

Aerial against the reference, handedness confirmed by eye. Walk the spine pad → forecourt, and check
each relocated building's threshold meets the deck. Spawn clearance and a clear exit from the moved
Barracks. Weapon rack approachable inside the moved Armory. All 19 building lights still with their
buildings. Collision and navigation over every moved footprint, with a rebuild. Mission-director
references intact. Watch deployment and return. Reserve still empty with a usable approach.

Stopping here for your review.
