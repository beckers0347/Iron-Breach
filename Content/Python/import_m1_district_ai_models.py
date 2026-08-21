"""
M1 District -- AI 3D model import (Tripo3D or Meshy)
=========================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Companion to build_m1_district.py, same job as the garrison's
import_ai_models.py: replaces the district's placeholder prop boxes with real
generated meshes. This project's existing pipeline uses Meshy (Content/Python/
import_ai_models.py, the meshy editor plugin) -- if you're now generating on
Tripo3D instead, the workflow is the same shape (generate -> download FBX ->
drop in a folder -> run an import script), just a different site and a couple
of download-dialog labels. Export settings below are written for Tripo3D;
if you end up using Meshy for some of these, match import_ai_models.py's
settings instead (Resize ON, Height in cm, Origin=Bottom, Format=FBX).

THE SHOPPING LIST -- what build_m1_district.py is waiting on
--------------------------------------------------------------
Every one of these has a live placeholder box in the level right now (via
real_or_placeholder() in the district script) -- generating and importing
the mesh below is a drop-in swap, no level script changes needed. Ranked
roughly by how well AI text-to-3D actually handles this kind of shape (background
hardware/vehicles are Tripo3D/Meshy's sweet spot; anything organic/hero-scale
is not -- see the note at the very bottom about PALAWAN and the Caryatid frame,
which deliberately are NOT on this list):

  - SM_EvacBus.fbx        -- boxy civilian evac bus, Height=280cm (roofline).
                              3 placed in the Dread street.
  - SM_DeterrentEmplacement.fbx -- Bellringer acoustic emplacement: a squat
                              military hardware turret/rig, mixed metal
                              surfaces, exposed cabling/horns reading as
                              "sonic," Height=450cm. 2 placed at the gun line.
  - SM_SiegeGun.fbx        -- garrison siege gun on a fixed mount, Height=350cm.
                              1 placed at the gun line.
  - SM_BakerySign.fbx      -- small hanging shop sign + bracket, weathered,
                              Height=250cm. 1 placed at the carry's first turn.
  - SM_Stretcher.fbx       -- military field stretcher, Height=50cm. 1 placed
                              at the hospital muster.
  - SM_TideMarkRing.fbx    -- a painted ring motif on a curved greave/plate
                              fragment (small, mostly flat) -- if this doesn't
                              generate cleanly as a 3D prop, it's genuinely
                              better as a decal/texture in-editor instead of an
                              AI mesh; don't burn credits chasing it. Height=80cm.

TRIPO3D SPECIFICS (checked against Tripo's own docs, Aug 2026)
-------------------------------------------------------------
Tripo3D's export panel is NOT the same shape as Meshy's -- there is no
documented "Resize ON / Height in cm / Origin=Bottom" toggle like the
garrison script's import_ai_models.py assumes for Meshy. What Tripo3D does
give you:
  - Export formats: USD, FBX, OBJ, STL, GLB, 3MF. Use FBX (matches this
    script's importer, same as the Meshy pipeline).
  - Default export scale is 1 unit = 1 cm -- but that's a UNIT convention,
    not a promise the model comes out at the real-world size you asked for
    in the prompt (a "2.8m bus" prompt does not guarantee a mesh that
    measures 280cm tall on import). Check the imported mesh's bounds in the
    Static Mesh Editor against the target height in the shopping list below
    and set a scale on the placeholder swap in build_m1_district.py's
    real_or_placeholder() call for that prop if it's off.
  - No documented base/bottom pivot option -- imported meshes may be
    center-pivoted. If a prop floats or sinks relative to its ground pad
    once placed, that's why; nudge its Z in the editor by hand, same "verify
    once visible" approach this project's scripts already use elsewhere
    (the garrison script's ramp roll, sea wall, etc.).
  - "Refine" (a second pass after the initial generation) produces real
    PBR textures (metallic/roughness/AO), unlike Meshy's untextured "grey
    clay" exports -- worth clicking before downloading. Because of this,
    import_materials/import_textures below are ON (importing Tripo's own
    material) rather than the garrison pipeline's off-then-reapply-a-shared-
    material approach; per-item MATERIAL_OVERRIDE stays available if you'd
    rather force the shared AI-texture look for visual consistency.
  - Prompt structure that works well per Tripo's own guidance: "Subject +
    Detail Description + Style Definition" -- see
    Docs/M1_DISTRICT_TRIPO3D_PROMPTS.md for one ready-to-paste prompt per
    item on the shopping list below, written in that structure.

HOW TO RUN IT
-------------
1. Generate each model (prompts in Docs/M1_DISTRICT_TRIPO3D_PROMPTS.md),
   Refine for PBR texture, download as FBX.
2. Move/rename the downloaded file into:
       X:\\IronBreach\\Content\\LevelPrototyping\\AIModels_District\\SM_EvacBus.fbx
   (create the AIModels_District folder if it doesn't exist -- kept separate
   from the garrison's AIModels folder so the two districts' asset lists don't
   collide or get mixed up when re-running either import script.)
3. Run from the Output Log console:
       py "X:/IronBreach/Content/Python/import_m1_district_ai_models.py"
   or the Python console tab:
       exec(open("X:/IronBreach/Content/Python/import_m1_district_ai_models.py").read())
4. Re-run build_m1_district.py -- it checks for each mesh by path and swaps
   the matching placeholder box for the real mesh automatically, exactly like
   the garrison's truck/crane/ship swap.

Safe to re-run: existing mesh assets get re-imported in place, not duplicated.

WHY PALAWAN AND THE CARYATID FRAME ARE NOT ON THIS LIST
----------------------------------------------------------
Both are placed as placeholder silhouettes in build_m1_district.py on purpose,
not as an oversight. Tripo3D/Meshy-class text-to-3D is genuinely good at
background hardware (this list) and genuinely bad at two things this mission
needs: (1) a 74m creature that has to read as a specific, recurring individual
across the whole campaign (KAIJU-CODEX.md), and (2) an 80-95m two-pilot mech
with a cockpit, gantry-scale detail, and a paint/battle-damage system that
recurs for the rest of the game (CARYATID-architecture.md, BASTION-CITY-
DESIGN.md's Drydock). Both are worth a real sculpt (or at minimum a heavily
art-directed multi-pass AI generation with a LOT of iteration and cleanup) --
running one Tripo3D prompt and dropping the output in is very likely to produce
something the game is stuck looking at for its entire first act. Recommend
treating those two as their own dedicated art tasks, not folded into this
prop-import pass.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\LevelPrototyping\AIModels_District"
DEST_PATH = "/Game/M1_District/AIModels"

# (source filename, destination asset name, target height in cm, material
# OVERRIDE path or None). Material is None by default everywhere -- Tripo's
# own Refine-pass PBR material is kept as-imported. Set an override path only
# if you specifically want a prop to match the shared AI-texture look instead
# of its own generated material (e.g. to visually match SM_Truck_Cargo).
MODELS = [
    ("SM_EvacBus.fbx", "SM_EvacBus", 280.0, None),
    ("SM_DeterrentEmplacement.fbx", "SM_DeterrentEmplacement", 450.0, None),
    ("SM_SiegeGun.fbx", "SM_SiegeGun", 350.0, None),
    ("SM_BakerySign.fbx", "SM_BakerySign", 250.0, None),
    ("SM_Stretcher.fbx", "SM_Stretcher", 50.0, None),
    ("SM_TideMarkRing.fbx", "SM_TideMarkRing", 80.0, None),
]

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[M1 District AI Models] Skipped '{label}': {e}")
        return None


def import_model(filename, asset_name):
    src = os.path.join(SOURCE_DIR, filename)
    if not os.path.exists(src):
        unreal.log_error(
            f"[M1 District AI Models] Missing source file: {src} -- generate it and move/rename it "
            f"into that folder first. See this script's docstring for the full shopping list."
        )
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    # ON (unlike the Meshy garrison pipeline's OFF): Tripo3D's Refine pass
    # produces real PBR textures baked into the FBX, worth keeping instead of
    # overwriting with a shared flat material. See MODELS' override column
    # for the rare case you want the shared look instead.
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    try:
        options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    except Exception:
        pass
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])

    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{asset_name}.{asset_name}")
    if mesh is None:
        unreal.log_error(f"[M1 District AI Models] Import failed for {filename} -- check the Output Log above.")
    return mesh


def apply_material(mesh, material_path):
    if mesh is None or not material_path:
        return
    mat = unreal.EditorAssetLibrary.load_asset(material_path)
    if mat is None:
        unreal.log_warning(f"[M1 District AI Models] Material not found at '{material_path}' -- mesh left with imported/default material.")
        return
    mesh.set_material(0, mat)


def check_height(mesh, asset_name, target_height_cm):
    """Tripo3D doesn't document a resize-to-real-world-height export option
    (unlike Meshy's Resize/Height-in-cm toggle), so the imported mesh's actual
    size is whatever the generator produced -- logs actual vs. target so a
    mismatch is a one-line Output Log read, not a surprise once it's placed at
    1:1 scale in build_m1_district.py and looks like the wrong size next to
    the player capsule."""
    if mesh is None:
        return
    bounds = mesh.get_bounding_box()
    actual_height_cm = bounds.max.z - bounds.min.z
    if actual_height_cm <= 0.01:
        unreal.log_warning(f"[M1 District AI Models] {asset_name}: could not read a sane bounding height.")
        return
    ratio = target_height_cm / actual_height_cm
    if abs(ratio - 1.0) > 0.15:
        unreal.log_warning(
            f"[M1 District AI Models] {asset_name}: imported at {actual_height_cm:.0f}cm tall, "
            f"target is {target_height_cm:.0f}cm (ratio {ratio:.2f}x). build_m1_district.py places "
            f"this at real_scale=(1,1,1) -- pass real_scale=({ratio:.2f},{ratio:.2f},{ratio:.2f}) "
            f"in that call, or rescale the asset itself in the Static Mesh Editor, before re-running "
            f"the blockout script."
        )
    else:
        unreal.log(f"[M1 District AI Models] {asset_name}: {actual_height_cm:.0f}cm tall, close enough to the {target_height_cm:.0f}cm target.")


def enable_nanite(mesh):
    """Same reasoning as the garrison's import script: high-detail AI exports
    are often 500k-1.5M triangles uncut -- Nanite handles that natively."""
    if mesh is None:
        return
    settings = mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", settings)


def fix_collision(mesh):
    """Same fix as the garrison's import script -- raw AI exports have no
    simple collision, which defaults to per-triangle COMPLEX collision for
    every physics/overlap/trace query. A box is plenty for background props."""
    if mesh is None:
        return
    unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is not None:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)


def run():
    built = 0
    for filename, asset_name, target_height_cm, material_override in MODELS:
        mesh = safe(lambda f=filename, n=asset_name: import_model(f, n), f"import {filename}")
        if mesh is None:
            continue
        if material_override:
            safe(lambda m=mesh, mp=material_override: apply_material(m, mp), f"apply material override for {asset_name}")
        safe(lambda m=mesh: enable_nanite(m), f"enable Nanite for {asset_name}")
        safe(lambda m=mesh: fix_collision(m), f"fix collision for {asset_name}")
        safe(lambda m=mesh, n=asset_name, h=target_height_cm: check_height(m, n, h), f"check height for {asset_name}")
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        built += 1
    unreal.log(f"[M1 District AI Models] Imported {built}/{len(MODELS)} model(s) at {DEST_PATH}. Check any height-mismatch warnings above, then re-run build_m1_district.py to swap them in.")


run()
