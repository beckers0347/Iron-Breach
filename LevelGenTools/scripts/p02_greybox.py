"""p02_greybox.py - Phase 2: create/open the level and build the greybox.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p02_greybox.py"

Builds (all tagged GEN_Generated + GEN_Phase2, re-runnable):
  - flat-colour greybox materials (green ground, red wall, tan road, grey buildings, orange towers)
  - ground plateau and perimeter marker walls from level.json bounds
  - road strips from layout.json
  - one footprint box per structure (real mesh bounds, real orientation) + text label
  - zone labels, scale reference cubes (180 cm person, 8 m vehicle) and a PlayerStart

Look for:
  [Thornfield] Greybox spawned: <n> actors
  [Thornfield] VERIFY: footprint PASS
  [Thornfield] VERIFY: player_start PASS at (x,y,z)
  [Thornfield] VERIFY: scale_refs PASS
"""
import os
import sys
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unreal
import importlib
import gen_common as G
importlib.reload(G)   # UE keeps Python modules loaded between runs; pick up edits

PHASE = 2
CUBE = "/Engine/BasicShapes/Cube"


def open_level(level):
    path = level["level_path"]
    sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        ok = sub.load_level(path)
        G.log("Loaded existing level %s (%s)" % (path, ok))
    else:
        ok = sub.new_level(path)
        G.log("Created new level %s (%s)" % (path, ok))
    return bool(ok)


GB_COLORS = {          # name -> linear RGB
    "Ground": (0.10, 0.16, 0.08),
    "Wall": (0.55, 0.08, 0.08),
    "Road": (0.55, 0.42, 0.22),
    "Apron": (0.35, 0.35, 0.40),
    "Building": (0.75, 0.75, 0.80),
    "Tower": (0.95, 0.55, 0.10),
    "Ref": (1.0, 0.9, 0.0),
}
_MATS = {}


def greybox_material(kind):
    """Create (or reuse) a flat colour material /Game/.../Greybox/M_GB_<kind>."""
    if kind in _MATS:
        return _MATS[kind]
    folder = "/Game/IronBreach/Thornfield/Greybox"
    path = "%s/M_GB_%s" % (folder, kind)
    mat = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mat is None:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_GB_%s" % kind, folder, unreal.Material,
                                                                       unreal.MaterialFactoryNew())
        lib = unreal.MaterialEditingLibrary
        node = lib.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        r, g, b = GB_COLORS[kind]
        node.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
        lib.connect_material_property(node, "", unreal.MaterialProperty.MP_BASE_COLOR)
        lib.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)  # visible in Unlit view too
        lib.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    _MATS[kind] = mat
    return mat


def box_actor(label, center, size, yaw=0.0, kind=None):
    """Cube actor with the given world centre (cm), size (cm) and yaw."""
    a = G.spawn_static_mesh(CUBE, center, (0, yaw, 0), (size[0] / 100.0, size[1] / 100.0, size[2] / 100.0), label, PHASE)
    if kind:
        try:
            a.static_mesh_component.set_material(0, greybox_material(kind))
        except Exception as e:
            G.warn("Material %s failed on %s: %r" % (kind, label, e))
    return a


def top_down_camera(level):
    """Park the viewport high above the base looking straight down, North (+Y) at the top of the screen."""
    try:
        b = level["bounds_cm"]
        cx, cy = (b["min"][0] + b["max"][0]) / 2.0, (b["min"][1] + b["max"][1]) / 2.0
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        ues.set_level_viewport_camera_info(unreal.Vector(cx, cy, 30000.0), unreal.Rotator(roll=0, pitch=-90, yaw=-90))
        G.log("Viewport set to top-down over the base (North (-Y) up, East right, matching the S01 plan). Switch the viewport to Lit/Unlit as you like.")
    except Exception as e:
        G.warn("Could not set viewport camera: %r" % e)


def text_label(text, loc, size=250.0, yaw=0.0):
    a = G.spawn_by_class(unreal.TextRenderActor, loc, (0, yaw, 0), "LBL_" + text.replace(" ", "_"), PHASE)
    try:
        comp = a.text_render
        comp.set_text(text)
        comp.set_editor_property("world_size", size)
        comp.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    except Exception as e:
        G.warn("Text label %s: %r" % (text, e))
    return a


