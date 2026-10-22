report('GRAPH API ' + str([n for n in dir(unreal) if any(k in n for k in ['GraphEditor', 'K2Node', 'ObjectTools', 'GraphNode'])]))
bp = unreal.load_asset('/Game/Moedas/BP_Moeda')
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for prop in ['nodes', 'schema']:
    try: report('GRAPH PROPERTY ' + prop + ': ' + str(graph.get_editor_property(prop)))
    except Exception as e: report('GRAPH PROPERTY ' + prop + ': ' + str(e))
