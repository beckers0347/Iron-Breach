"""Read-only probe of the marking material used for the garrison's deck markings (never saves, never edits).

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script=Scripts/ib_probe_marking_material.py
    env: IB_GARRISON_OUT = output folder (material_probe.json)

Why: the PF1 markings use MI_Landmass_HelipadMarking (an instance of M_FlatCol, colour 0.95/0.82/0.15). In the
captures they read ochre in direct sun but near-black in shade, which a plain yellow dielectric paint would not do.
This records, from the engine, what drives the parent's Base Color / Metallic / Roughness / Specular inputs, the
parameter names and defaults, and which of the instance's overrides the parent actually exposes.
"""
import json, os, traceback
from pathlib import Path
import unreal

MI_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_HelipadMarking.MI_Landmass_HelipadMarking"
OUT = Path(os.environ.get("IB_GARRISON_OUT") or str(Path(unreal.Paths.project_saved_dir()) / "material_probe"))
MEL = unreal.MaterialEditingLibrary
res = {"tool": "ib_probe_marking_material.py", "instance": MI_PATH, "errors": [], "writes": "none (read-only)"}


def err(what):
    res["errors"].append({"what": what, "detail": traceback.format_exc()[-600:]})


def colour(c):
    return [round(float(c.r), 4), round(float(c.g), 4), round(float(c.b), 4), round(float(c.a), 4)]


def expr_info(e):
    if e is None:
        return None
    d = {"class": e.get_class().get_name()}
    for prop in ("parameter_name", "default_value", "r", "constant", "desc"):
        try:
            v = e.get_editor_property(prop)
            d[prop] = colour(v) if isinstance(v, unreal.LinearColor) else (str(v) if isinstance(v, unreal.Name) else v)
        except Exception:
            pass
    return d


mi = unreal.EditorAssetLibrary.load_asset(MI_PATH)
res["instance_loaded"] = mi is not None
parent = None
if mi is not None:
    try:
        parent = mi.get_editor_property("parent")
        res["parent"] = parent.get_path_name() if parent else None
    except Exception:
        err("parent")
    try:
        res["instance_vector_overrides"] = [
            {"name": str(v.get_editor_property("parameter_info").get_editor_property("name")),
             "value": colour(v.get_editor_property("parameter_value"))}
            for v in mi.get_editor_property("vector_parameter_values")]
        res["instance_scalar_overrides"] = [
            {"name": str(v.get_editor_property("parameter_info").get_editor_property("name")),
             "value": float(v.get_editor_property("parameter_value"))}
            for v in mi.get_editor_property("scalar_parameter_values")]
    except Exception:
        err("instance overrides")
    try:
        bp = mi.get_editor_property("base_property_overrides")
        res["instance_base_property_overrides"] = {k: str(bp.get_editor_property(k)) for k in
                                                   ("override_shading_model", "override_blend_mode", "override_two_sided")}
    except Exception:
        err("base property overrides")
    for kind, names_fn, get_fn in (("scalar", MEL.get_scalar_parameter_names, MEL.get_material_instance_scalar_parameter_value),
                                   ("vector", MEL.get_vector_parameter_names, MEL.get_material_instance_vector_parameter_value)):
        try:
            names = [str(n) for n in names_fn(mi)]
            vals = {}
            for n in names:
                try:
                    v = get_fn(mi, n)
                    vals[n] = colour(v) if isinstance(v, unreal.LinearColor) else round(float(v), 4)
                except Exception:
                    vals[n] = "unreadable"
            res["instance_effective_%s_parameters" % kind] = vals
        except Exception:
            err("instance %s parameters" % kind)
base = parent
while base is not None and not isinstance(base, unreal.Material):
    try:
        base = base.get_editor_property("parent")
    except Exception:
        base = None
if base is not None:
    res["base_material"] = base.get_path_name()
    for prop in ("shading_model", "blend_mode", "two_sided", "use_material_attributes"):
        try:
            res.setdefault("base_material_properties", {})[prop] = str(base.get_editor_property(prop))
        except Exception:
            pass
    for kind, names_fn, get_fn in (("scalar", MEL.get_scalar_parameter_names, MEL.get_material_default_scalar_parameter_value),
                                   ("vector", MEL.get_vector_parameter_names, MEL.get_material_default_vector_parameter_value)):
        try:
            vals = {}
            for n in [str(n) for n in names_fn(base)]:
                try:
                    v = get_fn(base, n)
                    vals[n] = colour(v) if isinstance(v, unreal.LinearColor) else round(float(v), 4)
                except Exception:
                    vals[n] = "unreadable"
            res["base_default_%s_parameters" % kind] = vals
        except Exception:
            err("base %s parameters" % kind)
    inputs = {}
    for label, mp in (("base_color", "MP_BASE_COLOR"), ("metallic", "MP_METALLIC"), ("specular", "MP_SPECULAR"),
                      ("roughness", "MP_ROUGHNESS"), ("emissive", "MP_EMISSIVE_COLOR")):
        try:
            inputs[label] = expr_info(MEL.get_material_property_input_node(base, getattr(unreal.MaterialProperty, mp)))
        except Exception:
            inputs[label] = "unreadable"
    res["base_inputs"] = inputs
    over = [o["name"] for o in res.get("instance_vector_overrides", [])]
    exposed = list((res.get("base_default_vector_parameters") or {}).keys())
    res["instance_overrides_exposed_by_base"] = {n: n in exposed for n in over}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "material_probe.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
unreal.log("MARKING MATERIAL PROBE: wrote %s (%d errors)" % (OUT / "material_probe.json", len(res["errors"])))
