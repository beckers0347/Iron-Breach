"""
IBPY: ib_furnish_garrison.py

Imports the Blender furniture/decoration kit (SourceArt/Carrowgate/Props -> /Game/Buildings/Props) and furnishes the
garrison buildings: Barracks, Mech Hangar, Armory, Medical, Command, Mess Hall and the two Main Gate towers.

Layouts are authored in each building's Blender frame (metres; front wall = -Y, prop yaw 0 faces -Y). The script
converts to world (UE flips Y) using the building actor's transform, drops props on the floor, gives each a box
collision and tags it IB_Furniture so a re-run replaces the previous furnishing.

Run in the editor (level open), then File > Save All:   py "X:/IronBreach/Scripts/ib_furnish_garrison.py"
"""
import json
import math
import os
import sys
import unreal

PROP_SRC = "X:/IronBreach/SourceArt/Carrowgate/Props"
PROP_DEST = "/Game/Buildings/Props"
MAT_SHARED = "/Game/Buildings/Carrowgate_Common/Materials"
TAG = "IB_Furniture"
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "X:/IronBreach/Scripts"
if _here not in sys.path:
    sys.path.insert(0, _here)
import ib_barracks_materials as mats_mod

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AT = unreal.AssetToolsHelpers.get_asset_tools()
FAILED = []


def log(m):
    unreal.log("IBPY: " + m)


# ------------------------------------------------------------------------------------------ materials
def materials():
    out = {}
    for name, spec in mats_mod.SPECS.items():
        for path in ("/Game/Buildings/Barracks_02/Materials/M_Barracks02_" + name, MAT_SHARED + "/M_Barracks02_" + name):
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                out[name] = unreal.EditorAssetLibrary.load_asset(path)
                break
        else:
            try:
                m = AT.create_asset("M_Barracks02_" + name, MAT_SHARED, unreal.Material, unreal.MaterialFactoryNew())
                mats_mod._build(name, spec, m)
                mats_mod.MEL.recompile_material(m)
                unreal.EditorAssetLibrary.save_loaded_asset(m)
                out[name] = m
                log("  built material " + name)
            except Exception as e:
                log("  material %s failed: %r" % (name, e))
    return out


# ------------------------------------------------------------------------------------------ import
def import_prop(name, info, mats):
    path = "%s/SM_Prop_%s.fbx" % (PROP_SRC, name)
    t = unreal.AssetImportTask()
    t.filename = path
    t.destination_path = PROP_DEST
    t.destination_name = "SM_Prop_" + name
    t.automated = True
    t.save = False
    t.replace_existing = True
    o = unreal.FbxImportUI()
    o.import_mesh = True
    o.import_materials = True
    o.import_textures = False
    o.import_as_skeletal = False
    o.import_animations = False
    sm = o.static_mesh_import_data
    sm.set_editor_property("combine_meshes", True)
    sm.set_editor_property("auto_generate_collision", False)
    sm.set_editor_property("generate_lightmap_u_vs", False)
    t.options = o
    AT.import_asset_tasks([t])
    mesh = unreal.load_asset("%s/SM_Prop_%s" % (PROP_DEST, name))
    if not mesh:
        raise RuntimeError("import failed: " + name)
    # box collision from the Blender bounds (UCX hulls do not survive the scripted import)
    mn, mx = info["min"], info["max"]
    k = unreal.KBoxElem()
    k.set_editor_property("center", unreal.Vector((mn[0] + mx[0]) * 50.0, -(mn[1] + mx[1]) * 50.0, (mn[2] + mx[2]) * 50.0))
    k.set_editor_property("rotation", unreal.Rotator(0, 0, 0))
    k.set_editor_property("x", (mx[0] - mn[0]) * 100.0)
    k.set_editor_property("y", (mx[1] - mn[1]) * 100.0)
    k.set_editor_property("z", (mx[2] - mn[2]) * 100.0)
    bs = mesh.get_editor_property("body_setup")
    agg = bs.get_editor_property("agg_geom")
    agg.set_editor_property("box_elems", [k])
    bs.set_editor_property("agg_geom", agg)
    bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
    # materials by slot name
    slots = list(mesh.get_editor_property("static_materials"))
    for i, s in enumerate(slots):
        sn = str(s.get_editor_property("imported_material_slot_name"))
        if sn in mats:
            mesh.set_material(i, mats[sn])
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return mesh


# ------------------------------------------------------------------------------------------ layouts
def row(prop, x0, x1, n, y, yaw):
    return [(prop, x0 + (x1 - x0) * i / max(1, n - 1), y, yaw) for i in range(n)]


