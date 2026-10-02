# Carrow Gate garrison, layout pass 1 — revised (September 23, 2026)

Revision from `Docs/CLAUDE_GARRISON_INVENTORY_REVIEW_2026-09-23.md`, against the real inventory you
ran. Three scripts rewritten in `Scripts/`. No Unreal launched, no build, no map or asset written, no
apply run, no live save, no git or lock operation, no menu, network or progression change.

**Nothing has been executed against the engine.** The plan logic was dry-run with `unreal` stubbed,
reading your actual `actors.json`, and every number in §4 comes from that run. It proves the
arithmetic and the guards; it proves nothing about the editor.

---

## 1. What the previous pass got wrong, and why

Your diagnosis was right and the root cause was upstream of the frame: I inferred the site's axis
from the player-start yaw. `PS_Barracks_MissionStart` faces −Y because it faces out of the barracks
door. It says nothing about which way the compound points. Everything downstream inherited that.

The real evidence says otherwise, and it is unambiguous:

- `Carrowgate Garrison/Main Gate` sits at X ≈ −1750, and all of `CG Mainland` lies at X < 665. **The
  land is at −X.** The garrison is a mole running out to +X.
- `Carrowgate Garrison/Docks / Harbor` sits at Y ≈ −4000. **The docks are on the −Y side.**

So the spine runs along X, not Y — the previous pass had the site rotated 90°, which is why picking
"the largest flat cluster" then handed it 104 km² of mainland and shrubbery.

The revised frame derives both axes from actors:

- **Landward** = the cardinal direction from the platform centre toward the Main Gate → **−X**.
- **Image-right** = the sign of the docks' offset *projected onto the axis across the spine* → **−Y**.

That second one needed care. Snapping the docks' direction to a cardinal axis of its own returns the
spine, because the docks are 62 m down-spine and 51 m across it — the larger component is the wrong
one. Projecting onto the perpendicular is the correct test and it is what the script does. The frame
then reports its own handedness in the report, so a mirrored plan cannot pass unnoticed.

**On handedness generally:** the reference aerial looks landward, so its right-hand side is the
player's left when facing out to sea. Reading it naively would have mirrored the compound. Deriving
image-right from where the docks already are removes the question entirely — and the answer agrees
with the reference, dock and ship on the right.

---

## 2. Frame and support

| | |
|---|---|
| platform | `GarrisonPlatform_New`, mesh `Body2`, uniform scale 1500 |
| extent | X −3500 → 17404, Y −7803 → 9993 (**209 m along the spine, 178 m across**) |
| seaward tip | (17404.2, 1094.7) |
| landward | −X · image-right | −Y |

**The bounding-box top is not a ground height, and the map proves it.** Barracks, Mess Hall and
Command & Comms have their bases at Z 378; Armory, Sensor Array, Watch Tower and the docks have
theirs at Z 78. The platform is one shaped mesh with at least two terraces 3 m apart.

So the inventory now traces a downward grid over the platform footprint (400 cm step, ~2,400
samples) and records the ground height and hit/miss per cell. Every placement is checked against it:
coverage ≥ 88% of sampled cells, terrace spread ≤ 150 cm across the footprint, and the vertical
delta for a move is the difference of the two medians — so a building crossing terraces keeps
exactly the relationship to the deck it already had. In the dry run that produced dz = +300 for the
Armory and Sensor Array moving up to the rear terrace, and −300 for Command & Comms moving down,
which is the right answer and not one I typed in.

---

## 3. Assemblies, not clusters

Grouping is now the **authored actor folders**. A proximity cluster over tall meshes is not a
building: it strands roofs, doors and lamps and merges neighbours. `Carrowgate Garrison/Watch Tower`
is 136 actors including `04_Watch Tower_DoorFrame`, and it moves as one thing.

Roles are assigned **semantically**, not by nearest free slot:

| assembly | role | why |
|---|---|---|
| Watch Tower | `control_tower` | the reference's left platform carries a watch tower |
| Command & Comms | `control_ops` | it is the operations building beside that tower |
| Barracks, Mess Hall, Vehicle Bay | left service row | the reference's left cluster |
| Armory, Sensor Array | right service row | the reference's right cluster |
| Parade Yard | forecourt paving | a 5 cm slab; paving, not a building |
| Civic Route | dock approach | a 5 cm slab beside the pier |
| Docks / Harbor | `dock_berth` | hull and both cranes move outboard of the new pier |
| **Main Gate** | **held** | the landward road in, which the reference keeps behind the compound |
| **Ground, Lighting** | **held** | the platform itself; lighting is reviewed after the structure |

Gameplay actors travel with the assembly that owns them and each one is named in the manifest:
`PS_Barracks_MissionStart` with the Barracks, and the five door frames with their buildings.

