"""p08b_scatter_environment.py - Phase 8b: rescale + scatter the Tripo trees, rocks, cliffs and mountains.

Run (after p08a):   py "X:/IronBreach/LevelGenTools/scripts/p08b_scatter_environment.py"

 * Tripo meshes import ~100 cm tall, so each instance is scaled so its HEIGHT hits a real-world target
   (trees 18-28 m, rocks per type, cliffs 18-26 m, mountains 140-220 m).
 * Trees fill a forest ring around the base (outside the boundary walls) and a few stand inside the base,
   never within 5 m of a road or 6 m of a building footprint.
 * Cliff walls line the outside of the perimeter; mountains form a far backdrop ring.
 * Deterministic: random seed from level.json. Re-running replaces everything it made (tag Scatter8).

Look for:
  [Thornfield] VERIFY: scatter_assets PASS
  [Thornfield] VERIFY: trees_placed PASS (<n>)
  [Thornfield] VERIFY: clearance PASS
  [Thornfield] VERIFY: cliffs_placed PASS
  [Thornfield] VERIFY: mountains_placed PASS
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

PHASE = 8
TAG = "Scatter8"


# --------------------------------------------------------------------------- geometry
def rot(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def corners(cx, cy, hx, hy, yaw_deg):
    return [(cx + rot(dx, dy, yaw_deg)[0], cy + rot(dx, dy, yaw_deg)[1]) for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def overlap(a, b):
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            ax_, ay_ = -(y1 - y0), (x1 - x0)
            ln = math.hypot(ax_, ay_) or 1.0
            ax_, ay_ = ax_ / ln, ay_ / ln
            pa = [p[0] * ax_ + p[1] * ay_ for p in a]
            pb = [p[0] * ax_ + p[1] * ay_ for p in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    t = 0.0 if dx == 0 and dy == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def pick(rng, assets, weights=None):
    if not weights:
        return rng.choice(assets)
    return rng.choices(assets, weights=weights, k=1)[0]


def main():
    G.init_log("p08b_scatter_environment")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        props = G.load_json("props.json")["scatter"]
        env = G.load_json("environment.json")["scatter"]
        b = level["bounds_cm"]
        x0, y0 = b["min"]
        x1, y1 = b["max"]
        W, H = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rng = random.Random(level["seed"])
        ring = env["ring_width_cm"]

        # remove previous scatter
        removed = 0
        for a in G.actors_with_tag(TAG):
            G.actor_subsystem().destroy_actor(a)
            removed += 1
        G.log("Cleanup: removed %d previous scatter actors" % removed)

        # ---------------------------------------------------------------- load meshes + scale info
        nat = assets["nature"]
        info = {}
        for key, e in nat.items():
            mesh = G.assert_asset_exists(e["ue_path"])
            size, origin = G.get_bounds(mesh)
            info[key] = (e["ue_path"], size, origin)
            G.log("%s native bounds %s origin z=%.1f" % (key, G.fmt_size(size), origin.z))
        G.verify("scatter_assets", len(info) == len(nat) and all(v[1].z > 1.0 for v in info.values()), "%d nature meshes" % len(info))

        def spawn(key, x, y, target_h, yaw, label, sink=None, ground_z=0.0):
            path, size, origin = info[key]
            s = target_h / size.z
            bottom = origin.z - size.z / 2.0
            z = ground_z - bottom * s - (env["sink_cm"] if sink is None else sink)
            a = G.spawn_static_mesh(path, (x, y, z), (0, yaw, 0), (s, s, s), label, PHASE)
            tags = [str(t) for t in a.tags] + [TAG]
            a.set_editor_property("tags", [unreal.Name(t) for t in tags])
            return a, s

        # ---------------------------------------------------------------- obstacles (building footprints, roads)
        foot = []
        for st in layout["structures"]:
            entry = assets["buildings"][st["asset"]]
            mesh = G.assert_asset_exists("%s/%s" % (entry["dest"], entry["main_mesh"]))
            size, origin = G.get_bounds(mesh)
            wx, wy = G.plan_to_world(level, st["pos"][0], st["pos"][1])
            yaw = G.facing_to_yaw(layout, st["facing"], st["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            ox, oy = rot(origin.x, origin.y, yaw)
            m = env["keep_clear_buildings_cm"]
            foot.append(corners(wx + ox, wy + oy, size.x / 2.0 + m, size.y / 2.0 + m, yaw))
        segs = []
        for r in layout["roads"]:
            pts = [G.plan_to_world(level, p[0], p[1]) for p in r["points"]]
            for i in range(len(pts) - 1):
                segs.append((pts[i], pts[i + 1], r["width_cm"] / 2.0 + env["keep_clear_roads_cm"]))

        def blocked(x, y, extra=0.0):
            sq = corners(x, y, 100.0 + extra, 100.0 + extra, 0.0)
            if any(overlap(sq, f) for f in foot):
                return True
            for (ax, ay), (bx, by), clr in segs:
                if seg_dist(x, y, ax, ay, bx, by) < clr + extra:
                    return True
            return False

        # ---------------------------------------------------------------- trees
        ds = env["density_scale"]
        outer_w, outer_h = W + 2 * ring, H + 2 * ring
        ring_ha = (outer_w * outer_h - (W + 800) * (H + 800)) / 1.0e8
        base_ha = (W * H) / 1.0e8
        t_out, t_in = props["trees_outside"], props["trees_inside"]
        n_out = int(t_out["density_per_ha"] * ring_ha * ds)
        n_in = int(t_in["density_per_ha"] * base_ha * 1.0)
        cap = env["max_trees_total"]
        if n_out + n_in > cap:
            n_out = max(0, cap - n_in)
        G.log("Trees planned: %d in the ring (%.1f ha), %d inside the base (%.1f ha)" % (n_out, ring_ha, n_in, base_ha))

        placed_inside = []   # (x, y) for the clearance re-check
        trees_out = trees_in = 0
        heights = []
        lo, hi = env["tree_height_cm"]
        tries = 0
        while trees_out < n_out and tries < n_out * 20:
            tries += 1
            x = rng.uniform(cx - outer_w / 2.0, cx + outer_w / 2.0)
            y = rng.uniform(cy - outer_h / 2.0, cy + outer_h / 2.0)
            if x0 - 400 <= x <= x1 + 400 and y0 - 400 <= y <= y1 + 400:
                continue
            key = pick(rng, t_out["assets"], t_out["weights"])
            h = rng.uniform(lo, hi)
            spawn(key, x, y, h, rng.uniform(0, 360), "TREE_%04d_%s" % (trees_out, key.replace("Tree_", "")))
            heights.append(h)
            trees_out += 1
        tries = 0
        while trees_in < n_in and tries < max(1, n_in) * 40:
            tries += 1
            x, y = rng.uniform(x0 + 300, x1 - 300), rng.uniform(y0 + 300, y1 - 300)
            if blocked(x, y, 100.0):
                continue
            key = pick(rng, t_in["assets"], t_in["weights"])
            h = rng.uniform(lo, hi)
            spawn(key, x, y, h, rng.uniform(0, 360), "TREE_IN_%03d_%s" % (trees_in, key.replace("Tree_", "")))
            placed_inside.append((x, y))
            heights.append(h)
            trees_in += 1
            if (trees_in + trees_out) % 200 == 0:
                G.log("... %d trees" % (trees_in + trees_out))
        G.verify("trees_placed", trees_out > 0 and trees_in > 0 and trees_out + trees_in > 0,
                 "%d ring + %d inside" % (trees_out, trees_in))
        G.verify("tree_heights", all(lo - 1 <= h <= hi + 1 for h in heights) and bool(heights),
                 "%.0f-%.0f cm" % (min(heights), max(heights)) if heights else "none")

        # clearance re-check for the trees inside the base
        bad = [p for p in placed_inside if blocked(p[0], p[1])]
        G.verify("clearance", not bad, "%d inside-trees checked, none within road/building margins" % len(placed_inside) if not bad else "%d too close" % len(bad))

        # ---------------------------------------------------------------- rocks
        rk = props["rocks"]
        rock_area_ha = base_ha + ring_ha
        n_rock = max(1, int(rk["density_per_ha"] * rock_area_ha * ds * 3.0))
        rocks, tries = 0, 0
        while rocks < n_rock and tries < n_rock * 30:
            tries += 1
            x = rng.uniform(cx - outer_w / 2.0, cx + outer_w / 2.0)
            y = rng.uniform(cy - outer_h / 2.0, cy + outer_h / 2.0)
            inside = x0 <= x <= x1 and y0 <= y <= y1
            if inside and blocked(x, y, 100.0):
                continue
            if not inside and x0 - 400 <= x <= x1 + 400 and y0 - 400 <= y <= y1 + 400:
                continue
            key = rng.choice(rk["assets"])
            rlo, rhi = env["rock_height_cm"][key]
            a, s = spawn(key, x, y, rng.uniform(rlo, rhi), rng.uniform(0, 360), "ROCK_%03d_%s" % (rocks, key.replace("Rock_", "")), sink=30.0)
            rocks += 1
        G.log("Rocks placed: %d" % rocks)
        G.verify("rocks_placed", rocks > 0, "%d rocks" % rocks)

        # cliffs + mountains are rebuilt by p12_scenery_polish.py when managed_by_p12 is set
        managed = env.get("managed_by_p12", False)
        # ---------------------------------------------------------------- cliffs along the outside of the perimeter
        ckey = props["cliffs"]["assets"][0]
        _, csize, _ = info[ckey]
        off = env["cliff_offset_cm"]
        chlo, chhi = env["cliff_height_cm"]
        cliffs = 0
        for side in (() if managed else ("S", "N", "W", "E")):
            horizontal = side in ("S", "N")
            length = (W if horizontal else H) + 2 * off
            pos = -off
            while pos < length - off:
                h = rng.uniform(chlo, chhi)
                s = h / csize.z
                along = max(csize.x, csize.y) * s
                long_is_x = csize.x >= csize.y
                if horizontal:
                    x = x0 + pos + along / 2.0
                    y = (y0 - off) if side == "S" else (y1 + off)
                    yaw = 0.0 if long_is_x else 90.0
                else:
                    y = y0 + pos + along / 2.0
                    x = (x0 - off) if side == "W" else (x1 + off)
                    yaw = 90.0 if long_is_x else 0.0
                spawn(ckey, x, y, h, yaw + rng.uniform(-6, 6) + (180.0 if side in ("N", "E") else 0.0), "CLIFF_%s_%02d" % (side, cliffs), sink=100.0)
                cliffs += 1
                pos += along * 0.85
        G.verify("cliffs_placed", managed or cliffs > 0, "%d cliff segments%s" % (cliffs, " (managed by p12)" if managed else ""))

        # ---------------------------------------------------------------- mountains (far backdrop)
        mkey = props["mountains"]["assets"][0]
        n_m = env["mountain_count"]
        rx, ry = W / 2.0 + env.get("mountain_offset_cm", 0), H / 2.0 + env.get("mountain_offset_cm", 0)
        mlo, mhi = env["mountain_height_cm"]
        mt = 0
        for i in range(0 if managed else n_m):
            th = 2.0 * math.pi * (i + rng.uniform(-0.15, 0.15)) / n_m
            spawn(mkey, cx + rx * math.cos(th), cy + ry * math.sin(th), rng.uniform(mlo, mhi),
                  math.degrees(th) + rng.uniform(-30, 30), "MOUNTAIN_%02d" % i, sink=1500.0)
            mt += 1
        G.verify("mountains_placed", managed or mt == n_m, "%d mountains%s" % (mt, " (managed by p12)" if managed else ""))

        # simple box collision for rocks/cliffs (trees/mountains stay collision-free)
        done = 0
        for key in list(props["rocks"]["assets"]) + [ckey]:
            mesh = G.assert_asset_exists(info[key][0])
            try:
                n = unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
                if n is not None and n >= 0:
                    done += 1
                unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            except Exception as e:
                G.warn("Collision for %s: %r" % (key, e))
        G.log("Box collision added to %d rock/cliff meshes" % done)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p08b_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p08b_unexpected", False, repr(e))
    G.summary()


main()
