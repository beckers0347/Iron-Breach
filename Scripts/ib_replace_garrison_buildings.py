"""
IBPY: ib_replace_garrison_buildings.py

Replaces the remaining Tripo garrison buildings (Armory, Medical, Command, Mess Hall, Main Gate) with the
procedural Blender buildings in X:/IronBreach/SourceArt/Carrowgate (same style as Barracks_02 / Hangar_04):
hollow static shell + UCX collision + animated skeletal doors driven by AIBSensorDoor + interior point lights.

PREREQUISITE  Open CarrowGateGarrison_BoulderShore3 (or the live garrison map). AIBSensorDoor must be compiled.

RUN   py "X:/IronBreach/Scripts/ib_replace_garrison_buildings.py"

Per building it: imports the FBXs -> /Game/Buildings/<Name>, reuses the Barracks_02 procedural materials by slot name,
reads the old Tripo actor's bounds + its door frame direction, spawns the new shell and its sensor doors at the same
spot (facing the same way), spawns the interior/exterior lights, and PARKS the old actors (hidden, no collision,
folder _Replaced_<Name>) -- never deletes them.

SAFE TO RE-RUN: everything it spawns carries the tag IB_<Name> and is replaced on the next run.
NOTHING IS SAVED -- review in the viewport, then File > Save All.

Options (edit below):  ONLY = ("Armory",) to do a subset;  DRY_RUN = True to only log the plan.
"""
import importlib
import json
import math
import os
import sys
import unreal

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "X:/IronBreach/Scripts"
if _here not in sys.path:
    sys.path.insert(0, _here)
import ib_barracks_materials as mats_mod
importlib.reload(mats_mod)

SRC_ROOT = "X:/IronBreach/SourceArt/Carrowgate"
ONLY = tuple(x for x in os.environ.get("IB_ONLY", "").split(",") if x)      # e.g. ("Armory", "Medical")
DRY_RUN = os.environ.get("IB_DRY_RUN", "") == "1"
PARK_OLD = True
SNAP_YAW_TO_90 = True
NEW_FOLDER = "Carrowgate Garrison"
OLD_SUFFIX = "_REPLACED"
SENSOR_CLASS_PATH = "/Script/IronBreach.IBSensorDoor"
CLOSE_DELAY = 1.5
DECK_Z = 385.0

BUILDINGS = {
    "Armory":   dict(old=("Armory",), old_doors=("Armory_DoorFrame",), label="Armory"),
    "Medical":  dict(old=("Medical",), old_doors=("Medical_DoorFrame",), label="Medical"),
    "Command":  dict(old=("Command",), old_doors=("Command_DoorFrame",), label="Command"),
    "MessHall": dict(old=("Mess_Hall",), old_doors=("Mess_Hall_DoorFrame",), label="Mess_Hall"),
    "MainGate": dict(old=("SM_MainGate_Tripo",), old_doors=("BP_MainGateDoor",), label="MainGate", front=(-1.0, 0.0)),
}
LIGHT_COLORS = {"amber": (255, 214, 160), "white": (255, 244, 225), "blue": (150, 190, 255), "red": (255, 90, 70)}


def log(m):
    unreal.log("IBPY: " + m)


def warn(m):
    unreal.log_warning("IBPY: WARNING -- " + m)


FAILED = False


def err(m):
    global FAILED
    FAILED = True
    unreal.log_error("IBPY: ERROR -- " + m)


EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def bl(p):
    return unreal.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)


def all_actors():
    return EAS.get_all_level_actors()


def tags_of(a):
    return [str(t) for t in a.tags]


def base_label(a):
    return a.get_actor_label().replace(OLD_SUFFIX, "")


# ------------------------------------------------------------------------------------ materials
def get_materials():
    """Reuse Barracks_02's procedural materials; build only the missing ones in a shared folder."""
    out = {}
    barracks = "/Game/Buildings/Barracks_02/Materials/M_Barracks02_"
    shared = "/Game/Buildings/Carrowgate_Common/Materials"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for name, spec in mats_mod.SPECS.items():
        for path in (barracks + name, shared + "/M_Barracks02_" + name):
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                out[name] = unreal.EditorAssetLibrary.load_asset(path)
                break
        else:
            try:
                mat = tools.create_asset("M_Barracks02_" + name, shared, unreal.Material, unreal.MaterialFactoryNew())
                mats_mod._build(name, spec, mat)
                mats_mod.MEL.recompile_material(mat)
                out[name] = mat
                log("  built material " + name)
            except Exception as e:
                warn("material %s failed: %r" % (name, e))
    return out


