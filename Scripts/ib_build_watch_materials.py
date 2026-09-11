"""
Iron Breach -- THE WATCH planet materials (headless).
UnrealEditor-Cmd ... -run=pythonscript -script=Scripts/ib_build_watch_materials.py

Creates two materials under /Game/IronBreach/Watch, both a single Custom (HLSL) node:

  M_WatchMap     Surface / Unlit.  UV -> (height, city density, moisture) of the invented world.
                 UIBPlanetWidget draws it ONCE into a 2048x1024 render target at startup
                 (UKismetRenderingLibrary::DrawMaterialToRenderTarget), reads it back to snap the
                 sector pins onto coastlines and to pick a sea level, then hands the RT to:
  M_WatchPlanet  User Interface / Opaque.  Ray-casts a unit sphere per pixel of the full-screen
                 Image and shades it: ocean + sun glint, biomes, snow/sea ice, warped-FBM clouds
                 with a swirl storm, city lights on the night side, atmosphere rim + halo,
                 terminator warmth, a faint 15-degree graticule, stars.  Parameters (set per tick
                 by the widget):
                    RotX/RotY/RotZ  columns of the planet->world rotation
                    Cam             (dist, tan(fov/2), aspect)
                    Shift           (sx, sy, 0)  principal-point shift in uv units (uv.y = 0.5 at the top edge)
                    Sun, Storm      world-space sun dir / planet-frame storm centre
                    Sea, CloudT, Gamma, Map (texture)

The original mockup's projection is retained; terrain, weather and lighting are refined here.
Re-running the script rebuilds both material graphs in place (FORCE); this is the source of truth.
"""
import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

PATH = "/Game/IronBreach/Watch"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
FORCE = True

NOISE_FNS = r"""
  float hash13(float3 p3){ p3 = frac(p3*0.1031); p3 += dot(p3, p3.zyx+31.32); return frac((p3.x+p3.y)*p3.z); }
  float3 hash33(float3 p3){ p3 = frac(p3*float3(0.1031,0.1030,0.0973)); p3 += dot(p3, p3.yxz+33.33); return frac((p3.xxy+p3.yxx)*p3.zyx); }
  float vnoise(float3 x){ float3 i = floor(x); float3 f = frac(x); f = f*f*(3.0-2.0*f);
    return lerp(lerp(lerp(hash13(i),hash13(i+float3(1,0,0)),f.x), lerp(hash13(i+float3(0,1,0)),hash13(i+float3(1,1,0)),f.x),f.y),
                lerp(lerp(hash13(i+float3(0,0,1)),hash13(i+float3(1,0,1)),f.x), lerp(hash13(i+float3(0,1,1)),hash13(i+float3(1,1,1)),f.x),f.y), f.z); }
  float fbm(float3 p, int oct){ float a = 0.5, s = 0.0, n = 0.0;
    [loop] for(int i = 0; i < oct; i++){ s += a*vnoise(p); n += a; p = p*2.03 + float3(1.7,9.2,3.1); a *= 0.5; }
    return s/n; }
"""

MAP_HLSL = r"""
struct WatchMapFx {
""" + NOISE_FNS + r"""
  float worleyEdge(float3 p){ float3 i = floor(p), f = frac(p); float f1 = 8.0, f2 = 8.0;
    [unroll] for(int x = -1; x <= 1; x++) [unroll] for(int y = -1; y <= 1; y++) [unroll] for(int z = -1; z <= 1; z++){
      float3 g = float3(x,y,z); float3 o = hash33(i+g); float3 r = g+o-f; float d = dot(r,r);
      if(d < f1){ f2 = f1; f1 = d; } else if(d < f2){ f2 = d; } }
    return sqrt(f2)-sqrt(f1); }
};
WatchMapFx F;
float lon = (UV.x-0.5)*6.2831853; float lat = (0.5-UV.y)*3.14159265;
float3 p = float3(cos(lat)*cos(lon), sin(lat), -cos(lat)*sin(lon));
float3 w = p*1.15 + 0.6*(float3(F.fbm(p*0.9+float3(7.1,2.3,5.7),4), F.fbm(p*0.9+float3(3.3,8.1,1.9),4), F.fbm(p*0.9+float3(11.2,4.4,9.6),4)) - 0.5);
float base = F.fbm(w*1.6, 6);
float ridged = 1.0 - abs(F.fbm(p*3.3+float3(21.0,21.0,21.0),5)*2.0-1.0);
// High-frequency terrain is baked once; the coast and pin readback share this height.
float mountains = pow(1.0-abs(F.fbm(p*34.0,5)*2.0-1.0),5.0);
float h = base + 0.22*ridged*smoothstep(0.42,0.62,base);
h += (F.fbm(p*72.0,4)-0.5)*0.028 + mountains*0.045*smoothstep(0.49,0.62,base);
float moist = F.fbm(p*2.4+float3(31.7,5.5,12.2),4);
float edge = F.worleyEdge(p*115.0);
float roads = 1.0 - smoothstep(0.012,0.055,edge);
float hubs = smoothstep(0.58,0.8,F.fbm(p*7.0+float3(50.0,50.0,50.0),4));
float region = smoothstep(0.40,0.62,F.fbm(p*1.8+float3(90.0,90.0,90.0),3));
float districts = smoothstep(0.46,0.68,F.fbm(p*38.0+17.0,3));
float blocks = smoothstep(0.48,0.75,F.vnoise(p*650.0));
float city = region*districts*(0.28*roads + 0.85*blocks)*(0.3+0.7*hubs);
return float3(saturate(h), city, moist);
"""

