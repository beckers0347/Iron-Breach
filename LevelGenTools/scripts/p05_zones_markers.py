"""p05_zones_markers.py - Phase 5: gameplay zones and markers.

Run (after p04):   py "X:/IronBreach/LevelGenTools/scripts/p05_zones_markers.py"

Spawns
  * a TriggerBox per zone in layout.json (tag Zone_<name>, 9 sized boxes + the whole-base Forest_Perimeter box)
  * a TargetPoint "ENTRY_<structure>" in front of every structure (tag Entrance) - for AI / objectives / audio later
  * a TargetPoint "WP_<road>_<nn>" at every road control point (tag RoadPoint)
All actors are tagged GEN_Phase5 and live in the Generated/Phase5 outliner folder.

Look for:
  [Thornfield] VERIFY: zones_placed PASS
  [Thornfield] VERIFY: zone_coverage PASS
  [Thornfield] VERIFY: entrances_placed PASS
  [Thornfield] VERIFY: roadpoints_placed PASS
  [Thornfield] VERIFY: player_start_zone PASS
"""
import os
import sys
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 5


def _add_tags(actor, tags):
    cur = [str(t) for t in actor.tags]
    for t in tags:
        if t not in cur:
            cur.append(t)
    actor.set_editor_property("tags", [unreal.Name(t) for t in cur])


def _inside(zone_box, x, y):
    cx, cy, hx, hy = zone_box
    return abs(x - cx) <= hx and abs(y - cy) <= hy


def main():
    G.init_log("p05_zones_markers")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        zt = level["base_plateau_z"]

        G.cleanup_phase(PHASE)

        # ------------------------------------------------------------------ zones
        zone_boxes = {}     # id -> (cx, cy, hx, hy) in world cm
        zones_ok = 0
        for z in layout["zones"]:
            cx, cy = G.plan_to_world(level, z["center"][0], z["center"][1])
            sx, sy = z["size"]
            height = 6000.0 if z["id"] == 10 else 1500.0
            a = G.spawn_by_class(unreal.TriggerBox, (cx, cy, zt + height / 2.0), (0, 0, 0), "ZONE_%s" % z["name"], PHASE)
            try:
                box = a.get_component_by_class(unreal.BoxComponent)
                box.set_editor_property("box_extent", unreal.Vector(sx / 2.0, sy / 2.0, height / 2.0))
                _add_tags(a, ["Zone", "Zone_%s" % z["name"], "ZoneId_%d" % z["id"]])
                zone_boxes[z["id"]] = (cx, cy, sx / 2.0, sy / 2.0)
                zones_ok += 1
                G.log("Zone %02d %s at (%.0f, %.0f) size %.0f x %.0f" % (z["id"], z["name"], cx, cy, sx, sy))
            except Exception as e:
                G.err("Zone %s: %r" % (z["name"], e))
        G.verify("zones_placed", zones_ok == len(layout["zones"]), "%d of %d" % (zones_ok, len(layout["zones"])))

        # ------------------------------------------------------------------ entrances
        ent_ok, outside_zone = 0, []
        for s in layout["structures"]:
            entry = assets["buildings"][s["asset"]]
            mesh = G.assert_asset_exists("%s/%s" % (entry["dest"], entry["main_mesh"]))
            size, origin = G.get_bounds(mesh)
            wx, wy = G.plan_to_world(level, s["pos"][0], s["pos"][1])
            yaw = G.facing_to_yaw(layout, s["facing"], s["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            ox, oy = origin.x * c - origin.y * sn, origin.x * sn + origin.y * c
            vx, vy = layout["facing_vectors"][s["facing"]]
            fang = math.degrees(math.atan2(vy, vx)) + s["yaw_offset_deg"]
            fdx, fdy = math.cos(math.radians(fang)), math.sin(math.radians(fang))
            depth = abs(size.x * abs(fdx) + size.y * abs(fdy)) / 2.0
            ex, ey = wx + ox + fdx * (depth + 500.0), wy + oy + fdy * (depth + 500.0)
            a = G.spawn_by_class(unreal.TargetPoint, (ex, ey, zt + 50.0), (0, fang, 0), "ENTRY_%s" % s["label"], PHASE)
            _add_tags(a, ["Entrance", "Entrance_%s" % s["label"], "Zone_%d" % s["zone"]])
            ent_ok += 1
            # the structure's own centre must sit inside its assigned zone box
            zb = zone_boxes.get(s["zone"])
            if zb is None or not _inside(zb, wx, wy):
                outside_zone.append(s["label"])
        G.verify("entrances_placed", ent_ok == len(layout["structures"]), "%d of %d" % (ent_ok, len(layout["structures"])))
        G.verify("zone_coverage", not outside_zone,
                 "every structure centre is inside its zone" if not outside_zone else "outside own zone: %s" % outside_zone)

        # ------------------------------------------------------------------ road waypoints
        wp_ok, wp_expected = 0, 0
        for r in layout["roads"]:
            for i, p in enumerate(r["points"]):
                wp_expected += 1
                wx, wy = G.plan_to_world(level, p[0], p[1])
                a = G.spawn_by_class(unreal.TargetPoint, (wx, wy, zt + 20.0), (0, 0, 0), "WP_%s_%02d" % (r["name"], i), PHASE)
                _add_tags(a, ["RoadPoint", "Road_%s" % r["name"]])
                wp_ok += 1
        G.verify("roadpoints_placed", wp_ok == wp_expected and wp_ok > 0, "%d road points" % wp_ok)

        # ------------------------------------------------------------------ player start in the Barracks zone
        ps_struct = next(s for s in layout["structures"] if s.get("player_start"))
        zb = zone_boxes.get(ps_struct["zone"])
        ps = next((a for a in G.actor_subsystem().get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
        ok = False
        if ps is not None and zb is not None:
            l = ps.get_actor_location()
            ok = _inside(zb, l.x, l.y)
        G.verify("player_start_zone", ok, "PlayerStart is inside zone %d (%s)" % (ps_struct["zone"], ps_struct["label"]))

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p05_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p05_unexpected", False, repr(e))
    G.summary()


main()
