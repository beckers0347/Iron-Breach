"""
One-shot diagnostic -- prints the actual state of SM_Truck_Cargo's Nanite and
collision settings so we can confirm (rather than guess) whether the PIE lag
is a Nanite-build problem, a collision problem, or something else. Run from
the Output Log console:
    py "X:/IronBreach/Content/Python/check_truck_mesh.py"
"""
import unreal

MESH_PATH = "/Game/LevelPrototyping/AIModels/SM_Truck_Cargo.SM_Truck_Cargo"

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if mesh is None:
    unreal.log_error(f"[Truck Check] Could not load {MESH_PATH}")
else:
    nanite = mesh.get_editor_property("nanite_settings")
    unreal.log(f"[Truck Check] Nanite enabled: {nanite.get_editor_property('enabled')}")

    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is None:
        unreal.log_warning("[Truck Check] No BodySetup found on the mesh -- no simple collision exists.")
    else:
        agg = body_setup.get_editor_property("agg_geom")
        num_boxes = len(agg.get_editor_property("box_elems"))
        unreal.log(f"[Truck Check] Simple collision box count: {num_boxes}")
        unreal.log(f"[Truck Check] Collision trace flag: {body_setup.get_editor_property('collision_trace_flag')}")

    unreal.log(f"[Truck Check] Num triangles (LOD0, via get_num_triangles): {mesh.get_num_triangles(0)}")
    unreal.log(f"[Truck Check] Num vertices (LOD0): {mesh.get_num_vertices(0)}")

# Also check the actual placed actor's mobility + collision preset in the level.
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
found = False
for actor in actor_subsystem.get_all_level_actors():
    if actor.get_actor_label() == "VehicleBay_Truck_01":
        found = True
        comp = actor.static_mesh_component
        unreal.log(f"[Truck Check] Actor mobility: {comp.mobility}")
        unreal.log(f"[Truck Check] Actor collision enabled: {comp.get_editor_property('body_instance').get_editor_property('collision_enabled')}")
        unreal.log(f"[Truck Check] Actor static mesh set: {comp.static_mesh.get_name() if comp.static_mesh else None}")
if not found:
    unreal.log_warning("[Truck Check] No actor labeled 'VehicleBay_Truck_01' found in the level.")