def layouts():
    L = {}
    # ---- Barracks_02 (interior x -14.8..17.2, y +-7.5). Keep the middle aisle and the NPC spots clear.
    b = []
    for x in (-11.0, -8.0, -5.0, -2.0, 8.0, 11.0, 14.0):
        b += [("Bunk", x, 6.45, 0), ("Footlocker", x + 1.6, 6.45, 90)]
    for x in (-11.0, -8.0, 8.0, 11.0, 14.0):
        b += [("Bunk", x, -6.45, 180), ("Footlocker", x + 1.6, -6.45, 90)]
    b += [("Locker", 16.7, y, -90) for y in (-6.3, -5.65, -5.0, -4.35, -3.7, -3.05, -2.4, 2.4, 3.05, 3.7, 4.35, 5.0, 5.65, 6.3)]
    b += [("MessTable", 11.0, 0.0, 0), ("Bench", 11.0, -0.8, 0), ("Bench", 11.0, 0.8, 0), ("FloorMat", -6.5, 0.0, 0)]
    b += [("RadioDesk", 4.6, 6.5, 0), ("Chair", 4.6, 5.5, 180), ("Stool", 6.8, 5.8, 0)]
    b += [("CrateStack", 16.0, 6.6, 20), ("CrateStack", 16.0, -6.6, 160), ("AmmoCrate", 15.2, 5.2, 0), ("AmmoCrate", 15.2, -5.2, 0)]
    b += [("TrashBin", -14.0, -6.2, 0), ("TrashBin", -14.0, 6.2, 0), ("ShelfUnit", 6.4, -6.95, 180), ("WorkLight", 6.2, 3.6, 0)]
    L["Barracks"] = (0.0, b)
    # ---- Mech Hangar (interior roughly x -12..11, y +-13.2); centre kept clear for the mech, side doors at x~3.
    h = []
    for x in (-9.0, -5.5, 6.5, 9.5):
        h += [("Workbench", x, 12.75, 0), ("Workbench", x, -12.75, 180)]
    h += [("ToolChest", 10.3, y, -90) for y in (-8.0, -7.1, -6.2, -5.3, 5.3, 6.2, 7.1, 8.0)]
    h += [("PartsCrate", -1.0, 12.4, 0), ("PartsCrate", -1.0, -12.4, 180), ("GasCylinders", 8.0, -11.6, 0), ("GasCylinders", -11.0, 11.6, 0)]
    h += [("Barrel", -11.2, -11.5, 0), ("Barrel", -10.4, -11.7, 0), ("Barrel", -11.4, -10.7, 0), ("Barrel", 10.6, 11.4, 0)]
    h += [("CrateStack", 8.5, 11.3, 15), ("CrateStack", -11.0, -8.6, 90), ("WorkLight", -7.0, 9.0, 0), ("WorkLight", -7.0, -9.0, 0),
          ("WorkLight", 5.0, 9.0, 0), ("WorkLight", 5.0, -9.0, 0), ("ShelfUnit", 10.5, 0.0, -90) if False else ("AmmoCrate", 9.8, 3.0, 0)]
    h += [("FloorMat", -4.0, 7.2, 0), ("FloorMat", -4.0, -7.2, 0), ("TrashBin", 10.5, -9.5, 0), ("TrashBin", 10.5, 9.5, 0)]
    L["Mech_Hangar"] = (0.0, h)
    # ---- Armory (interior x +-11.1, y -7.5..7.6); racks/bench/crates exist in the mesh already.
    a = [("ShelfUnit", 10.6, y, -90) for y in (-5.5, -3.6, -1.7, 0.2, 2.1, 4.0, 5.9)]
    a += [("CrateStack", 9.2, -6.6, 30), ("AmmoCrate", 6.5, -3.0, 0), ("AmmoCrate", 7.2, -3.2, 20), ("AmmoCrate", 6.8, -3.5, 90),
          ("AmmoCrate", -3.0, 3.4, 0), ("Chair", -7.5, -1.2, 180), ("Chair", -4.8, 1.2, 0), ("WorkLight", -10.4, 4.0, 0),
          ("Barrel", 10.3, 7.0, 0), ("Barrel", 9.6, 7.2, 0), ("TrashBin", 10.4, -7.0, 0), ("Workbench", 3.4, 6.9, 0),
          ("Stool", 3.4, 5.7, 0), ("FloorMat", 0.0, -5.0, 0), ("ToolChest", -10.6, 0.0, 90), ("ToolChest", -10.6, 1.0, 90)]
    L["Armory"] = (0.15, a)
    # ---- Medical (interior x +-9.2, y +-6.2); beds/curtains/counter exist in the mesh.
    m = [("IVStand", x + 0.7, 5.5, 0) for x in (-8.0, -6.0, -4.0, -2.0, 0.0)]
    m += [("MedCabinet", x, -6.55, 180) for x in (-6.4, -5.4, 5.4, 6.4)]
    m += [("ShelfUnit", 8.7, -4.8, -90), ("ShelfUnit", 8.7, -2.9, -90), ("Desk", -7.6, -5.3, 0), ("Chair", -7.6, -4.3, 0),
          ("TrashBin", 8.6, 5.6, 0), ("Stool", 3.4, 1.4, 0), ("Stool", 6.7, 1.4, 0), ("FloorMat", -4.0, -1.5, 0),
          ("Cot", -8.4, 0.6, 90), ("MedCabinet", -9.0, 2.5, 90), ("AmmoCrate", 7.0, -6.0, 0)]
    L["Medical"] = (0.15, m)
    # ---- Command (interior x +-7.5, y -7..6.5). Tower core fills x -3..3, y 0..6.
    c = [("ServerRack", -7.0, y, 90) for y in (-5.8, -4.8, -3.8, -2.8)]
    c += [("WallScreen", 7.4, -3.0, -90), ("Console", -4.6, -6.35, 180), ("Chair", -4.6, -5.3, 0), ("Console", 4.6, -6.35, 180),
          ("Chair", 4.6, -5.3, 0), ("Chair", -2.9, -1.0, 90), ("Chair", 2.9, -1.0, -90), ("Chair", 0.0, -3.0, 180),
          ("FloorMat", 0.0, -1.0, 0), ("TrashBin", -7.0, 5.6, 0), ("WorkLight", 6.2, 4.0, 0), ("Desk", 6.2, 1.2, -90),
          ("Chair", 5.2, 1.2, -90), ("Stool", -6.2, 1.0, 0), ("ServerRack", -7.0, 0.2, 90)]
    L["Command"] = (0.15, c)
    # ---- Mess Hall (interior x +-11.2, y +-5.2); tables + counter exist in the mesh.
    e = [("Stove", -10.4, 4.5, 0), ("Stove", -9.0, 4.5, 0), ("Fridge", 10.5, 4.7, 0), ("ShelfUnit", 11.0, 0.5, -90),
         ("ShelfUnit", -11.1, -2.5, 90), ("TrashBin", -11.0, -4.5, 0), ("TrashBin", 11.0, -4.5, 0), ("Barrel", 10.4, -4.2, 0)]
    e += [("Stool", x, 3.0, 0) for x in (3.5, 5.0, 6.5, 8.0)]
    e += [("CrateStack", -11.0, 1.0, 90), ("AmmoCrate", 9.5, -3.2, 0), ("FloorMat", 0.0, 1.8, 0), ("Counter", -6.0, 4.5, 0) if False else ("FloorMat", -6.0, 2.8, 0)]
    L["Mess_Hall"] = (0.15, e)
    # ---- Main Gate towers (tower interior x +-3.9, y +-6): placed with the tower offset (+-9.75, 0).
    g = [("Locker", 3.7, y, -90) for y in (-3.0, -2.35, -1.7)] + [("Console", -1.5, -5.3, 180), ("Chair", -1.5, -4.3, 0),
         ("WeaponRack", -3.6, 2.5, 90), ("AmmoCrate", 3.2, 4.8, 0), ("Barrel", -3.4, 5.2, 0), ("TrashBin", 3.4, 5.2, 0), ("FloorMat", 0.0, 0.5, 0)]
    right = [(p, x + 9.75, y, w) for (p, x, y, w) in g]
    left = [(p, -9.75 - x, y, -w) for (p, x, y, w) in g]      # mirror the whole tower layout about its centre
    L["MainGate"] = (0.15, right + left)
    return L


