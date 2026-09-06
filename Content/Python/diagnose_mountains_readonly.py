"""
DIAGNOSE MOUNTAIN PEAKS -- READ-ONLY, no mutations
================================================================
IRON BREACH / Unreal Engine 5.8

WHY THIS EXISTS
----------------
There's a black, torn/ribbon-shaped mountain silhouette that keeps showing
up in the same rough spot across different camera angles -- consistent
position across angles means it's most likely ONE specific mountain actor
with something genuinely wrong (bad scale, bad rotation putting a
ridge-shaped mesh edge-on to begin with, or a Nanite/proxy rendering quirk --
the MOUNTAIN_ASSET_KIT comments in build_carrowgate_mainland.py already flag
that this exact pack had unmeasurable bounds for unclear reasons). Rather
than guess at a fix again, this just prints hard numbers for every peak so
the actual outlier can be picked out by eye instead of inferred.

This does NOT move, retexture, or otherwise touch anything -- purely reads
and logs. Safe to run any number of times.

WHAT TO DO WITH THE OUTPUT
----------------------------
Look for the line whose world_size_m or scale looks wildly different from
its neighbors (e.g. one axis 5-10x larger/smaller than the others, or a
world_size far outside the ~15-70m range everything else falls in). Paste
that specific line (or a few lines around it) back and I'll target a fix
directly at that actor instead of touching the whole range again.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_mountains_readonly.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MOUNTAIN_FOLDER_ROOT = "CG Mainland/Mountains"


def log(msg):
    print("[DiagMountains] %s" % msg)


def is_under_folder(actor, root):
    folder = str(actor.get_folder_path())
    return folder == root or folder.startswith(root + "/")


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    # Only the direct "Mountains" folder -- excludes the invisible Wall
    # collision segments in "Mountains/Wall", which aren't the visible peaks.
    peak_actors = [a for a in all_actors if str(a.get_folder_path()) == MOUNTAIN_FOLDER_ROOT]

    log("Found %d peak actor(s) directly in '%s' (Wall subfolder excluded)." % (len(peak_actors), MOUNTAIN_FOLDER_ROOT))
    log("Columns: label | mesh | rotation(pitch,yaw,roll) | scale | world_size_m(x,y,z) | aspect(xy:z) | material")

    rows = []
    for a in peak_actors:
        comp = a.static_mesh_component if isinstance(a, unreal.StaticMeshActor) else None
        mesh = comp.static_mesh if comp else None
        mat = comp.get_material(0) if comp else None
        scale = a.get_actor_scale3d()
        rot = a.get_actor_rotation()
        origin, extent = a.get_actor_bounds(False)
        size_m = (extent.x * 2 / 100.0, extent.y * 2 / 100.0, extent.z * 2 / 100.0)
        footprint = max(size_m[0], size_m[1])
        aspect = footprint / size_m[2] if size_m[2] > 1e-6 else 0.0
        rows.append((a.get_actor_label(), mesh.get_name() if mesh else "(none)", rot, scale, size_m, aspect,
                     mat.get_name() if mat else "(none)"))

    for label, mesh_name, rot, scale, size_m, aspect, mat_name in sorted(rows, key=lambda r: r[0]):
        log("  %-14s mesh=%-28s rot=(%.0f,%.0f,%.0f) scale=(%.3f,%.3f,%.3f) world_size_m=(%.1f,%.1f,%.1f) footprint:height=%.2f material=%s" % (
            label, mesh_name, rot.pitch, rot.yaw, rot.roll, scale.x, scale.y, scale.z,
            size_m[0], size_m[1], size_m[2], aspect, mat_name))

    # Flag statistical outliers automatically so they're easy to spot in a long log.
    if rows:
        heights = [r[4][2] for r in rows]
        avg_h = sum(heights) / len(heights)
        aspects = [r[5] for r in rows]
        avg_aspect = sum(aspects) / len(aspects)
        log("--- Averages: height=%.1fm, footprint:height aspect=%.2f ---" % (avg_h, avg_aspect))
        for label, mesh_name, rot, scale, size_m, aspect, mat_name in rows:
            h = size_m[2]
            if h > avg_h * 2.5 or h < avg_h * 0.25 or aspect < avg_aspect * 0.3:
                log("  ** SUSPECT %-14s height=%.1fm (avg %.1fm) footprint:height=%.2f (avg %.2f) -- likely the odd one **" % (
                    label, h, avg_h, aspect, avg_aspect))


run()
