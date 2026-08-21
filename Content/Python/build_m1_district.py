"""
M1 "LANDFALL" -- District blockout generator (beats 4.2-4.4: Dread/Burst/Aftermath)
=====================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
A one-shot Editor Python script that grey-boxes the Carrow district the M1
"LANDFALL" mission design doc (M1_LANDFALL_Mission_Design.md) calls for after
the garrison: the evacuation street (4.2 DREAD), the eruption + route-clearing
+ gun line + collapse sprint (4.3 BURST), and the 400m carry to the hospital
muster plus the sea-wall glimpse (4.4 AFTERMATH). It is the sibling script to
build_carrowgate_garrison.py, which deliberately stops at the garrison's Civic
Route exit and does NOT build this district (see that script's own docstring:
"this script does NOT place an active AIBKaijuSpawner in the garrison... the
district/kaiju action is out of scope of this script"). This is that district.

Same conventions as build_carrowgate_garrison.py on purpose -- same M=100
meters-to-uu scale, same load_mat_with_fallback AI-texture materials, same
spawn_block/prop_block/safe()/ROOT_FOLDER-cleanup pattern -- so anyone who has
read that script can read this one. Self-contained (does not import the other
script): copies/adapts the handful of helpers it needs instead of importing,
matching this project's existing one-shot-script convention (each Python
script in Content/Python/ already runs standalone via `py "path"`).

HOW TO RUN IT
-------------
1. File > New Level > Empty Level, Save As
   Content/LevelPrototyping/Lvl_M1_District (or wherever you want it -- the
   script just spawns into whatever level is currently open).
2. From the Output Log console (~): py "X:/IronBreach/Content/Python/build_m1_district.py"
   or the Python console tab: exec(open("X:/IronBreach/Content/Python/build_m1_district.py").read())
3. Press P to preview nav, Build > Build Paths, then Save Current Level.
4. Optional but recommended: run import_m1_district_ai_models.py AFTER
   generating the prop meshes it expects (see that script's docstring) --
   this script places placeholder boxes for every prop and swaps in the real
   mesh automatically if it's already been imported, same pattern as the
   garrison's truck/crane/ship swap.

Re-running is safe/idempotent: clears the "M1 District" outliner folder first.

LAYOUT NOTES
------------
Fresh level, fresh origin -- this is NOT the same coordinate space as the
garrison level. +X = deeper into the district, away from the garrison Civic
Route entry point (matches the garrison's own "+X = toward the coast" logic:
you keep walking the same direction you were already walking). +Y = toward
the sea wall / harbor side. Z=0 is street level throughout except where noted
(rubble piles, the stairwell interior, the sea-wall walkway are all close to
Z=0 -- this is street-grade district, not the garrison's multi-level platform).

The path is ~900m of X and jogs in Y at three points to give Ms. Idris's
turn-by-turn carry ("Left at the bakery... ") actual turns to call, per the
mission doc's §4.4 requirement that "the level design must make that last
stretch legible" without a HUD marker. Actual carry distance (CARRY_START to
HOSPITAL_MUSTER, summed over the real waypoint polyline) is computed and
logged at the bottom against the doc's 400m figure.

WHAT THIS SCRIPT DOES NOT DO
-----------------------------
- No PALAWAN mesh/animation, no Level Sequencer eruption cinematic, no crowd
  AI, no VO, no collapse VFX/Chaos destruction, no actual gameplay (carry
  input lock, deterrent flinch, extraction counting). Those are Blueprint /
  Sequencer / C++ work that a Python blockout script cannot respons­ibly fake
  its way through -- see Docs/M1_DISTRICT_BP_WIRING.md for the wiring plan
  and this doc's own §12 build notes for the honest cost ranking ("district
  block-out and its two collapse states, PALAWAN's animation set, Idris VO +
  facial performance, crowd polish" -- in that order of cost).
- PALAWAN itself is placed as ROUTE MARKERS (small tagged spheres, one per
  key point of its drift from eruption to calcified) plus a distant
  placeholder silhouette at the eruption point if BP_Kaiju_Palawan exists in
  this checkout, mirroring add_distant_palawan() in the garrison script. A
  real spline component needs a Blueprint actor class (see the wiring doc) --
  this script can't safely fabricate one from a bare Python actor spawn.
- Two collapse states (pre-eruption intact district / post-eruption rubble)
  are noted as a TODO per zone rather than built twice -- this script builds
  the POST-collapse geometry throughout (what the player actually plays
  through in 4.3-4.4), since that is the traversal-critical one. Building a
  fully intact pre-eruption version of every block for a ~90-second scripted
  collapse sequence is real content work, flagged, not attempted here.
"""

import math
import unreal

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

M = 100.0  # meters -> Unreal units (cm)
ROOT_FOLDER = "M1 District"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
SPHERE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere.Sphere")

if CUBE_MESH is None:
    unreal.log_error("[M1 District] Could not load /Engine/BasicShapes/Cube.Cube -- aborting.")
    raise SystemExit

CHAMFER_MESH = unreal.EditorAssetLibrary.load_asset("/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube")
if CHAMFER_MESH is None:
    unreal.log_warning("[M1 District] SM_ChamferCube not found -- ground pads will keep sharp cube edges.")


def load_mat(path):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if mat is None:
        unreal.log_warning(f"[M1 District] Material not found at '{path}' -- affected meshes keep engine default grey.")
    return mat


def load_mat_with_fallback(primary_path, fallback_path, label):
    mat = unreal.EditorAssetLibrary.load_asset(primary_path)
    if mat is not None:
        return mat
    unreal.log_warning(f"[M1 District] {label} not found at '{primary_path}' -- run import_ai_textures.py first (it's the garrison's, this district reuses the same materials). Falling back.")
    return load_mat(fallback_path) if fallback_path else None


