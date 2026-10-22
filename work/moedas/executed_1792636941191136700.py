import json
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(unreal.load_asset('/Game/Moedas/BP_Moeda'))
level.load_level('/Game/Moedas/Mapa_TesteMoedas')
TEST = {'stage': 'start', 'next': time.monotonic()+2, 'checks': [], 'index': 0}
def check(name, condition, detail):
    TEST['checks'].append({'name':name,'passed':bool(condition),'detail':str(detail)})
    report('TEST ' + name + ': ' + str(condition) + ' ' + str(detail))
    if not condition: raise RuntimeError(name + ': ' + str(detail))
def test_tick(delta):
    if time.monotonic() < TEST['next']: return
    TEST['next'] = time.monotonic()+1.0
    try:
        stage = TEST['stage']
        if stage == 'start':
            level.editor_request_begin_play()
            TEST['stage'] = 'wait_world'
            TEST['next'] += 3
        elif stage == 'wait_world':
            world = unreal.EditorLevelLibrary.get_game_world()
            if not world: return
            player = unreal.GameplayStatics.get_player_pawn(world, 0)
            if not player: return
            TEST['world']=world; TEST['player']=player
            gi = unreal.GameplayStatics.get_game_instance(world)
            TEST['gi']=gi
            check('contador inicia zerado',gi.get_editor_property('TotalMoedas')==0,gi.get_editor_property('TotalMoedas'))
            cls=unreal.load_class(None,'/Game/Moedas/BP_Moeda.BP_Moeda_C')
            TEST['cls']=cls
            coins=sorted(unreal.GameplayStatics.get_all_actors_of_class(world,cls),key=lambda a:a.get_actor_location().x)
            TEST['coins']=coins
            check('cinco moedas na demonstracao',len(coins)==5,len(coins))
            TEST['rotation']=coins[0].get_actor_rotation().yaw
            transform=unreal.Transform(location=unreal.Vector(300,0,120))
            npc=unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(world,unreal.DefaultPawn,transform,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN)
            unreal.GameplayStatics.finish_spawning_actor(npc,transform)
            TEST['npc']=npc
            TEST['stage']='npc'
        elif stage == 'npc':
            check('outro pawn nao coleta',TEST['gi'].get_editor_property('TotalMoedas')==0,TEST['gi'].get_editor_property('TotalMoedas'))
            rotation=TEST['coins'][0].get_actor_rotation().yaw
            check('moeda gira',abs(rotation-TEST['rotation'])>0.1,rotation)
            TEST['npc'].destroy_actor()
            TEST['stage']='move'
        elif stage == 'move':
            i=TEST['index']
            TEST['player'].set_actor_location(unreal.Vector(300+i*200,0,120),False,True)
            TEST['stage']='collect'
        elif stage == 'collect':
            i=TEST['index']; expected=(i+1 if i<4 else 9)
            total=TEST['gi'].get_editor_property('TotalMoedas')
            check('coleta '+str(i+1),total==expected,total)
            remaining=unreal.GameplayStatics.get_all_actors_of_class(TEST['world'],TEST['cls'])
            check('moeda desaparece '+str(i+1),len(remaining)==4-i,len(remaining))
            TEST['index']+=1
            TEST['stage']='move' if TEST['index']<5 else 'stable'
        elif stage == 'stable':
            check('sem soma duplicada',TEST['gi'].get_editor_property('TotalMoedas')==9,TEST['gi'].get_editor_property('TotalMoedas'))
            level.editor_request_end_play()
            TEST['stage']='done'
        elif stage == 'done':
            (ROOT/'test_results.json').write_text(json.dumps({'passed':True,'checks':TEST['checks']},indent=2,ensure_ascii=False),encoding='utf-8')
            report('ALL_PLAY_TESTS_PASSED')
            unreal.unregister_slate_post_tick_callback(TEST_TICK_HANDLE)
    except Exception:
        report(traceback.format_exc())
        (ROOT/'test_results.json').write_text(json.dumps({'passed':False,'checks':TEST['checks'],'error':traceback.format_exc()},indent=2,ensure_ascii=False),encoding='utf-8')
        if level.is_in_play_in_editor(): level.editor_request_end_play()
        unreal.unregister_slate_post_tick_callback(TEST_TICK_HANDLE)
TEST_TICK_HANDLE=unreal.register_slate_post_tick_callback(test_tick)