PLANET_HLSL = r"""
struct WatchFx {
""" + NOISE_FNS + r"""
  float weather(float3 p, float tm) {
    float3 jet = p*float3(3.0,9.0,3.0);
    float warp = fbm(p*3.1+float3(tm*0.3,4.0,9.0),3);
    jet += float3(warp*2.4,warp*0.7,tm);
    float fronts = fbm(jet,4);
    float fibers = fbm(p*float3(40.0,95.0,40.0)+warp*5.0+tm,3);
    return smoothstep(0.52,0.76,fronts + (fibers-0.5)*0.12);
  }
};
WatchFx F;
// Shared with UIBPlanetWidget::Project. Keep rotation, UV and camera contracts exact.
float2 uv = float2((UV.x-0.5)*Cam.z, 0.5-UV.y) + Shift.xy;
float3 rd = normalize(float3(uv*2.0*Cam.y, -1.0));
float3 ro = float3(0.0, 0.0, Cam.x);
float b = dot(ro,rd), c = dot(ro,ro)-1.0, disc = b*b-c;
float3 sun = normalize(Sun);
float3 col = float3(0.002,0.003,0.007);
float2 sc = float2(atan2(rd.x,rd.z),asin(clamp(rd.y,-1.0,1.0)))*300.0;
float sh = F.hash13(float3(floor(sc),7.0));
float star = smoothstep(0.998,1.0,sh)*(1.0-smoothstep(0.02,0.18,length(frac(sc)-0.5)));
col += float3(0.6,0.72,0.9)*star;
if(disc < 0.0) {
  float dperp = sqrt(max(c+1.0-b*b,0.0));
  float lit = smoothstep(-0.2,0.5,dot(normalize(ro-b*rd),sun));
  float halo = exp(-(dperp-1.0)*50.0);
  col += halo*lerp(float3(0.008,0.02,0.065),float3(0.16,0.48,0.82),lit)*0.8;
  return pow(max(col,0.0),Gamma);
}
float t = -b-sqrt(disc);
float3 p = ro+t*rd, n = normalize(p);
float3 pf = float3(dot(p,RotX),dot(p,RotY),dot(p,RotZ));
float3 sp = float3(dot(sun,RotX),dot(sun,RotY),dot(sun,RotZ));
float lat = asin(clamp(pf.y,-1.0,1.0)), lon = atan2(-pf.z,pf.x);
float2 muv = float2(frac(lon/6.2831853+0.5),0.5-lat/3.14159265);
float4 m = Texture2DSample(Map,MapSampler,muv);
float h=m.r, city=m.g, moist=m.b;
float coastAA=max(fwidth(h)*0.7,0.0012);
float land=smoothstep(Sea-coastAA,Sea+coastAA,h);
float e=saturate((h-Sea)/max(0.001,1.0-Sea));
float alat=abs(lat)/1.5708;
float detail=F.fbm(pf*190.0,3);
float3 lowland=lerp(float3(0.105,0.17,0.11),float3(0.36,0.30,0.20),smoothstep(0.38,0.70,1.0-moist));
float3 ground=lerp(lowland,float3(0.31,0.30,0.27),smoothstep(0.09,0.29,e));
ground *= 0.75+detail*0.48;
float snow=max(smoothstep(0.65,0.83,e+alat*0.16),smoothstep(0.77,0.92,alat+detail*0.04));
ground=lerp(ground,float3(0.78,0.84,0.86),snow);
float shelf=smoothstep(Sea-0.035,Sea,h);
float3 ocean=lerp(float3(0.015,0.055,0.115),float3(0.035,0.18,0.23),shelf*0.62);
float ice=smoothstep(0.85,0.94,alat+F.vnoise(pf*60.0)*0.035);
ocean=lerp(ocean,float3(0.63,0.76,0.79),ice);
// Surface gradients: relief shades the terrain, but does not displace the sphere or pins.
float relief=land*(e*0.0018+detail*0.00006);
float3 dpdx=ddx(p), dpdy=ddy(p);
float3 r1=cross(dpdy,n), r2=cross(n,dpdx);
float det=dot(dpdx,r1);
float3 grad=sign(det)*(ddx(relief)*r1+ddy(relief)*r2)/max(abs(det),0.00000001);
float3 terrainN=normalize(n-grad*smoothstep(0.06,0.2,dot(n,-rd)));
float ndl=dot(n,sun);
float light=sqrt(saturate(dot(terrainN,sun)));
float day=smoothstep(-0.03,0.12,ndl);
float night=1.0-smoothstep(-0.13,0.04,ndl);
col=lerp(ocean,ground,land)*(0.025+(0.10+light*0.90)*day);
float rs=saturate(dot(reflect(rd,n),sun));
col+=(pow(rs,280.0)*0.70+pow(rs,35.0)*0.035)*(1.0-land)*(1.0-ice)*day*float3(1.0,0.86,0.67);
// Sheared fronts and fine cirrus. Fixed octave count keeps the close view bounded.
float cov=F.weather(pf,CloudT);
float cirrus=pow(saturate(F.fbm(pf*float3(19,58,19)+CloudT,3)-0.47)*3.0,2.0)*0.2;
cov=saturate(cov+cirrus);
// Hurricane in a tangent frame: broken spiral arms, an irregular eyewall, a small dark eye.
float ds=acos(clamp(dot(pf,Storm),-1.0,1.0));
float stormR=0.085;
if(ds<stormR*2.4) {
  float3 sx=normalize(cross(abs(Storm.y)<0.95?float3(0,1,0):float3(1,0,0),Storm));
  float3 sy=cross(Storm,sx);
  float ang=atan2(dot(pf,sy),dot(pf,sx));
  float rr=ds/stormR;
  float fibers=F.fbm(pf*155.0,3);
  float spiral=0.5+0.5*sin(ang*2.0-rr*10.0+fibers*4.5);
  float arms=lerp(0.24,0.75,smoothstep(0.1,0.95,spiral))*exp(-rr*rr*0.75);
  float eyewall=exp(-pow((rr-0.26)/0.13,2.0))*(0.70+fibers*0.3);
  float eye=smoothstep(0.075,0.15,rr+fibers*0.015);
  float cyclone=saturate(arms+eyewall*0.65+(fibers-0.5)*0.25)*eye;
  cov=lerp(cov,cyclone,exp(-rr*rr*0.26));
}
float shadow=F.weather(normalize(pf-sp*0.009),CloudT);
col*=1.0-shadow*0.23*day;
float cloudLight=0.028+(0.25+0.75*sqrt(saturate(ndl)))*day;
float3 cloud=lerp(float3(0.56,0.65,0.75),float3(0.94,0.96,1.0),smoothstep(0.2,0.8,cov))*cloudLight;
col=lerp(col,cloud,cov*0.92);
float coastal=exp(-e*22.0);
float lights=city*land*coastal*(1.0-smoothstep(0.65,0.85,alat))*night*(1.0-cov);
col+=float3(1.0,0.68,0.32)*lights*1.05;
float facing=saturate(dot(n,-rd));
float fres=pow(1.0-facing,3.5);
float atmo=smoothstep(-0.22,0.45,ndl);
col+=fres*lerp(float3(0.012,0.035,0.095),float3(0.20,0.52,0.9),atmo)*1.05;
col+=float3(0.55,0.24,0.10)*exp(-pow(ndl*12.0,2.0))*0.035*(1.0-fres);
// Navigation overlay sits lightly on top of the geography.
float2 grid=float2(lon/6.2831853*24.0,lat/3.14159265*12.0);
float2 gd=abs(frac(grid+0.5)-0.5)/max(fwidth(grid),float2(0.0001,0.0001));
float gl=1.0-smoothstep(0.25,0.9,min(gd.x,gd.y));
col+=float3(0.20,0.42,0.55)*gl*0.018*(1.0-fres);
return pow(clamp(col,0.0,1.2),Gamma);
"""


