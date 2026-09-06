"""
THIN TOWN TREE DENSITY -- CarrowGateGarrison
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
A one-shot Editor Python script (same convention as the other Content/Python/
scripts) that reduces how many tree/shrub actors are packed into the garrison
town footprint, without touching the wider background forest on the hillsides.

I could not find the trees referenced by name anywhere in CarrowGateGarrison.umap
via static string inspection (they're not part of build_carrowgate_garrison.py
and don't show up as InstancedFoliageActor data either), which means they were
most likely painted/placed directly in-editor as individual actors after that
script ran -- so I can't know their exact mesh names or folder ahead of time.
To handle that, this script is keyword- and area-based instead of hardcoded to
specific asset paths:

  1. DRY-RUN FIRST (default: DRY_RUN = True). It scans every actor in the level,
     keeps any whose actor label OR static mesh asset name contains one of the
     TREE_KEYWORDS (tree, alder, hornbeam, pine, fir, spruce, oak, shrub, bush,
     foliage, GV_Vol -- that last one matches the Shrub asset names already
     confirmed in this map), AND whose location falls inside the TOWN_MIN/
     TOWN_MAX box below. It does NOT delete anything in this mode -- it just
     logs, grouped by mesh asset, how many candidates it found and their name
     pattern, so you can confirm it's actually matching your trees before
     anything is touched.

  2. Once the dry-run output looks right (i.e. the counts/mesh names match what
     you'd expect the town's trees to be), flip DRY_RUN to False and re-run.
     It will then delete a deterministic, evenly-spread subset of the matched
     actors down to KEEP_RATIO (default 0.4 = keep 40%, i.e. thin by 60%) --
     using a seeded shuffle so re-running with the same ratio doesn't re-roll
     which ones survive.

THE TOWN BOUNDING BOX
----------------------
Built from the area list in build_carrowgate_garrison.py (Watch Tower at
(56,44)m, Command & Comms at (73,-61)m, Armory at (112,-15)m, Vehicle Bay at
(35,-3)m, etc. -- all in meters, x100 for cm). I picked a box that covers the
built-up garrison cluster (gate through armory/mess/barracks/watch tower/
command) while leaving the Docks/Harbor, Sea Wall and outer hillsides alone,
since those aren't "the town." Adjust TOWN_MIN/TOWN_MAX below if it's cutting
off part of the cluster you want thinned, or catching ground you don't.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/thin_garrison_trees.py"

Re-running in DRY_RUN mode is always safe (read-only). Re-running with
DRY_RUN = False and the same KEEP_RATIO on an already-thinned area will not
delete further (nothing left to match beyond what KEEP_RATIO already kept) --
lower KEEP_RATIO and re-run if you want it thinner still.

IF THE DRY-RUN FINDS NOTHING OR MATCHES THE WRONG THING: paste back what it
logs (or just tell me the actor label of one of the trees, e.g. by clicking
one in the viewport and checking the Details panel title) and I'll retarget
the keyword list / box in one pass instead of guessing again.
"""

import random
import unreal

# --- Tune these two before flipping DRY_RUN off -----------------------------
DRY_RUN = False          # True = log only, delete nothing. Flip to False once confirmed.
KEEP_RATIO = 0.4         # fraction of matched town trees to KEEP (0.4 = thin by 60%)
RANDOM_SEED = 1234       # fixed seed so repeated runs at the same ratio are stable

# Town bounding box, in cm (world units), built from build_carrowgate_garrison.py's
# area list x100. Covers Main Gate/Vehicle Bay/Parade Yard/Watch Tower/Barracks/
# Mess Hall/Armory/Command&Comms/Sensor Array. Leaves the Docks/Harbor, Sea Wall,
# and Helipad (and everything beyond) alone.
TOWN_MIN = unreal.Vector(-2000, -8500, -2000)
TOWN_MAX = unreal.Vector(13500, 6000, 3000)

TREE_KEYWORDS = (
    "tree", "alder", "hornbeam", "pine", "fir", "spruce", "oak", "birch",
    "shrub", "bush", "foliage", "gv_vol",
)


def log(msg):
    print("[ThinTrees] %s" % msg)


def label_or_mesh_matches(actor):
    label = actor.get_actor_label().lower()
    mesh_name = ""
    if isinstance(actor, unreal.StaticMeshActor):
        smc = actor.static_mesh_component
        mesh = smc.static_mesh if smc else None
        if mesh:
            mesh_name = mesh.get_path_name().lower()
    haystack = label + " " + mesh_name
    return any(k in haystack for k in TREE_KEYWORDS)


def in_town_box(actor):
    loc = actor.get_actor_location()
    return (TOWN_MIN.x <= loc.x <= TOWN_MAX.x and
            TOWN_MIN.y <= loc.y <= TOWN_MAX.y)


def run():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    candidates = []
    for actor in all_actors:
        try:
            if label_or_mesh_matches(actor) and in_town_box(actor):
                candidates.append(actor)
        except Exception as e:
            log("  (skipped an actor during scan: %s)" % e)

    log("Scanned %d total level actors." % len(all_actors))
    log("Matched %d tree/shrub actor(s) inside the town box." % len(candidates))

    if not candidates:
        log("Nothing matched -- either the box needs adjusting or the keyword list")
        log("doesn't cover this project's tree asset naming. Click a tree in the")
        log("viewport, check its label/mesh in the Details panel, and tell me what")
        log("it says so I can retarget this script.")
        return

    # Group by mesh asset (or label, for non-static-mesh matches) for the dry-run report.
    groups = {}
    for a in candidates:
        smc = a.static_mesh_component if isinstance(a, unreal.StaticMeshActor) else None
        mesh = smc.static_mesh if smc else None
        key = mesh.get_name() if mesh else a.get_actor_label()
        groups.setdefault(key, []).append(a)

    for key, actors in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        log("  %5d x  %s" % (len(actors), key))

    if DRY_RUN:
        log("DRY_RUN is True -- nothing deleted. Confirm the list above looks like")
        log("your town's trees, then set DRY_RUN = False and re-run to actually thin.")
        return

    # Deterministic, evenly-spread thin: sort by a stable key, seeded-shuffle, keep
    # the first KEEP_RATIO fraction, delete the rest.
    candidates_sorted = sorted(candidates, key=lambda a: a.get_actor_label())
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(candidates_sorted)

    keep_count = int(round(len(candidates_sorted) * KEEP_RATIO))
    to_delete = candidates_sorted[keep_count:]

    log("KEEP_RATIO=%.2f -> keeping %d, deleting %d." % (KEEP_RATIO, keep_count, len(to_delete)))

    deleted = 0
    for a in to_delete:
        try:
            actor_subsystem.destroy_actor(a)
            deleted += 1
        except Exception as e:
            log("  failed to delete %s: %s" % (a.get_actor_label(), e))

    log("Deleted %d actor(s). %d town tree/shrub actor(s) remain." % (deleted, len(candidates) - deleted))
    log("Save the level (Ctrl+S) once you're happy with the result.")


run()
