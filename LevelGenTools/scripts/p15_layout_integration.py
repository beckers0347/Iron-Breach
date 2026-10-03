"""p15_layout_integration.py - make the base read like the reference photo: forest packed between the buildings,
earth berms behind the bunkers, and short wall runs only at the gate and the hangar side.

Run (after p12/p13):   py "X:/IronBreach/LevelGenTools/scripts/p15_layout_integration.py"
Safe to re-run (everything is tagged GEN_Phase15). Tunables: config/environment.json -> scatter.integration

Look for:
  [Thornfield] VERIFY: fill_forest PASS
  [Thornfield] VERIFY: berm_mounds PASS
  [Thornfield] VERIFY: wall_runs PASS
  [Thornfield] VERIFY: nothing_on_roads PASS
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

PHASE = 15


def rot(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    t = 0.0 if dx == 0 and dy == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def rect_dist(px, py, cx, cy, hx, hy, yaw):
    lx, ly = rot(px - cx, py - cy, -yaw)
    return math.hypot(max(abs(lx) - hx, 0.0), max(abs(ly) - hy, 0.0))


def noise(x, y):
    return (math.sin(x / 3100.0 + 1.3) + math.sin(y / 2700.0 + 0.7) + math.sin((x + y) / 2300.0) + math.sin((x - y) / 1900.0 + 2.0)) / 4.0


def main():
    G.init_log("p15_layout_integration")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        env = G.load_json("environment.json")["scatter"]
        cfg = env["integration"]
        b = level["bounds_cm"]
        x0, y0 = b["min"]
        x1, y1 = b["max"]
        rng = random.Random(level["seed"] + 15)
        G.cleanup_phase(PHASE)

        # ---------------------------------------------------------------- obstacles
        foot, berm_targets = [], []
        for st in layout["structures"]:
            e = assets["buildings"][st["asset"]]
            mesh = G.assert_asset_exists("%s/%s" % (e["dest"], e["main_mesh"]))
            size, origin = G.get_bounds(mesh)
            wx, wy = G.plan_to_world(level, st["pos"][0], st["pos"][1])
            yaw = G.facing_to_yaw(layout, st["facing"], st["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            ox, oy = rot(origin.x, origin.y, yaw)
            cx, cy = wx + ox, wy + oy
            foot.append((cx, cy, size.x / 2.0, size.y / 2.0, yaw))
            if st["asset"] == "BermBunker":
                vx, vy = layout["facing_vectors"][st["facing"]]
                fang = math.degrees(math.atan2(vy, vx)) + st["yaw_offset_deg"]
                fdx, fdy = math.cos(math.radians(fang)), math.sin(math.radians(fang))
                depth = abs(size.x * abs(fdx) + size.y * abs(fdy))
                width = abs(size.x * abs(fdy) + size.y * abs(fdx))
                berm_targets.append((st["label"], cx, cy, fdx, fdy, depth, width))
        roads = []
        for r in layout["roads"]:
            pts = [G.plan_to_world(level, p[0], p[1]) for p in r["points"]]
            roads.append((pts, r["width_cm"] / 2.0))
        # gate road leaving the base
        gx = roads[0][0][0][0]
        roads.append(([(gx, y1), (gx, y1 + 16000)], roads[0][1]))
        entries = [(a.get_actor_location().x, a.get_actor_location().y) for a in G.actors_with_tag("Entrance")]

        def road_d(x, y):
            return min(seg_dist(x, y, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) - half
                       for pts, half in roads for i in range(len(pts) - 1))

        def clear(x, y, extra_b=0.0):
            for cx, cy, hx, hy, yaw in foot:
                if rect_dist(x, y, cx, cy, hx, hy, yaw) < cfg["keep_clear_building_cm"] + extra_b:
                    return False
            if road_d(x, y) < cfg["keep_clear_road_extra_cm"] + extra_b:
                return False
            for ex, ey in entries:
                if math.hypot(x - ex, y - ey) < cfg["keep_clear_entry_cm"]:
                    return False
            return True

        # ---------------------------------------------------------------- 1. forest packed into the base
        nat = assets["nature"]
        tkeys = [k for k in nat if k.startswith("Tree_") and "Snag" not in k]
        snag = [k for k in nat if "Snag" in k]
        info = {}
        for k in tkeys + snag:
            m = G.assert_asset_exists(nat[k]["ue_path"])
            size, origin = G.get_bounds(m)
            info[k] = (nat[k]["ue_path"], size, origin)
        step, edge = cfg["fill_step_cm"], cfg["edge_forest_cm"]
        planted, cap = 0, int(cfg["fill_trees_max"])
        cand = []
        gxs = int((x1 - x0) / step)
        gys = int((y1 - y0) / step)
        for i in range(gxs + 1):
            for j in range(gys + 1):
                x = x0 + i * step + rng.uniform(-step * 0.45, step * 0.45)
                y = y0 + j * step + rng.uniform(-step * 0.45, step * 0.45)
                if not (x0 + 200 < x < x1 - 200 and y0 + 200 < y < y1 - 200):
                    continue
                d_edge = min(x - x0, x1 - x, y - y0, y1 - y)
                f = noise(x, y)
                if d_edge < edge:
                    ok = True
                else:
                    ok = f > -0.10 or rng.random() < 0.03
                if ok and clear(x, y):
                    cand.append((f + (1.0 if d_edge < edge else 0.0), x, y))
        # forest flanking the gate road outside the base
        gap_w = float(env.get("gate_gap_width_cm", 1600))
        road_len = float(env.get("gate_road_length_cm", 16000))
        flank = float(cfg.get("corridor_flank_cm", 6000))
        ccand = []
        for i in range(int(2 * flank / step) + 1):
            for j in range(int((road_len + 4000.0) / step) + 1):
                x = gx - flank + i * step + rng.uniform(-step * 0.45, step * 0.45)
                y = y1 + 200.0 + j * step + rng.uniform(-step * 0.45, step * 0.45)
                if abs(x - gx) < gap_w / 2.0 + 500.0:
                    continue
                if y > y1 + road_len + 2000.0:
                    continue
                if rng.random() < 0.75 and noise(x, y) > -0.35 and clear(x, y):
                    ccand.append((x, y))
        rng.shuffle(ccand)
        cand_corr = ccand[:int(cfg.get("corridor_trees", 260))]
        rng.shuffle(cand)
        G.log("Forest candidates: %d (cap %d)" % (len(cand), cap))
        for _, x, y in cand[:cap]:
            k = rng.choice(snag) if (snag and rng.random() < 0.03) else rng.choice(tkeys)
            path, size, origin = info[k]
            h = rng.uniform(1800, 2800)
            s = h / size.z
            z = -(origin.z - size.z / 2.0) * s - 20.0
            G.spawn_static_mesh(path, (x, y, z), (0, rng.uniform(0, 360), 0), (s, s, s), "FILLTREE_%04d" % planted, PHASE)
            planted += 1
        for x, y in cand_corr:
            k = rng.choice(tkeys)
            path, size, origin = info[k]
            h = rng.uniform(1800, 2800)
            s = h / size.z
            z = -(origin.z - size.z / 2.0) * s - 20.0
            G.spawn_static_mesh(path, (x, y, z), (0, rng.uniform(0, 360), 0), (s, s, s), "FILLTREE_C%04d" % planted, PHASE)
            planted += 1
        G.verify("fill_forest", planted >= 150, "%d trees packed between the buildings" % planted)
        bad = 0
        for a in G.actors_with_tag("GEN_Phase15"):
            if a.get_actor_label().startswith("FILLTREE_"):
                l = a.get_actor_location()
                if road_d(l.x, l.y) < 150:
                    bad += 1
        G.verify("nothing_on_roads", bad == 0, "no fill trees within 150 cm of a road edge" if bad == 0 else "%d trees on roads" % bad)

        # ---------------------------------------------------------------- 2. berm mounds behind the bunkers
        mkey = next(k for k in nat if k.startswith("Mountain_"))
        mmesh = G.assert_asset_exists(nat[mkey]["ue_path"])
        msize, morg = G.get_bounds(mmesh)
        mounds = 0
        for label, cx, cy, fdx, fdy, depth, width in berm_targets:
            h = rng.uniform(*cfg["mound_height_cm"])
            wtarget = width * cfg["mound_width_factor"]
            sxy = wtarget / max(msize.x, msize.y)
            sz = h / msize.z
            hw = max(msize.x, msize.y) * sxy / 2.0
            mx, my = cx - fdx * (depth / 2.0 + hw * 0.45), cy - fdy * (depth / 2.0 + hw * 0.45)
            z = -(morg.z - msize.z / 2.0) * sz - 250.0
            a = G.spawn_static_mesh(nat[mkey]["ue_path"], (mx, my, z), (0, math.degrees(math.atan2(fdy, fdx)) + rng.uniform(-15, 15), 0),
                                    (sxy, sxy, sz), "BERM_%s" % label, PHASE)
            mounds += 1
        G.verify("berm_mounds", mounds == len(berm_targets) and mounds > 0, "%d earth berms behind the bunkers" % mounds)

        # ---------------------------------------------------------------- 3. short wall runs: gate flanks + hangar side
        wpath = assets["props"]["PerimeterWall"]["ue_path"]
        G.assert_asset_exists(wpath)
        gap = float(env.get("gate_gap_width_cm", 1600)) / 2.0 + 300.0
        flank = float(cfg["wall_flank_cm"])
        seg = 400.0
        walls = 0
        pos = gap
        while pos < flank:
            for sgn in (-1, 1):
                G.spawn_static_mesh(wpath, (gx + sgn * pos, y1 - 150.0, 0.0), (0, 0, 0), (1, 1, 1), "WALLRUN_G_%03d" % walls, PHASE)
                walls += 1
            pos += seg
        hang = next((f for f in zip(layout["structures"], foot) if "Hangar" in f[0]["asset"]), None)
        if hang is not None:
            hy = hang[1][1]
            half = float(cfg["wall_east_half_cm"])
            yy = max(y0 + 500.0, hy - half)
            while yy < min(y1 - 500.0, hy + half):
                if road_d(x1 - 150.0, yy) > 400.0:
                    G.spawn_static_mesh(wpath, (x1 - 150.0, yy, 0.0), (0, 90, 0), (1, 1, 1), "WALLRUN_E_%03d" % walls, PHASE)
                    walls += 1
                yy += seg
        G.verify("wall_runs", walls > 20, "%d wall segments (gate flanks + hangar side only)" % walls)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e)); G.verify("p15_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e); G.verify("p15_unexpected", False, repr(e))
    G.summary()


main()