# Reuses the SAME AI-texture materials the garrison built -- one texture set
# for the whole game's blockout pass rather than a second district-specific
# set, per the mission doc's own minimal-footprint spirit for M1.
MAT_WALL = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Wall.M_AI_Wall",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray", "M_AI_Wall")
MAT_GROUND = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark", "M_AI_Ground")
MAT_RAMP = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Ramp.M_AI_Ramp",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_02.MI_PrototypeGrid_Gray_02", "M_AI_Ramp")
MAT_FURNITURE = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Furniture.M_AI_Furniture",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_Round.MI_PrototypeGrid_Gray_Round", "M_AI_Furniture")
MAT_FLATCOL_BASE = load_mat("/Game/LevelPrototyping/Materials/M_FlatCol.M_FlatCol")
MAT_VEHICLE = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Vehicle.M_AI_Vehicle", None, "M_AI_Vehicle") or MAT_FURNITURE
MAT_GLASS = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Glass.M_AI_Glass", None, "M_AI_Glass") or MAT_FLATCOL_BASE


def safe(fn, label):
    try:
        fn()
    except Exception as e:  # noqa: BLE001 -- one-shot editor tool, keep going on failure
        unreal.log_warning(f"[M1 District] Skipped '{label}': {e}")


def cleanup_previous_run():
    removed = 0
    for a in actor_subsystem.get_all_level_actors():
        try:
            folder = str(a.get_folder_path())
        except Exception:
            continue
        if folder == ROOT_FOLDER or folder.startswith(ROOT_FOLDER + "/"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        unreal.log(f"[M1 District] Cleared {removed} actor(s) from a previous run before rebuilding.")


safe(cleanup_previous_run, "Cleanup previous run")


# ---------------------------------------------------------------------------
# Core placement helpers (adapted from build_carrowgate_garrison.py)
# ---------------------------------------------------------------------------

def spawn_block(label, folder, location_m, size_m, rotation_deg=(0.0, 0.0, 0.0), material=MAT_WALL, mesh=None):
    """location_m is the box CENTER in meters. mesh defaults to the sharp engine cube;
    pass mesh=CHAMFER_MESH for bevelled ground pads."""
    location = unreal.Vector(location_m[0] * M, location_m[1] * M, location_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh if mesh is not None else CUBE_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def spawn_mesh_actor(label, folder, asset_path, loc_m, rotation_deg=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), material=None):
    """Places a real imported mesh (e.g. via import_m1_district_ai_models.py) if it
    exists at asset_path; returns None otherwise so callers fall back to a placeholder."""
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if mesh is None:
        return None
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def prop_block(label, folder, loc_m, size_m, rot_z=0.0, material=MAT_FURNITURE):
    """Convenience wrapper for a single placeholder prop box, center-pivoted."""
    return spawn_block(label, folder, loc_m, size_m, (0.0, 0.0, rot_z), material=material)


def real_or_placeholder(label, folder, asset_path, loc_m, placeholder_size_m, rot_z=0.0,
                         material=MAT_FURNITURE, real_scale=(1.0, 1.0, 1.0)):
    """The garrison script's swap pattern: try the real AI-generated mesh first (dropped
    in by import_m1_district_ai_models.py), fall back to a labeled placeholder box."""
    real = spawn_mesh_actor(label, folder, asset_path, loc_m, (0.0, 0.0, rot_z), real_scale, material=None)
    if real is not None:
        return real
    return prop_block(label, folder, loc_m, placeholder_size_m, rot_z, material=material)


def tag_actor(actor, *tags):
    if actor is None:
        return
    for t in tags:
        actor.tags.append(unreal.Name(t))


def spawn_trigger(label, folder, loc_m, size_m, tag):
    """A TriggerBox marking a checkpoint / extraction-muster / beat-boundary volume.
    No logic lives here -- BP_ level scripting (or a future C++ hook) reads these by
    tag. See Docs/M1_DISTRICT_BP_WIRING.md."""
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    trigger = actor_subsystem.spawn_actor_from_class(unreal.TriggerBox, location, unreal.Rotator(0, 0, 0))
    trigger.set_actor_label(label)
    trigger.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    box = trigger.get_component_by_class(unreal.BoxComponent)
    if box is not None:
        box.set_box_extent(unreal.Vector(size_m[0] * M / 2.0, size_m[1] * M / 2.0, size_m[2] * M / 2.0))
    tag_actor(trigger, tag)
    return trigger


def spawn_marker(label, folder, loc_m, tag, radius_m=0.5, color=(1.0, 0.2, 0.2)):
    """A small tagged sphere marking a point of interest that has no geometry of its
    own yet -- PALAWAN route points, the Idris-found spot, the calcification pose,
    the naming-beat mark, etc. Cheap, visible in the editor, greppable by tag."""
    actor = prop_block(label, folder, loc_m, (radius_m * 2, radius_m * 2, radius_m * 2), material=MAT_FLATCOL_BASE)
    actor.static_mesh_component.set_static_mesh(SPHERE_MESH if SPHERE_MESH is not None else CUBE_MESH)
    if MAT_FLATCOL_BASE is not None:
        try:
            mid = unreal.MaterialInstanceDynamic.create(MAT_FLATCOL_BASE, actor)
            mid.set_vector_parameter_value("Color", unreal.LinearColor(color[0], color[1], color[2], 1.0))
            actor.static_mesh_component.set_material(0, mid)
        except Exception:
            pass  # M_FlatCol's parameter name may differ -- cosmetic only, not fatal
    tag_actor(actor, tag)
    return actor


# ---------------------------------------------------------------------------
# Glow-vein material -- a small self-contained material build, same pattern
# as build_glass_material.py (Constant3Vector -> Emissive). Static color, not
# animated/pulsing -- "good enough for a blockout pass," per that script's
# own stated bar. A Niagara/parameter-driven pulse is a later pass.
# ---------------------------------------------------------------------------

def build_glow_vein_material():
    path_dir = "/Game/LevelPrototyping/AITextures"
    name = "M_AI_GlowVein"
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    full_path = f"{path_dir}/{name}.{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        material = unreal.EditorAssetLibrary.load_asset(full_path)
        mel.delete_all_material_expressions(material)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(name, path_dir, unreal.Material, factory)
    if material is None:
        unreal.log_error("[M1 District] Could not create/load M_AI_GlowVein.")
        return None

    emissive_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, -100)
    emissive_color.set_editor_property("constant", unreal.LinearColor(0.55, 1.0, 0.35, 1.0))  # gold-green
    emissive_mult = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -250, -100)
    emissive_mult.set_editor_property("const_b", 6.0)  # bloom-catching brightness, tune in-editor
    mel.connect_material_expressions(emissive_color, "", emissive_mult, "A")
    mel.connect_material_property(emissive_mult, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    base_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, 100)
    base_color.set_editor_property("constant", unreal.LinearColor(0.05, 0.08, 0.05, 1.0))
    mel.connect_material_property(base_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


MAT_GLOWVEIN = safe(build_glow_vein_material, "Glow-vein material") or MAT_FLATCOL_BASE
if MAT_GLOWVEIN is None:
    MAT_GLOWVEIN = MAT_FLATCOL_BASE


# ---------------------------------------------------------------------------
# 4.2 DREAD -- "The Birds Are Gone" (~X=0 to X=150)
# Evac street: rowhouse facades, buses loading, wardens, escalation ladder
# (birdless sky is audio-only -- nothing to block out; dogs-gone-silent gets
# a K9 marker; glow-veins get visible strips, brightening toward X=150).
# ---------------------------------------------------------------------------

DREAD_START_X = 0.0
DREAD_END_X = 150.0
STREET_WIDTH = 14.0
FACADE_HEIGHT = 9.0
FACADE_DEPTH = 1.0


def add_street_pad(label, folder, x0, x1, y_center=0.0, width=STREET_WIDTH, material=MAT_GROUND):
    length = x1 - x0
    cx = (x0 + x1) / 2.0
    spawn_block(label, folder, (cx, y_center, 0.0), (length, width, 0.3), material=material, mesh=CHAMFER_MESH)


def add_facade_row(folder, x0, x1, side_y, spacing=12.0, gap_prob_every=3):
    """side_y is the row's centerline Y (facades face the street). Places a
    repeating row of flat building-front slabs -- NOT enterable, this is street
    dressing, not the garrison's hollow rooms. Every `gap_prob_every`-th slot is
    left open (an alley/gap) instead of a facade, for visual variety."""
    n = max(1, int((x1 - x0) / spacing))
    for i in range(n):
        cx = x0 + spacing * (i + 0.5)
        if (i + 1) % gap_prob_every == 0:
            continue
        spawn_block(f"Facade_{folder}_{i:02d}", folder, (cx, side_y, FACADE_HEIGHT / 2.0),
                    (spacing * 0.9, FACADE_DEPTH, FACADE_HEIGHT), material=MAT_WALL)
        # A dark window cutout suggestion (a glass-material slab set back slightly)
        spawn_block(f"Facade_{folder}_{i:02d}_Window", folder,
                    (cx, side_y + (FACADE_DEPTH * 0.6 if side_y > 0 else -FACADE_DEPTH * 0.6), FACADE_HEIGHT * 0.6),
                    (spacing * 0.5, 0.1, FACADE_HEIGHT * 0.25), material=MAT_GLASS)


def add_dread_beat():
    folder = "4.2 Dread - Evac Street"
    add_street_pad("Dread_Street_Pad", folder, DREAD_START_X - 10, DREAD_END_X + 10)
    add_facade_row(folder, DREAD_START_X, DREAD_END_X, STREET_WIDTH / 2.0 + 1.0)
    add_facade_row(folder, DREAD_START_X, DREAD_END_X, -(STREET_WIDTH / 2.0 + 1.0))

    # 3 evac buses loading along the street -- placeholder boxes swapped for a
    # real mesh by import_m1_district_ai_models.py (SM_EvacBus).
    bus_xs = [30.0, 75.0, 120.0]
    for i, bx in enumerate(bus_xs):
        real_or_placeholder(f"EvacBus_{i+1:02d}", folder, "/Game/M1_District/AIModels/SM_EvacBus.SM_EvacBus",
                             (bx, -(STREET_WIDTH / 2.0 - 2.0), 0.0), (9.0, 2.6, 3.0), rot_z=0.0,
                             material=MAT_VEHICLE, real_scale=(1.0, 1.0, 1.0))
        # Extraction-counter muster trigger at each bus -- HUD's civilians-extracted
        # counter first ticks up here (mechanic taught low-stakes, per §6 of the doc).
        spawn_trigger(f"ExtractionMuster_Bus_{i+1:02d}", folder, (bx, -(STREET_WIDTH / 2.0 - 2.0), 1.0),
                      (4.0, 4.0, 3.0), "ExtractionMuster")

    # K9 unit refusing to work -- escalation beat 2, a simple marker (no dog AI here).
    spawn_marker("K9_RefusesToWork_Marker", folder, (55.0, 4.0, 0.4), "Escalation_DogsGoneSilent", color=(0.9, 0.7, 0.2))

    # Glow-vein filament strips in the road seams, brightening block by block
    # toward the eruption (escalation beat 3). Thin emissive strips, sparser
    # early, denser near the end.
    n_strips = 10
    for i in range(n_strips):
        t = i / (n_strips - 1)
        x = DREAD_START_X + t * (DREAD_END_X - DREAD_START_X)
        width = 0.15 + 0.35 * t  # thin early, wider (more "arterial") near the end
        spawn_block(f"GlowVein_{i:02d}", folder, (x, 0.0, 0.06), (3.0, width, 0.02), material=MAT_GLOWVEIN)
    # "The flowers" child-reaches-for-a-vein beat marker, ~2/3 down the street.
    spawn_marker("ChildReachesForVein_Marker", folder, (DREAD_START_X + (DREAD_END_X - DREAD_START_X) * 0.66, 1.5, 0.4),
                 "Escalation_TheFlowers", color=(0.55, 1.0, 0.35))

    # PlayerStart for testing this beat in isolation (Checkpoint 1 -- also see
    # Docs/M1_DISTRICT_BP_WIRING.md for the level-transition volume that should
    # sit here, matching the garrison's Civic Route exit).
    ps = actor_subsystem.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(DREAD_START_X * M, 0, 1 * M), unreal.Rotator(0, 0, 0))
    ps.set_actor_label("PlayerStart_Dread")
    ps.set_folder_path(f"{ROOT_FOLDER}/{folder}")

    spawn_trigger("Checkpoint_Dread", folder, (DREAD_START_X, 0.0, 1.5), (3.0, STREET_WIDTH, 3.0), "Checkpoint")
    spawn_trigger("Checkpoint_Burst_RoadLifts", folder, (DREAD_END_X, 0.0, 1.5), (3.0, STREET_WIDTH, 3.0), "Checkpoint")


