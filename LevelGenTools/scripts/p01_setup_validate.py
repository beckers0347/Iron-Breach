"""p01_setup_validate.py - Phase 1: confirm Python works, configs are consistent,
every asset loads, and print bounds / collision / Nanite status per mesh.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p01_setup_validate.py"

Look for:
  [Thornfield] VERIFY: python_ok PASS
  [Thornfield] VERIFY: configs PASS
  [Thornfield] VERIFY: asset <key> PASS (bounds XxYxZ)
  [Thornfield] VERIFY: collision <key> PASS (<n> convex)
  [Thornfield] VERIFY: doors <key> PASS (<n> door meshes)
  [Thornfield] VERIFY: all_assets PASS
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unreal
import importlib
import gen_common as G
importlib.reload(G)   # UE keeps Python modules loaded between runs; pick up edits


def _collision_counts(mesh):
    """Return dict of simple-collision primitive counts, or None if unreadable."""
    counts = {}
    try:
        body = mesh.get_editor_property("body_setup")
        agg = body.get_editor_property("agg_geom")
        for prop in ("convex_elems", "box_elems", "sphere_elems", "sphyl_elems"):
            try:
                counts[prop.split("_")[0]] = len(agg.get_editor_property(prop))
            except Exception:
                pass
    except Exception as e:
        G.warn("agg_geom read failed: %r" % e)
    lib = unreal.EditorStaticMeshLibrary
    for name, fn in (("lib_convex", "get_convex_collision_count"), ("lib_box", "get_box_collision_count")):
        try:
            counts[name] = getattr(lib, fn)(mesh)
        except Exception:
            pass
    try:
        counts["complexity"] = str(mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag"))
    except Exception:
        pass
    return counts or None


def _nanite_on(mesh):
    try:
        return bool(mesh.get_editor_property("nanite_settings").get_editor_property("enabled"))
    except Exception:
        return None


def check_configs():
    names = ["level.json", "assets.json", "layout.json", "props.json", "lighting.json"]
    cfgs, bad = {}, []
    for n in names:
        try:
            cfgs[n] = G.load_json(n)
        except Exception as e:
            bad.append("%s: %s" % (n, e))
    G.verify("configs", not bad, "; ".join(bad) if bad else "5 files parsed")
    return cfgs


def check_layout(level, assets, layout):
    b = level["bounds_cm"]
    problems = []
    for s in layout["structures"]:
        if s["asset"] not in assets["buildings"]:
            problems.append("%s: unknown asset %s" % (s["label"], s["asset"]))
        x, y = s["pos"]
        if not (b["min"][0] <= x <= b["max"][0] and b["min"][1] <= y <= b["max"][1]):
            problems.append("%s outside bounds" % s["label"])
        if s["facing"] not in layout["facing_vectors"]:
            problems.append("%s bad facing" % s["label"])
    G.verify("layout_refs", not problems, "; ".join(problems) if problems else "%d structures" % len(layout["structures"]))
    starts = [s for s in layout["structures"] if s.get("player_start")]
    G.verify("player_start_defined", len(starts) == 1, "%d marked" % len(starts))


def check_building(key, entry, tol):
    ok = True
    missing = []
    folder = entry["dest"]
    main_path = "%s/%s" % (folder, entry["main_mesh"])
    try:
        mesh = G.assert_asset_exists(main_path)
    except G.GenError as e:
        existing = unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False)
        G.err(str(e))
        G.err("    assets actually in %s: %s" % (folder, [str(a).split(".")[0].split("/")[-1] for a in existing]))
        G.verify("asset %s" % key, False, "missing %s - run p00_import_assets.py" % main_path)
        return False

    size, origin = G.get_bounds(mesh)
    G.verify("asset %s" % key, True, "bounds %s cm" % G.fmt_size(size))

    # Scale sanity (WARN only; hangar/gate sizes in the spec include aprons or pads)
    exp = entry.get("expected_size_m")
    if exp:
        for axis, got, want in zip("XYZ", (size.x, size.y, size.z), exp):
            if want > 0 and abs(got / 100.0 - want) / want > tol:
                G.warn("%s %s size %.1f m vs expected ~%.1f m (check import scale / spec guess)" % (key, axis, got / 100.0, want))

    # Collision (UE may turn box-shaped UCX hulls into box primitives, so count every primitive type)
    cc = _collision_counts(mesh)
    want = entry.get("expected_ucx")
    if cc is None:
        G.warn("Could not read collision for %s" % key)
    else:
        total = max(sum(cc.get(k, 0) for k in ("convex", "box", "sphere", "sphyl")),
                    cc.get("lib_convex", 0) + cc.get("lib_box", 0))
        G.log("collision detail %s: %s" % (key, cc))
        G.verify("collision %s" % key, total > 0, "%d primitives, UCX in FBX %s" % (total, want))
        if want is not None and total > 0 and total != want:
            G.warn("%s: %d collision primitives vs %d UCX meshes in the FBX" % (key, total, want))
        ok &= total > 0

    nan = _nanite_on(mesh)
    if nan is False:
        G.warn("%s: Nanite is OFF on %s" % (key, entry["main_mesh"]))
    elif nan is None:
        G.warn("%s: could not read Nanite flag" % key)

    # Door meshes listed in the building JSON
    jpath = os.path.join(G.project_dir(), entry["door_json"].replace("/", os.sep))
    try:
        with open(jpath, "r", encoding="utf-8") as f:
            door_cfg = json.load(f)
        doors = door_cfg.get("doors", {})
        for dname in doors:
            if not unreal.EditorAssetLibrary.does_asset_exist("%s/%s" % (folder, dname)):
                missing.append(dname)
        G.verify("doors %s" % key, not missing,
                 "%d door meshes" % len(doors) if not missing else "missing: %s" % missing)
        ok &= not missing
    except Exception as e:
        G.verify("doors %s" % key, False, "cannot read %s (%s)" % (jpath, e))
        ok = False
    return ok


def check_nature(key, entry):
    try:
        mesh = G.assert_asset_exists(entry["ue_path"])
    except G.GenError as e:
        G.err(str(e))
        G.verify("asset %s" % key, False, "missing - run p00_import_assets.py")
        return False
    size, _ = G.get_bounds(mesh)
    G.verify("asset %s" % key, True, "bounds %s cm" % G.fmt_size(size))
    return True


def check_textures(cfg):
    miss = []
    for s in cfg["sets"]:
        for suf in cfg["suffixes"]:
            p = "%s/T_%s_%s" % (cfg["dest"], s, suf)
            if not unreal.EditorAssetLibrary.does_asset_exist(p):
                miss.append(p)
    G.verify("textures", not miss, "%d present" % (len(cfg["sets"]) * len(cfg["suffixes"])) if not miss else "missing %d, first %s" % (len(miss), miss[0]))
    return not miss


def main():
    G.init_log("p01_setup_validate")
    try:
        G.verify("python_ok", True, "UE %s" % unreal.SystemLibrary.get_engine_version())
        cfgs = check_configs()
        if len(cfgs) < 5:
            raise G.GenError("Config files missing or invalid; cannot continue")
        level, assets, layout = cfgs["level.json"], cfgs["assets.json"], cfgs["layout.json"]
        check_layout(level, assets, layout)

        all_ok = True
        for key, entry in assets["buildings"].items():
            all_ok &= check_building(key, entry, level["scale_check_tolerance"])
        for key, entry in assets["nature"].items():
            all_ok &= check_nature(key, entry)
        all_ok &= check_textures(assets["textures"])
        G.verify("all_assets", all_ok)
    except G.GenError as e:
        G.err(str(e))
        G.verify("p01_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p01_unexpected", False, repr(e))
    G.summary()


main()
