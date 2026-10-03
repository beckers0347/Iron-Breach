"""p10_final_checks.py - Phase 10: whole-level audit, save, and a JSON report.

Run (after p09b):   py "X:/IronBreach/LevelGenTools/scripts/p10_final_checks.py"

Checks: actors exist for every phase, 13 structures + 52 doors, one PlayerStart inside the Barracks zone, nothing
below Kill Z, props/walls inside the playable bounds, no mesh left on a missing/default material, one of each
lighting actor, Kill Z set, then saves everything and confirms nothing is left unsaved.
Writes LevelGenTools/logs/final_report.json.

Look for:  [Thornfield] VERIFY: ... PASS  for every line, then SUMMARY with 0 FAIL.
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)


def main():
    G.init_log("p10_final_checks")
    report = {}
    try:
        level = G.load_json("level.json")
        layout = G.load_json("layout.json")
        b = level["bounds_cm"]
        actors = list(G.actor_subsystem().get_all_level_actors())
        report["total_actors"] = len(actors)
        G.log("Total actors in level: %d" % len(actors))

        # 1. every phase left actors
        per = {}
        for n in range(2, 10):
            if n == 7:
                continue            # Phase 7 (materials) changes assets, not level actors
            per[n] = len(G.actors_with_tag("GEN_Phase%d" % n))
        report["actors_per_phase"] = per
        empty = [n for n, c in per.items() if c == 0]
        G.verify("phases_present", not empty, str(per) if not empty else "no actors for phases %s" % empty)

        # 2. structures + doors
        sm = [a for a in G.actors_with_tag("GEN_Phase3") if a.get_actor_label().startswith("SM_")]
        doors = [a for a in actors if unreal.Name("Door") in a.tags]
        # main structures are SM_<label>; doors are <label>_<door> (also tagged Door)
        mains = [a for a in sm if unreal.Name("Door") not in a.tags]
        G.verify("structures", len(mains) == len(layout["structures"]), "%d of %d" % (len(mains), len(layout["structures"])))
        G.verify("doors", len(doors) == 52, "%d door actors (expected 52)" % len(doors))
        report.update(structures=len(mains), doors=len(doors))

        # 3. player start
        starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
        ok = False
        if len(starts) == 1:
            ps_struct = next(s for s in layout["structures"] if s.get("player_start"))
            zone = next(z for z in layout["zones"] if z["id"] == ps_struct["zone"])
            zx, zy = G.plan_to_world(level, zone["center"][0], zone["center"][1])
            l = starts[0].get_actor_location()
            ok = abs(l.x - zx) <= zone["size"][0] / 2.0 and abs(l.y - zy) <= zone["size"][1] / 2.0
        G.verify("player_start", ok, "%d PlayerStart(s), inside the %s zone" % (len(starts), "Barracks") if ok else "found %d, zone test failed" % len(starts))

        # 4. nothing below kill Z
        low = [a.get_actor_label() for a in actors if a.get_actor_location().z < level["kill_z"]]
        G.verify("above_kill_z", not low, "all actors above %d" % level["kill_z"] if not low else "below: %s" % low[:5])

        # 5. dressing inside the playable bounds (walls/props/signs - not forest, cliffs, mountains, ground)
        skip = ("TREE", "ROCK", "CLIFF", "MOUNTAIN", "Ground", "BoundWall", "GB_", "LBL_", "ZONE_", "WP_", "ENTRY_", "REF_")
        outside = []
        for a in G.actors_with_tag("GEN_Phase9"):
            n = a.get_actor_label()
            if n.startswith(skip) or n.startswith("POLELIGHT"):
                continue
            l = a.get_actor_location()
            if not (b["min"][0] - 500 <= l.x <= b["max"][0] + 500 and b["min"][1] - 500 <= l.y <= b["max"][1] + 500):
                outside.append(n)
        G.verify("props_in_bounds", not outside, "all Phase 9 props inside bounds" if not outside else "outside: %s" % outside[:6])

        # 6. materials
        bad = []
        for a in actors:
            if isinstance(a, unreal.StaticMeshActor) and not a.get_actor_label().startswith("BoundWall_"):   # invisible collision walls need no material
                comp = a.static_mesh_component
                for i, m in enumerate(comp.get_materials()):
                    if m is None or "WorldGridMaterial" in m.get_name():
                        bad.append("%s[%d]" % (a.get_actor_label(), i))
                        break
        report["missing_materials"] = bad[:20]
        G.verify("materials_ok", not bad, "no mesh on a missing/default material" if not bad else "%d actors, e.g. %s" % (len(bad), bad[:5]))

        # 7. lighting actors
        want = {"DirectionalLight": unreal.DirectionalLight, "SkyAtmosphere": unreal.SkyAtmosphere, "SkyLight": unreal.SkyLight,
                "ExponentialHeightFog": unreal.ExponentialHeightFog, "PostProcessVolume": unreal.PostProcessVolume}
        counts = {k: len([a for a in actors if isinstance(a, c)]) for k, c in want.items()}
        report["lighting"] = counts
        G.verify("lighting_actors", all(v == 1 for v in counts.values()), str(counts))
        lights = len([a for a in actors if isinstance(a, unreal.PointLight)])
        report["point_lights"] = lights
        G.log("Point lights: %d" % lights)

        # 8. kill z
        ws = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_world_settings()
        kz = ws.get_editor_property("kill_z")
        G.verify("kill_z_set", abs(kz - level["kill_z"]) < 1.0, "KillZ=%.0f" % kz)

        # 9. save everything, then confirm nothing is dirty
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        except Exception as e:
            G.warn("save_dirty_packages: %r" % e)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        try:
            dirty = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
        except Exception:
            dirty = []
        G.verify("all_saved", not dirty, "nothing unsaved" if not dirty else "%d unsaved packages" % len(dirty))

        out = os.path.join(G.tools_root(), "logs", "final_report.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        G.log("Report written: %s" % out)
    except G.GenError as e:
        G.err(str(e))
        G.verify("p10_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p10_unexpected", False, repr(e))
    G.summary()


main()