safe(add_dread_beat, "4.2 Dread beat")


# ---------------------------------------------------------------------------
# 4.3 BURST -- eruption, route clearing, gun line, collapse sprint
# (~X=150 to X=480)
# ---------------------------------------------------------------------------

ERUPTION_X = 210.0


def add_rubble_cluster(label, folder, loc_m, spread_m=6.0, count=5, material=MAT_WALL):
    """A handful of jumbled cube chunks -- the project's go-to for 'collapsed
    building' without hand-authoring debris meshes, same spirit as the garrison's
    placeholder-box philosophy."""
    for i in range(count):
        ang = (i / count) * math.tau + (hash(label) % 100) * 0.01
        r = spread_m * (0.3 + 0.7 * ((i * 37) % 100) / 100.0)
        dx, dy = math.cos(ang) * r, math.sin(ang) * r
        size = 1.2 + ((i * 53) % 100) / 100.0 * 2.5
        rot = (((i * 71) % 360), ((i * 113) % 360), ((i * 29) % 360))
        spawn_block(f"{label}_{i:02d}", folder, (loc_m[0] + dx, loc_m[1] + dy, loc_m[2] + size / 2.0),
                    (size, size, size), rotation_deg=rot, material=material)


def add_eruption_zone():
    folder = "4.3a Burst - Eruption Crater"
    # Crater lip -- a sunken ground pad reading as ground that just swelled/tore.
    spawn_block("Crater_Floor", folder, (ERUPTION_X, 0.0, -1.5), (40.0, 30.0, 0.3), material=MAT_GROUND, mesh=CHAMFER_MESH)
    for ring_i, (radius, count) in enumerate([(10, 6), (16, 10)]):
        for i in range(count):
            ang = (i / count) * math.tau
            spawn_block(f"CraterLip_{ring_i}_{i:02d}", folder,
                        (ERUPTION_X + math.cos(ang) * radius, math.sin(ang) * radius * 0.75, -0.5 + ring_i * 0.3),
                        (4.0, 4.0, 1.0 + ring_i * 0.5), rotation_deg=(0, 0, math.degrees(ang)), material=MAT_GROUND)
    add_rubble_cluster("Eruption_CollapsedBlock", folder, (ERUPTION_X - 8, 12, 0), spread_m=10, count=8)
    add_rubble_cluster("Eruption_CollapsedBlock_B", folder, (ERUPTION_X + 10, -14, 0), spread_m=9, count=7)

    # PALAWAN: not placed as a fightable actor (mission design LOCKED: no combat
    # AI, no health, no targeting -- see this script's own header + the wiring
    # doc). Placed here as a distant silhouette IF BP_Kaiju_Palawan already
    # exists in this checkout (mirrors add_distant_palawan() in the garrison
    # script), plus a chain of tagged route markers tracing its scripted drift
    # from surfacing here to calcifying two blocks short of the hospital -- see
    # PALAWAN_ROUTE below. A real BP_Palawan_Scripted spline actor should read
    # these marker locations when it's built (Docs/M1_DISTRICT_BP_WIRING.md).
    bp_asset_path = "/Game/Kaiju/BP_Kaiju_Palawan"
    palawan_class = None
    if unreal.EditorAssetLibrary.does_asset_exist(bp_asset_path):
        palawan_class = unreal.EditorAssetLibrary.load_blueprint_class(bp_asset_path)
    if palawan_class is not None:
        silhouette = actor_subsystem.spawn_actor_from_class(
            palawan_class, unreal.Vector(ERUPTION_X * M, 0, 0), unreal.Rotator(0, 0, 0))
        silhouette.set_actor_label("PALAWAN_EruptionSilhouette")
        silhouette.set_folder_path(f"{ROOT_FOLDER}/{folder}")
        unreal.log_warning(
            "[M1 District] Placed BP_Kaiju_Palawan at the eruption point for silhouette/scale "
            "reference ONLY -- it is the fightable AIBCharacter_Kaiju class (health/armor/organs). "
            "M1's PALAWAN must be non-combat per the mission design (LOCKED). Do not leave this "
            "actor in the shipped level as-is -- either strip its combat components in a level-only "
            "BP child, or (recommended) replace with a dedicated BP_Palawan_Scripted per the wiring doc."
        )
    else:
        unreal.log_warning(
            "[M1 District] BP_Kaiju_Palawan not found at /Game/Kaiju/ -- skipping the eruption "
            "silhouette placeholder. See Docs/M1_DISTRICT_BP_WIRING.md for building the real, "
            "non-combat BP_Palawan_Scripted actor this beat actually needs."
        )
    spawn_trigger("Checkpoint_Burst_Eruption", folder, (ERUPTION_X, 0.0, 1.5), (3.0, 30.0, 3.0), "Checkpoint")