# ------------------------------------------------------------------------------------ import
def fbx_ui(skeletal):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_materials", True)
    ui.set_editor_property("import_as_skeletal", bool(skeletal))
    try:
        ui.set_editor_property("mesh_type_to_import",
                               unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeletal else unreal.FBXImportType.FBXIT_STATIC_MESH)
    except Exception:
        pass
    ui.set_editor_property("automated_import_should_detect_type", False)
    if skeletal:
        ui.set_editor_property("import_animations", True)
        ui.set_editor_property("create_physics_asset", False)
    else:
        ui.set_editor_property("import_animations", False)
        sm = ui.static_mesh_import_data
        sm.set_editor_property("combine_meshes", True)
        sm.set_editor_property("auto_generate_collision", False)
        sm.set_editor_property("generate_lightmap_u_vs", False)
        sm.set_editor_property("remove_degenerates", True)
        try:
            sm.set_editor_property("build_nanite", True)
        except Exception:
            pass
    return ui


def import_fbx(path, dest_path, dest_name, skeletal):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", fbx_ui(skeletal))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    assets = []
    for p in [str(x) for x in task.get_editor_property("imported_object_paths")]:
        a = unreal.EditorAssetLibrary.load_asset(p)
        if a:
            assets.append(a)
    return assets


def set_box_collision(mesh, info):
    """UCX hulls do not survive the scripted FBX import on this engine build; write the same boxes as simple collision."""
    boxes = info.get("hull_boxes", [])
    try:
        bs = mesh.get_editor_property("body_setup")
        agg = bs.get_editor_property("agg_geom")
        elems = []
        for c, sz, yaw in boxes:
            k = unreal.KBoxElem()
            k.set_editor_property("center", unreal.Vector(c[0] * 100.0, -c[1] * 100.0, c[2] * 100.0))
            k.set_editor_property("rotation", unreal.Rotator(0.0, 0.0, -yaw))
            k.set_editor_property("x", sz[0] * 100.0)
            k.set_editor_property("y", sz[1] * 100.0)
            k.set_editor_property("z", sz[2] * 100.0)
            elems.append(k)
        agg.set_editor_property("box_elems", elems)
        bs.set_editor_property("agg_geom", agg)
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
        mesh.modify()
        n = len(bs.get_editor_property("agg_geom").get_editor_property("box_elems"))
        log("  %s: wrote %d box collision primitives (UCX hulls had not imported)" % (mesh.get_name(), n))
    except Exception as e:
        warn("box collision failed (%r) -- falling back to Use Complex Collision As Simple" % e)
        try:
            bs = mesh.get_editor_property("body_setup")
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            mesh.modify()
        except Exception as e2:
            warn("complex-as-simple fallback failed too: %r" % e2)


