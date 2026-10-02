"""
IBPY: ib_barracks_materials.py  (helper module, imported by ib_replace_barracks.py and ib_barracks_tune.py)

Builds clean procedural materials for Barracks_02 (no textures, no UVs needed -- everything is driven by
world position, so it also works on the skinned doors and on the Nanite shell):

  Concrete_Weathered  light grey concrete, large soft blotches + fine grain
  Armor_Paint         dark gunmetal, slight metal, fine grain
  Door_Metal          slightly lighter steel
  Hazard_Stripes      yellow/black diagonal stripes (world space)
  Yellow_Paint        bollard yellow
  Window_Glass        near-black glossy (opaque, so Nanite-friendly)
  Light_Strip         warm emissive
  Black_Opening       black
  Bolt_Steel / Pipe_Steel   bright / dark metal

Every colour/roughness number is in the SPECS table: tweak there and re-run ib_barracks_tune.py.
Nothing is saved automatically.
"""
import unreal

MEL = unreal.MaterialEditingLibrary


def log(msg):
    unreal.log(f"IBPY: {msg}")


# linear-space colours
SPECS = {
    "Concrete_Weathered": {"kind": "concrete", "dark": (0.34, 0.335, 0.32), "light": (0.42, 0.415, 0.40), "rough": 0.9},
    "Interior_Concrete": {"kind": "concrete", "dark": (0.30, 0.255, 0.19), "light": (0.37, 0.32, 0.24), "rough": 0.92},
    "Armor_Paint": {"kind": "painted", "dark": (0.052, 0.054, 0.058), "light": (0.064, 0.067, 0.072), "rough": 0.6, "metal": 0.35},
    "Door_Metal": {"kind": "painted", "dark": (0.075, 0.078, 0.083), "light": (0.09, 0.094, 0.1), "rough": 0.55, "metal": 0.4},
    "Hazard_Stripes": {"kind": "hazard", "a": (0.80, 0.52, 0.0), "b": (0.015, 0.015, 0.015), "rough": 0.7},
    "Yellow_Paint": {"kind": "flat", "color": (0.75, 0.50, 0.0), "rough": 0.55},
    "Window_Glass": {"kind": "flat", "color": (0.008, 0.015, 0.022), "rough": 0.06, "metal": 0.0},
    "Light_Strip": {"kind": "emissive", "color": (1.0, 0.82, 0.5), "strength": 10.0},
    "Black_Opening": {"kind": "flat", "color": (0.005, 0.005, 0.005), "rough": 0.9},
    "Bolt_Steel": {"kind": "flat", "color": (0.20, 0.205, 0.21), "rough": 0.55, "metal": 0.5},
    "Pipe_Steel": {"kind": "flat", "color": (0.09, 0.092, 0.096), "rough": 0.6, "metal": 0.4},
}


def _x(mat, cls, px, py):
    return MEL.create_material_expression(mat, cls, px, py)


def _c3(mat, rgb, px, py):
    e = _x(mat, unreal.MaterialExpressionConstant3Vector, px, py)
    e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return e


def _c1(mat, v, px, py):
    e = _x(mat, unreal.MaterialExpressionConstant, px, py)
    e.set_editor_property("r", float(v))
    return e


def _noise(mat, scale, levels, px, py):
    e = _x(mat, unreal.MaterialExpressionNoise, px, py)
    try:
        e.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU)
    except Exception as ex:
        log(f"    (noise_function not set: {ex})")
    for k, v in (("scale", scale), ("levels", levels), ("output_min", 0.0), ("output_max", 1.0)):
        try:
            e.set_editor_property(k, v)
        except Exception as ex:
            log(f"    (noise.{k} not set: {ex})")
    return e


def _lerp(mat, a, b, alpha, px, py):
    e = _x(mat, unreal.MaterialExpressionLinearInterpolate, px, py)
    MEL.connect_material_expressions(a, "", e, "A")
    MEL.connect_material_expressions(b, "", e, "B")
    MEL.connect_material_expressions(alpha, "", e, "Alpha")
    return e


def _mul(mat, a, b, px, py):
    e = _x(mat, unreal.MaterialExpressionMultiply, px, py)
    MEL.connect_material_expressions(a, "", e, "A")
    MEL.connect_material_expressions(b, "", e, "B")
    return e


def _prop(expr, prop):
    MEL.connect_material_property(expr, "", prop)


