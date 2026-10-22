import unreal, pathlib, traceback, json, time

ROOT = pathlib.Path(r'C:\Users\Bruno\Unreal---Atividade 5.7\work\moedas')
def report(message):
    with (ROOT / 'status.log').open('a', encoding='utf-8') as f:
        f.write(str(message) + '\n')
    unreal.log(str(message))

def setup():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    def bp(name, parent):
        path = '/Game/Moedas/' + name
        asset = unreal.load_asset(path)
        if not asset:
            factory = unreal.BlueprintFactory()
            factory.set_editor_property('parent_class', parent)
            asset = tools.create_asset(name, '/Game/Moedas', unreal.Blueprint, factory)
        return asset
    gi = bp('BP_ContadorMoedas', unreal.GameInstance)
    coin = bp('BP_Moeda', unreal.Actor)
    lib = unreal.BlueprintEditorLibrary
    for asset, name, kind, default in [(gi, 'TotalMoedas', 'int', 0), (coin, 'ValorMoeda', 'int', 1), (coin, 'JaColetada', 'bool', False)]:
        lib.add_member_variable(asset, name, lib.get_basic_type_by_name(kind))
        lib.compile_blueprint(asset)
        unreal.get_default_object(asset.generated_class()).set_editor_property(name, default)
    lib.set_blueprint_variable_instance_editable(coin, 'ValorMoeda', True)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(coin)
    root = handles[1]
    def component(name, cls):
        for h in sub.k2_gather_subobject_data_for_blueprint(coin):
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            if str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)) == name:
                return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, coin)
        handle, reason = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=coin))
        if str(reason): report('component ' + name + ': ' + str(reason))
        sub.rename_subobject(handle, name)
        return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle), coin)
    sphere = component('AreaColeta', unreal.SphereComponent)
    sphere.set_sphere_radius(65.0)
    sphere.set_collision_profile_name('Trigger')
    sphere.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
    sphere.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_OVERLAP)
    sphere.set_editor_property('generate_overlap_events', True)
    mesh = component('VisualMoeda', unreal.StaticMeshComponent)
    mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    mesh.set_editor_property('relative_scale3d', unreal.Vector(0.55, 0.55, 0.085))
    mesh.set_editor_property('relative_rotation', unreal.Rotator(90, 0, 0))
    mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    mesh.set_editor_property('generate_overlap_events', False)
    mat = unreal.load_asset('/Game/Moedas/M_MoedaDourada')
    if not mat:
        mat = tools.create_asset('M_MoedaDourada', '/Game/Moedas', unreal.Material, unreal.MaterialFactoryNew())
        mel = unreal.MaterialEditingLibrary
        color = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        color.set_editor_property('constant', unreal.LinearColor(1.0, 0.55, 0.035, 1.0))
        mel.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
        metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 160)
        metal.set_editor_property('r', 0.7)
        mel.connect_material_property(metal, '', unreal.MaterialProperty.MP_METALLIC)
        rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 260)
        rough.set_editor_property('r', 0.28)
        mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
    mesh.set_material(0, mat)
    rotation = component('RotacaoMoeda', unreal.RotatingMovementComponent)
    rotation.set_editor_property('rotation_rate', unreal.Rotator(0, 100, 0))
    lib.compile_blueprint(coin)
    for asset in [gi, coin, mat]: unreal.EditorAssetLibrary.save_loaded_asset(asset)
    for path in ['/Game/BC_Player', '/Game/perso/BC_Player', '/Game/NC_PLAYER']:
        asset = unreal.load_asset(path)
        if asset:
            report(path + ': ' + str(asset.generated_class()))
    report('SETUP_READY')
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([coin])

try:
    setup()
except Exception:
    report(traceback.format_exc())

def tick(delta):
    command = ROOT / 'command.py'
    if command.exists():
        source = command.read_text(encoding='utf-8-sig')
        command.rename(ROOT / ('executed_' + str(time.time_ns()) + '.py'))
        try: exec(compile(source, str(command), 'exec'), globals())
        except Exception: report(traceback.format_exc())

TICK_HANDLE = unreal.register_slate_post_tick_callback(tick)

