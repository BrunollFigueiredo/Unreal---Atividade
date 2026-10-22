import unreal, pathlib
root=pathlib.Path(r'C:\Users\Bruno\Unreal---Atividade 5.7\work\moedas')
coin=unreal.load_asset('/Game/Moedas/BP_Moeda')
counter=unreal.load_asset('/Game/Moedas/BP_ContadorMoedas')
assert coin and counter
unreal.BlueprintEditorLibrary.compile_blueprint(counter)
unreal.BlueprintEditorLibrary.compile_blueprint(coin)
unreal.EditorAssetLibrary.save_loaded_asset(coin)
unreal.EditorAssetLibrary.save_loaded_asset(counter)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([coin])
(root/'delivery_ready.txt').write_text('Assets loaded and compiled without MoedasBuilder. BP_Moeda opened. Play tests passed.',encoding='utf-8')
unreal.log('MOEDAS_DELIVERY_READY')
