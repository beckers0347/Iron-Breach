"""Fortress environment pass. Run with UnrealEditor-Cmd -run=pythonscript.
Creates assets under /Game/IronBreach/Environment/Bastion and updates only CarrowGateGarrison.
Original map backup: Saved/BastionPolish/before/CarrowGateGarrison.umap.
IB_BASTION_PREVIEW=1 builds the assets but leaves level changes unsaved.
"""
import unreal, math, os, json
from pathlib import Path

LEVEL = "/Game/LevelPrototyping/CarrowGateGarrison"
ROOT = "/Game/IronBreach/Environment/Bastion"
OUT = Path(unreal.Paths.project_saved_dir()) / "BastionPolish"
OUT.mkdir(parents=True, exist_ok=True)
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
actors = EAS.get_all_level_actors()

def log(s): unreal.log("BASTION: " + s)
def setp(obj, name, value): obj.set_editor_property(name, value)
def expr(mat, cls): return MEL.create_material_expression(mat, cls)
def wire(src, dst, pin, output=""):
    if not MEL.connect_material_expressions(src, output, dst, pin):
        raise RuntimeError(f"Connection failed: {src.get_name()} -> {dst.get_name()}.{pin}")
def output(matnode, prop):
    if not MEL.connect_material_property(matnode, "", prop): raise RuntimeError(f"Property connection failed: {prop}")
def constant(mat, value):
    if isinstance(value, tuple):
        e = expr(mat, unreal.MaterialExpressionConstant3Vector)
        setp(e, "constant", unreal.LinearColor(r=value[0], g=value[1], b=value[2], a=1))
    else:
        e = expr(mat, unreal.MaterialExpressionConstant)
        setp(e, "r", value)
    return e
