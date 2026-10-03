"""p17b_scatter_grass.py - lay real grass patches over the open ground (not on buildings, roads or pads).

Run (after p17a and p16):   py "X:/IronBreach/LevelGenTools/scripts/p17b_scatter_grass.py"
Safe to re-run (tag GEN_Phase17). Tunables: config/environment.json -> scatter.grass

Look for:
  [Thornfield] VERIFY: grass_placed PASS
  [Thornfield] VERIFY: grass_clear_of_roads PASS
"""
import os
import sys
import math
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 17


def rot(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def rect_dist(px, py, cx, cy, hx, hy, yaw):
    lx, ly = rot(px - cx, py - cy, -yaw)
    return math.hypot(max(abs(lx) - hx, 0.0), max(abs(ly) - hy, 0.0))


def main():
    G.init_log("p17b_scatter_grass")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        env = G.load_json("environment.json")["scatter"]
        cfg = env["grass"]
        g = assets["grass"]
        b = level["bounds_cm"]
        x0, y0 = b["min"]
        x1, y1 = b["max"]
        rng = random.Random(level["seed"] + 17)
        G.cleanup_phase(PHASE)

        paths = ["%s/SM_GrassPatch_%d" % (g["dest"], i) for i in range(int(g["variants"]))]
        for p in paths:
            G.assert_asset_exists(p)

        # ---- obstacles
        foot = []
        for st in layout["structures"]:
            e = assets["buildings"][st["asset"]]
            mesh = G.assert_asset_exists("%s/%s" % (e["dest"], e["main_mesh"]))
            size, origin = G.get_bounds(mesh)
            wx, wy = G.plan_to_world(level, st["pos"][0], st["pos"][1])
            yaw = G.facing_to_yaw(layout, st["facing"], st["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            ox, oy = rot(origin.x, origin.y, yaw)
            foot.append((wx + ox, wy + oy, size.x / 2.0, size.y / 2.0, yaw))
        main_pts, spur_pts, pad_pts = [], [], []
        for a in G.actor_subsystem().get_all_level_actors():
            lab = a.get_actor_label()
            if lab.startswith(("ROAD_Main_", "ROAD_Out_")) and "_SH_" not in lab and "Rut" not in lab:
                l = a.get_actor_location(); main_pts.append((l.x, l.y))
            elif lab.startswith("ROAD_Spur_") and "_SH_" not in lab:
                l = a.get_actor_location(); spur_pts.append((l.x, l.y))
            elif lab.startswith("PAD_"):
                l = a.get_actor_location(); pad_pts.append((l.x, l.y))
        G.log("Obstacles: %d buildings, %d main-road pieces, %d spur pieces, %d pads" % (len(foot), len(main_pts), len(spur_pts), len(pad_pts)))
        if not main_pts:
            G.warn("No ROAD_ pieces found - run p16_dirt_roads.py first or grass will cover the roads")

        # spatial hash for road points
        H = 1000.0
        grid = {}

        def add(pts, kind):
            for (x, y) in pts:
                grid.setdefault((int(x // H), int(y // H)), []).append((x, y, kind))
        add(main_pts, cfg["keep_clear_main_cm"])
        add(spur_pts, cfg["keep_clear_spur_cm"])
        add(pad_pts, cfg["keep_clear_pad_cm"])

        def blocked(x, y):
            for cx, cy, hx, hy, yaw in foot:
                if rect_dist(x, y, cx, cy, hx, hy, yaw) < cfg["keep_clear_building_cm"]:
                    return True
            gx_, gy_ = int(x // H), int(y // H)
            for i in range(gx_ - 1, gx_ + 2):
                for j in range(gy_ - 1, gy_ + 2):
                    for px, py, r in grid.get((i, j), ()):
                        if math.hypot(x - px, y - py) < r:
                            return True
            return False

        # gate corridor region
        gx = layout["roads"][0]["points"][0][0]
        road_len = float(env.get("gate_road_length_cm", 16000))
        corridor = (gx - 4000.0, gx + 4000.0, y1, y1 + road_len)

        cell = float(cfg["cell_cm"])
        slo, shi = cfg["scale_range"]
        placed, tries = 0, 0
        cx_ = x0 + cell / 2.0
        regions = [(x0, x1, y0, y1), corridor]
        for (ax0, ax1, ay0, ay1) in regions:
            ix = 0
            while ax0 + (ix + 0.5) * cell < ax1:
                iy = 0
                while ay0 + (iy + 0.5) * cell < ay1:
                    x, y = ax0 + (ix + 0.5) * cell, ay0 + (iy + 0.5) * cell
                    iy += 1
                    tries += 1
                    if placed >= int(cfg["max_patches"]) or rng.random() < cfg["skip_prob"]:
                        continue
                    ok = True
                    for dx in (-0.5, 0.0, 0.5):
                        for dy in (-0.5, 0.0, 0.5):
                            if blocked(x + dx * cell, y + dy * cell):
                                ok = False
                                break
                        if not ok:
                            break
                    if not ok:
                        continue
                    s = rng.uniform(slo, shi)
                    a = G.spawn_static_mesh(rng.choice(paths), (x, y, 0.0), (0, rng.choice((0, 90, 180, 270)), 0), (s, s, 1.0), "GRASS_%04d" % placed, PHASE)
                    c = a.static_mesh_component
                    c.set_collision_profile_name("NoCollision")
                    try:
                        c.set_editor_property("cast_shadow", False)
                    except Exception:
                        pass
                    placed += 1
                ix += 1
        G.log("Grass patches: %d placed from %d cells" % (placed, tries))
        G.verify("grass_placed", placed > 300, "%d patches of real grass" % placed)

        bad = 0
        for a in G.actors_with_tag("GEN_Phase17"):
            l = a.get_actor_location()
            for px, py in main_pts:
                if abs(l.x - px) < 300 and abs(l.y - py) < 300:
                    bad += 1
                    break
        G.verify("grass_clear_of_roads", bad == 0, "no patch centred on a road" if bad == 0 else "%d patches on roads" % bad)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e)); G.verify("p17b_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e); G.verify("p17b_unexpected", False, repr(e))
    G.summary()


main()
