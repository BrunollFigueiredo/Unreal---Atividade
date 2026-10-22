import uuid, pathlib
ROOT = pathlib.Path(__file__).parent
def guid(): return uuid.uuid4().hex.upper()
def q(value): return '"' + str(value).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n') + '"'
nodes=[]
class Node:
    def __init__(self, name, cls, x, y, **props):
        self.name=name; self.cls=cls; self.x=x; self.y=y; self.props=props; self.pins=[]; nodes.append(self)
    def pin(self,name,kind='exec',out=False,obj=None,default=None,**extra):
        p={'id':guid(),'name':name,'kind':kind,'out':out,'obj':obj,'default':default,'extra':extra,'links':[], 'node':self}
        self.pins.append(p); return p
def link(a,b): a['links'].append(b); b['links'].append(a)
def call(name,fn,owner,x,y,pure=False):
    return Node(name,'K2Node_CallFunction',x,y,FunctionReference=f'(MemberParent="/Script/CoreUObject.Class\'/Script/Engine.{owner}\'",MemberName="{fn}")',**({'bIsPureFunc':'True'} if pure else {}))
def variable(name,var,x,y,set=False,external=False,kind='int'):
    ref=f'(MemberName="{var}",bSelfContext=True)'
    if external: ref=f'(MemberParent="/Script/Engine.BlueprintGeneratedClass\'/Game/Moedas/BP_ContadorMoedas.BP_ContadorMoedas_C\'",MemberName="{var}")'
    n=Node(name,'K2Node_VariableSet' if set else 'K2Node_VariableGet',x,y,VariableReference=ref)
    if set: n.exe=n.pin('execute'); n.then=n.pin('then',out=True)
    n.value=n.pin(var,kind,out=not set)
    if set: n.result=n.pin('Output_Get',kind,out=True)
    if external: n.target=n.pin('self','object',obj='/Game/Moedas/BP_ContadorMoedas.BP_ContadorMoedas_C')
    return n