safe(add_eruption_zone, "4.3a Eruption crater")

# PALAWAN's scripted drift, eruption -> two blocks short of the hospital,
# calcified. Points are hand-placed along/near the player's own path so the
# creature reads as present without ever being an obstacle. Distances are
# approximate district geography, not precision blocking.
PALAWAN_ROUTE = [
    (ERUPTION_X, 0.0, "Surfaces"),
    (ERUPTION_X + 60, -40.0, "Moving off, indifferent, on its own line"),
    (ERUPTION_X + 140, -20.0, "Crosses behind the gun line at range (deterrent-flinch redirects, never stops it)"),
    (480.0, 90.0, "Slows"),
    (580.0, 160.0, "Calcified -- two blocks short of the hospital"),
]


def add_palawan_route_markers():
    folder = "4.3a Burst - Eruption Crater/PALAWAN Route"
    for i, (x, y, note) in enumerate(PALAWAN_ROUTE):
        m = spawn_marker(f"PALAWAN_Route_{i:02d}_{note[:24].replace(' ', '_')}", folder, (x, y, 0.5),
                          "PALAWAN_RoutePoint", radius_m=1.0, color=(0.6, 0.1, 0.1))
        unreal.log(f"[M1 District] PALAWAN route point {i}: ({x:.0f}, {y:.0f}) -- {note}")


