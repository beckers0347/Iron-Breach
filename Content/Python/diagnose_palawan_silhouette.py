"""
DIAGNOSE THE DISTANT PALAWAN SILHOUETTE -- READ-ONLY, no mutations
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
The mountain diagnostic came back clean -- all 145 peaks are tightly
clustered in height/aspect, nothing flagged as an outlier -- so the black
torn/ribbon shape in your screenshots almost certainly isn't one of them.

build_carrowgate_garrison.py has a separate function, add_distant_palawan(),
that spawns an actual PALAWAN kaiju character (BP_Kaiju_Palawan) far in the
distance as pure atmosphere/set-dressing, labeled "PALAWAN_DistantSilhouette".
Its own code comment warns it "scales up at BeginPlay (ApplySpecies)" -- i.e.
it only reaches its real huge size once you're in Play mode, not in the
plain editor viewport. Several of your screenshots showing the black shape
are in PIE, which fits. A humanoid/kaiju-rigged character scaled up huge and
viewed from far away -- thin limbs, a tail, an idle-animation pose -- would
read exactly as a torn, forked black silhouette rather than a mountain.

This just finds that actor (if it exists) and logs everything about it --
mesh/skeletal mesh, scale, location, rotation, current animation, material --
without changing anything.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_palawan_silhouette.py"

Run it once in the plain editor (not PIE) and, if you can, once WHILE in PIE
too (Play, then open the console and run the same command) -- the scale
number is the one that matters, since that's what "scales up at BeginPlay"
means: it may look totally different between those two runs.
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[DiagPalawan] %s" % msg)


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    candidates = [a for a in all_actors if "palawan" in a.get_actor_label().lower()
                  or "silhouette" in a.get_actor_label().lower()]

    log("Found %d actor(s) with 'palawan' or 'silhouette' in their label." % len(candidates))

    if not candidates:
        log("None found by label -- if it exists under a different name, search the Outliner "
            "for 'Atmosphere' folder or anything Kaiju-related far from the garrison/mainland "
            "(around world X=40000cm / 400m per add_distant_palawan()'s spawn call) and tell me "
            "its actual label.")
        return

    for a in candidates:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scale = a.get_actor_scale3d()
        folder = str(a.get_folder_path())
        origin, extent = a.get_actor_bounds(False)

        log("  label='%s'  class=%s  folder='%s'" % (a.get_actor_label(), a.get_class().get_name(), folder))
        log("    location=(%.0f, %.0f, %.0f)  rotation=(%.0f,%.0f,%.0f)  scale=(%.2f,%.2f,%.2f)" % (
            loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll, scale.x, scale.y, scale.z))
        log("    live_bounds_size_m=(%.1f, %.1f, %.1f)" % (
            extent.x * 2 / 100.0, extent.y * 2 / 100.0, extent.z * 2 / 100.0))

        # Try to find a skeletal mesh component (kaiju characters are almost certainly
        # skeletal, not static mesh) and report its mesh + current material.
        found_mesh = False
        for comp in a.get_components_by_class(unreal.SkeletalMeshComponent):
            found_mesh = True
            skel_mesh = comp.skeletal_mesh
            mat = comp.get_material(0)
            log("    SkeletalMeshComponent: mesh=%s  visible=%s  hidden_in_game=%s  material=%s" % (
                skel_mesh.get_name() if skel_mesh else "(none)",
                comp.is_visible(), comp.bHiddenInGame if hasattr(comp, "bHiddenInGame") else "?",
                mat.get_name() if mat else "(none)"))
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            found_mesh = True
            mesh = comp.static_mesh
            mat = comp.get_material(0)
            log("    StaticMeshComponent: mesh=%s  visible=%s  material=%s" % (
                mesh.get_name() if mesh else "(none)", comp.is_visible(),
                mat.get_name() if mat else "(none)"))
        if not found_mesh:
            log("    (no SkeletalMeshComponent or StaticMeshComponent found on this actor)")


run()
