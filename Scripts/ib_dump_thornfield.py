import unreal, collections, json
unreal.EditorLoadingAndSavingUtils.load_map("/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison")
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
cnt = collections.Counter(a.get_class().get_name() for a in acts)
P = lambda s: unreal.log("TFDUMP " + s)
P("TOTAL %d" % len(acts)); 
for k, v in cnt.most_common(): P("CLASS %s %d" % (k, v))
def g(o, n):
    try: return o.get_editor_property(n)
    except Exception as e: return "ERR"
for a in acts:
    c = a.get_class().get_name()
    if c in ("DirectionalLight","SkyLight","ExponentialHeightFog","PostProcessVolume","SkyAtmosphere","VolumetricCloud","Landscape","PlayerStart","LightmassImportanceVolume"):
        comp = None
        P("ACT %s %s loc=%s rot=%s" % (c, a.get_actor_label(), a.get_actor_location(), a.get_actor_rotation()))
        if c == "DirectionalLight":
            lc = a.get_component_by_class(unreal.DirectionalLightComponent)
            P("  sun intensity=%s color=%s temp=%s usetemp=%s" % (g(lc,"intensity"), g(lc,"light_color"), g(lc,"temperature"), g(lc,"use_temperature")))
        if c == "SkyLight":
            lc = a.get_component_by_class(unreal.SkyLightComponent)
            P("  sky intensity=%s color=%s realtime=%s srctype=%s" % (g(lc,"intensity"), g(lc,"light_color"), g(lc,"real_time_capture"), g(lc,"source_type")))
        if c == "ExponentialHeightFog":
            lc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
            for n in ("fog_density","fog_height_falloff","fog_inscattering_color","volumetric_fog","start_distance","fog_max_opacity","directional_inscattering_color"):
                P("  fog %s=%s" % (n, g(lc,n)))
        if c == "PostProcessVolume":
            s = g(a, "settings")
            for n in ("override_auto_exposure_bias","auto_exposure_bias","override_color_gain","color_gain","override_color_saturation","color_saturation","auto_exposure_min_brightness","auto_exposure_max_brightness","override_auto_exposure_min_brightness"):
                P("  pp %s=%s" % (n, g(s,n)))
            P("  unbound=%s" % g(a,"unbound"))
# extents of actors by label prefix
pre = collections.defaultdict(list)
for a in acts:
    l = a.get_actor_label()
    key = ''.join(ch for ch in l.split('_')[0:2] and '_'.join(l.split('_')[:2]) if not ch.isdigit())
    pre[key].append(a)
for k, v in sorted(pre.items(), key=lambda kv: -len(kv[1]))[:60]:
    P("LABEL %s n=%d first=%s" % (k, len(v), v[0].get_actor_location()))
open("X:/IronBreach/Saved/tf_dump_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