safe(add_palawan_route_markers, "PALAWAN route markers")


def add_route_clearing():
    """Three route-clearing micro-obstacles between the eruption and the gun
    line -- shoot to open paths, not to wound, per §4.3 encounter flow."""
    folder = "4.3b Burst - Route Clearing"
    add_street_pad("RouteClear_Street_Pad", folder, ERUPTION_X + 20, ERUPTION_X + 110, y_center=0.0, width=16.0)
    add_rubble_cluster("RouteClear_Rubble_A", folder, (ERUPTION_X + 35, 8, 0), spread_m=6, count=5)
    add_rubble_cluster("RouteClear_Rubble_B", folder, (ERUPTION_X + 70, -8, 0), spread_m=6, count=5)

    # 1. Snagged cable-stay / fire escape -- a diagonal blockage the player
    # shoots to drop as a bridge-ramp.
    cable_x = ERUPTION_X + 35
    spawn_block("CableStay_Blockage", folder, (cable_x, 0.0, 4.0), (0.3, 10.0, 0.3), rotation_deg=(0, 35, 0), material=MAT_VEHICLE)
    spawn_trigger("CableStay_ShootTarget", folder, (cable_x, 0.0, 6.5), (1.0, 1.0, 1.0), "Interactable_ShootToClear")

    # 2. Demo-charge facade (Bricks places it) -- a wall segment that drops
    # when shot / detonated.
    demo_x = ERUPTION_X + 65
    spawn_block("DemoCharge_Facade", folder, (demo_x, -6.0, 4.5), (0.5, 8.0, 9.0), material=MAT_WALL)
    spawn_trigger("DemoCharge_ShootTarget", folder, (demo_x, -6.0, 4.5), (1.0, 1.0, 1.0), "Interactable_ShootToClear")
    spawn_marker("Bricks_PlacesCharge_Marker", folder, (demo_x - 1.5, -6.0, 0.5), "NPC_Marker_Bricks", color=(0.8, 0.6, 0.2))

    # 3. Gas/spark valve -- called shots on valves suppresses hazard.
    valve_x = ERUPTION_X + 95
    spawn_block("GasValve_Panel", folder, (valve_x, 5.0, 1.5), (1.5, 0.3, 1.5), material=MAT_VEHICLE)
    spawn_trigger("GasValve_ShootTarget", folder, (valve_x, 5.0, 1.5), (1.0, 1.0, 1.0), "Interactable_ShootToClear")

    spawn_trigger("Checkpoint_Burst_MidPoint", folder, (ERUPTION_X + 110, 0.0, 1.5), (3.0, 16.0, 3.0), "Checkpoint")


safe(add_route_clearing, "4.3b Route clearing")


GUN_LINE_X = 360.0


def add_gun_line():
    """Sea-wall deterrent battery: the honest-ceiling beat. Bellringer acoustic
    pieces + the garrison's siege gun, both placeholder structures pending real
    hardware meshes."""
    folder = "4.3c Burst - Gun Line"
    add_street_pad("GunLine_Approach_Pad", folder, ERUPTION_X + 110, GUN_LINE_X + 20, y_center=10.0, width=18.0)

    # Sea wall itself: a long low barrier the battery sits on, +Y side.
    spawn_block("SeaWall_Barrier", folder, (GUN_LINE_X, 26.0, 1.5), (40.0, 2.0, 3.0), material=MAT_WALL)

    # Two Bellringer acoustic emplacements -- the "ringing" weapon that makes
    # PALAWAN's limb flinch once per hit, never damage.
    for i, bx in enumerate([GUN_LINE_X - 10, GUN_LINE_X + 10]):
        real_or_placeholder(f"Bellringer_Emplacement_{i+1:02d}", folder,
                             f"/Game/M1_District/AIModels/SM_DeterrentEmplacement.SM_DeterrentEmplacement",
                             (bx, 24.0, 0.0), (3.0, 3.0, 4.5), rot_z=180.0, material=MAT_VEHICLE)
        spawn_trigger(f"Bellringer_HitVolume_{i+1:02d}", folder, (bx, 22.0, 3.0), (2.0, 2.0, 3.0), "DeterrentBattery_HitVolume")

    # The siege gun -- fires, accomplishes nothing but noise and spall.
    real_or_placeholder("SiegeGun", folder, "/Game/M1_District/AIModels/SM_SiegeGun.SM_SiegeGun",
                         (GUN_LINE_X, 20.0, 0.0), (4.0, 6.0, 3.5), rot_z=180.0, material=MAT_VEHICLE)

    # Chokepoint geometry: rubble narrows the convoy route right past the
    # battery, so this is where PALAWAN's flinch actually buys the seconds.
    spawn_block("Chokepoint_Wall_West", folder, (GUN_LINE_X - 4, 2.0, 2.0), (3.0, 0.6, 4.0), material=MAT_WALL)
    spawn_block("Chokepoint_Wall_East", folder, (GUN_LINE_X + 4, -2.0, 2.0), (3.0, 0.6, 4.0), material=MAT_WALL)
    spawn_trigger("ExtractionMuster_Convoy_GunLine", folder, (GUN_LINE_X, 0.0, 1.0), (6.0, 8.0, 3.0), "ExtractionMuster")

    spawn_trigger("Checkpoint_Burst_GunLine", folder, (GUN_LINE_X + 20, 10.0, 1.5), (3.0, 18.0, 3.0), "Checkpoint")


safe(add_gun_line, "4.3c Gun line")


COLLAPSE_START_X = GUN_LINE_X + 40  # 400
COLLAPSE_END_X = COLLAPSE_START_X + 80  # 480
NEARMISS_X = (COLLAPSE_START_X + COLLAPSE_END_X) / 2.0


