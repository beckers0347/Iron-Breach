import unreal

def import_raw_asset(file_path, dest_path, dest_name, is_mesh=False):
    """Imports an FBX or texture file from the local drive."""
    import_task = unreal.AssetImportTask()
    import_task.filename = file_path
    import_task.destination_path = dest_path
    import_task.destination_name = dest_name
    import_task.replace_existing = True
    import_task.automated = True
    import_task.save = True

    if is_mesh:
        fbx_options = unreal.FbxImportUI()
        fbx_options.import_mesh = True
        fbx_options.import_materials = False
        fbx_options.import_textures = False
        fbx_options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        import_task.options = fbx_options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])
    
    imported_objects = import_task.get_objects()
    return imported_objects[0] if imported_objects else None

def generate_and_wire_material(dest_path, asset_name, tex_color, tex_normal):
    """Generates a material, wires the textures, and compiles it."""
    material_name = f"M_{asset_name}"
    material_factory = unreal.MaterialFactoryNew()
    new_material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=material_name, package_path=dest_path,
        asset_class=unreal.Material, factory=material_factory
    )

    if tex_color:
        color_node = unreal.MaterialEditingLibrary.create_material_expression(
            new_material, unreal.MaterialExpressionTextureSample, -300, -150)
        color_node.texture = tex_color
        unreal.MaterialEditingLibrary.connect_material_property(
            color_node, "", unreal.MaterialProperty.MP_BASE_COLOR)

    if tex_normal:
        normal_node = unreal.MaterialEditingLibrary.create_material_expression(
            new_material, unreal.MaterialExpressionTextureSample, -300, 150)
        normal_node.texture = tex_normal
        unreal.MaterialEditingLibrary.connect_material_property(
            normal_node, "", unreal.MaterialProperty.MP_NORMAL)

    unreal.MaterialEditingLibrary.recompile_material(new_material)
    return new_material

def create_blueprint_with_mesh(dest_path, asset_name, static_mesh):
    """Creates an Actor Blueprint and adds the Static Mesh as a component."""
    bp_name = f"BP_{asset_name}"
    
    # 1. Create the base Blueprint Asset
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)
    
    my_blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=bp_name,
        package_path=dest_path,
        asset_class=unreal.Blueprint,
        factory=factory
    )
    
    if not my_blueprint:
        unreal.log_error("Failed to create Blueprint.")
        return None

    # 2. Access the Subobject Data Subsystem to add components (UE5 feature)
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    
    # Gather existing data (to find the root component)
    bp_data = subsystem.k2_gather_subobject_data_for_blueprint(my_blueprint)
    root_data_handle = bp_data[0] 
    
    # 3. Add a new Static Mesh Component
    add_params = unreal.AddNewSubobjectParams()
    add_params.parent_handle = root_data_handle
    add_params.new_class = unreal.StaticMeshComponent
    add_params.blueprint_context = my_blueprint
    
    component_handle, fail_reason = subsystem.add_new_subobject(add_params)
    
    if not fail_reason.is_empty():
        unreal.log_error(f"Failed to add component: {fail_reason}")
        return my_blueprint
        
    # 4. Apply the imported mesh to the newly created component
    subobject_data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(component_handle)
    component_template = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(subobject_data)
    
    if isinstance(component_template, unreal.StaticMeshComponent):
        component_template.set_editor_property("static_mesh", static_mesh)
        
    # 5. Compile the Blueprint to save changes
    unreal.BlueprintEditorLibrary.compile_blueprint(my_blueprint)
    unreal.log(f"Successfully generated Blueprint: {bp_name}")
    
    return my_blueprint

def spawn_asset_in_level(asset, location_xyz, rotation_pyr=(0.0, 0.0, 0.0)):
    """Spawns the final asset (Blueprint or Mesh) into the viewport."""
    spawn_location = unreal.Vector(*location_xyz)
    spawn_rotation = unreal.Rotator(*rotation_pyr)
    
    spawned_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        asset, spawn_location, spawn_rotation
    )
    return spawned_actor

def create_animation_blueprint(dest_path, asset_name, skeleton_package_path):
    """Creates a new Animation Blueprint assigned to a specific skeleton."""
    bp_name = f"ABP_{asset_name}"
    
    # 1. Load the target skeleton using its exact Unreal Engine path
    skeleton_asset = unreal.EditorAssetLibrary.load_asset(skeleton_package_path)
    
    if not isinstance(skeleton_asset, unreal.Skeleton):
        unreal.log_error(f"Failed to find a valid Skeleton at path: {skeleton_package_path}")
        return None

    # 2. Set up the specific factory for Animation Blueprints
    factory = unreal.AnimBlueprintFactory()
    factory.target_skeleton = skeleton_asset
    
    # 3. Create the Asset
    new_anim_bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=bp_name,
        package_path=dest_path,
        asset_class=unreal.AnimBlueprint,
        factory=factory
    )
    
    if new_anim_bp:
        unreal.log(f"Successfully generated Animation Blueprint: {bp_name}")
        
    return new_anim_bp

# =============================================================================
# IRON BREACH AUTOMATION PIPELINE
# =============================================================================
def run_iron_breach_pipeline():
    # Paths for Iron Breach assets
    source_mesh = "C:/Assets/Models/Kaiju_Alpha.fbx"
    source_color = "C:/Assets/Textures/Kaiju_Alpha_Color.png"
    source_normal = "C:/Assets/Textures/Kaiju_Alpha_Normal.png"
    
    unreal_dir = "/Game/IronBreach/Kaiju/Alpha"
    prefix = "Kaiju_Alpha"

    unreal.log("--- Executing Iron Breach Full Import Pipeline ---")
    
    # 1. Import
    mesh_obj = import_raw_asset(source_mesh, unreal_dir, f"SM_{prefix}", is_mesh=True)
    color_tex = import_raw_asset(source_color, unreal_dir, f"T_{prefix}_Color")
    normal_tex = import_raw_asset(source_normal, unreal_dir, f"T_{prefix}_Normal")

    # 2. Material
    if mesh_obj:
        gen_mat = generate_and_wire_material(unreal_dir, prefix, color_tex, normal_tex)
        if isinstance(mesh_obj, unreal.StaticMesh) and gen_mat:
            mesh_obj.set_material(0, gen_mat)

    # 3. Blueprint Generation
    if mesh_obj:
        blueprint_asset = create_blueprint_with_mesh(unreal_dir, prefix, mesh_obj)

    # 4. Spawn Blueprint into Level
    if blueprint_asset:
        spawned_bp = spawn_asset_in_level(
            asset=blueprint_asset, 
            location_xyz=(500.0, 0.0, 100.0), 
            rotation_pyr=(0.0, -90.0, 0.0) 
        )
        if spawned_bp:
            unreal.log(f"Success! Spawned Blueprint Actor: {spawned_bp.get_actor_label()}")

    # 5. Create Animation Blueprint (Make sure to use your exact Skeleton path here!)
    my_skeleton_path = "/Game/IronBreach/Characters/Infantry/Mesh/SK_Infantry_Skeleton.SK_Infantry_Skeleton"
    create_animation_blueprint(
        dest_path="/Game/IronBreach/Characters/Infantry/Animations", 
        asset_name="Infantry_Master", 
        skeleton_package_path=my_skeleton_path
    )

# Run it
run_iron_breach_pipeline()