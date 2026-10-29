# Integracao HTTP / JSON — atividade 5.7

Blueprint: Content/bp_http.uasset.
Estrutura JSON: Content/Struct_PlayerAPI.uasset (campo nome do tipo String).
Plugins HttpBlueprint e JsonBlueprintUtilities habilitados.

No mapa Untitled, o ator API_Player_Select_Insert_Delete recebe os comandos:
- BeginPlay e G: SelectBD, GET /player/{PlayerId}, le nome e salva em NomePlayer.
- I: InsertBD, converte a estrutura com NomePlayer em JSON, envia POST /player/insertPlayer e guarda insertId em PlayerId.
- Delete: DeleteBD, envia DELETE /player/deletePlayer/{PlayerId}.

Selecione o ator no mapa para configurar ApiBaseUrl, PlayerId e NomePlayer.
ApiBaseUrl padrao: http://127.0.0.1:3000 (sem barra final).
Aperte Play, clique na janela do jogo e use as teclas.
Mensagens ficam na tela e no Output Log. Nenhuma exclusao ocorre no BeginPlay.

API: C:\Users\Bruno\API_Connect_Game.
Dependencias instaladas. Preencha .env conforme .env.example e crie a tabela usando schema.sql.
Execute iniciar-api.cmd. GET /health confirma a conexao com MySQL.
O banco real depende das credenciais locais; o arquivo .env nao e versionado.

As imagens mostram GET /player ligado a um campo nome, mas essa rota retorna uma lista.
Por isso o Blueprint consulta /player/{PlayerId}, que retorna o objeto esperado.
O nome no POST e String, pois a coluna nome e textual; nao e um Set de Strings.
DELETE usa o ID da URL; nenhum corpo e necessario para identificar o registro.
O plugin HTTP considera resposta HTTP recebida como sucesso de transporte mesmo em 404:
os fluxos de escrita tambem verificam o campo success retornado pela API.

Copia anterior de bp_http, Untitled e DefaultEngine.ini: work/player_api/backup.
Codigo da ferramenta de montagem e relatorios: work/player_api.
A ferramenta e usada apenas na edicao; o jogo usa somente os plugins oficiais HTTP/JSON.
