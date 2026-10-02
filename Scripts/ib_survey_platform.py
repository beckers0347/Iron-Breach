"""
IBPY: ib_survey_platform.py

READ-ONLY. Getting exact numbers for the dock/Garrison platform before
building any road lines, the helipad H/circle, or door caution stripes.
Reports every actor under the 'Carrowgate Garrison' folder tree (and
anything with 'Garrison', 'Dock', 'Helipad', 'Platform', 'Hangar' in its
label, in case folder placement is inconsistent), with:
  - label, folder, class, mesh path (if any)
  - world location / yaw / scale
  - local bounds extent + origin (so we can work out real-world footprint
    size/shape, and for round platforms, estimate a radius from the X/Y
    extents)

This will tell us: the platform/dock shape and size, where the round
helipad pad actually is and how big it is (for the H + circle), and
confirms the white cube mech-hangar placeholder's exact position/size.

Touches nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_survey_platform.py"
Paste back the full output.
"""

import unreal

KEYWORDS = ["garrison", "dock", "helipad", "platform", "hangar", "helicopter", "crane"]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()

    matches = []
    for a in all_actors:
        label = a.get_actor_label()
        folder = str(a.get_folder_path())
        haystack = (label + " " + folder).lower()
        if "carrowgate garrison" in folder.lower() or any(k in haystack for k in KEYWORDS):
            matches.append(a)

    log(f"Total matching actors: {len(matches)}")

    for a in matches:
        label = a.get_actor_label()
        folder = str(a.get_folder_path()) or "(root)"
        cls = a.get_class().get_name()
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scale = a.get_actor_scale3d()

        mesh_comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
        static_mesh = mesh_comp.get_editor_property("static_mesh") if mesh_comp else None

        if static_mesh:
            mesh_path = static_mesh.get_path_name()
            bounds = static_mesh.get_bounds()
            ext = bounds.box_extent
            origin = bounds.origin
            world_ext_x = ext.x * scale.x
            world_ext_y = ext.y * scale.y
            world_ext_z = ext.z * scale.z
            approx_radius = (world_ext_x + world_ext_y) / 2.0
            log(
                f"[{label}] class={cls} folder='{folder}'\n"
                f"    mesh='{mesh_path}'\n"
                f"    loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) yaw={rot.yaw:.1f} "
                f"scale=({scale.x:.2f},{scale.y:.2f},{scale.z:.2f})\n"
                f"    local_bounds_extent=({ext.x:.1f},{ext.y:.1f},{ext.z:.1f}) local_bounds_origin=({origin.x:.1f},{origin.y:.1f},{origin.z:.1f})\n"
                f"    world_extent_approx=({world_ext_x:.1f},{world_ext_y:.1f},{world_ext_z:.1f}) "
                f"approx_radius_if_round={approx_radius:.1f}"
            )
        else:
            log(f"[{label}] class={cls} folder='{folder}' (no static mesh) "
                f"loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) yaw={rot.yaw:.1f}")

    log("Done. Nothing was modified.")


main()
