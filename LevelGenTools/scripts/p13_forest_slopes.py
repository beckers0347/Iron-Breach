"""p13_forest_slopes.py - dress the mountains like forested hills and tame the light-pole glow.

Run (after p12):   py "X:/IronBreach/LevelGenTools/scripts/p13_forest_slopes.py"
Safe to re-run.
 * Traces down onto each MOUNTAIN_ mesh and plants spruce/pine on the slopes (scatter.slope_trees_total).
 * Re-tunes every POLELIGHT_ so the poles stop blowing out into white blobs (pole_light_cd, pole_light_radius_cm).

Look for:
  [Thornfield] VERIFY: slope_trees PASS
  [Thornfield] VERIFY: pole_lights PASS
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

PHASE = 13


_DIAG = {"n": 0}


def _hit_point(world, sx, sy, z_top, z_bot):
    try:
        res = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(sx, sy, z_top), unreal.Vector(sx, sy, z_bot),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    except Exception as e:
        G.warn("trace failed: %r" % e)
        return None
    if _DIAG["n"] < 2:
        G.log("trace result type %s: %r" % (type(res).__name__, res))
        _DIAG["n"] += 1
    hit = res
    if isinstance(res, tuple):
        if not res[0]:
            return None
        hit = res[1]
    if hit is None:
        return None
    try:
        if not hit.get_editor_property("blocking_hit"):
            return None
    except Exception:
        pass
    for prop in ("impact_point", "location"):
        try:
            v = hit.get_editor_property(prop)
            return v.x, v.y, v.z
        except Exception:
            pass
    return None


def main():
    G.init_log("p13_forest_slopes")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        props = G.load_json("props.json")["scatter"]
        env = G.load_json("environment.json")["scatter"]
        rng = random.Random(level["seed"] + 13)
        G.cleanup_phase(PHASE)
        world = unreal.EditorLevelLibrary.get_editor_world()

        # ---- pole lights
        n_pl = 0
        for a in G.actor_subsystem().get_all_level_actors():
            if a.get_actor_label().startswith("POLELIGHT_"):
                c = a.get_component_by_class(unreal.PointLightComponent)
                try:
                    c.set_editor_property("intensity", float(env.get("pole_light_cd", 1800)))
                    c.set_editor_property("attenuation_radius", float(env.get("pole_light_radius_cm", 1800)))
                    n_pl += 1
                except Exception as e:
                    G.warn("pole light: %r" % e)
        G.verify("pole_lights", n_pl > 0, "%d pole lights re-tuned" % n_pl)

        # ---- slope trees
        mountains = [a for a in G.actor_subsystem().get_all_level_actors() if a.get_actor_label().startswith("MOUNTAIN_")]
        G.log("Found %d mountains" % len(mountains))
        tree_keys = [k for k in props["trees"]["assets"] if "Snag" not in k] if "trees" in props else \
            [k for k in assets["nature"] if k.startswith("Tree_") and "Snag" not in k]
        info = {}
        for k in tree_keys:
            e = assets["nature"][k]
            m = G.assert_asset_exists(e["ue_path"])
            size, origin = G.get_bounds(m)
            info[k] = (e["ue_path"], size, origin)
        # mountains need collision for the traces: complex-as-simple on the mesh, BlockAll on the actors
        seen = set()
        for m in mountains:
            comp = m.static_mesh_component
            comp.set_collision_profile_name("BlockAll")
            mesh = comp.static_mesh
            pth = mesh.get_path_name()
            if pth not in seen:
                seen.add(pth)
                try:
                    mesh.get_editor_property("body_setup").set_editor_property(
                        "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                    mesh.modify()
                except Exception as e:
                    G.warn("mountain collision flag: %r" % e)
        G.log("Mountain collision enabled on %d mesh(es)" % len(seen))
        total = int(env.get("slope_trees_total", 900))
        hlo, hhi = env.get("slope_tree_height_cm", [2200, 3400])
        zmin = float(env.get("slope_min_z_cm", 250))
        planted, tries = 0, 0
        while mountains and planted < total and tries < total * 12:
            tries += 1
            m = rng.choice(mountains)
            o, ext = m.get_actor_bounds(False)
            x = o.x + rng.uniform(-ext.x, ext.x) * 0.95
            y = o.y + rng.uniform(-ext.y, ext.y) * 0.95
            hp = _hit_point(world, x, y, o.z + ext.z + 500.0, -2000.0)
            if hp is None:
                continue
            hx, hy, hz = hp
            if hz < zmin or hz > (o.z + ext.z) * 0.9:
                continue
            k = rng.choice(tree_keys)
            path, size, origin = info[k]
            h = rng.uniform(hlo, hhi)
            s = h / size.z
            z = hz - (origin.z - size.z / 2.0) * s - 60.0
            a = G.spawn_static_mesh(path, (hx, hy, z), (0, rng.uniform(0, 360), 0), (s, s, s), "SLOPETREE_%04d" % planted, PHASE)
            planted += 1
        G.log("Slope trees planted: %d (%d traces)" % (planted, tries))
        G.verify("slope_trees", planted >= total * 0.5, "%d of %d requested" % (planted, total))

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e)); G.verify("p13_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e); G.verify("p13_unexpected", False, repr(e))
    G.summary()


main()
