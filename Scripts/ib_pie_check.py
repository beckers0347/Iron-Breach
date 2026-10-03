"""Starts PIE on BoulderShore3, screenshots the player's view at set times, logs, quits. Saves nothing."""
import unreal, time, os
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
OUT = os.environ.get("IB_PIE_OUT", "X:/IronBreach/Saved/PIEShots/run")
SHOTS = [float(x) for x in os.environ.get("IB_PIE_TIMES", "4,12,22,30,38,46,54,64").split(",")]
os.makedirs(OUT, exist_ok=True)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
unreal.SystemLibrary.execute_console_command(None, "Log LogIronBreach Verbose")
st = {"t0": time.monotonic(), "phase": "wait", "pie_t0": None, "i": 0}

def tick(dt):
    try:
        _tick(dt)
    except Exception as e:
        unreal.log_error("PIECHK tick error %r" % e)
        st["i"] += 1


def _tick(dt):
    now = time.monotonic()
    if st["phase"] == "wait" and now - st["t0"] > 8:
        LES.editor_request_begin_play()
        st["phase"] = "play"; st["pie_t0"] = now
        unreal.log("PIECHK begin play requested")
    elif st["phase"] == "play":
        el = now - st["pie_t0"]
        if st["i"] < len(SHOTS) and el >= SHOTS[st["i"]]:
            name = "t%03d" % int(SHOTS[st["i"]])
            unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, OUT + "/" + name + ".png")
            pw = unreal.EditorLevelLibrary.get_game_world() if hasattr(unreal.EditorLevelLibrary, "get_game_world") else None
            if pw:
                for a in unreal.GameplayStatics.get_all_actors_of_class(pw, unreal.SkeletalMeshActor):
                    if a.get_name().startswith("NPC") or "NPC" in a.get_actor_label() if hasattr(a, "get_actor_label") else False:
                        pass
                for a in unreal.GameplayStatics.get_all_actors_of_class(pw, unreal.SkeletalMeshActor):
                    l = a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name()
                    if "PLACEHOLDER" in l:
                        c = a.skeletal_mesh_component
                        try:
                            unreal.log("PIECHK %s ANIM %s mode=%s playing=%s anim=%s footL=%s hand=%s" % (l, name, c.get_animation_mode(), c.is_playing(), c.get_editor_property("animation_data").get_editor_property("anim_to_play"), c.get_socket_location("LeftFoot"), c.get_socket_location("Hips")))
                        except Exception as ex:
                            unreal.log("PIECHK anim probe err %r" % ex)
                        loc = a.get_actor_location(); r = a.get_actor_rotation()
                        unreal.log("PIECHK %s %s at (%.0f,%.0f,%.0f) yaw %.0f hidden=%s" % (name, l, loc.x, loc.y, loc.z, r.yaw, a.get_editor_property("hidden")))
                pc = unreal.GameplayStatics.get_player_pawn(pw, 0)
                if pc:
                    loc = pc.get_actor_location()
                    unreal.log("PIECHK %s player at (%.0f,%.0f,%.0f)" % (name, loc.x, loc.y, loc.z))
            st["i"] += 1
        elif st["i"] >= len(SHOTS) and el > SHOTS[-1] + 4:
            LES.editor_request_end_play()
            st["phase"] = "end"; st["end_t"] = now
    elif st["phase"] == "end" and now - st["end_t"] > 4:
        unreal.unregister_slate_post_tick_callback(st["h"])
        open("X:/IronBreach/Saved/pie_done.txt", "w").write("ok")
        unreal.SystemLibrary.quit_editor()

st["h"] = unreal.register_slate_post_tick_callback(tick)
