"""PS1 pad-ring marking: the candidate-local DEFERRED DECAL material graph, shared by
Scripts/ib_garrison_ring_stability.py (which saves it into the candidate's own subfolder) and
Scripts/ib_garrison_ring_check.py (which builds an identical TRANSIENT copy for the in-memory A/B preview).

The ring is drawn analytically, not by geometry: for every pixel the decal pass receives, the decal UV is turned
into the radial distance s = |p| - R (cm) from the ring's centre line, and the pixel's footprint in s is taken from
the decal UV derivatives (DecalDerivative -> ddx/ddy of the UV, times the decal's width in cm). The coverage is the
exact 1-D box-filter overlap of that footprint with the paint band |s| <= W/2:

    coverage = clamp((min(s + fw/2, W/2) - max(s - fw/2, -W/2)) / fw, 0, 1),   fw = |ds/dx| + |ds/dy|

so a resolvable line is solid with a one-pixel anti-aliased edge, and a line thinner than a pixel fades to its true
share of the pixel (W/fw) instead of being hit or missed by the sample point. The paint's Base Color, roughness,
metallic and specular are the FF1 paint's own values (M_FlatCol defaults: Base Color (0.85, 0.60, 0.22) linear,
Roughness 1, Metallic 0, Specular 0.5); the normal is not written, so the deck's own surface normal stays.
Domain: Deferred Decal; Blend Mode: Translucent (with Substrate on, a deferred decal takes the material's own blend
mode); no emissive, so the paint is lit exactly like the deck under it.
"""
import unreal

MEL = unreal.MaterialEditingLibrary
RADIUS, HALF_WIDTH, HALF_SIZE = 1890.0, 20.0, 1950.0      # cm: ring centre-line radius, half the 40 cm width, decal half-size
RGB = (0.85, 0.60, 0.22)                                   # FF1's MI_FF1_DeckPaintAmber 'Base Color' (linear), unchanged
ROUGHNESS, METALLIC, SPECULAR = 1.0, 0.0, 0.5
RING_CODE = """float SizeCm = 2.0 * HalfSize;
float2 PosCm = (UV - 0.5) * SizeCm;
float RadCm = length(PosCm);
float2 Radial = PosCm / max(RadCm, 0.001);
float DsDx = dot(Radial, DUVDX * SizeCm);
float DsDy = dot(Radial, DUVDY * SizeCm);
float Footprint = max(abs(DsDx) + abs(DsDy), 0.001);
float Dist = RadCm - Radius;
float Lo = max(Dist - 0.5 * Footprint, -HalfWidth);
float Hi = min(Dist + 0.5 * Footprint, HalfWidth);
return saturate((Hi - Lo) / Footprint);"""
RING_CODE_HARD = """float SizeCm = 2.0 * HalfSize;
float2 PosCm = (UV - 0.5) * SizeCm;
float Dist = length(PosCm) - Radius;
return step(abs(Dist), HalfWidth);"""
CUSTOM_INPUTS = ("UV", "DUVDX", "DUVDY", "Radius", "HalfWidth", "HalfSize")
SCALARS = (("RingRadius", "Radius", RADIUS), ("RingHalfWidth", "HalfWidth", HALF_WIDTH), ("RingHalfSize", "HalfSize", HALF_SIZE))


def custom_input(name):
    """FCustomInput's InputName is an edit-only property: the struct takes no constructor arguments from Python."""
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    return ci


def build(m, hard=False):
    """Builds the graph into an EMPTY Material. Returns what each connection call returned. hard=True builds the
    DIAGNOSTIC variant (preview only, never saved): the same decal with a hard in/out edge and no filtering, to
    separate the effect of the representation (decal vs geometry) from the effect of the filtering."""
    # a deferred decal takes the material's own Blend Mode (the older DecalBlendMode is protected and not used):
    # with Substrate on, the DeferredDecal domain accepts Translucent (Grey Transmittance), Colored Transmittance,
    # AlphaComposite or Colored Transmittance Only. Translucent: the paint's coverage comes from Opacity. The blend
    # mode is set BEFORE the domain so that no intermediate state (decal + opaque) is ever compiled.
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    dd = MEL.create_material_expression(m, unreal.MaterialExpressionDecalDerivative, -1100, 160)
    cu = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -650, 40)
    cu.set_editor_property("code", RING_CODE_HARD if hard else RING_CODE)
    cu.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    cu.set_editor_property("description", "PS1 pad ring coverage (%s)" % ("HARD EDGE, unfiltered: diagnostic" if hard else "analytic, box-filtered"))
    cu.set_editor_property("inputs", [custom_input(n) for n in CUSTOM_INPUTS])
    conn = {"uv": MEL.connect_material_expressions(tc, "", cu, "UV"),
            "ddx": MEL.connect_material_expressions(dd, "DDX", cu, "DUVDX"),
            "ddy": MEL.connect_material_expressions(dd, "DDY", cu, "DUVDY")}
    y = 320
    for pname, pin, val in SCALARS:
        sp = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1100, y)
        sp.set_editor_property("parameter_name", pname)
        sp.set_editor_property("default_value", val)
        conn[pname] = MEL.connect_material_expressions(sp, "", cu, pin)
        y += 90
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -650, -360)
    col.set_editor_property("parameter_name", "Base Color")
    col.set_editor_property("default_value", unreal.LinearColor(RGB[0], RGB[1], RGB[2], 1.0))
    consts = {}
    for name, val, yy in (("roughness", ROUGHNESS, -200), ("metallic", METALLIC, -140), ("specular", SPECULAR, -80)):
        k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -650, yy)
        k.set_editor_property("r", val)
        consts[name] = k
    conn["base_color"] = MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    conn["roughness"] = MEL.connect_material_property(consts["roughness"], "", unreal.MaterialProperty.MP_ROUGHNESS)
    conn["metallic"] = MEL.connect_material_property(consts["metallic"], "", unreal.MaterialProperty.MP_METALLIC)
    conn["specular"] = MEL.connect_material_property(consts["specular"], "", unreal.MaterialProperty.MP_SPECULAR)
    conn["opacity"] = MEL.connect_material_property(cu, "", unreal.MaterialProperty.MP_OPACITY)
    return {k: bool(v) for k, v in conn.items()}


