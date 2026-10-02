"""Read-only menu art audit; run via Unreal's PythonScript commandlet.

Loads existing assets to report real item icon/mesh links, armor skeletons and
the infantry Blueprint defaults. Does not create, import, edit, or save assets;
does not open a map, spawn actors, capture icons, or touch player saves.
Each record is emitted as JSON with a [ReferenceAssets] prefix.
"""
import json
import unreal


def emit(kind, **record):
    unreal.log("[ReferenceAssets] " + json.dumps({"kind": kind, **record}, ensure_ascii=False, sort_keys=True))


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def path(obj):
    if obj is None:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def load(asset_path):
    try:
        return unreal.load_asset(asset_path)
    except Exception as error:
        emit("load_error", path=asset_path, error=str(error))
        return None


def texture_size(texture):
    if texture is None:
        return None
    try:
        return [texture.blueprint_get_size_x(), texture.blueprint_get_size_y()]
    except Exception:
        return None


def class_name(data):
    try:
        return str(data.asset_class_path.asset_name)
    except Exception:
        return str(data.asset_class)


def material_paths(obj):
    materials = prop(obj, "materials", prop(obj, "static_materials", []))
    return [path(prop(material, "material_interface")) for material in materials]


registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(synchronous_search=True)
item_paths = set()
for root in ("/Game/Weapons", "/Game/Items", "/Game/IronBreach/Items"):
    for data in registry.get_assets_by_path(root, recursive=True):
        name = str(data.asset_name)
        cls = class_name(data)
        package = str(data.package_name)
        if name.startswith(("DA_Visual_", "DA_Item_")):
            item_paths.add(package)
        if cls == "Texture2D" and "/Icons/" in package:
            texture = data.get_asset()
            emit("existing_icon", path=path(texture), pixels=texture_size(texture))

for asset_path in sorted(item_paths):
    asset = load(asset_path)
    if asset is None:
        continue
    if not isinstance(asset, unreal.IBItemDefinition):
        emit("non_item", path=path(asset), asset_class=asset.get_class().get_name())
        continue
    icon = prop(asset, "icon")
    mesh = prop(asset, "viewmodel_mesh")
    legacy_visual = prop(asset, "visual_data")
    if mesh is None and legacy_visual is not None:
        mesh = prop(legacy_visual, "viewmodel_mesh")
    emit("item", path=path(asset), asset_class=asset.get_class().get_name(),
         display_name=str(prop(asset, "display_name")), category=str(prop(asset, "category")),
         equip_slot=str(prop(asset, "equip_slot")), icon=path(icon), icon_pixels=texture_size(icon),
         viewmodel_mesh=path(mesh), legacy_visual=path(legacy_visual),
         combat=path(prop(asset, "combat_data")), mesh_materials=material_paths(mesh) if mesh else [])

mesh_paths = (
    "/Game/Characters/Infantry/Meshes/StarterArmor/SK_StarterArmor",
    "/Game/Characters/Infantry/Meshes/Chaos_Armor/Chaos_Armor",
    "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
    "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple",
)
for asset_path in mesh_paths:
    mesh = load(asset_path)
    if mesh is None:
        continue
    emit("body_mesh", path=path(mesh), asset_class=mesh.get_class().get_name(),
         skeleton=path(prop(mesh, "skeleton")), materials=material_paths(mesh),
         imported_bounds=str(prop(mesh, "imported_bounds", prop(mesh, "bounds"))))

for asset_path in (
    "/Game/Characters/Infantry/Animations/idle",
    "/Game/Characters/Infantry/Animations/idle__2_",
    "/Game/Characters/Infantry/Animations/idle__3_",
    "/Game/Characters/Infantry/Animations/Chaos_Armor_Anim",
    "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle",
):
    animation = load(asset_path)
    if animation:
        emit("idle_animation", path=path(animation), skeleton=path(prop(animation, "skeleton")))

for blueprint_path in (
    "/Game/Characters/Infantry/BP_IBCharacter_Infantry",
    "/Game/Characters/Infantry/Animations/ABP_InfantryTripo3D",
):
    blueprint = load(blueprint_path)
    if blueprint is None:
        continue
    emit("blueprint", path=path(blueprint), target_skeleton=path(prop(blueprint, "target_skeleton")))
    try:
        generated = blueprint.generated_class()
        default = unreal.get_default_object(generated)
        body = prop(default, "mesh")
        emit("infantry_default", path=path(default), male_body=path(prop(default, "male_body")),
             female_body=path(prop(default, "female_body")),
             body_mesh=path(prop(body, "skeletal_mesh_asset", prop(body, "skeletal_mesh"))) if body else None,
             anim_class=path(prop(body, "anim_class")) if body else None,
             body_rotation=str(prop(body, "relative_rotation")) if body else None,
             body_scale=str(prop(body, "relative_scale3d")) if body else None)
    except Exception as error:
        emit("default_error", path=blueprint_path, error=str(error))

emit("complete", item_candidates=len(item_paths), body_meshes=len(mesh_paths))