def do_import(name, info, mats):
    root = "/Game/Buildings/" + name
    folder = os.path.join(SRC_ROOT, name)
    res = {"static": None, "doors": {}}
    assets = import_fbx(os.path.join(folder, "SM_%s.fbx" % name), root + "/Static", "SM_" + name, False)
    meshes = [a for a in assets if isinstance(a, unreal.StaticMesh)]
    if not meshes:
        err("%s: static import produced no StaticMesh" % name)
        return None
    mesh = meshes[0]
    try:
        n_hull = unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh)
    except Exception as e:
        n_hull = -1
        warn("could not count hulls: %r" % e)
    log("  %s: %d convex collision hulls (expect %d), bounds half-extent %s" % (name, n_hull, info.get("n_hulls", -1), mesh.get_bounds().box_extent))
    if n_hull <= 0:
        set_box_collision(mesh, info)
    mats_mod.apply_to_static_mesh(mesh, mats)
    res["static"] = mesh
    for key, d in info["doors"].items():
        dn = "SK_%s_Door_%s" % (name, key)
        ddir = "%s/Doors/%s" % (root, key)
        if unreal.EditorAssetLibrary.does_directory_exist(ddir):
            unreal.EditorAssetLibrary.delete_directory(ddir)    # fresh import: re-imports into an existing skeleton drop the animation
        assets = import_fbx(os.path.join(folder, d["fbx"]), "%s/Doors/%s" % (root, key), dn, True)
        sk = [a for a in assets if isinstance(a, unreal.SkeletalMesh)]
        an = [a for a in assets if isinstance(a, unreal.AnimSequence)]
        pre = "%s/Doors/%s/AS_%s_Door_%s_Open" % (root, key, name, key)
        if sk and not an:
            fdir = "%s/Doors/%s" % (root, key)
            found = []
            for ap in unreal.EditorAssetLibrary.list_assets(fdir, recursive=False, include_folder=False):
                obj = unreal.EditorAssetLibrary.load_asset(ap)
                if isinstance(obj, unreal.AnimSequence):
                    found.append(obj)
            log("  door %s: import returned no animation object; found in folder: %s" % (key, [f.get_name() for f in found]))
            an = found
        if not sk or not an:
            err("%s door %s: import produced skeletal=%d anim=%d" % (name, key, len(sk), len(an)))
            return None
        anim = an[0]
        old_path = anim.get_path_name().split(".")[0]
        new_path = "%s/Doors/%s/AS_%s_Door_%s_Open" % (root, key, name, key)
        if old_path != new_path:
            if unreal.EditorAssetLibrary.does_asset_exist(new_path):
                unreal.EditorAssetLibrary.delete_asset(new_path)
            if unreal.EditorAssetLibrary.rename_asset(old_path, new_path):
                anim = unreal.EditorAssetLibrary.load_asset(new_path)
        res["doors"][key] = (sk[0], anim)
    return res


# ------------------------------------------------------------------------------------ old actors
def find_old(cfg, actors, tag):
    labels = cfg["old"]
    old = None
    for a in actors:
        if tag in tags_of(a):
            continue
        if base_label(a) in labels and isinstance(a, unreal.StaticMeshActor):
            old = a
            break
    doors = [a for a in actors if base_label(a) in cfg["old_doors"] and tag not in tags_of(a)]
    return old, doors


def placement(cfg, old, doors):
    o, e = old.get_actor_bounds(False)
    bottom = o.z - e.z
    floor_z = DECK_Z if abs(bottom - DECK_Z) < 45.0 else bottom
    if cfg.get("front"):
        dx, dy = cfg["front"]
        src = "explicit"
    elif doors:
        dl = doors[0].get_actor_location()
        dx, dy = dl.x - o.x, dl.y - o.y
        src = doors[0].get_actor_label()
    else:
        dx, dy, src = 0.0, -1.0, "default -Y"
    mag = math.hypot(dx, dy) or 1.0
    dx, dy = dx / mag, dy / mag
    yaw = math.degrees(math.atan2(-dx, dy))          # new building's front is local +Y (Blender -Y)
    if SNAP_YAW_TO_90:
        yaw = round(yaw / 90.0) * 90.0
    log("  old '%s': centre (%.0f,%.0f) half (%.0f,%.0f,%.0f) bottom %.0f -> floor %.0f; front from %s -> yaw %.0f"
        % (old.get_actor_label(), o.x, o.y, e.x, e.y, e.z, bottom, floor_z, src, yaw))
    return unreal.Vector(o.x, o.y, floor_z), yaw, (o, e)


def retire(actor, folder):
    label = actor.get_actor_label()
    if not label.endswith(OLD_SUFFIX):
        actor.set_actor_label(label + OLD_SUFFIX)
    actor.set_actor_hidden_in_game(True)
    actor.set_actor_enable_collision(False)
    try:
        actor.set_is_temporarily_hidden_in_editor(True)
    except Exception:
        pass
    try:
        actor.set_folder_path(folder)
    except Exception:
        pass


def clear_previous(tag):
    n = 0
    for a in all_actors():
        if tag in tags_of(a):
            EAS.destroy_actor(a)
            n += 1
    if n:
        log("  removed %d actor(s) from a previous run" % n)


# ------------------------------------------------------------------------------------ spawn
def local_to_world(p, place, yaw):
    v = bl(p)
    r = math.radians(yaw)
    return unreal.Vector(place.x + v.x * math.cos(r) - v.y * math.sin(r),
                         place.y + v.x * math.sin(r) + v.y * math.cos(r),
                         place.z + v.z)


def tag(a, t):
    a.set_editor_property("tags", [unreal.Name(t)])