One actor needed catching by hand. `BP_WeaponRack` stands at (8646, −3353), inside the Armory's
footprint, but carries **no folder**, so the authored grouping misses it — move the Armory and the
rack is left standing in open ground where the dock now goes. A small explicit table adopts it into
the Armory by exact label; it moves by that assembly's delta and nothing else's, and the report names
it on its own line. Nothing gameplay-related moves on its own. The kaiju spawner, the five act directors and the recast mesh are
protected outright — the apply step refuses rather than touching one.

Slots are nominal, and the site gets the last word: if a footprint lands on a terrace step, inside
the hangar reserve, within 6 m of a neighbour or across the road, the plan searches a bounded ±0.08
offset grid and takes the nearest clean position, recording the nudge. If nothing is clean it keeps
the nominal and reports the problem, so a conflict is never hidden by moving a building somewhere
worse. The dry run used that three times.

---

## 4. The manifest (dry run against your inventory)

```
role             folder                    n   from                    to                 dist     dz
control_tower    Watch Tower             136   [13819, -2300]    ->    [10924, 8035]     10733     +0
control_ops      Command & Comms          26   [ 4019, -1500]    ->    [ 9461, 5544]      8901   -300
service_left_1   Barracks                 28   [ 7000,  8500]    ->    [ 5907, 7145]      1741     +0
service_left_2   Mess Hall                26   [ 3000,  8519]    ->    [ 3294, 7145]      1405     +0
service_left_3   Vehicle Bay               4   [ 4051,  3879]    ->    [ 3294, 3764]       766     +0
service_right_1  Armory *                 30   [ 9000, -3000]    ->    [ 5907, -4956]     3660   +300
service_right_2  Sensor Array             24   [10500, -5000]    ->    [ 3294, -4956]     7206   +300
forecourt_yard   Parade Yard               1   [ 4089,  5397]    ->    [ 4548, -2465]     7875     +0
dock_approach    Civic Route               1   [11591, -3003]    ->    [11133, -5134]     2180     +0
dock_berth       Docks / Harbor            3   [13199, -4001]    ->    [11133, -6380]     3151     +0
```

`*` the Armory's 30 includes `BP_WeaponRack`, adopted as above.

279 actor transforms, 50 surface pieces, **0 blocking problems**.

### Surfaces actually created

The previous version logged unfilled roles and built nothing. This one builds, from meshes your
inventory shows are placed in the map:

| piece | × | mesh | material |
|---|---|---|---|
| Forecourt deck, road deck, neck deck | 3 | `SM_ChamferCube` | `M_Bastion_Paving` |
| Landing pad deck | 1 | `SM_ChamferCube` | `MI_Landmass_Helipad` |
| Control platform deck, dock deck | 2 | `SM_ChamferCube` | `M_Bastion_Concrete` |
| Circular pad marking | 24 | `Cube`, tangential segments | `MI_Landmass_HelipadMarking` |
| Road centre dashes | 6 | `Cube` | `MI_Landmass_HelipadMarking` |
| Dock bollards | 10 | `Cylinder` | `M_Bastion_Concrete` |
| Hangar reserve outline | 4 | `Cube` | `MI_Landmass_HelipadMarking` |

The ring is drawn as segments rather than a disc because a filled disc would hide the pad it is
painted on, and two stacked slabs would z-fight. Every created actor is labelled `IBG1_*`, tagged
`IB_GarrisonPass1` and filed under `Carrowgate Garrison/Pass1`. **The reserve is outlined, not built
on** — it stays yours.

### Navigation

`NavMeshBounds_CarrowgateGarrison` currently covers Y −14000 → 5500, and the platform reaches
Y 9993. The rear service rows would have no navigation at all. The plan proposes recentring it on
the platform, applied **only** with `IB_GARRISON_NAV=1`, and says plainly in the report that the
volume's brush extent cannot be set from Python — you adjust that in the editor and rebuild
navigation afterwards.

---

## 5. Repeat safety and stale input

Every transform carries the actor's **absolute source and target**, keyed by actor path. On apply,
each actor is one of three things:

- at its target → counted as already done, untouched;
- at its recorded source → moved to the absolute target;
- **at neither → the whole run refuses before anything moves.**

