"""
Iron Breach -- inventory CarrowGateGarrison for the "what's still missing"
punch list (textures + models). Read-only: makes no changes to the level.

Runs directly in the editor's Python console:
    exec(open(r"X:\IronBreach\Scripts\ib_inventory_garrison_level.py").read())

Writes a plain-text report to:
    X:\IronBreach\Claude outputs\GARRISON_INVENTORY.txt
so it can be read back without scrolling through the Output Log.
"""
import unreal

EAS = unreal.EditorActorSubsystem()
OUT_PATH = r"X:\IronBreach\Claude outputs\GARRISON_INVENTORY.txt"

# Materials/mesh names that mean "still a placeholder, not final art"
PLACEHOLDER_MATERIAL_HINTS = [
    "basicshape", "worldgridmaterial", "checker", "m_basic", "defaultmaterial",
    "material'/engine", "m_garrison_building_concrete",
]
PLACEHOLDER_MESH_HINTS = [
    "cube", "shape_cube", "shape_cylinder", "shape_sphere", "shape_plane", "blockout",
]
PLACEHOLDER_LABEL_HINTS = [
    "placeholder", "blockout", "temp", "todo", "wip",
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_mesh_and_materials(actor):
    """Best-effort: returns (static_mesh_path_or_None, [material_path_or_None, ...])"""
    smc = None
    try:
        smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    except Exception:
        pass
    if not smc:
        return None, []
    mesh = smc.get_editor_property("static_mesh")
    mesh_path = mesh.get_path_name() if mesh else None
    mats = []
    try:
        num = smc.get_num_materials()
        for i in range(num):
            m = smc.get_material(i)
            mats.append(m.get_path_name() if m else None)
    except Exception:
        pass
    return mesh_path, mats


def is_placeholder_mesh(mesh_path):
    if not mesh_path:
        return True
    lower = mesh_path.lower()
    return any(h in lower for h in PLACEHOLDER_MESH_HINTS)


def is_placeholder_material(mat_path):
    if not mat_path:
        return True
    lower = mat_path.lower()
    return any(h in lower for h in PLACEHOLDER_MATERIAL_HINTS)


def main():
    log("=== inventorying CarrowGateGarrison ===")
    actors = EAS.get_all_level_actors()
    log(f"INFO total actors in level: {len(actors)}")

    lines = []
    lines.append("IRON BREACH -- CarrowGateGarrison inventory")
    lines.append(f"Total actors: {len(actors)}")
    lines.append("")

    flagged = []
    by_class_count = {}

    for a in actors:
        label = a.get_actor_label()
        cls = a.get_class().get_name()
        by_class_count[cls] = by_class_count.get(cls, 0) + 1

        label_flag = any(h in label.lower() for h in PLACEHOLDER_LABEL_HINTS)
        mesh_path, mats = get_mesh_and_materials(a)
        mesh_flag = is_placeholder_mesh(mesh_path) if mesh_path is not None else False
        mat_flags = [is_placeholder_material(m) for m in mats] if mats else []
        mat_flag = any(mat_flags) if mats else False

        if label_flag or mesh_flag or mat_flag:
            reasons = []
            if label_flag:
                reasons.append("label suggests placeholder")
            if mesh_flag:
                reasons.append(f"mesh looks like a primitive/blockout ({mesh_path})")
            if mat_flag:
                bad_mats = [m for m, f in zip(mats, mat_flags) if f]
                reasons.append(f"placeholder/flat material(s): {bad_mats}")
            flagged.append((label, cls, reasons))

    lines.append("=== ACTOR CLASS COUNTS (top 40) ===")
    for cls, count in sorted(by_class_count.items(), key=lambda x: -x[1])[:40]:
        lines.append(f"  {count:5d}  {cls}")
    lines.append("")

    lines.append(f"=== FLAGGED AS LIKELY PLACEHOLDER/MISSING ART ({len(flagged)}) ===")
    for label, cls, reasons in flagged:
        lines.append(f"  [{cls}] {label}")
        for r in reasons:
            lines.append(f"      - {r}")
    lines.append("")

    # Also specifically report the 6 known garrison buildings' current material state
    lines.append("=== KNOWN GARRISON BUILDINGS: current material per mesh piece ===")
    building_prefixes = [
        "04_Watch Tower", "05_Barracks", "06_Mess Hall",
        "07_Armory", "08_Command & Comms", "09_Sensor Array",
    ]
    for prefix in building_prefixes:
        lines.append(f"-- {prefix} --")
        for a in actors:
            label = a.get_actor_label()
            if label.startswith(prefix):
                mesh_path, mats = get_mesh_and_materials(a)
                lines.append(f"    {label}  mesh={mesh_path}  mats={mats}")
        lines.append("")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log(f"=== inventory written to {OUT_PATH} ({len(flagged)} flagged actors) ===")


try:
    main()
except Exception:
    import traceback
    log("FAIL unhandled exception")
    unreal.log_error(traceback.format_exc())
