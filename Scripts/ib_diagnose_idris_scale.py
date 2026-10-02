"""
IBPY: ib_diagnose_idris_scale.py

Read-only. Ms_Idris_wSkeleton is importing enormous and lying on her side
(classic Tripo3D FBX export issue -- wrong up-axis + a scale baked into the
rig). Before I write a fix, I need actual numbers instead of guessing:

  1. The mesh's bounds (so we know exactly how oversized it is and can
     compute the correction factor to get her to roughly human height,
     ~180cm).
  2. Its FBX import data (import rotation / uniform scale / translation),
     if Unreal exposes it on this asset -- tells us whether the problem is
     import-time settings we can just redo, or baked into the source file.
  3. The transform of any placed actor(s) using this mesh in the current
     level, so we know if the fix belongs on the asset or per-instance.

Changes nothing. Just reports.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_diagnose_idris_scale.py"
Paste back the full output.
"""

import unreal

MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_wSkeleton"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== DIAGNOSE IDRIS SCALE ====")

    mesh = unreal.load_asset(MESH_PATH)
    if mesh is None:
        log(f"ERROR: could not load {MESH_PATH}")
        return

    log(f"Loaded: {mesh.get_path_name()}  (class: {mesh.get_class().get_name()})")

    # Bounds
    try:
        bounds = mesh.get_bounds()
        box = bounds.box_extent
        origin = bounds.origin
        log(f"Bounds box_extent (half-size, cm): x={box.x:.2f} y={box.y:.2f} z={box.z:.2f}")
        log(f"Bounds origin (cm): x={origin.x:.2f} y={origin.y:.2f} z={origin.z:.2f}")
        log(f"Full size (cm): x={box.x*2:.2f} y={box.y*2:.2f} z={box.z*2:.2f}")
        longest_axis = max(box.x, box.y, box.z) * 2
        log(f"Longest full dimension: {longest_axis:.2f} cm "
            f"(~{longest_axis/100:.1f} m) -- a standing human should read ~175-185 cm tall.")
    except Exception as e:
        log(f"Could not read bounds: {e}")

    # Import data
    try:
        import_data = mesh.get_editor_property("asset_import_data")
        log(f"asset_import_data: {import_data}")
        if import_data is not None:
            sources = import_data.get_editor_property("source_data")
            log(f"  source file(s): {sources}")
    except Exception as e:
        log(f"Could not read asset_import_data: {e}")

    # Any FBX-specific import settings sometimes stored separately
    for prop_name in ("import_uniform_scale", "import_rotation", "import_translation"):
        try:
            val = mesh.get_editor_property(prop_name)
            log(f"  {prop_name}: {val}")
        except Exception:
            pass  # not every version exposes these directly on the mesh

    # Skeleton
    try:
        skel = mesh.get_editor_property("skeleton")
        log(f"Skeleton: {skel.get_path_name() if skel else None}")
    except Exception as e:
        log(f"Could not read skeleton ref: {e}")

    # Placed actors using this mesh
    log("---- Placed actors referencing this mesh in the current level ----")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    found_any = False
    for a in all_actors:
        if not isinstance(a, unreal.SkeletalMeshActor):
            continue
        comp = a.skeletal_mesh_component
        used_mesh = comp.get_skeletal_mesh_asset() if hasattr(comp, "get_skeletal_mesh_asset") else comp.skeletal_mesh
        if used_mesh and used_mesh.get_path_name() == mesh.get_path_name():
            found_any = True
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            log(f"  '{a.get_actor_label()}': loc={loc}  rot(roll={rot.roll:.1f},pitch={rot.pitch:.1f},yaw={rot.yaw:.1f})  scale={scale}")
    if not found_any:
        log("  No placed SkeletalMeshActor in this level is using this exact mesh asset.")

    log("==== DONE ====")


main()