def rotate(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def main():
    G.init_log("p02_greybox")
    count = 0
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        if not open_level(level):
            raise G.GenError("Could not create/open level %s" % level["level_path"])
        G.cleanup_phase(PHASE)

        # Pre-existing default PlayerStarts would fight ours: report them.
        stray = [a for a in G.actor_subsystem().get_all_level_actors()
                 if isinstance(a, unreal.PlayerStart) and unreal.Name(G.TAG_ALL) not in a.tags]
        for a in stray:
            G.warn("Untagged PlayerStart present: %s (delete it by hand)" % a.get_actor_label())

        b = level["bounds_cm"]
        w, d = b["max"][0] - b["min"][0], b["max"][1] - b["min"][1]
        cx, cy = b["min"][0] + w / 2.0, b["min"][1] + d / 2.0
        zt = level["base_plateau_z"]

        # ---- ground plateau (top surface at base_plateau_z) ----
        ground = box_actor("GB_Ground", (cx, cy, zt - 10), (w, d, 20), kind="Ground")
        count += 1
        # ---- perimeter marker walls (5.4 m, silhouette only; blocking is Phase 4) ----
        wall_h, wall_t = 540.0, 80.0
        for name, c, sz in (("S", (cx, b["min"][1], zt + wall_h / 2), (w, wall_t, wall_h)),
                            ("N", (cx, b["max"][1], zt + wall_h / 2), (w, wall_t, wall_h)),
                            ("W", (b["min"][0], cy, zt + wall_h / 2), (wall_t, d, wall_h)),
                            ("E", (b["max"][0], cy, zt + wall_h / 2), (wall_t, d, wall_h))):
            box_actor("GB_Perimeter_%s" % name, c, sz, kind="Wall")
            count += 1

        # ---- roads ----
        road_count = 0
        for road in layout["roads"]:
            pts = [G.plan_to_world(level, q[0], q[1]) for q in road["points"]]
            for i in range(len(pts) - 1):
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                L = math.hypot(x1 - x0, y1 - y0)
                if L < 1:
                    continue
                yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
                box_actor("GB_Road_%s_%02d" % (road["name"], i), ((x0 + x1) / 2, (y0 + y1) / 2, zt + 2),
                          (L, road["width_cm"], 4), yaw,
                          kind="Road" if road["surface"] == "dirt" else "Apron")
                road_count += 1
        count += road_count

        # ---- structures: footprint box with real bounds & orientation ----
        placed, outside = 0, []
        native = level["mesh_native_front_yaw_deg"]
        player_pos = None
        for s in layout["structures"]:
            entry = assets["buildings"][s["asset"]]
            mesh = G.assert_asset_exists("%s/%s" % (entry["dest"], entry["main_mesh"]))
            size, origin = G.get_bounds(mesh)
            yaw = G.facing_to_yaw(layout, s["facing"], s["yaw_offset_deg"], native)
            ox, oy = rotate(origin.x, origin.y, yaw)
            wx, wy = G.plan_to_world(level, s["pos"][0], s["pos"][1])
            c = (wx + ox, wy + oy, zt + origin.z)
            box_actor("GB_%s" % s["label"], c, (size.x, size.y, size.z), yaw,
                      kind="Tower" if s["asset"] in ("WatchTower", "CommsTower") else "Building")
            text_label(s["label"], (wx, wy, zt + size.z + 300), 300.0)
            count += 2
            placed += 1
            # rotated axis-aligned extent of the footprint
            ca, sa = abs(math.cos(math.radians(yaw))), abs(math.sin(math.radians(yaw)))
            hx, hy = (size.x * ca + size.y * sa) / 2.0, (size.x * sa + size.y * ca) / 2.0
            if (c[0] - hx < b["min"][0] or c[0] + hx > b["max"][0] or
                    c[1] - hy < b["min"][1] or c[1] + hy > b["max"][1]):
                outside.append(s["label"])
            G.log("Greybox %s at (%.0f, %.0f) yaw=%.1f size %s" % (s["label"], s["pos"][0], s["pos"][1], yaw, G.fmt_size(size)))
            if s.get("player_start"):
                player_pos = (wx, wy, zt + 100.0, yaw)

        # ---- zone labels ----
        for z in layout["zones"]:
            if z["id"] == 10:
                continue
            zx, zy = G.plan_to_world(level, z["center"][0], z["center"][1])
            text_label("Z%02d %s" % (z["id"], z["name"]), (zx, zy, zt + 40), 200.0)
            count += 1

        # ---- scale reference cubes near the gate ----
        gx, gy = G.plan_to_world(level, *layout["structures"][0]["pos"])
        ref_person = box_actor("REF_Person_180cm", (gx + 1200, gy - 2500, zt + 90), (50, 50, 180), kind="Ref")
        ref_vehicle = box_actor("REF_Vehicle_800cm", (gx + 1700, gy - 2500, zt + 150), (800, 300, 300), kind="Ref")
        count += 2

        # ---- player start ----
        if player_pos is None:
            raise G.GenError("No structure flagged player_start in layout.json")
        ps = G.spawn_by_class(unreal.PlayerStart, player_pos[:3], (0, player_pos[3] + 0.0, 0), "PlayerStart_Thornfield", PHASE)
        count += 1

        G.log("Greybox spawned: %d actors" % count)
        top_down_camera(level)

        # ---- VERIFY ----
        gl = ground.get_actor_location()
        gs = ground.get_actor_scale3d()
        G.verify("footprint", abs(gs.x * 100 - w) < 1 and abs(gs.y * 100 - d) < 1 and abs(gl.z + 10 - zt) < 1,
                 "%.0f x %.0f cm" % (w, d))
        G.verify("structures_greybox", placed == len(layout["structures"]), "%d of %d" % (placed, len(layout["structures"])))
        G.verify("greybox_inside_bounds", not outside, "outside: %s" % outside if outside else "all inside")
        pl = ps.get_actor_location()
        G.verify("player_start", True, "at (%.0f, %.0f, %.0f)" % (pl.x, pl.y, pl.z))
        G.verify("scale_refs", ref_person is not None and ref_vehicle is not None, "180 cm person + 800 cm vehicle")
        G.verify("roads", road_count > 0, "%d segments" % road_count)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p02_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p02_unexpected", False, repr(e))
    G.summary()


main()
