import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()
targets = [a for a in actors if a.get_actor_label() in (
    "WatchTowerShaft_Wall_S_01", "RoofCap_North", "ObservationPlatform_01_Rail_1",
    "07_Armory_DoorFrame".replace("DoorFrame",""),  # placeholder, ignore
)]
# just grab any 3 watchtower dynamic mesh actors directly
targets = [a for a in actors if a.get_actor_label() in ("WatchTowerShaft_Wall_S_01", "RoofCap_North", "ObservationPlatform_01_Rail_1", "ArmoryShell_Wall_S_01", "Armory_ReinforcedRoof")]
for a in targets:
    dcomps = a.get_components_by_class(unreal.DynamicMeshComponent)
    for c in dcomps:
        try:
            mesh = c.get_dynamic_mesh()
            num_tris = mesh.get_triangle_count() if mesh else -1
        except Exception as e:
            num_tris = f"ERR:{e}"
        visible = c.is_visible()
        hidden_in_game = c.get_editor_property("hidden_in_game") if c else None
        mat = c.get_material(0) if c else None
        log(f"{a.get_actor_label()}: tris={num_tris} visible={visible} hidden_in_game={hidden_in_game} material={mat}")
log("=== done ===")
