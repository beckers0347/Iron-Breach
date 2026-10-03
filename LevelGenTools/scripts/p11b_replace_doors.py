"""p11b_replace_doors.py - swap the 52 static door meshes for AIBSensorDoor actors (proximity-opened, no Blueprint).

Run (after p11a):   py "X:/IronBreach/LevelGenTools/scripts/p11b_replace_doors.py"

For every door in every building's JSON it spawns the existing C++ actor AIBSensorDoor at the building origin
(same position/yaw the static door had), calls ConfigureDoor(skeletal mesh, open animation) and ConfigureVolumes
(sensor box = door bounds + margin, blocker box = door bounds). Walk up and the door opens, walk away and it closes
after CloseDelay. The old static door actors are removed. Re-running is safe (tag GEN_Phase11).

Look for:
  [Thornfield] VERIFY: doors_spawned PASS (52 sensor doors)
  [Thornfield] VERIFY: doors_configured PASS
  [Thornfield] VERIFY: static_doors_removed PASS
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 11


def main():
    G.init_log("p11b_replace_doors")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        cfg = assets["door_skeletals"]
        zt = level["base_plateau_z"]
        if not hasattr(unreal, "IBSensorDoor"):
            raise G.GenError("unreal.IBSensorDoor not found - the IronBreach C++ module (World/IBSensorDoor) is not loaded in this editor session")

        G.cleanup_phase(PHASE)
        old = [a for a in G.actors_with_tag("GEN_Phase3") if unreal.Name("Door") in a.tags]
        for a in old:
            G.actor_subsystem().destroy_actor(a)
        G.log("Removed %d static door actors" % len(old))

        spawned, configured, bad = 0, 0, []
        expected = 0
        for s in layout["structures"]:
            entry = assets["buildings"][s["asset"]]
            key = s["asset"]
            jpath = os.path.join(G.project_dir(), entry["door_json"].replace("/", os.sep))
            with open(jpath, "r", encoding="utf-8") as f:
                doors = json.load(f).get("doors", {})
            wx, wy = G.plan_to_world(level, s["pos"][0], s["pos"][1])
            yaw = G.facing_to_yaw(layout, s["facing"], s["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            for dname, d in doors.items():
                expected += 1
                folder = "%s/%s" % (cfg["dest_root"], key)
                try:
                    sk = G.assert_asset_exists("%s/SK_%s" % (folder, dname))
                    an = G.assert_asset_exists("%s/A_%s_Open" % (folder, dname))
                except G.GenError as e:
                    bad.append("%s (%s)" % (dname, e))
                    continue
                label = "%s_%s" % (s["label"], dname.replace("SM_", ""))
                a = G.spawn_by_class(unreal.IBSensorDoor, (wx, wy, zt), (0, yaw, 0), label, PHASE)
                spawned += 1
                a.configure_door(sk, an)
                b = sk.get_bounds()
                o, e = b.origin, b.box_extent
                m = float(cfg["sensor_margin_cm"])
                a.configure_volumes(
                    unreal.Vector(o.x, o.y, o.z), unreal.Vector(e.x + m, e.y + m, max(e.z, 150.0) + 100.0),
                    unreal.Vector(o.x, o.y, o.z), unreal.Vector(max(e.x, 8.0), max(e.y, 8.0), max(e.z, 20.0)),
                    unreal.Rotator(0, 0, 0))
                try:
                    a.set_editor_property("close_delay", float(cfg.get("close_delay_s", 2.0)))
                except Exception as ex:
                    G.warn("close_delay: %r" % ex)
                tags = [str(t) for t in a.tags] + ["Door", "DoorType_%s" % d["type"]]
                a.set_editor_property("tags", [unreal.Name(t) for t in tags])
                if a.door_mesh.get_editor_property("skeletal_mesh_asset") is not None:
                    configured += 1
        G.log("Sensor doors spawned: %d of %d" % (spawned, expected))
        G.verify("doors_spawned", spawned == expected and expected == 52, "%d sensor doors" % spawned)
        G.verify("doors_configured", configured == spawned and not bad, "%d configured" % configured if not bad else "problems: %s" % bad[:4])
        left = [a for a in G.actor_subsystem().get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and unreal.Name("Door") in a.tags]
        G.verify("static_doors_removed", not left, "no static door actors left" if not left else "%d remain" % len(left))
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p11b_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p11b_unexpected", False, repr(e))
    G.summary()


main()
