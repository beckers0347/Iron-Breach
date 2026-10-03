"""p09b_dress_props.py - Phase 9: place the prop kit (perimeter wall, light poles, barriers, containers, crates ...).

Run (after p09a):   py "X:/IronBreach/LevelGenTools/scripts/p09b_dress_props.py"

 * Perimeter wall segments around the whole base (gap where the road leaves). The red greybox markers are removed.
 * Light poles along the roads (alternating sides) with a warm point light on each.
 * Jersey-barrier chicane + tank traps just inside the gate.
 * Containers (some stacked), fuel tanks, generators, crates, pallets sampled per zone (config/props_layout.json).
 * A sign, and a crate/pallet cluster, beside every building entrance marker.
Nothing is placed within the clearance margins of roads or building footprints. Re-running replaces all Phase 9 actors.

Look for:
  [Thornfield] VERIFY: wall_placed PASS
  [Thornfield] VERIFY: poles_placed PASS
  [Thornfield] VERIFY: gate_dressing PASS
  [Thornfield] VERIFY: zone_props PASS
  [Thornfield] VERIFY: entrance_props PASS
  [Thornfield] VERIFY: prop_clearance PASS
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

PHASE = 9
NATIVE = 90.0     # prop front (-Y in Blender) -> UE yaw offset, same convention as the buildings


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


def main():
    G.init_log("p09b_dress_props")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        pl = G.load_json("props_layout.json")
        b = level["bounds_cm"]
        x0, y0 = b["min"]
        x1, y1 = b["max"]
        rng = random.Random(level["seed"] + 9)

        G.cleanup_phase(PHASE)
        # replace the red greybox perimeter markers with the real wall
        gone = 0
        for a in G.actors_with_tag("GEN_Phase2"):
            if a.get_actor_label().startswith("GB_Perimeter_"):
                G.actor_subsystem().destroy_actor(a)
                gone += 1
        G.log("Removed %d greybox perimeter markers" % gone)

        P = {k: v["ue_path"] for k, v in assets["props"].items()}
        for k, path in P.items():
            G.assert_asset_exists(path)

        # ---------------------------------------------------------------- obstacles
        foot = []
        for st in layout["structures"]:
            e = assets["buildings"][st["asset"]]
            mesh = G.assert_asset_exists("%s/%s" % (e["dest"], e["main_mesh"]))
            size, origin = G.get_bounds(mesh)
            wx, wy = G.plan_to_world(level, st["pos"][0], st["pos"][1])
            yaw = G.facing_to_yaw(layout, st["facing"], st["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            ox, oy = rot(origin.x, origin.y, yaw)
            foot.append((st["label"], wx + ox, wy + oy, size.x / 2.0, size.y / 2.0, yaw))
        roads = []
        for r in layout["roads"]:
            pts = [G.plan_to_world(level, p[0], p[1]) for p in r["points"]]
            roads.append((r["name"], pts, r["width_cm"] / 2.0))

        def near_building(x, y, radius, margin):
            sq = corners(x, y, radius, radius, 0.0)
            for _, fx, fy, hx, hy, yaw in foot:
                if overlap(sq, corners(fx, fy, hx + margin, hy + margin, yaw)):
                    return True
            return False

        def near_road(x, y, radius, margin):
            for _, pts, half in roads:
                for i in range(len(pts) - 1):
                    if seg_dist(x, y, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) < half + margin + radius:
                        return True
            return False

        def spawn(key, x, y, yaw, label, z=0.0):
            return G.spawn_static_mesh(P[key], (x, y, z), (0, yaw, 0), (1, 1, 1), label, PHASE)

        placed_pts = []      # (x, y, radius) of dressing props for the gap rule + re-check

        # ---------------------------------------------------------------- perimeter wall
        pw = pl["perimeter"]
        inset, seg = pw["inset_cm"], pw["segment_cm"]
        walls, skipped = 0, 0
        wall_on = pw.get("enabled", True)
        edges = [("S", y0 + inset, 0.0, True), ("N", y1 - inset, 0.0, True), ("W", x0 + inset, 90.0, False), ("E", x1 - inset, 90.0, False)]
        for name, fixed, yaw, horizontal in (edges if wall_on else []):
            lo, hi = (x0, x1) if horizontal else (y0, y1)
            pos = lo + seg / 2.0
            i = 0
            while pos < hi:
                x, y = (pos, fixed) if horizontal else (fixed, pos)
                if any(seg_dist(x, y, pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1]) < half + pw["road_gap_cm"]
                       for _, pts, half in roads for j in range(len(pts) - 1)):
                    skipped += 1
                else:
                    spawn("PerimeterWall", x, y, yaw, "WALL_%s_%03d" % (name, i))
                    walls += 1
                pos += seg
                i += 1
        G.log("Perimeter wall: %d segments, %d skipped for road gaps" % (walls, skipped))
        if wall_on:
            G.verify("wall_placed", walls > 150 and skipped >= 1, "%d segments, %d road gaps" % (walls, skipped))
        else:
            G.verify("wall_placed", walls == 0, "perimeter wall disabled in props_layout.json (open base)")

        # ---------------------------------------------------------------- light poles
        lp = pl["light_poles"]
        poles, side, since = 0, 1, 0.0
        for rname, pts, half in roads:
            if "Apron" in rname:
                continue
            carry = lp["spacing_cm"]
            for i in range(len(pts) - 1):
                ax, ay = pts[i]
                bx, by = pts[i + 1]
                L = math.hypot(bx - ax, by - ay)
                if L < 1:
                    continue
                dx, dy = (bx - ax) / L, (by - ay) / L
                nx, ny = -dy, dx
                d = carry
                while d < L and poles < lp["max"]:
                    px, py = ax + dx * d, ay + dy * d
                    qx, qy = px + nx * side * (half + lp["side_offset_cm"]), py + ny * side * (half + lp["side_offset_cm"])
                    side = -side
                    d += lp["spacing_cm"]
                    if near_building(qx, qy, 40.0, 300.0) or not (x0 + 400 < qx < x1 - 400 and y0 + 400 < qy < y1 - 400):
                        continue
                    yaw = math.degrees(math.atan2(-ny * -side, -nx * -side))   # arm reaches toward the road
                    spawn("LightPole", qx, qy, yaw, "POLE_%03d" % poles)
                    lx, ly = rot(145.0, 0.0, yaw)
                    lt = G.spawn_by_class(unreal.PointLight, (qx + lx, qy + ly, 680.0), (0, 0, 0), "POLELIGHT_%03d" % poles, PHASE)
                    c = lt.get_component_by_class(unreal.PointLightComponent)
                    for prop, val in (("intensity_units", unreal.LightUnits.CANDELAS), ("intensity", float(lp["light_cd"])),
                                      ("light_color", unreal.Color(r=255, g=225, b=180, a=255)),
                                      ("attenuation_radius", float(lp["attenuation_cm"])), ("cast_shadows", False)):
                        try:
                            c.set_editor_property(prop, val)
                        except Exception as e:
                            G.warn("pole light %s: %r" % (prop, e))
                    placed_pts.append((qx, qy, 40.0))
                    poles += 1
                carry = d - L
        G.verify("poles_placed", poles > 0, "%d light poles (cap %d)" % (poles, lp["max"]))

        # ---------------------------------------------------------------- gate chicane + tank traps (inside the base)
        gate = next(s for s in layout["structures"] if s["label"] == "Gate")
        gx, gy = G.plan_to_world(level, gate["pos"][0], gate["pos"][1])
        fx, fy = layout["facing_vectors"][gate["facing"]]
        ix, iy = -fx, -fy                       # into the base
        px_, py_ = -iy, ix                      # sideways
        gc = pl["gate_chicane"]
        n_jb = 0
        for row in range(gc["barrier_rows"]):
            dist = 1000.0 + gc["first_distance_cm"] + row * gc["row_gap_cm"]
            off = gc["stagger_cm"] * (1 if row % 2 == 0 else -1)
            x, y = gx + ix * dist + px_ * off, gy + iy * dist + py_ * off
            yaw = math.degrees(math.atan2(py_, px_))          # barrier long axis across the road
            spawn("JerseyBarrier", x, y, yaw, "JB_%d" % row)
            placed_pts.append((x, y, 160.0))
            n_jb += 1
        n_tt = 0
        tt = pl["tank_traps_outside_gate"]
        for i in range(tt["count"]):
            sgn = 1 if i % 2 == 0 else -1
            off = sgn * (1500.0 + (i // 2) * tt["spacing_cm"])
            x, y = gx + ix * (1000.0 + 2000.0) + px_ * off, gy + iy * (1000.0 + 2000.0) + py_ * off
            if near_building(x, y, 60.0, 100.0):
                continue
            spawn("TankTrap", x, y, rng.uniform(0, 360), "TT_%d" % i)
            placed_pts.append((x, y, 60.0))
            n_tt += 1
        G.verify("gate_dressing", n_jb == gc["barrier_rows"] and n_tt >= 3, "%d barriers, %d tank traps" % (n_jb, n_tt))

        # ---------------------------------------------------------------- zone props
        rad = pl["radius_cm"]
        want_total, got_total = 0, 0
        zones = {z["id"]: z for z in layout["zones"]}
        zone_sizes = {}
        for zid_s, counts in pl["random"].items():
            z = zones[int(zid_s)]
            zx, zy = G.plan_to_world(level, z["center"][0], z["center"][1])
            hx, hy = z["size"][0] / 2.0 + pl["zone_margin_cm"], z["size"][1] / 2.0 + pl["zone_margin_cm"]
            # the zone boxes hug the buildings, so sample a wider yard around them (zone_margin_cm)
            for key, n in counts.items():
                r = rad[key]
                got = 0
                for _ in range(n):
                    want_total += 1
                    for _try in range(120):
                        x, y = rng.uniform(zx - hx, zx + hx), rng.uniform(zy - hy, zy + hy)
                        if not (x0 + 600 < x < x1 - 600 and y0 + 600 < y < y1 - 600):
                            continue
                        if near_building(x, y, r, pl["keep_clear_buildings_cm"]) or near_road(x, y, r, pl["keep_clear_roads_cm"]):
                            continue
                        if any(math.hypot(x - ox_, y - oy_) < r + orad + pl["min_gap_cm"] for ox_, oy_, orad in placed_pts):
                            continue
                        yaw = rng.choice((0.0, 90.0, 180.0, 270.0)) + (rng.uniform(-6, 6) if key in ("Crate", "Pallet") else 0.0)
                        spawn(key, x, y, yaw, "%s_Z%s_%02d" % (key.upper(), zid_s, got))
                        if key == "CargoContainer" and rng.random() < pl["stack_chance"]:
                            spawn(key, x, y, yaw, "%s_Z%s_%02d_TOP" % (key.upper(), zid_s, got), z=259.0)
                        placed_pts.append((x, y, r))
                        got += 1
                        got_total += 1
                        break
        G.log("Zone props: %d of %d placed" % (got_total, want_total))
        G.verify("zone_props", want_total > 0 and got_total >= 0.9 * want_total, "%d of %d placed" % (got_total, want_total))

        # ---------------------------------------------------------------- entrance dressing
        ents = [a for a in G.actors_with_tag("GEN_Phase5") if unreal.Name("Entrance") in a.tags]
        ent_done = 0
        for a in ents:
            loc = a.get_actor_location()
            fyaw = a.get_actor_rotation().yaw
            fdx, fdy = math.cos(math.radians(fyaw)), math.sin(math.radians(fyaw))
            sx, sy = -fdy, fdx
            name = a.get_actor_label().replace("ENTRY_", "")
            x, y = loc.x + sx * 400.0, loc.y + sy * 400.0
            if not near_building(x, y, 50.0, 100.0):
                spawn("Sign", x, y, fyaw - NATIVE, "SIGN_%s" % name)
                placed_pts.append((x, y, 50.0))
                ent_done += 1
            cx_, cy_ = loc.x - sx * 450.0, loc.y - sy * 450.0
            if not near_building(cx_, cy_, 90.0, 100.0) and not near_road(cx_, cy_, 90.0, 50.0):
                spawn("Crate", cx_, cy_, fyaw + rng.uniform(-10, 10), "CRATE_ENTRY_%s" % name)
                spawn("Pallet", cx_ + sx * 130.0, cy_ + sy * 130.0, fyaw, "PALLET_ENTRY_%s" % name)
                placed_pts.append((cx_, cy_, 90.0))
        G.verify("entrance_props", ent_done >= max(1, int(0.7 * len(ents))), "%d signs for %d entrances" % (ent_done, len(ents)))

        # ---------------------------------------------------------------- clearance re-check (zone props only)
        bad = 0
        for a in G.actors_with_tag("GEN_Phase9"):
            n = a.get_actor_label()
            if n.startswith(("CARGOCONTAINER_Z", "FUELTANK_Z", "GENERATOR_Z")):
                l = a.get_actor_location()
                r = rad[{"CARGOCONTAINER": "CargoContainer", "FUELTANK": "FuelTank", "GENERATOR": "Generator"}[n.split("_")[0]]]
                if near_building(l.x, l.y, r - 20.0, 150.0):
                    bad += 1
        G.verify("prop_clearance", bad == 0, "large props clear of buildings" if bad == 0 else "%d too close" % bad)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p09b_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p09b_unexpected", False, repr(e))
    G.summary()


main()