def custom_node(mat, code, input_names, x=-300, y=0):
    node = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    node.set_editor_property("description", "IBWatch")
    inputs = []
    for name in input_names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", name)
        inputs.append(ci)
    node.set_editor_property("inputs", inputs)
    return node


def vector_param(mat, name, default, x, y):
    p = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", unreal.LinearColor(*default))
    return p


def scalar_param(mat, name, default, x, y):
    p = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", float(default))
    return p


def fresh_material(name):
    full = f"{PATH}/{name}"
    if EAL.does_asset_exist(full):
        if not FORCE:
            log(f"OK   exists, left alone: {full}")
            return None
        mat = EAL.load_asset(full)
        if not isinstance(mat, unreal.Material):
            raise RuntimeError(f"Expected Material at {full}, found {type(mat)}")
        MEL.delete_all_material_expressions(mat)
        log(f"     rebuilding graph in place: {full}")
        return mat
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(name, PATH, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError(f"create_asset failed for {full}")
    return mat


def build_map():
    mat = fresh_material("M_WatchMap")
    if mat is None:
        return
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    node = custom_node(mat, MAP_HLSL, ["UV"])
    MEL.connect_material_expressions(uv, "", node, "UV")
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    ok = EAL.save_asset(f"{PATH}/M_WatchMap")
    log(f"{'OK  ' if ok else 'FAIL'} M_WatchMap")


def build_planet():
    mat = fresh_material("M_WatchPlanet")
    if mat is None:
        return
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_UI)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    names = ["UV", "RotX", "RotY", "RotZ", "Cam", "Shift", "Sun", "Sea", "Storm", "CloudT", "Gamma", "Map"]
    node = custom_node(mat, PLANET_HLSL, names, -200, 0)
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, -520)
    MEL.connect_material_expressions(uv, "", node, "UV")
    y = -420
    for name, default in [("RotX", (1, 0, 0, 0)), ("RotY", (0, 1, 0, 0)), ("RotZ", (0, 0, 1, 0)),
                          ("Cam", (2.9, 0.364, 1.777, 0)), ("Shift", (0.25, 0.0, 0, 0)),
                          ("Sun", (0.74, 0.46, 0.34, 0)), ("Storm", (0.3, 0.3, 0.9, 0))]:
        p = vector_param(mat, name, default, -900, y)
        MEL.connect_material_expressions(p, "", node, name)
        y += 110
    for name, default in [("Sea", 0.5), ("CloudT", 0.0), ("Gamma", 2.2)]:
        p = scalar_param(mat, name, default, -900, y)
        MEL.connect_material_expressions(p, "", node, name)
        y += 90
    tex = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -900, y)
    tex.set_editor_property("parameter_name", "Map")
    default_tex = unreal.load_asset("/Engine/EngineMaterials/DefaultNormal.DefaultNormal")
    if default_tex is None:
        default_tex = unreal.load_asset("/Engine/EngineResources/DefaultTexture.DefaultTexture")
    if default_tex is not None:
        tex.set_editor_property("texture", default_tex)
        # linear (non-sRGB) data: the widget's render target is created with SRGB off
        try:
            srgb = bool(default_tex.get_editor_property("srgb"))
        except Exception:
            srgb = False
        tex.set_editor_property("sampler_type",
            unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if srgb else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        log(f"     Map default texture {default_tex.get_name()} srgb={srgb}")
    MEL.connect_material_expressions(tex, "", node, "Map")
    MEL.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    ok = EAL.save_asset(f"{PATH}/M_WatchPlanet")
    log(f"{'OK  ' if ok else 'FAIL'} M_WatchPlanet")


log("=== watch materials starting ===")
if not EAL.does_directory_exist(PATH):
    EAL.make_directory(PATH)
build_map()
build_planet()
log("WATCH MATERIALS DONE")
