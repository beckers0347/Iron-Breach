"""
Check whether the IK Rig / IK Retargeter Python API and plugin are actually
available in this project before attempting to script anything with them --
we've already hit two cases this session (SkeletalMeshLibrary, and the FBX
armature_nodetype quirk) where an API or plugin assumption turned out wrong
and cost a round trip. Cheap to check up front this time.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/check_ikrig_api.py"
"""

import unreal

names_to_check = [
    "IKRigController",
    "IKRigDefinition",
    "IKRetargeter",
    "IKRetargeterController",
    "IKRigBoneChain",
    "RigElementType",
]

for name in names_to_check:
    exists = hasattr(unreal, name)
    unreal.log(f"[CheckIKRig] unreal.{name}: {'FOUND' if exists else 'missing'}")

# Also check whether the IKRig plugin's asset factory classes are registered,
# which tells us whether the plugin is enabled at all even if these specific
# class names are wrong.
factory_candidates = [n for n in dir(unreal) if 'IKRig' in n or 'Retarget' in n]
unreal.log(f"[CheckIKRig] All unreal.* names containing 'IKRig' or 'Retarget': {factory_candidates}")