# ------------------------------------------------------------------------------------------ placement
def clear_old():
    n = 0
    for a in list(EAS.get_all_level_actors()):
        if TAG in [str(t) for t in a.tags]:
            EAS.destroy_actor(a)
            n += 1
    log("cleared %d previous furniture actors" % n)


def place(label, floor_up, items, meshes):
    b = next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == label), None)
    if not b:
        log("  %s: building not found, skipped" % label)
        return 0
    loc, psi = b.get_actor_location(), b.get_actor_rotation().yaw
    c, s = math.cos(math.radians(psi)), math.sin(math.radians(psi))
    n = 0
    for k, (prop, bx, by, th) in enumerate(items):
        mesh = meshes.get(prop)
        if not mesh:
            continue
        lx, ly = bx * 100.0, -by * 100.0
        pos = unreal.Vector(loc.x + lx * c - ly * s, loc.y + lx * s + ly * c, loc.z + floor_up * 100.0)
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, pos, unreal.Rotator(roll=0, pitch=0, yaw=psi - th))
        a.static_mesh_component.set_static_mesh(mesh)
        a.set_actor_label("FURN_%s_%s_%02d" % (label, prop, k))
        a.set_folder_path("Carrowgate Garrison/Furniture/" + label)
        a.set_editor_property("tags", [unreal.Name(TAG)])
        a.set_mobility(unreal.ComponentMobility.STATIC)
        n += 1
    log("  %s: %d props placed" % (label, n))
    return n


def main():
    log("=== ib_furnish_garrison ===")
    info = json.load(open(PROP_SRC + "/props.json"))
    mats = materials()
    meshes = {}
    for name, i in info.items():
        try:
            meshes[name] = import_prop(name, i, mats)
        except Exception as e:
            FAILED.append(name)
            unreal.log_error("IBPY: import %s failed: %r" % (name, e))
    log("imported %d/%d props" % (len(meshes), len(info)))
    clear_old()
    total = 0
    for label, (up, items) in layouts().items():
        total += place(label, up, items, meshes)
    log("=== done: %d props placed. failures: %s ===" % (total, FAILED or "none"))


main()
