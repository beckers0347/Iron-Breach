"""
DIAGNOSE COBBLESTONE / WALKWAY STATE
================================================================
IRON BREACH / Unreal Engine 5.8

Shane says the walkway's cobblestone looks stretched again and that he
moved some things around. This just reports facts, no changes:
  - Confirms M_AI_CobblestonePath's current tile-world-size (should be 90
    per fix_cobblestone_tile_scale.py).
  - Lists every actor currently wearing M_AI_CobblestonePath or
    MI_Landmass_Road, with location/scale, sorted so non-uniform scales
    (a real stretch driver even under triplanar, since a squashed mesh's
    face normals skew the triplanar blend weights) are easy to spot.
  - Flags any actor whose scale looks unusual (very large, very thin, or
    highly non-uniform XY).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_cobblestone.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

COBBLE_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
FLAT_ROAD_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"


def log(msg):
    print("[DiagnoseCobblestone] %s" % msg)


def run():
    mat = AL.load_asset(COBBLE_PATH)
    if mat:
        exprs = MEL.get_material_expressions(mat)
        const_nodes = [e for e in exprs if isinstance(e, unreal.MaterialExpressionConstant)]
        log("M_AI_CobblestonePath: %d expression(s) total, %d Constant node(s)." % (len(exprs), len(const_nodes)))
        for c in const_nodes:
            try:
                r = c.get_editor_property("R")
                if 0.001 < r < 1.0:
                    log("  Constant node R=%.5f  (1/R = %.1f -> looks like a tile-world-size of %.1fcm)" % (r, 1.0 / r, 1.0 / r))
            except Exception:
                pass
    else:
        log("M_AI_CobblestonePath NOT FOUND at %s" % COBBLE_PATH)

    all_actors = actor_subsystem.get_all_level_actors()

    def wearing(actor, path):
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            m = comp.get_material(0)
            if m and m.get_path_name().startswith(path):
                return True
        return False

    cobble_actors = [a for a in all_actors if wearing(a, COBBLE_PATH)]
    flat_actors = [a for a in all_actors if wearing(a, FLAT_ROAD_PATH)]

    log("Actors currently wearing M_AI_CobblestonePath: %d" % len(cobble_actors))
    log("Actors currently wearing MI_Landmass_Road (flat/untextured): %d" % len(flat_actors))

    log("--- Non-uniform / unusual-scale cobblestone actors ---")
    flagged = 0
    for a in cobble_actors:
        s = a.get_actor_scale3d()
        loc = a.get_actor_location()
        ratio = max(s.x, s.y) / max(min(s.x, s.y), 0.0001)
        if ratio > 3.0 or max(s.x, s.y, s.z) > 40.0 or min(s.x, s.y) < 0.5:
            flagged += 1
            log("  %s: loc=(%.0f,%.0f,%.0f) scale=(%.2f,%.2f,%.2f) xy_ratio=%.1f" % (
                a.get_actor_label(), loc.x, loc.y, loc.z, s.x, s.y, s.z, ratio))
    if not flagged:
        log("  (none flagged)")

    log("--- All MI_Landmass_Road (flat, never-textured) actors -- these are the ones that will look plain/gray, not cobblestone ---")
    for a in flat_actors[:60]:
        loc = a.get_actor_location()
        log("  %s at (%.0f,%.0f,%.0f)" % (a.get_actor_label(), loc.x, loc.y, loc.z))
    if len(flat_actors) > 60:
        log("  ...and %d more." % (len(flat_actors) - 60))

    log("Done.")


run()