def custom(mat, code, inputs, scalar=False):
    e = expr(mat, unreal.MaterialExpressionCustom)
    setp(e, "code", code)
    setp(e, "output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    custom_inputs = []
    for name in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", name); custom_inputs.append(ci)
    setp(e, "inputs", custom_inputs)
    for name, node in inputs.items(): wire(node, e, name)
    return e
def material(name):
    path = ROOT + "/" + name
    m = EAL.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not m: raise RuntimeError(path)
    MEL.delete_all_material_expressions(m)
    return m
def finish_material(m):
    MEL.layout_material_expressions(m)
    MEL.recompile_material(m)
    if not EAL.save_loaded_asset(m): raise RuntimeError("Material save failed: " + m.get_name())

# World-scale concrete: avoids stretching one photograph across long cuboid walls.
concrete = material("M_Bastion_Concrete")
p = expr(concrete, unreal.MaterialExpressionWorldPosition)
n = expr(concrete, unreal.MaterialExpressionVertexNormalWS)
t = expr(concrete, unreal.MaterialExpressionTextureObject)
setp(t, "texture", EAL.load_asset("/Game/LevelPrototyping/AITextures/T_Wall_Concrete"))
color = custom(concrete, """
float3 w=pow(abs(N),4); w/=max(dot(w,1),0.001);
float3 c=Texture2DSample(Tex,TexSampler,P.yz/320).rgb*w.x
       +Texture2DSample(Tex,TexSampler,P.xz/320).rgb*w.y
       +Texture2DSample(Tex,TexSampler,P.xy/320).rgb*w.z;
float grey=dot(c,float3(0.2126,0.7152,0.0722));
float macro=sin(P.x*0.0013+sin(P.y*0.001))*sin(P.z*0.003+P.y*0.0019);
float damp=(1-smoothstep(-40,130,P.z))*0.28;
return clamp(lerp(grey.xxx,c,0.22)*float3(0.85,0.89,0.91)*(0.84+0.08*macro)*(1-damp),0.025,0.52);
""", {"P": p, "N": n, "Tex": t})
output(color, unreal.MaterialProperty.MP_BASE_COLOR)
rough = custom(concrete, "return lerp(0.49,0.87,smoothstep(-40,160,P.z));", {"P": p}, True)
output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
output(constant(concrete, 0.25), unreal.MaterialProperty.MP_SPECULAR)
finish_material(concrete)

paving = material("M_Bastion_Paving")
p = expr(paving, unreal.MaterialExpressionWorldPosition)
t = expr(paving, unreal.MaterialExpressionTextureObject)
setp(t,"texture",EAL.load_asset("/Game/LevelPrototyping/AITextures/T_Ground_Concrete"))
color = custom(paving, """
float3 c=Texture2DSample(Tex,TexSampler,P.xy/360).rgb;
float grey=0.16+0.09*dot(c,float3(0.2126,0.7152,0.0722));
float2 cell=abs(frac(P.xy/400)-0.5)*400;
float joint=1-smoothstep(0.6,1.8,200-max(cell.x,cell.y));
float weather=0.94+0.06*sin(P.x*0.0017)*sin(P.y*0.0012);
return grey.xxx*float3(0.94,0.97,1.0)*weather*(1-joint*0.22);
""", {"P":p,"Tex":t})
output(color,unreal.MaterialProperty.MP_BASE_COLOR)
output(constant(paving,0.78),unreal.MaterialProperty.MP_ROUGHNESS)
output(constant(paving,0.3),unreal.MaterialProperty.MP_SPECULAR)
finish_material(paving)

# The existing trunk material's normal sampler does not match its imported texture.
# Use the pack's diffuse with the actual color space and a matte response locally.
bark = material("M_Bastion_Bark")
uv = expr(bark,unreal.MaterialExpressionTextureCoordinate)
setp(uv,"v_tiling",3.0)
tex = EAL.load_asset("/Game/Landscaping/Shrubs/Textures/Shrubs/Bark_A/T_Bark_A_diffuse")
sample = expr(bark,unreal.MaterialExpressionTextureSample)
setp(sample,"texture",tex)
setp(sample,"sampler_type",unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if tex.get_editor_property("srgb") else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
wire(uv,sample,"UVs")
MEL.connect_material_property(sample,"RGB",unreal.MaterialProperty.MP_BASE_COLOR)
output(constant(bark,0.86),unreal.MaterialProperty.MP_ROUGHNESS)
finish_material(bark)

# A dense central water grid, gradually coarser out towards the 3 km footprint edge.
# 66k vertices / 131k triangles, one material; only the long swells displace geometry.
mesh_path = ROOT + "/SM_Bastion_Harbor"
mesh = EAL.load_asset(mesh_path) if EAL.does_asset_exist(mesh_path) else None
if mesh is None:
    obj = OUT / "SM_Bastion_Harbor.obj"
    count = 256
    coords = []
    for i in range(count + 1):
        u = 2*i/count-1
        coords.append(150000*(0.05*u + 0.95*u*u*u))
    with obj.open("w", encoding="ascii") as f:
        f.write("o SM_Bastion_Harbor\n")
        for y in coords:
            for x in coords: f.write(f"v {x:.5f} {y:.5f} 0\n")
        for j in range(count+1):
            for i in range(count+1): f.write(f"vt {i/count:.7f} {j/count:.7f}\n")
        f.write("vn 0 0 1\n")
        for j in range(count):
            for i in range(count):
                a=j*(count+1)+i+1; b=a+1; c=a+count+1; d=c+1
                f.write(f"f {a}/{a}/1 {b}/{b}/1 {d}/{d}/1\nf {a}/{a}/1 {d}/{d}/1 {c}/{c}/1\n")
    options = unreal.FbxImportUI()
    options.import_mesh = True; options.import_materials = False; options.import_textures = False
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.auto_generate_collision = False
    options.static_mesh_import_data.convert_scene = False
    task = unreal.AssetImportTask()
    task.filename = str(obj); task.destination_path = ROOT; task.destination_name = "SM_Bastion_Harbor"
    task.automated = True; task.save = True; task.options = options
    AT.import_asset_tasks([task])
    mesh = EAL.load_asset(mesh_path)
    if mesh is None: raise RuntimeError("Harbor grid import failed")
    bounds = mesh.get_bounds().box_extent
    log(f"Water grid bounds {bounds}")
    if bounds.z > 1 or bounds.x < 140000 or bounds.y < 140000: raise RuntimeError("Unexpected harbor grid orientation or scale")

water = material("M_Bastion_Harbor")
setp(water, "shading_model", unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
setp(water, "tangent_space_normal", False)
p = expr(water, unreal.MaterialExpressionWorldPosition)
clock = expr(water, unreal.MaterialExpressionTime)
camera = expr(water, unreal.MaterialExpressionCameraPositionWS)
distance = expr(water, unreal.MaterialExpressionDistanceToNearestSurface)
# Unconnected position uses the current world-space shading position.
normal = custom(water, """
float2 g=0;
float2 d[8]={float2(1,0.25),float2(0.5,1),float2(-0.7,1),float2(1,-0.6),float2(0.2,1),float2(-1,0.4),float2(0.8,0.6),float2(1,-0.2)};
float l[8]={3500,1800,900,430,210,105,57,29};
float a[8]={10,7,3,2.0,1.3,0.8,0.40,0.18};
float viewDistance=length(P-Camera);
[unroll] for(int i=0;i<8;i++) {
 float2 dir=normalize(d[i]); float k=6.283185/l[i];
 float phase=dot(P.xy,dir)*k-Time*sqrt(980*k)+i*1.93;
 float fade=1-smoothstep(l[i]*10,l[i]*40,viewDistance);
 g+=dir*(a[i]*k*cos(phase))*fade;
}
return normalize(float3(-g,1));
""", {"P": p, "Time": clock, "Camera": camera})
output(normal, unreal.MaterialProperty.MP_NORMAL)
wpo = custom(water, """
float h=10*sin(dot(P.xy,normalize(float2(1,0.25)))*0.0017952-Time*1.326)
       +7*sin(dot(P.xy,normalize(float2(0.5,1)))*0.0034907-Time*1.849+1.93)
       +3*sin(dot(P.xy,normalize(float2(-0.7,1)))*0.0069813-Time*2.615+3.86);
return float3(0,0,h);
""", {"P": p, "Time": clock})
output(wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
foam = custom(water, """
float noise=0.5+0.5*sin(P.x*0.038+sin(P.y*0.043+Time))*sin(P.y*0.065-Time*0.5);
float surge=0.58+0.42*sin(Time*0.7+P.x*0.0017+P.y*0.0011);
return smoothstep(3,18,Dist)*(1-smoothstep(40,90,Dist))*smoothstep(0.4,0.8,noise)*surge;
""", {"P": p, "Time": clock, "Dist": distance}, True)
color = custom(water, "return lerp(float3(0.006,0.022,0.028),float3(0.37,0.47,0.46),Foam*0.7);", {"Foam": foam})
output(color, unreal.MaterialProperty.MP_BASE_COLOR)
rough = custom(water, "return lerp(0.20,0.48,Foam);", {"Foam": foam}, True)
output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
output(constant(water, 0.5), unreal.MaterialProperty.MP_SPECULAR)
output(constant(water, 0.22), unreal.MaterialProperty.MP_OPACITY)
slw = expr(water, unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
wire(constant(water, (0.00005,0.00012,0.00015)), slw, "ScatteringCoefficients")
wire(constant(water, (0.0040,0.0025,0.0018)), slw, "AbsorptionCoefficients")
wire(constant(water, 0.15), slw, "PhaseG")
wire(constant(water, (0.85,0.93,0.96)), slw, "ColorScaleBehindWater")
finish_material(water)

changes = {"concrete_assignments": 0, "paving_assignments": 0, "bark_assignments": 0, "hidden_legacy_water": [], "lighting": []}
for a in actors:
    if not isinstance(a, unreal.StaticMeshActor): continue
    c = a.static_mesh_component
    label = a.get_actor_label()
    mats = [c.get_material(i) for i in range(c.get_num_materials())]
    if label in ("Water_Placeholder", "Water_Shallow", "Water_Deep") or label.startswith(("Surf_", "GarrisonShallow_", "GarrisonSurf_")):
        c.set_visibility(False); a.set_actor_hidden_in_game(True)
        changes["hidden_legacy_water"].append(label)
    for index, m in enumerate(mats):
        if not m: continue
        name = m.get_name()
        is_structure = any(k in label.lower() for k in ("wall", "floor", "platform", "foundation", "slab", "bunker", "gate", "tower", "roof", "stair", "quay"))
        if name == "M_AI_Wall" or (name == "WorldGridMaterial" and is_structure):
            c.set_material(index, concrete); changes["concrete_assignments"] += 1
        elif name in ("M_AI_Ground","T_Ground_Concrete_Mat","T_Ground_Concrete_Mat_Inst"):
            c.set_material(index,paving); changes["paving_assignments"] += 1
        elif name == "M_AI_TreeTrunk":
            c.set_material(index,bark); changes["bark_assignments"] += 1

sea = next((a for a in actors if a.get_actor_label() == "IB_Harbor_Surface"), None)
if sea is None:
    sea = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(10000,-4000,-35), unreal.Rotator())
    sea.set_actor_label("IB_Harbor_Surface")
c = sea.static_mesh_component
c.set_static_mesh(mesh); c.set_material(0, water)
c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
setp(c, "cast_shadow", False)
setp(c, "affect_distance_field_lighting", False)
setp(c, "bounds_scale", 1.01)

# Neutral early-morning key, cool sky fill, one restrained fog layer. Keyword color
# arguments avoid Python's Color(b,g,r,a) positional ordering reversing warm/cool.
for a in actors:
    if isinstance(a, unreal.DirectionalLight):
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        a.set_actor_rotation(unreal.Rotator(pitch=-13, yaw=165, roll=0), False)
        c.set_light_color(unreal.LinearColor(r=1,g=1,b=1,a=1))
        setp(c,"use_temperature",True); setp(c,"temperature",6200.0)
        c.set_intensity(1200.0)
        setp(c,"light_source_angle",1.2)
        setp(c,"volumetric_scattering_intensity",0.3)
        changes["lighting"].append(a.get_actor_label())
    elif isinstance(a, unreal.SkyLight):
        c = a.get_component_by_class(unreal.SkyLightComponent)
        c.set_intensity(1.35)
        setp(c,"real_time_capture",True)
        setp(c,"volumetric_scattering_intensity",1.0)
    elif isinstance(a, unreal.ExponentialHeightFog):
        c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        # Both existing volumes occupy exactly the same origin.
        if a.get_actor_label() == "ExponentialHeightFog2":
            c.set_visibility(False); a.set_actor_hidden_in_game(True)
        else:
            setp(c,"fog_density",0.009)
            setp(c,"fog_max_opacity",0.75)
            setp(c,"start_distance",1200.0)
            setp(c,"volumetric_fog_albedo",unreal.Color(r=190,g=210,b=230,a=255))
            setp(c,"volumetric_fog_extinction_scale",0.6)
    elif isinstance(a, unreal.PostProcessVolume) and a.get_actor_label() == "PPV_IB_CinematicLook":
        s = a.get_editor_property("settings")
        def ov(name, value): setp(s,"override_"+name,True); setp(s,name,value)
        ov("auto_exposure_min_brightness",1.0); ov("auto_exposure_max_brightness",8.0)
        ov("auto_exposure_bias",0.0)
        ov("white_temp",6500.0)
        ov("color_saturation",unreal.Vector4(0.96,0.96,0.96,1))
        ov("color_contrast",unreal.Vector4(1.025,1.025,1.025,1))
        ov("color_gain_shadows",unreal.Vector4(0.96,0.99,1.025,1))
        ov("color_saturation_shadows",unreal.Vector4(1,1,1,1))
        ov("color_gain_highlights",unreal.Vector4(1,1,1,1))
        ov("film_grain_intensity",0.025); ov("vignette_intensity",0.16)
        ov("bloom_intensity",0.22); ov("motion_blur_amount",0.12)
        a.set_editor_property("settings",s)

(OUT / "changes.json").write_text(json.dumps(changes, indent=2), encoding="utf-8")
if os.environ.get("IB_BASTION_PREVIEW") != "1":
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(): raise RuntimeError("Level save failed")
log("COMPLETE: " + json.dumps(changes))
