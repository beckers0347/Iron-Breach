"""p18_stages.py - extra stages for p18_match_reference.py (hide helpers, ground, rocks, trees, fog, slabs, props)."""
import random
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAT_DIR = "/Game/IronBreach/Thornfield/Materials"
PROP_DIR = "/Game/IronBreach/Thornfield/Props"


def log(m):
    unreal.log("[Thornfield] p18: " + m)


def lin(r, g, b):
    return unreal.LinearColor(r, g, b, 1.0)


def setp(o, n, v):
    try:
        o.set_editor_property(n, v)
        return True
    except Exception as e:
        log("could not set %s: %r" % (n, e))
        return False


def actors(cls):
    return [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == cls]


def label_of(a):
    return a.get_actor_label()


def stage_hide():
    n = 0
    for a in EAS.get_all_level_actors():
        if label_of(a).startswith(("FRONT_", "REF_", "LBL_", "ZONE_", "BoundWall_")):
            a.set_actor_hidden_in_game(True)
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                c.set_visibility(False)
            n += 1
    log("hidden %d helper actors" % n)


def make_mat(name, rgb, rough=0.95):
    path = MAT_DIR + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    r.set_editor_property("r", rough)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def stage_ground():
    gravel = make_mat("M_TF_Gravel2", (0.045, 0.041, 0.033))
    floor = make_mat("M_TF_ForestFloor2", (0.02, 0.03, 0.014))
    mount = make_mat("M_TF_MountainForest2", (0.016, 0.024, 0.012))
    for a in EAS.get_all_level_actors():
        l = label_of(a)
        if l == "GB_Ground":
            a.static_mesh_component.set_material(0, gravel)
        elif l == "Ground_Outer":
            a.static_mesh_component.set_material(0, floor)
        elif l.startswith(("MOUNTAIN_", "SEAMROCK_")) or (a.get_class().get_name() == "StaticMeshActor" and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name().startswith("Cliff_")):
            a.static_mesh_component.set_material(0, mount)
    log("ground / mountain materials set")


def stage_rocks():
    n = 0
    for a in list(EAS.get_all_level_actors()):
        if label_of(a).startswith(("ROCK_", "SEAMROCK_")) and a.get_class().get_name() == "StaticMeshActor":
            m = a.static_mesh_component.static_mesh
            if m and "GranitePillar" in m.get_name():
                EAS.destroy_actor(a)
                n += 1
    log("removed %d pillar rocks" % n)


YARD_BOXES = [(12000, 23500, 6200, 16500), (21000, 33500, 10500, 17200)]


def in_box(x, y, boxes):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in boxes)


def stage_trees():
    random.seed(7)
    n = 0
    for a in list(EAS.get_all_level_actors()):
        l = label_of(a)
        if l.startswith(("FILLTREE_", "TREE_IN", "TREE_")) and not l.startswith("TREE_Z"):
            p = a.get_actor_location()
            if in_box(p.x, p.y, YARD_BOXES) and random.random() < 0.92:
                EAS.destroy_actor(a)
                n += 1
    log("removed %d trees from yards" % n)


def stage_fog():
    for a in actors("ExponentialHeightFog"):
        c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        setp(c, "fog_density", 0.012)
        setp(c, "fog_height_falloff", 0.10)
        setp(c, "start_distance", 1500.0)
        setp(c, "fog_inscattering_luminance", lin(0.48, 0.5, 0.46))


def _box(label, cx, cy, sx, sy, z, th, mat, cube, yaw=0.0):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(cx, cy, z), unreal.Rotator(0, yaw, 0))
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(cube)
    a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, th / 100.0))
    a.static_mesh_component.set_material(0, mat)
    a.set_mobility(unreal.ComponentMobility.STATIC)
    return a


def stage_slabs():
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    apron = unreal.EditorAssetLibrary.load_asset(MAT_DIR + "/M_Apron")
    yellow = unreal.EditorAssetLibrary.load_asset(MAT_DIR + "/M_SafetyYellow")
    for a in list(EAS.get_all_level_actors()):
        if label_of(a).startswith("P18_SLAB"):
            EAS.destroy_actor(a)
    _box("P18_SLAB_Apron", 27000, 13600, 13000, 6800, 0.6, 1.2, apron, cube)
    _box("P18_SLAB_Yard", 17400, 9700, 6200, 3800, 0.6, 1.2, apron, cube)
    for i in range(5):
        _box("P18_SLAB_Line%d" % i, 22500 + i * 2700, 11000, 90, 1500, 1.4, 0.4, yellow, cube, 20.0)
    _box("P18_SLAB_LineH", 27600, 15100, 7000, 80, 1.4, 0.4, yellow, cube)
    log("slabs placed")


def stage_props():
    random.seed(11)
    for a in list(EAS.get_all_level_actors()):
        if label_of(a).startswith("P18_PROP"):
            EAS.destroy_actor(a)
    obst = []
    for a in EAS.get_all_level_actors():
        l = label_of(a)
        if l.startswith(("SM_", "ROAD_Main", "ROAD_Spur", "CRATE_", "CARGOCONTAINER_", "FUELTANK_", "GENERATOR_", "POLE_", "PAD_")):
            o, e = a.get_actor_bounds(False)
            if l.startswith("ROAD_"):
                obst.append((o.x, o.y, 420.0))
            else:
                obst.append((o.x, o.y, max(e.x, e.y) + 120.0))

    def free(x, y, r):
        return all((x - ox) ** 2 + (y - oy) ** 2 > (r + orr) ** 2 for ox, oy, orr in obst)

    def put(name, x0, x1, y0, y1, count, r, stack=0.0):
        mesh = unreal.EditorAssetLibrary.load_asset("%s/%s.%s" % (PROP_DIR, name, name))
        placed = 0
        tries = 0
        while placed < count and tries < count * 60:
            tries += 1
            x, y = random.uniform(x0, x1), random.uniform(y0, y1)
            if not free(x, y, r):
                continue
            yaw = random.choice([0, 90, 180, 270]) + random.uniform(-8, 8)
            a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 0), unreal.Rotator(0, yaw, 0))
            a.set_actor_label("P18_PROP_%s_%03d" % (name, placed))
            a.static_mesh_component.set_static_mesh(mesh)
            a.set_mobility(unreal.ComponentMobility.STATIC)
            obst.append((x, y, r))
            if stack and random.random() < stack:
                b = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 259), unreal.Rotator(0, yaw, 0))
                b.set_actor_label("P18_PROP_%s_top%03d" % (name, placed))
                b.static_mesh_component.set_static_mesh(mesh)
                b.set_mobility(unreal.ComponentMobility.STATIC)
            placed += 1
        log("%s: %d placed" % (name, placed))

    APRON = (21500, 32800, 11200, 16800)
    YARD = (14800, 20400, 7000, 12200)
    put("SM_CargoContainer", *APRON, 14, 420, stack=0.35)
    put("SM_FuelTank", *APRON, 3, 330)
    put("SM_Generator", *APRON, 4, 180)
    put("SM_Crate", *APRON, 40, 110)
    put("SM_Pallet", *APRON, 14, 110)
    put("SM_Crate", *YARD, 16, 110)
    put("SM_Generator", *YARD, 3, 180)
    put("SM_JerseyBarrier", 15500, 18200, 17300, 19000, 10, 200)
    put("SM_TankTrap", 15200, 18500, 19400, 21500, 10, 100)
    put("SM_JerseyBarrier", *YARD, 6, 200)
    put("SM_CargoContainer", 9000, 14000, 8300, 11800, 5, 420)
    put("SM_Crate", 9000, 14000, 5000, 14500, 14, 110)
