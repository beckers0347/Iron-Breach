"""
Single Animation Blueprint for the InfantryTripo3D action set
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Shane: "take all the animation sequences i have for the InfantryTripo3D
folder and create a single animation blueprint for all the actions."

Creates ONE Animation Blueprint -- ABP_InfantryTripo3D, saved right alongside
the animations at /Game/Characters/Infantry/InfantryTripo3D -- targeting
Chaos_Armor_Skeleton (the skeleton imported together with these 38 mocap
clips; NOT the older Chaos_Skeleton under Characters/Infantry/Skins/Chaos --
that one only has Chaosrun/Chaoswalk and is a different, incompatible
skeleton asset).

IMPORTANT LIMITATION -- READ THIS BEFORE RUNNING
--------------------------------------------------
Unreal's Python API does not expose a way to build an AnimGraph's actual node
network (state machines, states, transition rules, blend nodes) from script.
Checked the official 5.x Python API docs for this directly: unreal.AnimBlueprint
only exposes target_skeleton, get_animation_graphs() (read the graphs that
already exist), get_nodes_of_class() (find nodes of a class that already
exist), and add_node_asset_override() (swap which AnimSequence an EXISTING
node points to) -- nothing to create a new state machine or new nodes.
unreal.BlueprintEditorLibrary's graph functions (add_function_graph,
find_graph, compile_blueprint, etc.) are scoped to ordinary Blueprint event
graphs, not AnimGraphs. There is no supported Python equivalent of dragging
out a State Machine node, adding states, and wiring transition rules.

So this script does the two things that ARE reliably scriptable:
  1. Creates and compiles the ABP_InfantryTripo3D asset, target-skeleton set
     correctly, ready to open.
  2. Verifies every AnimSequence found under InfantryTripo3D actually uses
     that skeleton (catches an import mismatch before it becomes a confusing
     in-editor error), and logs the full list, pre-sorted into the groupings
     below -- so building the state machine by hand is mostly "drag these
     in, in this order" rather than starting from a blank list of 38 files.

SUGGESTED STATE GROUPING (build these as states/sub-state-machines in the
AnimGraph once the asset is open -- see the categorized log output when this
runs, and ANIM_GROUPS below for the exact file-to-group mapping):
  - Idle          -- idle, idle_2..5, rifle_aiming_idle, falling_idle
  - Locomotion    -- walking(_backwards), running, run_backwards, start/stop
                      walking & running, walk_backwards_stop, strafe(_2),
                      left_turn, right_turn
  - Combat/Rifle  -- firing_rifle, rifle_run, rifle_aiming_idle
  - Cover/Stealth -- cover_to_stand(_2), stand_to_cover(_2),
                      crouched_sneaking_left/right, left/right_cover_sneak
  - Jump/Fall     -- jump_forward, jump_backward, jumping_up,
                      falling_to_roll, hard_landing
  - Death         -- walking_to_dying
A locomotion Blend Space (2D speed/direction) driving the Locomotion group
the way BS_Armed_Locomotion / BS_Unarmed_Locomotion already do elsewhere in
this project is almost certainly the right call for that group specifically,
rather than one state per direction -- same pattern already proven to work
here, just pointed at these clips instead.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_infantry_tripo3d_animbp.py"

Safe to re-run: reuses the ABP if it already exists (just re-verifies the
skeleton and re-logs the grouped file list), doesn't touch any AnimGraph
work you've already done by hand.
"""

import unreal

ASSET_ROOT = "/Game/Characters/Infantry/InfantryTripo3D"
SKELETON_PATH = f"{ASSET_ROOT}/Chaos_Armor_Skeleton.Chaos_Armor_Skeleton"
ABP_NAME = "ABP_InfantryTripo3D"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

# name (without the .uasset / package suffix) -> suggested state-machine group,
# purely for the log output / your own reference while wiring the AnimGraph by
# hand -- doesn't affect what gets created.
ANIM_GROUPS = {
    "idle": "Idle", "idle__2_": "Idle", "idle__3_": "Idle", "idle__4_": "Idle", "idle__5_": "Idle",
    "rifle_aiming_idle": "Idle / Combat", "falling_idle": "Idle",
    "walking": "Locomotion", "walking_backwards": "Locomotion",
    "running": "Locomotion", "run_backwards": "Locomotion",
    "start_walking": "Locomotion", "start_walking_backwards": "Locomotion",
    "stop_walking": "Locomotion", "walk_backwards_stop": "Locomotion", "run_to_stop": "Locomotion",
    "strafe": "Locomotion", "strafe__2_": "Locomotion",
    "left_turn": "Locomotion", "right_turn": "Locomotion",
    "firing_rifle": "Combat", "rifle_run": "Combat",
    "cover_to_stand": "Cover/Stealth", "cover_to_stand__2_": "Cover/Stealth",
    "stand_to_cover": "Cover/Stealth", "stand_to_cover__2_": "Cover/Stealth",
    "crouched_sneaking_left": "Cover/Stealth", "crouched_sneaking_right": "Cover/Stealth",
    "left_cover_sneak": "Cover/Stealth", "right_cover_sneak": "Cover/Stealth",
    "jump_forward": "Jump/Fall", "jump_backward": "Jump/Fall", "jumping_up": "Jump/Fall",
    "falling_to_roll": "Jump/Fall", "hard_landing": "Jump/Fall",
    "walking_to_dying": "Death",
}


