# Integracao HTTP / JSON — atividade 5.7

Blueprint: Content/bp_http.uasset.
Estrutura JSON: Content/Struct_PlayerAPI.uasset (campo nome do tipo String).
Plugins HttpBlueprint e JsonBlueprintUtilities habilitados.

No mapa Untitled, o ator API_Player_Select_Insert_Delete consulta o jogador no BeginPlay.
Ao coletar BP_Moeda, o jogo soma o valor no contador da sessão e chama SalvarMoedasColetadas.
O evento envia POST /player/coins/{PlayerId} com a quantidade da moeda.
O MySQL soma o valor na coluna moedas e cria o jogador local se o ID ainda não existir.
InsertBD e DeleteBD continuam disponíveis como eventos no Blueprint.

Selecione o ator no mapa para configurar ApiBaseUrl e PlayerId.
ApiBaseUrl padrão: http://127.0.0.1:3000 (sem barra final).
Para testar, aperte Play e percorra o mapa até encostar na moeda.

A API está em `API_Connect_Game`, na raiz do repositório.
Siga o README da pasta para instalar as dependências, preparar o MySQL e iniciar a API.
O `.env.example` usa `root` como usuário e senha da atividade.
O `.env` com as credenciais locais fica fora do Git.


As imagens mostram GET /player ligado a um campo nome, mas essa rota retorna uma lista.
Por isso o Blueprint consulta /player/{PlayerId}, que retorna o objeto esperado.
O nome no POST e String, pois a coluna nome e textual; nao e um Set de Strings.
DELETE usa o ID da URL; nenhum corpo e necessario para identificar o registro.
O plugin HTTP considera resposta HTTP recebida como sucesso de transporte mesmo em 404:
os fluxos de escrita tambem verificam o campo success retornado pela API.

Copia anterior de bp_http, Untitled e DefaultEngine.ini: work/player_api/backup.
Codigo da ferramenta de montagem e relatorios: work/player_api.
A ferramenta e usada apenas na edicao; o jogo usa somente os plugins oficiais HTTP/JSON.