def add_collapse_sprint():
    """Sprint/slide/mantle traversal through a falling street. Ramps + gaps +
    mantle-height ledges rather than a flat pad -- this is the one stretch that
    most needs real hand-tuning once it's walkable; treat these as a first pass."""
    folder = "4.3d Burst - Collapse Sprint"
    add_street_pad("CollapseSprint_Pad", folder, COLLAPSE_START_X - 5, COLLAPSE_END_X + 5, width=12.0)

    # Alternating debris to mantle over + gaps to slide under, every ~15m.
    n = 5
    for i in range(n):
        x = COLLAPSE_START_X + (i + 0.5) * ((COLLAPSE_END_X - COLLAPSE_START_X) / n)
        if i % 2 == 0:
            spawn_block(f"MantleLedge_{i:02d}", folder, (x, 2.0, 0.6), (3.0, 4.0, 1.2), material=MAT_WALL)
        else:
            spawn_block(f"SlideGap_LowBeam_{i:02d}", folder, (x, -2.0, 2.3), (3.0, 4.0, 0.4), material=MAT_WALL)
        add_rubble_cluster(f"CollapseSprint_Rubble_{i:02d}", folder, (x, 0.0, 0.0), spread_m=4, count=3)

    # Scripted near-miss: a limb comes down a full block away, pressure wave
    # knocks the fireteam flat. Marker for the sequencer beat + a floor decal
    # footprint (a big flattened cylinder-ish cube) suggesting the impact.
    spawn_block("NearMiss_ImpactMark", folder, (NEARMISS_X + 12, -18.0, 0.05), (10.0, 10.0, 0.1), material=MAT_GROUND)
    spawn_marker("NearMiss_PressureWave_Marker", folder, (NEARMISS_X, 0.0, 1.0), "Scripted_PressureWave", color=(0.8, 0.3, 0.1))

    spawn_trigger("Checkpoint_Burst_CollapseSprint_End", folder, (COLLAPSE_END_X, 0.0, 1.5), (3.0, 12.0, 3.0), "Checkpoint")
    spawn_marker("SquadSplits_Marker", folder, (COLLAPSE_END_X + 5, 0.0, 1.0), "Beat_SquadSplits")


safe(add_collapse_sprint, "4.3d Collapse sprint")


# ---------------------------------------------------------------------------
# 4.4 AFTERMATH -- the stairwell, the 400m carry, hospital muster, sea wall
# ---------------------------------------------------------------------------

STAIRWELL_X = COLLAPSE_END_X + 20  # 500
STAIRWELL_Y = -25.0


def add_stairwell_room():
    """The one enterable interior in this level -- collapsed stairwell where
    Idris is pinned. Small hollow room, hand-built (not the garrison's
    spawn_room helper, to keep this script self-contained) since it's a single
    one-off space, not a repeated building type."""
    folder = "4.4a Aftermath - Stairwell"
    cx, cy = STAIRWELL_X, STAIRWELL_Y
    w, d, h = 6.0, 6.0, 5.0
    wt = 0.3
    # Floor
    spawn_block("Stairwell_Floor", folder, (cx, cy, -wt / 2.0), (w, d, wt), material=MAT_GROUND, mesh=CHAMFER_MESH)
    # Walls (north/south/east solid, west has the doorway gap back to the street)
    spawn_block("Stairwell_Wall_N", folder, (cx, cy + d / 2.0, h / 2.0), (w, wt, h), material=MAT_WALL)
    spawn_block("Stairwell_Wall_S", folder, (cx, cy - d / 2.0, h / 2.0), (w, wt, h), material=MAT_WALL)
    spawn_block("Stairwell_Wall_E", folder, (cx + w / 2.0, cy, h / 2.0), (wt, d, h), material=MAT_WALL)
    # Partial west wall either side of the doorway gap (2m opening, centered)
    gap = 2.0
    side_len = (d - gap) / 2.0
    spawn_block("Stairwell_Wall_W_A", folder, (cx - w / 2.0, cy + gap / 2.0 + side_len / 2.0, h / 2.0),
                (wt, side_len, h), material=MAT_WALL)
    spawn_block("Stairwell_Wall_W_B", folder, (cx - w / 2.0, cy - gap / 2.0 - side_len / 2.0, h / 2.0),
                (wt, side_len, h), material=MAT_WALL)
    # Partially-collapsed ceiling -- one slab knocked askew, matching "pinned in
    # a stairwell" rather than a clean intact room.
    spawn_block("Stairwell_Ceiling_Intact", folder, (cx, cy - d / 4.0, h), (w, d / 2.0, 0.3), material=MAT_WALL)
    spawn_block("Stairwell_Ceiling_Collapsed", folder, (cx + 0.5, cy + d / 4.0, h * 0.75),
                (w, d / 2.0, 0.3), rotation_deg=(20, 0, 3), material=MAT_WALL)
    add_rubble_cluster("Stairwell_Rubble", folder, (cx + 0.5, cy + 1.0, 0.0), spread_m=2.0, count=4)

    # Idris found here.
    spawn_marker("Idris_Found_Marker", folder, (cx, cy, 0.5), "Beat_IdrisFound", color=(0.9, 0.85, 0.6))

    # Short connector from the collapse sprint's end to this room's doorway.
    spawn_block("Stairwell_Connector_Pad", folder, ((COLLAPSE_END_X + STAIRWELL_X) / 2.0, (0 + STAIRWELL_Y) / 2.0, -0.05),
                (20.0, 8.0, 0.1), material=MAT_GROUND, mesh=CHAMFER_MESH)


safe(add_stairwell_room, "4.4a Stairwell")


# The carry: a hand-authored polyline (not a straight line) so Ms. Idris's
# turn-by-turn VO has real turns to call, and so the final 100m plays legibly
# without a HUD marker (the level geometry itself has to funnel the player).
CARRY_WAYPOINTS = [
    (STAIRWELL_X, STAIRWELL_Y, "CARRY_START -- out of the stairwell, into the dust"),
    (STAIRWELL_X + 60, STAIRWELL_Y, "Straight run past a collapsed shopfront"),
    (STAIRWELL_X + 60, STAIRWELL_Y + 65, "TURN 1 -- \"Left at the bakery, love\" (bakery landmark here, awning down)"),
    (STAIRWELL_X + 20, STAIRWELL_Y + 65, "Short dogleg past the bakery frontage"),
    (STAIRWELL_X + 20, STAIRWELL_Y + 130, "TURN 2 -- toward her sister's flat; she talks about the early shift"),
    (STAIRWELL_X + 90, STAIRWELL_Y + 130, "SHE STOPS -- mid-street, no sting, dust keeps falling (~2/3 of the carry)"),
    (STAIRWELL_X + 90, STAIRWELL_Y + 200, "TURN 3 -- last 100m, SILENT, no guide. Geometry alone must read this turn."),
    (STAIRWELL_X + 20, STAIRWELL_Y + 245, "Final approach -- hospital muster ahead, visible"),
]
HOSPITAL_MUSTER_LOC = (STAIRWELL_X + 20, STAIRWELL_Y + 260, "HOSPITAL MUSTER")


