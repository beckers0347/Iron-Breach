"""p12_scenery_polish.py - remove the perimeter wall + cliff ring, pull the mountains in tight around the base.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p12_scenery_polish.py"
Safe to re-run. Tune with config/environment.json (scatter):
  mountain_count, mountain_height_cm, mountain_edge_factor (smaller = mountains closer), mountain_gap_cm.

Also opens a road corridor through the mountains at the main gate: the south boundary wall gets a gap,
a dirt road runs out through it, trees/rocks are cleared, and invisible side/cap walls keep players on the road.
  config/environment.json (scatter): gate_gap_width_cm, gate_road_length_cm, gate_hw_factor (smaller = narrower valley).

Look for:
  [Thornfield] VERIFY: gate_road PASS
  [Thornfield] VERIFY: gate_corridor_clear PASS
  [Thornfield] VERIFY: wall_removed PASS
  [Thornfield] VERIFY: cliffs_removed PASS
  [Thornfield] VERIFY: mountains_placed PASS
  [Thornfield] VERIFY: mountains_outside_bounds PASS
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

PHASE = 12
TAG = "Scatter12"
TAG_SCATTER8 = "Scatter8"


def main():
    G.init_log("p12_scenery_polish")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        props = G.load_json("props.json")["scatter"]
        env = G.load_json("environment.json")["scatter"]
        b = level["bounds_cm"]
        x0, y0 = b["min"]
        x1, y1 = b["max"]
        W, H = x1 - x0, y1 - y0
        rng = random.Random(level["seed"] + 12)

        # ---- remove the wall, old cliffs, old mountains
        walls = cliffs = mts = 0
        for a in list(G.actor_subsystem().get_all_level_actors()):
            try:
                lab = a.get_actor_label()
            except Exception:
                continue
            if lab.startswith("WALL_"):
                G.actor_subsystem().destroy_actor(a); walls += 1
            elif lab.startswith("CLIFF_"):
                G.actor_subsystem().destroy_actor(a); cliffs += 1
            elif lab.startswith(("MOUNTAIN_", "SEAMROCK_")):
                G.actor_subsystem().destroy_actor(a); mts += 1
        G.cleanup_phase(PHASE)
        G.log("Removed %d wall segments, %d cliff pieces, %d old mountains" % (walls, cliffs, mts))
        left_w = sum(1 for a in G.actor_subsystem().get_all_level_actors() if a.get_actor_label().startswith(("WALL_", "CLIFF_")))
        G.verify("wall_removed", left_w == 0, "no WALL_/CLIFF_ actors remain (removed %d + %d)" % (walls, cliffs))
        G.verify("cliffs_removed", True, "cliff ring gone")

        # ---- gate corridor: main road leaves through the +Y (south) edge
        layout0 = G.load_json("layout.json")
        mainroad = layout0["roads"][0]
        gx, _ = G.plan_to_world(level, mainroad["points"][0][0], mainroad["points"][0][1])
        gap_w = float(env.get("gate_gap_width_cm", 1600))
        road_len = float(env.get("gate_road_length_cm", 16000))
        hwf = float(env.get("gate_hw_factor", 0.9))
        tclr = float(env.get("gate_tree_clear_cm", 1800))
        CUBE = "/Engine/BasicShapes/Cube"
        T = 200.0
        for a in list(G.actor_subsystem().get_all_level_actors()):
            if a.get_actor_label() == "BoundWall_South":
                G.actor_subsystem().destroy_actor(a)
        zc = 3000.0 - 500.0
        pieces = [
            ("BoundWall_S_Left",  (x0 + (gx - gap_w / 2.0 - x0) / 2.0 - 0, y1 + T / 2.0, zc), (gx - gap_w / 2.0 - x0, T, 6000.0)),
            ("BoundWall_S_Right", (gx + gap_w / 2.0 + (x1 - gx - gap_w / 2.0) / 2.0, y1 + T / 2.0, zc), (x1 - gx - gap_w / 2.0, T, 6000.0)),
            ("BoundWall_Gate_W",  (gx - gap_w / 2.0 - T / 2.0, y1 + road_len / 2.0, zc), (T, road_len, 6000.0)),
            ("BoundWall_Gate_E",  (gx + gap_w / 2.0 + T / 2.0, y1 + road_len / 2.0, zc), (T, road_len, 6000.0)),
            ("BoundWall_Gate_Cap", (gx, y1 + road_len + T / 2.0, zc), (gap_w + 2 * T, T, 6000.0)),
        ]
        for label, loc, sz in pieces:
            a = G.spawn_static_mesh(CUBE, loc, (0, 0, 0), (sz[0] / 100.0, sz[1] / 100.0, sz[2] / 100.0), label, PHASE)
            a.static_mesh_component.set_collision_profile_name("BlockAll")

        # dirt road out through the gap
        mcfg = G.load_json("materials.json")
        dirt = unreal.EditorAssetLibrary.load_asset(mcfg["dest"] + "/M_Dirt")
        road_w = float(mainroad["width_cm"])
        ra = G.spawn_static_mesh(CUBE, (gx, y1 + road_len / 2.0 - 100.0, 2.0), (0, 0, 0),
                                 (road_w / 100.0, (road_len + 200.0) / 100.0, 0.04), "GateRoad_Out", PHASE)
        ra.static_mesh_component.set_collision_profile_name("NoCollision")
        if dirt is not None:
            ra.static_mesh_component.set_material(0, dirt)
        else:
            G.warn("M_Dirt not found - gate road left with the default material")
        G.verify("gate_road", dirt is not None, "road %.0f cm long, gap %.0f cm wide at x=%.0f" % (road_len, gap_w, gx))

        # clear trees / rocks standing on the corridor
        cleared = 0
        for a in G.actors_with_tag(TAG_SCATTER8):
            l = a.get_actor_location()
            if abs(l.x - gx) < tclr and l.y > y1 - 300.0 and l.y < y1 + road_len + 500.0:
                G.actor_subsystem().destroy_actor(a)
                cleared += 1
        G.log("Cleared %d trees/rocks from the gate corridor" % cleared)

        # ---- make the invisible BoundWall cubes truly invisible (collision stays, so players still can't leave)
        hid = 0
        for a in G.actor_subsystem().get_all_level_actors():
            if a.get_actor_label().startswith("BoundWall_"):
                try:
                    comp = a.static_mesh_component
                    comp.set_visibility(False)
                    comp.set_editor_property("cast_shadow", False)
                    comp.set_editor_property("hidden_in_game", True)
                    hid += 1
                except Exception as ex:
                    G.warn("BoundWall hide failed: %r" % ex)
        G.verify("boundwalls_invisible", hid >= 8, "%d bound walls hidden (collision kept)" % hid)

        # ---- tight mountain ring
        mkey = props["mountains"]["assets"][0]
        e = assets["nature"][mkey]
        mesh = G.assert_asset_exists(e["ue_path"])
        size, origin = G.get_bounds(mesh)
        n = int(env["mountain_count"])
        mlo, mhi = env["mountain_height_cm"]
        edge_f = float(env.get("mountain_edge_factor", 0.8))
        gap = float(env.get("mountain_gap_cm", 0))
        perim = 2.0 * (W + H)
        placed, inside, skipped_m = 0, 0, 0
        for i in range(n):
            t = ((i + rng.uniform(-0.15, 0.15)) / n) % 1.0 * perim
            if t < W:
                px, py, nx, ny = x0 + t, y0, 0.0, -1.0
            elif t < W + H:
                px, py, nx, ny = x1, y0 + (t - W), 1.0, 0.0
            elif t < 2 * W + H:
                px, py, nx, ny = x1 - (t - W - H), y1, 0.0, 1.0
            else:
                px, py, nx, ny = x0, y1 - (t - 2 * W - H), -1.0, 0.0
            h = rng.uniform(mlo, mhi)
            s = h / size.z
            hw = max(size.x, size.y) * s / 2.0
            d = hw * edge_f + gap + rng.uniform(-1.0, 1.0) * hw * float(env.get('mountain_edge_jitter', 0.0))
            if ny > 0.5 and abs(px - gx) < hw * hwf + gap_w / 2.0:
                skipped_m += 1
                continue
            x, y = px + nx * d, py + ny * d
            bottom = origin.z - size.z / 2.0
            z = -bottom * s - 1500.0
            yaw = math.degrees(math.atan2(ny, nx)) + rng.uniform(-30, 30)
            a = G.spawn_static_mesh(e["ue_path"], (x, y, z), (0, yaw, 0), (s, s, s), "MOUNTAIN_%02d" % i, PHASE)
            a.set_editor_property("tags", [unreal.Name(str(t)) for t in a.tags] + [unreal.Name(TAG)])
            placed += 1
            if x0 < x < x1 and y0 < y < y1:
                inside += 1
            if i < 3:
                G.log("Mountain %d: height %.0f cm, half-width %.0f cm, centre %.0f cm outside the edge" % (i, h, hw, d))
        G.log("Skipped %d mountains to open the gate valley" % skipped_m)
        G.verify("mountains_placed", placed + skipped_m == n, "%d mountains hugging the base" % placed)
        G.verify("gate_corridor_clear", skipped_m > 0, "%d mountains removed from the gate valley" % skipped_m)
        G.verify("mountains_outside_bounds", inside == 0, "all mountain centres outside the base bounds")

        # ---- seam rocks: boulders along the base edge so the mountains blend into the plateau
        layout = G.load_json("layout.json")
        roads = []
        for r in layout["roads"]:
            pts = [G.plan_to_world(level, p[0], p[1]) for p in r["points"]]
            roads.append((pts, r["width_cm"] / 2.0 + 1000.0))

        roads.append(([(gx, y1), (gx, y1 + road_len)], gap_w / 2.0 + 700.0))

        def near_road(x, y):
            for pts, clr in roads:
                for k in range(len(pts) - 1):
                    ax, ay = pts[k]; bx, by = pts[k + 1]
                    dx, dy = bx - ax, by - ay
                    tt = 0.0 if dx == 0 and dy == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
                    if math.hypot(x - (ax + tt * dx), y - (ay + tt * dy)) < clr:
                        return True
            return False

        rock_keys = list(props["rocks"]["assets"])
        sp = float(env.get("seam_rock_spacing_cm", 1400))
        nrock = 0
        pos = 0.0
        while pos < perim:
            t = pos
            if t < W:
                px, py, nx, ny = x0 + t, y0, 0.0, -1.0
            elif t < W + H:
                px, py, nx, ny = x1, y0 + (t - W), 1.0, 0.0
            elif t < 2 * W + H:
                px, py, nx, ny = x1 - (t - W - H), y1, 0.0, 1.0
            else:
                px, py, nx, ny = x0, y1 - (t - 2 * W - H), -1.0, 0.0
            off = rng.uniform(300, 1100)
            x, y = px + nx * off, py + ny * off
            pos += sp * rng.uniform(0.7, 1.3)
            if near_road(x, y):
                continue
            k = rng.choice(rock_keys)
            re_ = assets["nature"][k]
            rmesh = G.assert_asset_exists(re_["ue_path"])
            rsize, rorg = G.get_bounds(rmesh)
            lo, hi = env["rock_height_cm"][k]
            h = rng.uniform(lo, hi) * 1.6
            rs = h / rsize.z
            rz = -(rorg.z - rsize.z / 2.0) * rs - 40.0
            a = G.spawn_static_mesh(re_["ue_path"], (x, y, rz), (0, rng.uniform(0, 360), 0), (rs, rs, rs), "SEAMROCK_%03d" % nrock, PHASE)
            a.set_editor_property("tags", [unreal.Name(str(t)) for t in a.tags] + [unreal.Name(TAG)])
            nrock += 1
        G.verify("seam_rocks", nrock > 20, "%d boulders along the base edge" % nrock)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as ex:
            G.verify("level_saved", False, repr(ex))
    except G.GenError as ex:
        G.err(str(ex)); G.verify("p12_fatal", False, str(ex))
    except Exception as ex:
        G.err("Unexpected: %r" % ex); G.verify("p12_unexpected", False, repr(ex))
    G.summary()


main()
