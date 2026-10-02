"""p04_collision_bounds.py - Phase 4: collision audit, invisible boundary walls, kill Z, player-start check.

Run (after p03_place_structures.py):   py "X:/IronBreach/LevelGenTools/scripts/p04_collision_bounds.py"

 1. Every building main mesh must have simple collision (UCX hulls) - audit.
 2. Door meshes get "use complex collision as simple" so closed doors block the player.
 3. Four invisible BlockAll walls (6000 cm tall) just outside the playable bounds.
 4. World Settings: Kill Z = level.json kill_z and world bounds checks on.
 5. Player start must be enclosed (ceiling above, floor below) - i.e. inside the Barracks.

Look for:
  [Thornfield] VERIFY: building_collision PASS
  [Thornfield] VERIFY: door_collision PASS
  [Thornfield] VERIFY: boundary_walls PASS
  [Thornfield] VERIFY: kill_z PASS
  [Thornfield] VERIFY: player_start_inside PASS
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 4
CUBE = "/Engine/BasicShapes/Cube"
WALL_T = 200.0       # wall thickness cm
WALL_H = 6000.0      # wall height cm


def _prim_count(mesh):
    try:
        agg = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
        return sum(len(agg.get_editor_property(p)) for p in ("convex_elems", "box_elems", "sphere_elems", "sphyl_elems"))
    except Exception:
        return 0


def _trace(world, start, end):
    """Line trace (complex) against the editor world. Returns hit distance in cm or None."""
    try:
        res = unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
            unreal.DrawDebugTrace.NONE, True)
    except Exception as e:
        G.warn("line_trace_single failed: %r" % e)
        return None
    hit = res
    if isinstance(res, tuple):
        if not res[0]:
            return None
        hit = res[1]
    elif res is None:
        return None
    for prop in ("distance",):
        try:
            return float(hit.get_editor_property(prop))
        except Exception:
            pass
    try:
        return float(hit.to_tuple()[2])
    except Exception:
        return None


def main():
    G.init_log("p04_collision_bounds")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        b = level["bounds_cm"]

        G.cleanup_phase(PHASE)

        # ---------------------------------------------------------------- 1. building collision audit
        missing = []
        for key, entry in assets["buildings"].items():
            mesh = G.assert_asset_exists("%s/%s" % (entry["dest"], entry["main_mesh"]))
            n = _prim_count(mesh)
            G.log("Collision %s: %d primitives (expected ~%d)" % (key, n, entry["expected_ucx"]))
            if n <= 0:
                missing.append(key)
        G.verify("building_collision", not missing, "all 8 have simple collision" if not missing else "none on %s" % missing)

        # ---------------------------------------------------------------- 2. door collision
        bad_doors = []
        seen = set()
        for a in G.actors_with_tag("Door"):
            comp = a.static_mesh_component
            mesh = comp.static_mesh
            if mesh is None:
                bad_doors.append(a.get_actor_label())
                continue
            path = mesh.get_path_name()
            if path in seen:
                continue
            seen.add(path)
            try:
                bs = mesh.get_editor_property("body_setup")
                bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                mesh.modify()
            except Exception as e:
                bad_doors.append("%s (%r)" % (mesh.get_name(), e))
        for a in G.actors_with_tag("Door"):
            try:
                a.static_mesh_component.set_collision_profile_name("BlockAll")
            except Exception:
                pass
        for p in seen:
            try:
                unreal.EditorAssetLibrary.save_asset(p.split(".")[0])
            except Exception:
                pass
        G.verify("door_collision", not bad_doors and len(seen) > 0,
                 "%d unique door meshes set to complex-as-simple" % len(seen) if not bad_doors else "failed: %s" % bad_doors)

        # ---------------------------------------------------------------- 3. boundary walls
        x0, y0 = b["min"]
        x1, y1 = b["max"]
        w, h = x1 - x0, y1 - y0
        zc = WALL_H / 2.0 - 500.0
        specs = [
            ("BoundWall_West",  (x0 - WALL_T / 2, y0 + h / 2, zc), (WALL_T, h + 2 * WALL_T, WALL_H)),
            ("BoundWall_East",  (x1 + WALL_T / 2, y0 + h / 2, zc), (WALL_T, h + 2 * WALL_T, WALL_H)),
            ("BoundWall_South", (x0 + w / 2, y0 - WALL_T / 2, zc), (w, WALL_T, WALL_H)),
            ("BoundWall_North", (x0 + w / 2, y1 + WALL_T / 2, zc), (w, WALL_T, WALL_H)),
        ]
        walls_ok = 0
        for label, loc, size in specs:
            a = G.spawn_static_mesh(CUBE, loc, (0, 0, 0), (size[0] / 100.0, size[1] / 100.0, size[2] / 100.0), label, PHASE)
            comp = a.static_mesh_component
            try:
                comp.set_collision_profile_name("BlockAll")
                comp.set_editor_property("hidden_in_game", True)
                walls_ok += 1
            except Exception as e:
                G.err("Wall %s setup failed: %r" % (label, e))
        G.verify("boundary_walls", walls_ok == 4, "%d of 4 BlockAll walls, hidden in game" % walls_ok)

        # ---------------------------------------------------------------- 4. kill Z
        try:
            world = unreal.EditorLevelLibrary.get_editor_world()
            ws = world.get_world_settings()
            ws.set_editor_property("kill_z", float(level["kill_z"]))
            ws.set_editor_property("enable_world_bounds_checks", True)
            got = ws.get_editor_property("kill_z")
            G.verify("kill_z", abs(got - level["kill_z"]) < 1.0, "KillZ=%.0f, bounds checks on" % got)
        except Exception as e:
            world = unreal.EditorLevelLibrary.get_editor_world()
            G.verify("kill_z", False, repr(e))

        # ---------------------------------------------------------------- 5. player start inside the Barracks
        ps = None
        for a in G.actor_subsystem().get_all_level_actors():
            if isinstance(a, unreal.PlayerStart):
                ps = a
                break
        if ps is None:
            G.verify("player_start_inside", False, "no PlayerStart in level")
        else:
            loc = ps.get_actor_location()
            up = _trace(world, loc + unreal.Vector(0, 0, 50), loc + unreal.Vector(0, 0, 3000))
            down = _trace(world, loc, loc + unreal.Vector(0, 0, -400))
            G.log("PlayerStart at (%.0f, %.0f, %.0f): ceiling hit %s cm up, floor hit %s cm down" % (loc.x, loc.y, loc.z, up, down))
            G.verify("player_start_inside", up is not None and up < 1500.0,
                     "ceiling %s cm above" % up if up is not None else "open sky above the PlayerStart - move it inside the Barracks")
            if down is None:
                G.warn("No floor under the PlayerStart (trace down 400 cm) - the Barracks interior floor may be below z=0 or too low")

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p04_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p04_unexpected", False, repr(e))
    G.summary()


main()