def carry_polyline_length_m(points):
    total = 0.0
    for i in range(1, len(points)):
        x0, y0 = points[i - 1][0], points[i - 1][1]
        x1, y1 = points[i][0], points[i][1]
        total += math.hypot(x1 - x0, y1 - y0)
    total += math.hypot(HOSPITAL_MUSTER_LOC[0] - points[-1][0], HOSPITAL_MUSTER_LOC[1] - points[-1][1])
    return total


def add_carry_route():
    folder = "4.4b Aftermath - The Carry"
    # Street pad following each leg of the polyline.
    all_points = [(p[0], p[1]) for p in CARRY_WAYPOINTS] + [(HOSPITAL_MUSTER_LOC[0], HOSPITAL_MUSTER_LOC[1])]
    for i in range(1, len(all_points)):
        x0, y0 = all_points[i - 1]
        x1, y1 = all_points[i]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        length = math.hypot(x1 - x0, y1 - y0)
        yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
        spawn_block(f"Carry_Pad_{i:02d}", folder, (cx, cy, -0.05), (length + 6.0, 10.0, 0.1),
                    rotation_deg=(0, 0, yaw), material=MAT_GROUND, mesh=CHAMFER_MESH)
        # Loose facade dressing along the outer edge, sparse (this is dust/rubble
        # street, not the dread beat's intact rowhouses).
        add_rubble_cluster(f"Carry_Debris_{i:02d}", folder, (cx, cy, 0.0), spread_m=4.0, count=2)

    # Landmarks called out in Ms. Idris's VO -- placed at the turns.
    bakery_pt = CARRY_WAYPOINTS[2]
    real_or_placeholder("Bakery_Landmark", folder, "/Game/M1_District/AIModels/SM_BakerySign.SM_BakerySign",
                         (bakery_pt[0] + 3, bakery_pt[1], 0.0), (2.0, 0.3, 2.5), rot_z=90.0, material=MAT_FURNITURE)
    spawn_marker("Bakery_Awning_Down_Marker", folder, (bakery_pt[0] + 3, bakery_pt[1] + 1, 1.5), "Landmark_Bakery", color=(0.7, 0.5, 0.2))

    sister_pt = CARRY_WAYPOINTS[4]
    spawn_marker("SistersFlat_Marker", folder, (sister_pt[0] - 3, sister_pt[1], 1.5), "Landmark_SistersFlat", color=(0.6, 0.6, 0.8))

    stops_pt = CARRY_WAYPOINTS[5]
    spawn_marker("Idris_Stops_Marker", folder, (stops_pt[0], stops_pt[1], 0.5), "Beat_IdrisStops", color=(0.9, 0.85, 0.6))

    for i, (x, y, note) in enumerate(CARRY_WAYPOINTS):
        unreal.log(f"[M1 District] Carry waypoint {i}: ({x:.0f}, {y:.0f}) -- {note}")

    total_len = carry_polyline_length_m(CARRY_WAYPOINTS)
    unreal.log(f"[M1 District] Carry route total length: {total_len:.0f}m (design doc target: 400m; nudge waypoints above to tune).")


safe(add_carry_route, "4.4b The carry")


def add_hospital_muster():
    folder = "4.4c Aftermath - Hospital Muster"
    hx, hy = HOSPITAL_MUSTER_LOC[0], HOSPITAL_MUSTER_LOC[1]
    spawn_block("Muster_Plaza_Pad", folder, (hx, hy, -0.05), (30.0, 30.0, 0.1), material=MAT_GROUND, mesh=CHAMFER_MESH)
    # Hospital facade (backdrop, not enterable -- this beat plays in the forecourt).
    spawn_block("Hospital_Facade", folder, (hx, hy + 16.0, 6.0), (26.0, 1.0, 12.0), material=MAT_WALL)
    for wx in (-9.0, -3.0, 3.0, 9.0):
        spawn_block(f"Hospital_Facade_Window_{wx}", folder, (hx + wx, hy + 15.3, 5.0), (2.0, 0.1, 6.0), material=MAT_GLASS)

    real_or_placeholder("Stretcher", folder, "/Game/M1_District/AIModels/SM_Stretcher.SM_Stretcher",
                         (hx, hy - 2.0, 0.0), (2.0, 0.7, 0.5), rot_z=0.0, material=MAT_FURNITURE)
    spawn_marker("Naming_Beat_Marker", folder, (hx, hy - 2.0, 1.5), "Beat_Naming", color=(0.9, 0.85, 0.4))

    # Extraction counter should finish incrementing around here -- last convoy
    # clearing the chokepoint plus stragglers reaching this plaza.
    spawn_trigger("ExtractionMuster_Hospital", folder, (hx, hy, 1.0), (14.0, 10.0, 3.0), "ExtractionMuster")
    spawn_trigger("Checkpoint_Aftermath_HospitalMuster", folder, (hx, hy - 12.0, 1.5), (12.0, 3.0, 3.0), "Checkpoint")

    # Mission-end title card location, per §4.4.
    spawn_marker("MissionEnd_TitleCard_Marker", folder, (hx, hy, 3.0), "Beat_MissionEnd", color=(1.0, 1.0, 1.0))


safe(add_hospital_muster, "4.4c Hospital muster")