event=Node('Coletar','K2Node_Event',0,0,EventReference='(MemberParent="/Script/CoreUObject.Class\'/Script/Engine.Actor\'",MemberName="ReceiveActorBeginOverlap")',bOverrideFunction='True')
event.then=event.pin('then',out=True); other=event.pin('OtherActor','object',True,'/Script/Engine.Actor')
player=call('Jogador','GetPlayerPawn','GameplayStatics',0,240,True); player.pin('PlayerIndex','int',default='0'); pawn=player.pin('ReturnValue','object',True,'/Script/Engine.Pawn')
equal=call('SomenteJogador','EqualEqual_ObjectObject','KismetMathLibrary',250,180,True)
link(other,equal.pin('A','object',obj='/Script/CoreUObject.Object')); link(pawn,equal.pin('B','object',obj='/Script/CoreUObject.Object')); eq=equal.pin('ReturnValue','bool',True)
branch=Node('EhJogador','K2Node_IfThenElse',520,0); link(event.then,branch.pin('execute')); link(eq,branch.pin('Condition','bool')); yes=branch.pin('then',out=True); branch.pin('else',out=True)
already=variable('TravaColeta','JaColetada',520,240,kind='bool')
guard=Node('EvitarDuplicacao','K2Node_IfThenElse',780,0); link(yes,guard.pin('execute')); link(already.value,guard.pin('Condition','bool')); guard.pin('then',out=True); proceed=guard.pin('else',out=True)
instance=call('ContadorSessao','GetGameInstance','GameplayStatics',780,240,True); gi=instance.pin('ReturnValue','object',True,'/Script/Engine.GameInstance')
cast=Node('AcessarContador','K2Node_DynamicCast',1040,0,TargetType='"/Script/Engine.BlueprintGeneratedClass\'/Game/Moedas/BP_ContadorMoedas.BP_ContadorMoedas_C\'"',bIsPureCast='False')
link(proceed,cast.pin('execute')); link(gi,cast.pin('Object','object',obj='/Script/CoreUObject.Object')); ok=cast.pin('then',out=True); cast.pin('CastFailed',out=True); wallet=cast.pin('AsBP Contador Moedas','object',True,'/Game/Moedas/BP_ContadorMoedas.BP_ContadorMoedas_C')
lock=variable('MarcarColetada','JaColetada',1360,0,set=True,kind='bool'); lock.value['default']='true'; link(ok,lock.exe)
value=variable('ValorDaMoeda','ValorMoeda',1050,440)
clamp=call('ValorPositivo','Max','KismetMathLibrary',1320,440,True); link(value.value,clamp.pin('A','int')); clamp.pin('B','int',default='1'); positive=clamp.pin('ReturnValue','int',True)
total=variable('TotalAtual','TotalMoedas',1320,250,external=True); link(wallet,total.target)
add=call('SomarMoedas','Add_IntInt','KismetMathLibrary',1590,270,True); link(total.value,add.pin('A','int')); link(positive,add.pin('B','int')); sum_pin=add.pin('ReturnValue','int',True)
save=variable('AtualizarTotal','TotalMoedas',1840,0,set=True,external=True); link(lock.then,save.exe); link(wallet,save.target); link(sum_pin,save.value)
conv=call('TotalComoTexto','Conv_IntToString','KismetStringLibrary',2080,270,True); link(save.result,conv.pin('InInt','int')); string=conv.pin('ReturnValue','string',True)
concat=call('TextoContador','Concat_StrStr','KismetStringLibrary',2330,250,True); concat.pin('A','string',default='Moedas: '); link(string,concat.pin('B','string')); label=concat.pin('ReturnValue','string',True)
print_node=call('MostrarTotal','PrintString','KismetSystemLibrary',2600,0); link(save.then,print_node.pin('execute')); printed=print_node.pin('then',out=True); link(label,print_node.pin('InString','string')); print_node.pin('bPrintToScreen','bool',default='true'); print_node.pin('bPrintToLog','bool',default='true'); print_node.pin('TextColor','struct',obj='/Script/CoreUObject.LinearColor',default='(R=1.0,G=0.8,B=0.05,A=1.0)'); print_node.pin('Duration','real',default='3.0',subcategory='float'); print_node.pin('Key','name',default='ContadorMoedas')
destroy=call('Desaparecer','K2_DestroyActor','Actor',2920,0); link(printed,destroy.pin('execute')); destroy.pin('then',out=True)

parts=[]
for n in nodes:
    parts.append(f'Begin Object Class=/Script/BlueprintGraph.{n.cls} Name="{n.name}"')
    for k,v in n.props.items(): parts.append(f'   {k}={v}')
    parts.extend([f'   NodePosX={n.x}',f'   NodePosY={n.y}',f'   NodeGuid={guid()}'])
    for p in n.pins:
        fields=[f'PinId={p["id"]}',f'PinName={q(p["name"])}']
        if p['out']: fields.append('Direction="EGPD_Output"')
        fields.append(f'PinType.PinCategory="{p["kind"]}"')
        if p['obj']:
            cls='ScriptStruct' if p['kind']=='struct' else ('BlueprintGeneratedClass' if p['obj'].startswith('/Game/') else 'Class')
            prefix='/Script/Engine.' if cls=='BlueprintGeneratedClass' else '/Script/CoreUObject.'
            fields.append(f'PinType.PinSubCategoryObject="{prefix}{cls}\'{p["obj"]}\'"')
        if p['extra'].get('subcategory'): fields.append(f'PinType.PinSubCategory="{p["extra"]["subcategory"]}"')
        if p['default'] is not None: fields.append('DefaultValue='+q(p['default']))
        if p['links']: fields.append('LinkedTo=('+''.join(f'{v["node"].name} {v["id"]},' for v in p['links'])+')')
        parts.append('   CustomProperties Pin ('+','.join(fields)+',)')
    parts.append('End Object')
(ROOT/'BP_Moeda_graph.txt').write_text('\n'.join(parts),encoding='utf-8')
print(f'{len(nodes)} nodes written')
