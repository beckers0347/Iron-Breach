"""Find the harbor water plane + quay/player heights so the new sea sits right."""
import unreal, os
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
def log(m): unreal.log(f"IBPY: {m}")
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
acts = unreal.EditorActorSubsystem().get_all_level_actors()
log(f"=== water inspect: {len(acts)} actors ===")
# PlayerStart = where the player stands (quay height reference)
for a in acts:
    if isinstance(a, unreal.PlayerStart):
        log(f"PlayerStart at {a.get_actor_location()}")
# candidate water actors: label/mesh/material mentions water/ocean/sea, or very flat & huge
cands = []
for a in acts:
    if not isinstance(a, unreal.StaticMeshActor): continue
    smc = a.static_mesh_component
    if not smc: continue
    mesh = smc.static_mesh
    mname = mesh.get_name() if mesh else ""
    mats = []
    try:
        for i in range(smc.get_num_materials()):
            m = smc.get_material(i); mats.append(m.get_name() if m else "None")
    except Exception: pass
    label = a.get_actor_label()
    text = (label + " " + mname + " " + " ".join(mats)).lower()
    o, ext = a.get_actor_bounds(False)
    flat_huge = ext.z < 50 and ext.x > 5000 and ext.y > 5000
    if any(k in text for k in ("water","ocean","sea","harbor","harbour","lake","river")) or flat_huge:
        cands.append((a, label, mname, mats, o, ext))
log(f"--- {len(cands)} water-ish candidates ---")
for a,label,mname,mats,o,ext in cands[:20]:
    log(f"  '{label}' mesh={mname} mats={mats} center={o} extent={ext} scale={a.get_actor_scale3d()}")
# ground reference: biggest flat meshes near the player Z (the quay)
log("=== DONE ===")