def add_seawall_glimpse():
    """Short spur off the muster plaza -- the walk back at first light, the
    kneeling Caryatid/frame tableau and the tide-mark ring."""
    folder = "4.4d Aftermath - Sea Wall Glimpse"
    hx, hy = HOSPITAL_MUSTER_LOC[0], HOSPITAL_MUSTER_LOC[1]
    sx, sy = hx, hy + 70.0
    spawn_block("SeaWall_Spur_Pad", folder, (hx, (hy + sy) / 2.0, -0.05), (10.0, 70.0, 0.1), material=MAT_GROUND, mesh=CHAMFER_MESH)
    spawn_block("SeaWall_Walkway", folder, (sx, sy, -0.05), (30.0, 8.0, 0.1), material=MAT_GROUND, mesh=CHAMFER_MESH)
    spawn_block("SeaWall_Railing", folder, (sx, sy + 4.0, 1.0), (30.0, 0.2, 1.1), material=MAT_VEHICLE)

    # The kneeling frame tableau -- LONGSTONE per the mission doc's [PROPOSAL].
    # Placeholder silhouette only; a real frame mesh is way beyond a blockout
    # script and beyond most AI text-to-3D tools at usable game fidelity -- see
    # the wiring doc / final report for why this stays a placeholder.
    spawn_block("Caryatid_Kneeling_Silhouette", folder, (sx - 10.0, sy - 12.0, 4.0), (3.0, 3.0, 8.0),
                 rotation_deg=(0, 15, 0), material=MAT_WALL)
    spawn_marker("Caryatid_Kneeling_Marker", folder, (sx - 10.0, sy - 12.0, 8.5), "Landmark_LongstoneCaryatid", color=(0.5, 0.5, 0.6))
    real_or_placeholder("TideMark_Ring_Prop", folder, "/Game/M1_District/AIModels/SM_TideMarkRing.SM_TideMarkRing",
                         (sx - 10.0, sy - 14.0, 3.0), (0.8, 0.1, 0.8), rot_z=0.0, material=MAT_GLOWVEIN)

    spawn_trigger("Checkpoint_MissionEnd", folder, (sx, sy, 1.5), (6.0, 6.0, 3.0), "Checkpoint")


safe(add_seawall_glimpse, "4.4d Sea wall glimpse")


# ---------------------------------------------------------------------------
# NavMesh + lighting rig
# ---------------------------------------------------------------------------

def add_nav_volume():
    # Long box covering the whole ~900m path, generous margins in Y for the
    # carry's jogs east.
    center_x = (DREAD_START_X + HOSPITAL_MUSTER_LOC[0]) / 2.0
    center_y = (STAIRWELL_Y + (HOSPITAL_MUSTER_LOC[1] + 70)) / 2.0
    size_x = (HOSPITAL_MUSTER_LOC[0] - DREAD_START_X) + 60
    size_y = abs((HOSPITAL_MUSTER_LOC[1] + 70) - STAIRWELL_Y) + 60
    vol = actor_subsystem.spawn_actor_from_class(
        unreal.NavMeshBoundsVolume, unreal.Vector(center_x * M, center_y * M, 5 * M), unreal.Rotator(0, 0, 0))
    vol.set_actor_scale3d(unreal.Vector(size_x / 2.0, size_y / 2.0, 15.0))
    vol.set_folder_path(f"{ROOT_FOLDER}/NavMesh")
    unreal.log(f"[M1 District] NavMeshBoundsVolume centered ({center_x:.0f},{center_y:.0f}), covers ~{size_x:.0f}x{size_y:.0f}m.")


safe(add_nav_volume, "NavMeshBoundsVolume")


def try_set(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[M1 District] Could not set '{prop}' on {obj}: {e}")


def add_lighting():
    """Base rig only sets the QUIET/DREAD pre-dawn blue-black look (matches the
    garrison's own rig, since this level starts right where that one ends). The
    doc's full palette progression (pre-dawn -> sodium amber -> gold-green
    veins -> grey dust dawn) is a Level Sequencer lighting job across the
    mission's runtime, not something four static light actors can represent --
    flagged here, not faked."""
    sun = actor_subsystem.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 50 * M), unreal.Rotator(-8, 200, 0))
    sun.set_actor_label("DirLight_PreDawn")
    sun.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    try_set(sun_comp, "intensity", 400.0)
    try_set(sun_comp, "light_color", unreal.Color(140, 153, 179, 255))
    try_set(sun_comp, "atmosphere_sun_light", True)

    atmo = actor_subsystem.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    atmo.set_folder_path(f"{ROOT_FOLDER}/Lighting")

    sky = actor_subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    sky.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    try_set(sky_comp, "intensity", 0.3)
    try_set(sky_comp, "real_time_capture", True)

    fog = actor_subsystem.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    fog.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    try_set(fog_comp, "fog_density", 0.02)  # slightly denser than the garrison -- dust, per §9
    try_set(fog_comp, "fog_inscattering_luminance", unreal.LinearColor(0.35, 0.35, 0.4))

    ppv = actor_subsystem.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector((HOSPITAL_MUSTER_LOC[0] / 2.0) * M, 0, 10 * M), unreal.Rotator(0, 0, 0))
    ppv.set_actor_label("PPV_Unbound_ManualExposure")
    ppv.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    try_set(ppv, "unbound", True)
    try:
        settings = ppv.settings
        try_set(settings, "override_auto_exposure_method", True)
        try_set(settings, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        try_set(settings, "override_auto_exposure_bias", True)
        try_set(settings, "auto_exposure_bias", 5.5)  # same value the garrison landed on after bracketing
        ppv.set_editor_property("settings", settings)
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[M1 District] Could not touch PostProcessVolume settings struct: {e}")


safe(add_lighting, "Lighting rig")


# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

unreal.log(
    f"[M1 District] Built Dread street, eruption crater, route clearing, gun line, collapse sprint, "
    f"stairwell, {len(CARRY_WAYPOINTS)}-waypoint carry, hospital muster, and sea-wall glimpse under "
    f"outliner folder '{ROOT_FOLDER}'. Next: press P to preview nav / Build Paths, walk the whole path "
    f"once to sanity-check scale and turns, then Save Current Level. See Docs/M1_DISTRICT_BP_WIRING.md "
    f"for what this script deliberately did NOT build (PALAWAN's real actor, the deterrent flinch, the "
    f"carry's input-lock state, the extraction counter's HUD wiring, checkpoints' actual respawn logic)."
)
