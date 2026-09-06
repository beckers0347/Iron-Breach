"""
RETEXTURE ALL ROADS -- move every road actor onto the cobblestone material
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Root cause of "the paths are still matte grey": rebuild_path_network.py
(run earlier, per the "rebuild it without texture" request) put every
causeway / downtown street / outskirt road / joint actor onto
MI_Landmass_Road -- a FLAT, UNTEXTURED placeholder material (constant grey,
no texture sample at all).

Meanwhile all the texture work since then (Tripo3D stone generation,
import_and_apply_tripo_cobblestone.py, clean_rebuild_cobblestone_path.py)
was applied to a DIFFERENT material, M_AI_CobblestonePath. No actor in the
current road network wears that material, so none of that work could ever
show up in the viewport -- the two scripts were pointed at completely
different assets. This is the actual fix: reassign every road actor's
material from MI_Landmass_Road over to M_AI_CobblestonePath.

THE FIX
-------
Finds every actor currently wearing MI_Landmass_Road on material slot 0
(this is every Causeway_/Rail_/Street_X_/Street_Y_/Road_/RoadJoint_ actor --
matched by material rather than name so nothing is missed) and swaps its
material 0 to M_AI_CobblestonePath. Nothing else about the actor (position,
scale) changes.

Safe to re-run -- once switched, an actor is skipped on the next run.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/retexture_all_roads.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

FLAT_ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"
PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"


def log(msg):
    print("[RetextureAllRoads] %s" % msg)


def run():
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("ABORTED -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    cobblestone = AL.load_asset(PATH_MATERIAL_PATH)

    all_actors = actor_subsystem.get_all_level_actors()
    switched = 0
    already = 0
    for a in all_actors:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mat = comp.get_material(0)
            if not mat:
                continue
            p = mat.get_path_name()
            if p.startswith(FLAT_ROAD_MATERIAL_PATH):
                comp.set_material(0, cobblestone)
                switched += 1
            elif p.startswith(PATH_MATERIAL_PATH):
                already += 1

    log("Switched %d road actor(s) from MI_Landmass_Road -> M_AI_CobblestonePath. "
        "(%d were already on the cobblestone material.)" % (switched, already))
    log("Save and check the viewport / re-run PIE.")


run()
