"""
DIAGNOSE WHATEVER ACTOR(S) YOU HAVE SELECTED -- READ-ONLY
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
The reddish/brick triangular patch in your last screenshot (near the
buildings, cut off diagonally) is a corner I hadn't touched yet -- I traced
the label "Ground_SouthTaper_CivicRoute" you had selected in an earlier
screenshot to a "Civic Route" ground pad in build_carrowgate_garrison.py,
which uses MAT_GROUND (M_AI_Ground) -- a completely different, older
material than the cobblestone path work (M_AI_CobblestonePath) we've been
doing. If that's what you're pointing at, the corner-joint script genuinely
couldn't have fixed it -- it only touches the CG Mainland outskirt roads,
a different system entirely.

Before I guess again: select the actor(s) showing the problem in the
Outliner or viewport (click directly on the reddish patch / the corner
that doesn't connect), then run this. It just logs which material and mesh
you've actually got selected -- no mutations.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diag_selected_material.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[DiagSelected] %s" % msg)


def run():
    selected = actor_subsystem.get_selected_level_actors()
    if not selected:
        log("Nothing selected -- click the actor showing the problem in the Outliner or "
            "viewport first, then run this again.")
        return

    for a in selected:
        loc = a.get_actor_location()
        folder = str(a.get_folder_path())
        log("label='%s'  class=%s  folder='%s'  location=(%.0f,%.0f,%.0f)" % (
            a.get_actor_label(), a.get_class().get_name(), folder, loc.x, loc.y, loc.z))
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            mat = comp.get_material(0)
            log("  StaticMeshComponent: mesh=%s  material=%s  material_path=%s" % (
                mesh.get_name() if mesh else "(none)",
                mat.get_name() if mat else "(none)",
                mat.get_path_name() if mat else "(none)"))


run()
