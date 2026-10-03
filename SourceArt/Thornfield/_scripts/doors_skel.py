"""Export every door of every building as a SKELETAL mesh FBX (1 bone at the pivot + 'open' animation).
Run:  python3 doors_skel.py <out_root>   (bpy module, headless)
Bone axes: bone points +Y world with roll 0, so pose-space == world axes (slide = metres along axis,
hinge = Euler rotation about the axis), identical to the keyframes used in the static build."""
import sys, os, json, math
import bpy
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[-1]
BUILD = {"BermBunker": "out_bunker", "CentralBunker": "out_central", "CommsTower": "out_comms",
         "GateCheckpoint": "out_gate", "HangarBlock": "out_hangar", "WatchTower": "out_watch",
         "RearShed": "out_SM_RearShed", "MessHall": "out_SM_MessHall"}
FRAMES = (1, 40)


def export_door(key, folder, dname, info):
    blend = os.path.join(HERE, folder, "SM_%s.blend" % key)
    bpy.ops.wm.open_mainfile(filepath=blend)
    scn = bpy.context.scene
    scn.render.fps = 30
    scn.frame_start, scn.frame_end = FRAMES
    door = bpy.data.objects[dname]
    door.animation_data_clear()
    # bake the object transform into the vertices (building space), object back to identity
    door.data.transform(door.matrix_world)
    door.parent = None
    door.matrix_world = Matrix.Identity(4)
    # armature with one bone at the pivot
    arm_data = bpy.data.armatures.new("Door_Arm")
    arm = bpy.data.objects.new("Door_Arm", arm_data)
    scn.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones.new("Door")
    p = Vector(info["pivot"])
    eb.head = p
    eb.tail = p + Vector((0, 0.5, 0))
    eb.roll = 0.0
    bpy.ops.object.mode_set(mode="OBJECT")
    # skin the whole door to that bone
    vg = door.vertex_groups.new(name="Door")
    vg.add(list(range(len(door.data.vertices))), 1.0, "REPLACE")
    mod = door.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    door.parent = arm
    # animation
    pb = arm.pose.bones["Door"]
    pb.rotation_mode = "XYZ"
    kind, ax, amount = info["type"], info["axis"], info["open"]
    pb.keyframe_insert("location" if kind == "slide" else "rotation_euler", frame=FRAMES[0])
    if kind == "slide":
        pb.location = Vector(ax) * amount
        pb.keyframe_insert("location", frame=FRAMES[1])
    else:
        idx = [i for i in range(3) if ax[i]][0]
        r = [0, 0, 0]
        r[idx] = math.radians(amount) * (1 if ax[idx] > 0 else -1)
        pb.rotation_euler = tuple(r)
        pb.keyframe_insert("rotation_euler", frame=FRAMES[1])
    pb.location = (0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    arm.select_set(True)
    door.select_set(True)
    os.makedirs(os.path.join(OUT, key), exist_ok=True)
    path = os.path.join(OUT, key, dname + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             axis_forward="-Y", axis_up="Z", global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_NONE", mesh_smooth_type="FACE", add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
                             path_mode="STRIP")
    print("DOOR", key, dname, kind, os.path.getsize(path))


n = 0
for key, folder in BUILD.items():
    doors = json.load(open(os.path.join(HERE, folder, "SM_%s.json" % key)))["doors"]
    for dname, info in doors.items():
        export_door(key, folder, dname, info)
        n += 1
print("TOTAL", n)
