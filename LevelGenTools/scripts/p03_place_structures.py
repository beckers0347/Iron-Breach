"""p03_place_structures.py - Phase 3: place the real Blender buildings and their door meshes.

Run (after p02_greybox.py):   py "X:/IronBreach/LevelGenTools/scripts/p03_place_structures.py"

For every structure in layout.json it spawns the main mesh at its world position/yaw, then spawns each
separate door mesh at the door pivot from the building's JSON (door origins sit at the pivot, so the door
is placed at  building_position + rotate(pivot_local, yaw)).  A yellow FRONT marker cube is added in front
of each building so you can see which way the doors face.  The Phase-2 structure boxes are removed.

Look for:
  [Thornfield] Placed <name> at (x,y,z) yaw=..
  [Thornfield] VERIFY: no_overlaps PASS
  [Thornfield] VERIFY: inside_bounds PASS
  [Thornfield] VERIFY: open_space_clear PASS (<N>x<M> uu)
  [Thornfield] VERIFY: doors_placed PASS (<n> door meshes)
"""
import os
import sys
import json
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 3
CUBE = "/Engine/BasicShapes/Cube"
MARK_MAT = "/Game/IronBreach/Thornfield/Greybox/M_GB_Ref"


# --------------------------------------------------------------------------- geometry
def rot(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def corners(cx, cy, hx, hy, yaw_deg):
    return [(cx + rot(dx, dy, yaw_deg)[0], cy + rot(dx, dy, yaw_deg)[1])
            for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def overlap(a, b, margin=0.0):
    """Separating-axis test for two convex polygons (lists of (x,y)). margin>0 requires a gap."""
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
            if max(pa) + margin < min(pb) or max(pb) + margin < min(pa):
                return False
    return True


def main():
    G.init_log("p03_place_structures")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        zt = level["base_plateau_z"]
        b = level["bounds_cm"]
        native = level["mesh_native_front_yaw_deg"]

        G.cleanup_phase(PHASE)

        # Remove the Phase-2 footprint boxes + labels for structures (the real meshes replace them).
        labels = set(s["label"] for s in layout["structures"])
        removed = 0
        for a in G.actors_with_tag("GEN_Phase2"):
            name = a.get_actor_label()
            if name.startswith("GB_") and name[3:] in labels or (name.startswith("LBL_") and name[4:] in labels):
                G.actor_subsystem().destroy_actor(a)
                removed += 1
        G.log("Removed %d Phase-2 structure boxes/labels" % removed)

        mark_mat = unreal.EditorAssetLibrary.load_asset(MARK_MAT)
        footprints = {}          # label -> polygon
        placed, door_total, door_missing = 0, 0, []
        door_bounds_warn = []

        for s in layout["structures"]:
            entry = assets["buildings"][s["asset"]]
            main_path = "%s/%s" % (entry["dest"], entry["main_mesh"])
            mesh = G.assert_asset_exists(main_path)
            size, origin = G.get_bounds(mesh)
            wx, wy = G.plan_to_world(level, s["pos"][0], s["pos"][1])
            yaw = G.facing_to_yaw(layout, s["facing"], s["yaw_offset_deg"], native)
            label = "SM_%s" % s["label"]
            actor = G.spawn_static_mesh(main_path, (wx, wy, zt), (0, yaw, 0), (1, 1, 1), label, PHASE)
            loc = actor.get_actor_location()
            G.log("Placed %s at (%.0f, %.0f, %.0f) yaw=%.1f" % (s["label"], loc.x, loc.y, loc.z, yaw))
            placed += 1

            # footprint polygon from the mesh bounds (rotated with the actor)
            ox, oy = rot(origin.x, origin.y, yaw)
            footprints[s["label"]] = corners(wx + ox, wy + oy, size.x / 2.0, size.y / 2.0, yaw)

            # FRONT marker: a yellow post 3 m in front of the front face
            vx, vy = layout["facing_vectors"][s["facing"]]
            fang = math.degrees(math.atan2(vy, vx)) + s["yaw_offset_deg"]
            fdx, fdy = math.cos(math.radians(fang)), math.sin(math.radians(fang))
            depth = abs(size.x * abs(fdx) + size.y * abs(fdy)) / 2.0   # rough half-extent toward the front
            mx, my = wx + ox + fdx * (depth + 300), wy + oy + fdy * (depth + 300)
            mk = G.spawn_static_mesh(CUBE, (mx, my, zt + 200), (0, fang, 0), (1.0, 0.3, 4.0),
                                     "FRONT_%s" % s["label"], PHASE)
            if mark_mat is not None:
                mk.static_mesh_component.set_material(0, mark_mat)

            # door meshes at the JSON pivots (Blender metres, front = -Y) -> UE local cm (Y flipped)
            jpath = os.path.join(G.project_dir(), entry["door_json"].replace("/", os.sep))
            with open(jpath, "r", encoding="utf-8") as f:
                doors = json.load(f).get("doors", {})
            for dname, d in doors.items():
                dpath = "%s/%s" % (entry["dest"], dname)
                try:
                    dmesh = G.assert_asset_exists(dpath)
                except G.GenError:
                    door_missing.append(dname)
                    continue
                px, py, pz = d["pivot"]
                # Door FBX vertices are baked in BUILDING space (bounds offset == pivot distance in the first run),
                # so the door actor goes at the building origin with the building yaw; the pivot is stored in tags.
                da = G.spawn_static_mesh(dpath, (wx, wy, zt), (0, yaw, 0), (1, 1, 1),
                                         "%s_%s" % (s["label"], dname.replace("SM_", "")), PHASE)
                ax = d.get("axis", [0, 0, 1])
                tags = [str(t) for t in da.tags] + ["Door", "DoorType_%s" % d["type"],
                        "PivotCm_%.1f_%.1f_%.1f" % (px * 100.0, -py * 100.0, pz * 100.0),
                        "AxisBlender_%s" % "_".join("%g" % v for v in ax),
                        "Open_%s" % ("%g" % d["open"] if not isinstance(d.get("open"), (list, tuple)) else "_".join("%g" % v for v in d["open"]))]
                da.set_editor_property("tags", [unreal.Name(t) for t in tags])
                door_total += 1
                dsize, dorigin = G.get_bounds(dmesh)
                exp = math.hypot(px * 100.0, py * 100.0, pz * 100.0)
                got = math.hypot(dorigin.x, dorigin.y, dorigin.z)
                if abs(got - exp) > 0.6 * max(dsize.x, dsize.y, dsize.z) + 100.0:
                    door_bounds_warn.append("%s bounds centre %.0f cm from origin, pivot is %.0f cm" % (dname, got, exp))

        G.log("Placed %d structures, %d door meshes" % (placed, door_total))

        # ------------------------------------------------------------------ VERIFY
        # no overlaps (require a 1 m gap)
        names = list(footprints)
        clashes = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if overlap(footprints[names[i]], footprints[names[j]], margin=100.0):
                    clashes.append("%s x %s" % (names[i], names[j]))
        G.verify("no_overlaps", not clashes, "; ".join(clashes) if clashes else "%d footprints" % len(names))

        # inside bounds
        outside = []
        for n, poly in footprints.items():
            if any(p[0] < b["min"][0] or p[0] > b["max"][0] or p[1] < b["min"][1] or p[1] > b["max"][1] for p in poly):
                outside.append(n)
        G.verify("inside_bounds", not outside, "outside: %s" % outside if outside else "all inside")

        # open space: a 30 m x 20 m yard directly in front of the Command bunker must be empty
        cmd = next(s for s in layout["structures"] if s["label"] == "Command")
        vx, vy = layout["facing_vectors"][cmd["facing"]]
        cwx, cwy = G.plan_to_world(level, cmd["pos"][0], cmd["pos"][1])
        cdepth = 1900.0 + 200.0
        yx, yy = cwx + vx * (cdepth + 1000.0), cwy + vy * (cdepth + 1000.0)
        yard = corners(yx, yy, 1500.0, 1000.0, math.degrees(math.atan2(vy, vx)))
        blockers = [n for n, poly in footprints.items() if n != "Command" and overlap(yard, poly)]
        G.verify("open_space_clear", not blockers, "3000x2000 uu yard in front of Command" if not blockers else "blocked by %s" % blockers)

        G.verify("doors_placed", door_total > 0 and not door_missing,
                 "%d door meshes" % door_total if not door_missing else "missing %s" % door_missing)
        if door_bounds_warn:
            G.warn("Door meshes not where the pivot says (check by eye): %s" % door_bounds_warn)
        G.verify("structures_placed", placed == len(layout["structures"]), "%d of %d" % (placed, len(layout["structures"])))

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p03_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p03_unexpected", False, repr(e))
    G.summary()


main()