def _build(name, spec, mat):
    P = unreal.MaterialProperty
    kind = spec["kind"]
    if kind == "concrete":
        n_big = _noise(mat, 0.0018, 2, -900, -200)
        n_fine = _noise(mat, 0.03, 2, -900, 100)
        base = _lerp(mat, _c3(mat, spec["dark"], -900, -500), _c3(mat, spec["light"], -900, -350), n_big, -600, -300)
        grain = _lerp(mat, _c1(mat, 0.94, -700, 0), _c1(mat, 1.0, -700, 60), n_fine, -450, 40)
        _prop(_mul(mat, base, grain, -250, -150), P.MP_BASE_COLOR)
        _prop(_c1(mat, spec["rough"], -250, 100), P.MP_ROUGHNESS)
    elif kind == "painted":
        n_fine = _noise(mat, 0.02, 2, -700, -100)
        _prop(_lerp(mat, _c3(mat, spec["dark"], -700, -300), _c3(mat, spec["light"], -700, -200), n_fine, -400, -200), P.MP_BASE_COLOR)
        _prop(_c1(mat, spec["rough"], -300, 50), P.MP_ROUGHNESS)
        _prop(_c1(mat, spec["metal"], -300, 130), P.MP_METALLIC)
    elif kind == "hazard":
        wp = _x(mat, unreal.MaterialExpressionWorldPosition, -1200, 0)
        dot = _x(mat, unreal.MaterialExpressionDotProduct, -1000, 0)
        MEL.connect_material_expressions(wp, "", dot, "A")
        MEL.connect_material_expressions(_c3(mat, (1.0, 1.0, 1.0), -1200, 120), "", dot, "B")
        scaled = _mul(mat, dot, _c1(mat, 0.02, -1000, 120), -800, 0)          # one stripe pair every 50 cm
        frac = _x(mat, unreal.MaterialExpressionFrac, -620, 0)
        MEL.connect_material_expressions(scaled, "", frac, "")
        sub = _x(mat, unreal.MaterialExpressionSubtract, -460, 0)
        MEL.connect_material_expressions(frac, "", sub, "A")
        MEL.connect_material_expressions(_c1(mat, 0.5, -620, 100), "", sub, "B")
        hard = _mul(mat, sub, _c1(mat, 40.0, -460, 100), -300, 0)
        sat = _x(mat, unreal.MaterialExpressionSaturate, -150, 0)
        MEL.connect_material_expressions(hard, "", sat, "")
        _prop(_lerp(mat, _c3(mat, spec["a"], -300, -300), _c3(mat, spec["b"], -300, -200), sat, 0, -100), P.MP_BASE_COLOR)
        _prop(_c1(mat, spec["rough"], 0, 100), P.MP_ROUGHNESS)
    elif kind == "emissive":
        _prop(_c3(mat, (0.0, 0.0, 0.0), -300, -100), P.MP_BASE_COLOR)
        col = spec["color"]
        s = spec["strength"]
        _prop(_c3(mat, (col[0] * s, col[1] * s, col[2] * s), -300, 100), P.MP_EMISSIVE_COLOR)
    else:  # flat
        _prop(_c3(mat, spec["color"], -300, -100), P.MP_BASE_COLOR)
        _prop(_c1(mat, spec.get("rough", 0.6), -300, 50), P.MP_ROUGHNESS)
        if "metal" in spec:
            _prop(_c1(mat, spec["metal"], -300, 130), P.MP_METALLIC)


def build_all(dest_folder, prefix="M_Barracks02_"):
    """Create (or recreate) every material under dest_folder. Returns {slot_name: Material}."""
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    out = {}
    for name, spec in SPECS.items():
        path = f"{dest_folder}/{prefix}{name}"
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                unreal.EditorAssetLibrary.delete_asset(path)
            mat = tools.create_asset(f"{prefix}{name}", dest_folder, unreal.Material, unreal.MaterialFactoryNew())
            if not mat:
                raise RuntimeError("create_asset returned None")
            _build(name, spec, mat)
            MEL.recompile_material(mat)
            out[name] = mat
            log(f"  material {prefix}{name} built ({spec['kind']})")
        except Exception as ex:
            unreal.log_warning(f"IBPY: WARNING -- material {name} failed: {ex} (slot keeps its imported material)")
    return out


def apply_to_static_mesh(mesh, mats):
    slots = list(mesh.get_editor_property("static_materials"))
    for i, sm in enumerate(slots):
        slot = str(sm.get_editor_property("imported_material_slot_name"))
        if slot in mats:
            mesh.set_material(i, mats[slot])
            log(f"  {mesh.get_name()} slot {i} '{slot}' -> {mats[slot].get_name()}")
        else:
            log(f"  {mesh.get_name()} slot {i} '{slot}': no replacement")


def apply_to_component(comp, mats):
    for i, slot in enumerate(comp.get_material_slot_names()):
        m = mats.get(str(slot))
        if m:
            comp.set_material(i, m)
            log(f"    {comp.get_outer().get_name()} slot {i} '{slot}' -> {m.get_name()}")
