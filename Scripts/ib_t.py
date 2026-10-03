import unreal
c = unreal.Color(r=255, g=147, b=71, a=255); unreal.log("TFDUMP kw=%s" % (c,))
c2 = unreal.Color(255,147,71,255); unreal.log("TFDUMP pos=%s" % (c2,))
c3 = unreal.Color(); c3.r=255; c3.g=147; c3.b=71; unreal.log("TFDUMP attr=%s" % (c3,))
unreal.EditorLoadingAndSavingUtils.load_map("/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison")
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name()=="DirectionalLight":
        lc=a.get_component_by_class(unreal.DirectionalLightComponent)
        lc.set_editor_property("light_color", c3)
        unreal.log("TFDUMP readback=%s  " % (lc.get_editor_property("light_color"),))
        unreal.log("TFDUMP lightcolor_attr=%s" % (lc.light_color,))
open("X:/IronBreach/Saved/tf_dump_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
