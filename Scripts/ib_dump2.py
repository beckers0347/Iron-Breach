import unreal
unreal.EditorLoadingAndSavingUtils.load_map("/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison")
P = lambda s: unreal.log("TFDUMP " + s)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    c = a.get_class().get_name()
    if c == "DirectionalLight":
        lc = a.get_component_by_class(unreal.DirectionalLightComponent)
        P("sun color=%s" % (lc.get_editor_property("light_color"),))
        for n in ("intensity","cast_shadows","atmosphere_sun_light","atmosphere_sun_light_index","cast_volumetric_shadow","affects_world","mobility","use_temperature","temperature"):
            try: P("sun %s=%s" % (n, lc.get_editor_property(n)))
            except Exception as e: P("sun %s ERR" % n)
        P("sun rot=%s" % a.get_actor_rotation())
    if c == "SkyLight":
        lc = a.get_component_by_class(unreal.SkyLightComponent)
        P("sky color=%s int=%s" % (lc.get_editor_property("light_color"), lc.get_editor_property("intensity")))
    if c=="PostProcessVolume":
        s=a.get_editor_property("settings")
        for n in dir(s):
            if "exposure" in n and not n.startswith("override") and not n.startswith("_"):
                try: P("pp %s=%s" % (n, s.get_editor_property(n)))
                except Exception: pass
open("X:/IronBreach/Saved/tf_dump_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
