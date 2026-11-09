# Coleta de moedas

- Blueprint: `/Game/Moedas/BP_Moeda`.
- Arraste cópias para o seu mapa e ajuste `ValorMoeda` no painel Details (mínimo efetivo: 1).
- Ao encostar com o jogador local (Player 0), a moeda soma seu valor, mostra `Moedas: total` por 3 segundos e desaparece. Outros atores não coletam. A variável `JaColetada` impede somas repetidas.
- O total fica em `TotalMoedas`, no `/Game/Moedas/BP_ContadorMoedas`, configurado como Game Instance do projeto. Para consultar: Get Game Instance → Cast to BP_ContadorMoedas → Get TotalMoedas.
- O contador dura durante a sessão, inclusive nas trocas de mapa. Um novo Play começa com o contador da sessão em zero. Quando a API local está ativa, a coleta também soma o valor ao total do jogador no MySQL.

## Testar

Abra `/Game/Untitled`, pressione Play e percorra o mapa até a moeda. Use a API em `http://127.0.0.1:3000` para persistir as coletas.

O texto usa Print String para o protótipo (Development/Editor); não é um HUD para distribuição Shipping.

Validado em Play no Editor: compilação sem erros/avisos, rotação, bloqueio de outro pawn, coleta das cinco moedas, remoção e total final de 9 sem duplicação. Resultados em `work/moedas/test_results.json`.

Os assets são Blueprints e material nativos, sem dependência da ferramenta de geração. A pasta `work/moedas` contém os fontes da geração e os resultados de validação.
