"""Capture real recon stills with a settled editor viewport; never saves level packages.
Set IB_RECON_SHOT to carrow_gate, carrow_gate_yard, carrow_zone or firing_line.
Launch the editor with -ExecutePythonScript=<this file>. One map per process; exits without saving.
Editor frames (not a commandlet loop) are required for scene/texture streaming and exposure.
"""
import unreal, time, traceback, os
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
from pathlib import Path
OUT = Path(r"D:/Unreal Games/IronBreach/Saved/WatchPolish/recon")
OUT.mkdir(parents=True, exist_ok=True)
EAS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
# Editorial camera positions only; these do not change map authoring or gameplay.
SHOTS=[
 ("carrow_gate", "/Game/LevelPrototyping/CarrowGateGarrison", (-5000,-5800,3000), (-500,600,650)),
 ("carrow_gate_yard", "/Game/LevelPrototyping/CarrowGateGarrison", (6500,-6500,2600), (10500,-800,350)),
 ("carrow_zone", "/Game/Lvl_Plains", (-9000,-7000,10000), (13000,13000,0)),
 ("firing_line", "/Game/FirstPerson/Lvl_FirstPerson", (-200,-900,900), (1300,1100,250)),
]
SHOTS=[shot for shot in SHOTS if shot[0]==os.environ.get("IB_RECON_SHOT","carrow_gate")]
if not SHOTS: raise ValueError("Unknown IB_RECON_SHOT")
# Load before entering Slate tick: map replacement re-enters Slate while tearing down worlds.
unreal.EditorLoadingAndSavingUtils.load_map(SHOTS[0][1])
if SHOTS[0][0]=="carrow_zone":
 descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
 if descs: unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
state={"i":0,"phase":"load","deadline":time.monotonic()+4,"camera":None,"map":SHOTS[0][1]}
def finish():
 unreal.unregister_slate_post_tick_callback(state["handle"])
 unreal.log("IBRECON: finished; no levels saved")
 unreal.SystemLibrary.quit_editor()
def tick(dt):
 if time.monotonic()<state["deadline"] or state.get("busy",False): return
 state["busy"]=True
 try:
  if state["i"]>=len(SHOTS):
   finish(); return
  key,path,eye,look=SHOTS[state["i"]]
  if state["phase"]=="load":
   rot=unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*eye),unreal.Vector(*look))
   cam=EAS.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*eye),rot)
   cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view",70.0)
   state["camera"]=cam
   LES.set_level_viewport_camera_info(unreal.Vector(*eye),rot,LES.get_active_viewport_config_key())
   LES.editor_set_game_view(True)
   unreal.log(f"IBRECON: settling {key}")
   state["phase"]="capture"; state["deadline"]=time.monotonic()+14
  elif state["phase"]=="capture":
   state["task"]=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(key+".png")),state["camera"])
   unreal.log(f"IBRECON: screenshot requested {key}")
   state["phase"]="next"; state["deadline"]=time.monotonic()+5
  else:
   EAS.destroy_actor(state["camera"]); state["camera"]=None
   state["i"]+=1; state["phase"]="load"
 except Exception:
  unreal.log_error(traceback.format_exc()); finish()
 finally:
  state["busy"]=False
state["handle"]=unreal.register_slate_post_tick_callback(tick)
unreal.log("IBRECON: capture queue ready")
