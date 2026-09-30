"""
IBPY: ib_survey_garrison.py

READ-ONLY. Re-syncs me with the current state of CarrowGateGarrison after
you deleted and re-placed everything. Touches nothing -- just reports.

For every level actor with a StaticMeshComponent, logs:
  - Actor label (what I'll refer to it as)
  - Static mesh asset path (so I know it's a fresh Tripo3D import vs.
    something else)
  - World location / rotation (yaw) / scale
  - Local-space bounding box extents (half-size) and origin offset, so I
    can work out real-world footprint size without guessing
  - Whether it already has a "_Collision" duplicate asset sitting next to
    it from the old carving work (stale, would need re-doing) and its
    current collision_trace_flag / collision_enabled state

Also separately lists ALL other actors (non-static-mesh, e.g. lights,
triggers, volumes, blueprints) grouped by World Outliner folder, in case
useful landmarks (old DoorFrame blueprints, trigger boxes, etc.) already
exist that we can reuse for the new doors.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_survey_garrison.py"
Paste the full output back and I'll use it to plan the new door
placement + re-run the collision/door-hole carving on the current
buildings.
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    log(f"Total actors in level: {len(all_actors)}")

    mesh_actors = []
    other_actors = []

    for a in all_actors:
        mesh_comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
        static_mesh = mesh_comp.get_editor_property("static_mesh") if mesh_comp else None
        if mesh_comp and static_mesh:
            mesh_actors.append((a, mesh_comp, static_mesh))
        else:
            other_actors.append(a)

    log("==== STATIC MESH ACTORS (candidate buildings/props) ====")
    for a, mesh_comp, static_mesh in mesh_actors:
        label = a.get_actor_label()
        folder = str(a.get_folder_path()) or "(root)"
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scale = a.get_actor_scale3d()

        mesh_path = static_mesh.get_path_name()
        bounds = static_mesh.get_bounds()
        box_extent = bounds.box_extent
        origin = bounds.origin

        collision_enabled = mesh_comp.get_collision_enabled()
        body_setup = static_mesh.get_editor_property("body_setup")
        trace_flag = body_setup.get_editor_property("collision_trace_flag") if body_setup else None

        complex_mesh = None
        try:
            complex_mesh = static_mesh.get_editor_property("complex_collision_mesh")
        except Exception:
            pass

        log(
            f"  '{label}' folder='{folder}'\n"
            f"      mesh='{mesh_path}'\n"
            f"      loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) yaw={rot.yaw:.1f} "
            f"scale=({scale.x:.1f},{scale.y:.1f},{scale.z:.1f})\n"
            f"      local_bounds_extent=({box_extent.x:.1f},{box_extent.y:.1f},{box_extent.z:.1f}) "
            f"local_bounds_origin=({origin.x:.1f},{origin.y:.1f},{origin.z:.1f})\n"
            f"      collision_enabled={collision_enabled} trace_flag={trace_flag} "
            f"complex_collision_mesh={complex_mesh}"
        )

    log("==== NON-MESH ACTORS (by folder -- lights, triggers, volumes, blueprints, etc.) ====")
    by_folder = {}
    for a in other_actors:
        folder = str(a.get_folder_path()) or "(root)"
        by_folder.setdefault(folder, []).append(f"{a.get_actor_label()} [{a.get_class().get_name()}]")
    for folder in sorted(by_folder.keys()):
        log(f"  [{folder}] ({len(by_folder[folder])} actor(s)):")
        for entry in sorted(by_folder[folder]):
            log(f"      {entry}")

    log("Done. Nothing was modified.")


main()