def spawn_all(name, cfg, info, imports, mats, place, yaw, sensor_cls, t):
    building = EAS.spawn_actor_from_class(unreal.StaticMeshActor, place, unreal.Rotator(0.0, 0.0, yaw))
    building.static_mesh_component.set_static_mesh(imports["static"])
    building.set_actor_label(cfg["label"])
    building.set_folder_path(NEW_FOLDER)
    tag(building, t)
    doors = {}
    for key, d in info["doors"].items():
        sk, anim = imports["doors"][key]
        a = EAS.spawn_actor_from_class(sensor_cls, place, unreal.Rotator(0.0, 0.0, yaw))
        a.configure_door(sk, anim)
        a.configure_volumes(
            bl(d["sensor_c"]), unreal.Vector(d["sensor_h"][0] * 100.0, d["sensor_h"][1] * 100.0, d["sensor_h"][2] * 100.0),
            bl(d["blocker_c"]), unreal.Vector(d["blocker_h"][0] * 100.0, d["blocker_h"][1] * 100.0, d["blocker_h"][2] * 100.0),
            unreal.Rotator(0.0, d.get("blocker_pitch", 0.0), 0.0))
        a.set_editor_property("close_delay", CLOSE_DELAY)
        a.set_editor_property("open_duration_override", float(d.get("seconds", 1.2)))
        a.set_editor_property("player_pawns_only", True)
        if os.environ.get("IB_PREVIEW_OPEN") == "1":
            a.set_editor_property("editor_preview_progress", 1.0)
        mats_mod.apply_to_component(a.get_editor_property("door_mesh"), mats)
        a.set_actor_label("%s_Door_%s" % (cfg["label"], key))
        a.set_folder_path("%s/%s Doors" % (NEW_FOLDER, cfg["label"]))
        tag(a, t)
        a.attach_to_actor(building, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
        doors[key] = a
    n_l = 0
    for i, L in enumerate(info.get("lights", [])):
        a = EAS.spawn_actor_from_class(unreal.PointLight, local_to_world(L["p"], place, yaw), unreal.Rotator(0, 0, 0))
        c = a.get_component_by_class(unreal.PointLightComponent)
        ext = L["kind"] in ("blue", "red")
        c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
        c.set_editor_property("intensity", 900.0 if ext else 3500.0)
        rgb = LIGHT_COLORS.get(L["kind"], LIGHT_COLORS["white"])
        c.set_editor_property("light_color", unreal.Color(r=rgb[0], g=rgb[1], b=rgb[2], a=255))
        c.set_editor_property("attenuation_radius", 700.0 if ext else 1100.0)
        c.set_editor_property("source_radius", 4.0 if ext else 20.0)
        c.set_editor_property("cast_shadows", False)
        a.set_actor_label("%s_Light_%02d" % (cfg["label"], i))
        a.set_folder_path("%s/%s Lights" % (NEW_FOLDER, cfg["label"]))
        tag(a, t)
        n_l += 1
    log("  spawned '%s' + %d sensor door(s) + %d light(s)" % (building.get_actor_label(), len(doors), n_l))
    return building, doors


def trace(start, end, ignore=None):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    r = unreal.SystemLibrary.line_trace_single(world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
                                               ignore or [], unreal.DrawDebugTrace.NONE, True)
    if isinstance(r, tuple):
        hit, res = r[0], r[-1] if len(r) > 1 else None
    else:
        hit, res = bool(r), None
    return hit, res


def collision_check(name, building, place, yaw, info):
    """Horizontal traces at chest height from outside each side toward the centre; vertical trace onto the roof."""
    b = building.get_actor_bounds(False)
    ctr = b[0]
    ext = b[1]
    z = place.z + 150.0
    out = []
    for lab, dv in (("front", (0, 1)), ("back", (0, -1)), ("left", (-1, 0)), ("right", (1, 0))):
        r = math.radians(yaw)
        dx = dv[0] * math.cos(r) - dv[1] * math.sin(r)
        dy = dv[0] * math.sin(r) + dv[1] * math.cos(r)
        far = max(ext.x, ext.y) + 800.0
        s = unreal.Vector(ctr.x + dx * far, ctr.y + dy * far, z)
        e = unreal.Vector(ctr.x, ctr.y, z)
        hit, res = trace(s, e)
        what = ""
        if hit and res is not None:
            try:
                what = res.to_tuple()[9].get_actor_label() if False else str(res.get_editor_property("hit_object_handle"))
            except Exception:
                what = "hit"
        out.append("%s=%s" % (lab, "HIT" if hit else "miss"))
    top = unreal.Vector(ctr.x, ctr.y, place.z + ext.z * 2 + 500.0)
    hit, _ = trace(top, unreal.Vector(ctr.x, ctr.y, place.z - 100.0))
    out.append("roof/floor=%s" % ("HIT" if hit else "miss"))
    log("  %s collision traces (chest height, outside -> centre): %s" % (name, ", ".join(out)))


def aabb(o1, e1, o2, e2):
    return abs(o1.x - o2.x) < e1.x + e2.x and abs(o1.y - o2.y) < e1.y + e2.y


def verify(name, building, doors, actors, skip_tags):
    o, e = building.get_actor_bounds(False)
    log("  %s bounds: centre (%.0f,%.0f,%.0f) half (%.0f,%.0f,%.0f)" % (name, o.x, o.y, o.z, e.x, e.y, e.z))
    for a in actors:
        if a == building or not isinstance(a, unreal.StaticMeshActor):
            continue
        tg = tags_of(a)
        if any(x in tg for x in skip_tags):
            continue
        if a.is_temporarily_hidden_in_editor() if hasattr(a, "is_temporarily_hidden_in_editor") else False:
            continue
        p = a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else ""
        if "/TripoModels/" in p or "/Game/Buildings/" in p:
            o2, e2 = a.get_actor_bounds(False)
            if max(e2.x, e2.y) > 400.0 and aabb(o, e, o2, e2):
                warn("%s bounds overlap '%s' (%s) -- check spacing" % (name, a.get_actor_label(), p.split('/')[-1]))


def main():
    log("=== ib_replace_garrison_buildings START ===" + (" [DRY RUN]" if DRY_RUN else ""))
    sensor_cls = unreal.load_class(None, SENSOR_CLASS_PATH)
    if not sensor_cls:
        err("could not load %s (compile the C++ and restart the editor). Nothing changed." % SENSOR_CLASS_PATH)
        return
    mats = None if DRY_RUN else get_materials()
    done = []
    for name, cfg in BUILDINGS.items():
        if ONLY and name not in ONLY:
            continue
        log("---- %s ----" % name)
        jpath = os.path.join(SRC_ROOT, name, name + ".json")
        if not os.path.isfile(jpath):
            err("missing %s -- run the Blender build first. Skipped." % jpath)
            continue
        info = json.load(open(jpath))
        t = "IB_" + name
        actors = all_actors()
        old, door_old = find_old(cfg, actors, t)
        if old:
            place, yaw, (oo, oe) = placement(cfg, old, door_old)
        else:
            prev = next((a for a in actors if t in tags_of(a) and isinstance(a, unreal.StaticMeshActor)), None)
            if not prev:
                err("%s: old actor %s not found and no earlier spawn either. Skipped." % (name, cfg["old"]))
                continue
            place, yaw = prev.get_actor_location(), prev.get_actor_rotation().yaw
            log("  no old actor left; re-placing at the existing new building: (%.0f,%.0f,%.0f) yaw %.0f" % (place.x, place.y, place.z, yaw))
        if DRY_RUN:
            log("  DRY RUN: would import %d door(s), spawn at (%.0f,%.0f,%.0f) yaw %.0f, park %d old actor(s)"
                % (len(info["doors"]), place.x, place.y, place.z, yaw, 1 + len(door_old)))
            continue
        clear_previous(t)                                       # the old spawn references the door assets we re-import
        imports = do_import(name, info, mats)
        if not imports:
            err("%s: import failed." % name)
            continue
        building, doors = spawn_all(name, cfg, info, imports, mats, place, yaw, sensor_cls, t)
        if PARK_OLD and old:
            park = "_Replaced_" + cfg["label"]
            retire(old, park)
            for d in door_old:
                retire(d, park)
            log("  parked '%s' and %d door frame(s) in %s" % (old.get_actor_label(), len(door_old), park))
        verify(name, building, doors, all_actors(), [t])
        collision_check(name, building, place, yaw, info)
        done.append(name)
    log("=== DONE: %s. Nothing saved -- review, then File > Save All. ===" % (", ".join(done) or "nothing"))


main()