def run():
    skeleton = unreal.EditorAssetLibrary.load_asset(SKELETON_PATH)
    if skeleton is None:
        unreal.log_error(f"[InfantryTripo3D ABP] {SKELETON_PATH} not found -- can't create an Animation "
                          "Blueprint without a target skeleton. Double check the animations actually "
                          "imported (and imported a skeleton alongside them) before re-running this.")
        return

    # ---- Find every AnimSequence under the folder, and sanity-check each one
    # actually targets Chaos_Armor_Skeleton -- catches an accidental import
    # onto the wrong skeleton before it becomes a confusing "incompatible
    # skeleton" error inside the AnimGraph editor. ----
    found = {}
    mismatched = []
    for asset_path in unreal.EditorAssetLibrary.list_assets(ASSET_ROOT, recursive=False, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(asset, unreal.AnimSequence):
            continue
        name = asset.get_name()
        found[name] = asset
        anim_skeleton = asset.get_editor_property("skeleton")
        if anim_skeleton is not None and anim_skeleton.get_name() != skeleton.get_name():
            mismatched.append((name, anim_skeleton.get_name()))

    if not found:
        unreal.log_error(f"[InfantryTripo3D ABP] No AnimSequence assets found directly under {ASSET_ROOT} -- "
                          "nothing to build the Animation Blueprint against. Nothing created.")
        return

    if mismatched:
        unreal.log_warning(f"[InfantryTripo3D ABP] {len(mismatched)} sequence(s) target a DIFFERENT skeleton "
                            f"than {skeleton.get_name()} -- they won't play correctly on this ABP until "
                            "retargeted: " + ", ".join(f"{n} (-> {s})" for n, s in mismatched))

    # ---- Create (or reuse) the Animation Blueprint, targeting the skeleton. ----
    full_path = f"{ASSET_ROOT}/{ABP_NAME}.{ABP_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        anim_bp = unreal.EditorAssetLibrary.load_asset(full_path)
        unreal.log(f"[InfantryTripo3D ABP] {ABP_NAME} already exists -- reusing it (re-verifying skeleton/list only).")
    else:
        factory = unreal.AnimBlueprintFactory()
        factory.set_editor_property("target_skeleton", skeleton)
        anim_bp = asset_tools.create_asset(ABP_NAME, ASSET_ROOT, unreal.AnimBlueprint, factory)
        if anim_bp is None:
            unreal.log_error(f"[InfantryTripo3D ABP] Could not create {full_path}.")
            return
        unreal.log(f"[InfantryTripo3D ABP] Created {full_path}, target skeleton = {skeleton.get_name()}.")

    if anim_bp.get_editor_property("target_skeleton") != skeleton:
        anim_bp.set_editor_property("target_skeleton", skeleton)

    unreal.BlueprintEditorLibrary.compile_blueprint(anim_bp)
    unreal.EditorAssetLibrary.save_loaded_asset(anim_bp)

    # ---- Log the full, grouped list -- this is the part that saves you time
    # once you open the ABP and start actually wiring the AnimGraph by hand
    # (see the big comment at the top of this file for why that part can't
    # be scripted). ----
    by_group = {}
    for name in sorted(found):
        group = ANIM_GROUPS.get(name, "Ungrouped -- new/renamed since this script was written")
        by_group.setdefault(group, []).append(name)

    unreal.log(f"[InfantryTripo3D ABP] {full_path} ready, compiled, {len(found)} AnimSequence(s) found under "
               f"{ASSET_ROOT}. AnimGraph (state machine, blend spaces, transitions) still needs to be built "
               "by hand in the ABP editor -- Python can't script AnimGraph node creation. Suggested grouping:")
    for group in sorted(by_group):
        unreal.log(f"[InfantryTripo3D ABP]   {group}: " + ", ".join(by_group[group]))


run()
