settings = unreal.GameMapsSettings.get_game_maps_settings()
settings.set_editor_property('game_instance_class', unreal.SoftClassPath('/Game/Moedas/BP_ContadorMoedas.BP_ContadorMoedas_C'))
config = ROOT.parent.parent / 'Config' / 'DefaultEngine.ini'
text = config.read_text(encoding='utf-8-sig')
line = 'GameInstanceClass=/Game/Moedas/BP_ContadorMoedas.BP_ContadorMoedas_C'
if line not in text:
    text = text.replace('[/Script/EngineSettings.GameMapsSettings]', '[/Script/EngineSettings.GameMapsSettings]\n' + line, 1)
    config.write_text(text, encoding='utf-8')

level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level.new_level('/Game/Moedas/Mapa_TesteMoedas')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(600, 0, -25))
floor.set_actor_label('Piso_TesteMoedas')
floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(unreal.Vector(20, 8, 0.5))
sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-45, -30, 0))
sun.light_component.set_intensity(4.0)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 400))
sky.light_component.set_editor_property('real_time_capture', True)
actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 120))
coin_cls = unreal.load_class(None, '/Game/Moedas/BP_Moeda.BP_Moeda_C')
for i in range(5):
    actor = actors.spawn_actor_from_class(coin_cls, unreal.Vector(300+i*200, 0, 120))
    actor.set_actor_label('Moeda_%02d' % (i+1))
    actor.set_editor_property('ValorMoeda', 1 if i < 4 else 5)

unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(-350, -650, 500), unreal.Rotator(-18, 40, 0))
level.save_current_level()
unreal.EditorAssetLibrary.save_directory('/Game/Moedas')
report('DEMO_READY')