The stale sweep completes before the first mutation, so a partial application is not reachable.
Simulated on the real plan: first apply moves every actor once and leaves none behind; a second
apply moves nothing and finds them all already in place; tampering with one actor's position refuses the entire run. `set_actor_location(current
+ delta)` is gone.

Actors are resolved by `path`, never by list position — `get_all_level_actors()` does not promise an
order, and a skipped actor shifts an index. The inventory pairs each actor with its row at append
time rather than `zip`-ing two lists that may have diverged.

---

## 6. Commands

**1 — inventory (read-only):**
```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -run=pythonscript -script="D:\Unreal Games\IronBreach\Scripts\ib_inventory_garrison.py" -unattended -nosplash -abslog="D:\Unreal Games\IronBreach\Saved\GarrisonRestructure\inventory.log"
```
Writes `actors.json`, `assemblies.json`, `meshes.json`, `anchors.json`, **`support.json`**,
`summary.txt`. `IB_GARRISON_SUPPORT_STEP` tunes the trace grid; `IB_GARRISON_SUPPORT=0` skips it, and
the layout then refuses every placement for want of ground data, which is the correct failure.

**2 — plan (read-only):** same form with `ib_layout_garrison.py`. Writes `layout/plan.json` and
`layout/report.txt`. Read the report first: it lists the frame it derived, every move with its
support numbers, any nudges, what is held, the surfaces, the navigation proposal and any problems.

**3 — captures (editor, not a commandlet):**
```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -ExecutePythonScript="D:\Unreal Games\IronBreach\Scripts\ib_capture_garrison.py"
```
You were right that the commandlet form was wrong — the sequence runs on a Slate post-tick callback
and a commandlet has no tick. Six views: `aerial-reference`, `road-from-pad`, `road-from-rear`,
`control-platform`, `dock-and-berth`, `hangar-reserve`. Copy the folder aside before applying.

**4 — apply, after reviewing the plan and taking your backup:** `IB_GARRISON_APPLY=1` performs it
and does **not** save. Add `IB_GARRISON_SAVE=1` to save, `IB_GARRISON_NAV=1` to include the nav move.
`IB_GARRISON_PLAN=<path>` runs an edited plan instead of recomputing.

The aerial is derived from the same frame the plan uses — dry-run against your data it sits at
(26811, 1095, 22334) looking back at the platform centre, **47.9° below horizontal**, with the
control platform on the left of frame and the dock and berth on the right. That is the reference's
view, and the sides are checked rather than asserted.

---

## 7. Changed files

| File | Change |
|---|---|
| `Scripts/ib_inventory_garrison.py` | Rewritten: folder assemblies; frame from the named platform actor; traced support grid; numeric pitch/yaw/roll; reference properties reported as set / unset / unreadable; mainland, city, shoreline and navmesh folders excluded; actors paired with rows at append time. |
| `Scripts/ib_layout_garrison.py` | Rewritten: evidence-derived frame and handedness; semantic roles; whole-footprint validation against support, reserve, neighbours and lanes; bounded placement search; absolute transforms with stale refusal; real surface creation; navigation proposal. |
| `Scripts/ib_capture_garrison.py` | Rewritten: one shared garrison frame from the plan; corrected handedness; editor `-ExecutePythonScript` invocation documented; six views. |

Nothing else was touched. No C++, no content, no map.

---

## 8. Remaining fidelity limits

- **Nothing ran.** The dry run stubbed `unreal` and modelled the support grid as two terraces with a
  step at X ≈ 8100, inferred from where the existing buildings' bases sit. The real grid comes from
  real traces and may disagree; if it does, the placements shift and the report says so.
- The support trace uses `SystemLibrary.line_trace_single` against the editor world, obtained through
  `UnrealEditorSubsystem` with an `EditorLevelLibrary` fallback. Both are wrapped; if neither works
  the inventory reports `unavailable` and the layout refuses to place anything.
- 400 cm sampling resolves terraces well and platform *edges* only to within 4 m. A building placed
  near the rim may still overhang by a couple of metres. Worth a finer step for the pad and dock if
  the aerial looks wrong at the edges.
- The hull sits on the deck at base Z 80, not in the water — it is a prototype on a plinth. The pass
  moves it outboard beside the new pier and keeps that relationship rather than inventing a
  waterline.
- **Exact-art gaps:** no purpose-made pad ring, kerb, rail or seawall-cap asset. Markings are prototype
  cubes wearing the helipad-marking material and will read as paint from the air, not close up.
  `Seawall_Main` exists (5 placed) and is **not** used by this pass — perimeter work is a later one.
  The yellow-edged quay lines of the reference are not reproduced.
- The reference's building count is roughly eight or nine; the map has six real buildings plus a
  vehicle bay. The forecourt will read as sparser than the picture until more exist. This pass
  arranges what is there rather than inventing filler.
- Rotations are not changed. Every assembly keeps its current yaw, so doors face where they faced.
  Whether each door still faces sensibly onto the new lanes is a judgement for the captures.
- `garrison_mech` and the other optional director references: the revised inventory now reports
  `set` / `unset` / `unreadable` separately, so the next run distinguishes an unset reference from a
  failed read. The previous data cannot, and I have not assumed either way.

## 9. Focused checks after the first apply

Aerial against the reference, with handedness confirmed by eye. Walk the spine pad → forecourt.
Spawn clearance and a clear exit from the relocated Barracks. Weapon rack still approachable and
interactable in its new position inside the relocated Armory. Collision and navigation
over every moved footprint, with a rebuild, not a volume count. Mission-director references intact.
Watch deployment and return. The reserve still empty and its forecourt approach usable.

Stopping here for your review.