def facts(m):
    """What the engine reports about a material built by build()."""
    def safe(fn):
        try:
            return fn()
        except Exception as e:
            return "ERR: " + (str(e).splitlines() or [""])[-1][:160]
    f = {"object": safe(lambda: m.get_path_name()), "class": safe(lambda: m.get_class().get_name()),
         "domain": safe(lambda: str(m.get_editor_property("material_domain"))),
         "blend_mode": safe(lambda: str(m.get_editor_property("blend_mode"))),
         "num_expressions": safe(lambda: MEL.get_num_material_expressions(m))}
    props = {}
    for name in ("MP_BASE_COLOR", "MP_ROUGHNESS", "MP_METALLIC", "MP_SPECULAR", "MP_OPACITY", "MP_NORMAL", "MP_EMISSIVE_COLOR",
                 "MP_FRONT_MATERIAL"):
        node = safe(lambda name=name: MEL.get_material_property_input_node(m, getattr(unreal.MaterialProperty, name)))
        props[name] = (node.get_class().get_name() if node and not isinstance(node, str) else (None if not node else node))
    f["connected"] = props
    f["scalars"] = {p: safe(lambda p=p: round(float(MEL.get_material_default_scalar_parameter_value(m, p)), 4)) for p, _, _ in SCALARS}
    c = safe(lambda: MEL.get_material_default_vector_parameter_value(m, "Base Color"))
    f["base_color"] = [round(float(c.r), 6), round(float(c.g), 6), round(float(c.b), 6), round(float(c.a), 6)] \
        if c is not None and not isinstance(c, str) else c
    return f


def issues(f):
    out = []
    for k, v in (f.get("connections") or {}).items():
        if v is not True:
            out.append("connection %s returned %s" % (k, v))
    if "DEFERRED_DECAL" not in str(f.get("domain")):
        out.append("domain is %s" % f.get("domain"))
    bm = str(f.get("blend_mode")).upper()
    if "BLEND_TRANSLUCENT" not in bm or "COLORED" in bm:
        out.append("blend mode is %s, expected BLEND_TRANSLUCENT" % f.get("blend_mode"))
    con = f.get("connected") or {}
    real = lambda v: bool(v) and not str(v).startswith("ERR")
    for k in ("MP_BASE_COLOR", "MP_ROUGHNESS", "MP_METALLIC", "MP_SPECULAR", "MP_OPACITY"):
        if not real(con.get(k)):
            out.append("%s is not connected (%s)" % (k, con.get(k)))
    for k in ("MP_NORMAL", "MP_EMISSIVE_COLOR", "MP_FRONT_MATERIAL"):
        if real(con.get(k)):
            out.append("%s is connected (%s)" % (k, con.get(k)))
    want = {"RingRadius": RADIUS, "RingHalfWidth": HALF_WIDTH, "RingHalfSize": HALF_SIZE}
    for k, v in want.items():
        got = (f.get("scalars") or {}).get(k)
        if not isinstance(got, float) or abs(got - v) > 1e-3:
            out.append("%s is %s, expected %s" % (k, got, v))
    bc = f.get("base_color")
    if not isinstance(bc, list) or any(abs(a - b) > 1e-4 for a, b in zip(bc, list(RGB) + [1.0])):
        out.append("Base Color is %s, expected %s" % (bc, list(RGB) + [1.0]))
    return out


def stats(m):
    """The engine's shader statistics for the material (GUI only; zero instructions means it did not compile)."""
    try:
        st = MEL.get_statistics(m)
    except Exception as e:
        return "ERR: " + (str(e).splitlines() or [""])[-1][:160]
    out = {}
    for k in ("num_vertex_shader_instructions", "num_pixel_shader_instructions", "num_samplers", "num_pixel_texture_samples",
              "num_uv_scalars", "num_interpolator_scalars"):
        try:
            out[k] = int(st.get_editor_property(k))
        except Exception:
            out[k] = None
    return out
