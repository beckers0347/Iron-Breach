"""
Scan the project for existing tree/mountain/rock StaticMesh assets
========================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Shane mentioned there are already some tree and mountain meshes imported
somewhere in the project (from an earlier Tripo3D pass), but wasn't sure of
their exact paths or real-world sizing. build_carrowgate_mainland.py's
TREE_ASSET_KIT / MOUNTAIN_ASSET_KIT only pick up assets that live at exact,
hardcoded paths under /Game/Environment/CGMainland/AIModels/SM_Tree_* and
SM_Mountain_* -- so before wiring anything up, this script finds whatever
already exists, wherever it actually lives, and reports it.

Searches the whole /Game asset registry for StaticMesh assets whose name or
folder path contains a tree/mountain/rock-ish keyword, then for each match
reports its full path and its local (unscaled) bounding-box size in meters --
the same bounds check build_carrowgate_mainland.py's grounding fix
(_mesh_min_z_cm) now uses, so this tells us up front roughly how big each
one will come out once spawned, without having to place one and eyeball it.

Writes the results to a JSON file next to this script (mesh_scan_results.json)
so they can be read back programmatically, AND logs a readable summary to
the Output Log.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/scan_tree_mountain_assets.py"

Read-only -- doesn't touch any assets or actors.
"""

import json
import os

import unreal

TREE_KEYWORDS = ["tree", "pine", "oak", "birch", "shrub", "bush", "foliage"]
MOUNTAIN_KEYWORDS = ["mountain", "rock", "cliff", "peak", "ridge", "boulder", "outcrop", "foothill"]

# Don't re-report anything already sitting at the canonical kit paths --
# those are already correctly wired, nothing to discover about them.
EXCLUDE_PREFIX = "/Game/Environment/CGMainland/AIModels/"

registry = unreal.AssetRegistryHelpers.get_asset_registry()


def get_bounds_size_m(mesh):
    try:
        box = unreal.EditorStaticMeshLibrary.get_static_mesh_bounding_box(mesh)
        size = box.max - box.min
        return round(size.x / 100.0, 2), round(size.y / 100.0, 2), round(size.z / 100.0, 2)
    except Exception as exc:
        return None


def classify(name_lower, path_lower):
    haystack = name_lower + " " + path_lower
    if any(k in haystack for k in TREE_KEYWORDS):
        return "tree"
    if any(k in haystack for k in MOUNTAIN_KEYWORDS):
        return "mountain"
    return None


def run():
    ar_filter = unreal.ARFilter(
        class_names=["StaticMesh"],
        package_paths=["/Game"],
        recursive_paths=True,
        recursive_classes=True,
    )
    results = {"tree": [], "mountain": []}

    for asset_data in registry.get_assets(ar_filter):
        path = str(asset_data.package_name)
        if path.startswith(EXCLUDE_PREFIX):
            continue
        name = str(asset_data.asset_name)
        category = classify(name.lower(), path.lower())
        if category is None:
            continue
        mesh = asset_data.get_asset()
        size_m = get_bounds_size_m(mesh)
        full_path = f"{path}.{name}"
        results[category].append({"path": full_path, "size_m_xyz": size_m})

    for category in ("tree", "mountain"):
        results[category].sort(key=lambda e: e["path"])

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mesh_scan_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    unreal.log(f"[Mesh Scan] Found {len(results['tree'])} tree-ish and {len(results['mountain'])} mountain/rock-ish StaticMesh asset(s).")
    for category in ("tree", "mountain"):
        for entry in results[category]:
            unreal.log(f"[Mesh Scan]   [{category}] {entry['path']}  size(m)={entry['size_m_xyz']}")
    unreal.log(f"[Mesh Scan] Full results written to {out_path}")


run()
