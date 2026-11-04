# Duck Box Trainer — 0.3.0-alpha / Fabric 1.21.4

Treino local de Box PvP com bot ServerPlayerEntity, inventario e fisica vanilla,
arena procedural, modos de combate e quatro cosmeticos locais independentes do
DuckClientZ. Esta e uma alpha: a aparencia e a naturalidade exigem teste em jogo.

## Instalar / atualizar

- Minecraft Java1.21.4, Java21, Fabric Loader0.16.10+ e Fabric API0.119.3+1.21.4.
- Coloque apenas o JAR0.3.0 em `mods`, substituindo o DuckBox anterior.
- Para um mundo novo, copie `saves/DuckBoxTreino` para `.minecraft/saves`.
- O mundo DuckBoxTreino antigo pode ser reutilizado. Na primeira entrada,
  o mod reconstrui o painel para incluir os controles novos e mover o bau.
- Ha um jogador contra um bot por mundo. Comandos/controles exigem operador;
  o mundo do pacote ja permite comandos. Servidor privado: mod e Fabric API
  tambem no cliente de quem vai treinar. Nao e um bot para servidor publico.

Fabric API: https://modrinth.com/mod/fabric-api/version/0.119.3+1.21.4
O ZIP inclui um template de mundo plano; arena e lobby sao gerados pelo mod.

## Comecar

Abra o mundo, aguarde a montagem e escolha **DUEL** para combate. **TANK** e
um treino separado de sobrevivencia/evasao: nesse modo o bot nao ataca.
Escolha as regras, edite o bau do kit se quiser e clique em iniciar.
`/box parar` encerra e restaura o inventario anterior.

Arena padrao13x13, altura interna7. Tamanhos externos impares de9 a41 por
comando. O lobby inclui piso, iluminacao, estatua de pato e painel. A montagem
ocorre em lotes. `/box criar` em outro mundo edita um volume41x41x11 e o lobby
ao lado: use um local sem construcoes suas nesse volume.

## Regras: mesmo HP, dano/resistencia diferentes

| Regras | Vida maxima com o set/offhand | Atributo da espada | Resistencia mantida |
| --- | --- | --- | --- |
| NORMAL_SPAM | 135 | +20 | II |
| INSTA_KILL | 135 | +26, set anterior | I |

Afiacao54 permanece no preset. Os valores de dano sao modificadores: ataque
base, encantamento, armadura e efeitos continuam calculados pelo Minecraft.
A cadencia e15 tentativas em20 ticks elegiveis, em todas as dificuldades;
a20TPS equivale a15 CPS. Nao ignora invulnerabilidade entre danos nem alcance.
A precisao da mira e as decisoes variam com a dificuldade.

Ao iniciar, os dois recebem RegeneracaoII por20 segundos, AbsorcaoIV por2
minutos, Resistencia ao Fogo por5 minutos e a Resistencia do modo. A resistencia
e mantida durante o treino e reaplicada quando o totem remove os efeitos.
Regeneracao/absorcao nao sao infinitas: macas e totem seguem seus efeitos reais.
Dano de queda e colisao de elytra na parede sao cancelados apenas para os dois
participantes durante a partida. Outros danos e jogadores seguem vanilla.

## Kit padrao e totem vanilla

- Cabeca RasyMc com perfil/textura do jogador, Protecao60 e +60 de vida.
- Elytra inquebravel, +25 de vida, +255 de velocidade de ataque.
- **Um** corante amarelo brilhante na offhand: +30 de vida e +1,5 de dano.
  Ele **nao e um totem** e nao tem componente de protecao contra morte.
- Espada de ouro inquebravel, Afiacao54 e dano conforme as regras.
- Pernas e botas de netherita inquebraveis.
- Tres totens **vanilla** na hotbar e nove de reserva;128 foguetes,
  32 macas encantadas e32 teias. Sem reposicao infinita.

Vida com o corante:20+60+25+30=135. Ao trocar por totem, os30 de vida maxima e
1,5 de dano do corante deixam de valer; voltam quando ele retorna a offhand.
O bot guarda o corante e equipa totem com pouca vida. Se recuperar o suficiente,
troca de volta, sem duplicar nem apagar os itens. Retotem seleciona o totem na
mao principal e depois troca para a offhand; sem estoque na hotbar, pausa,
agacha e move ate tres totens existentes da reserva. O inventario do NPC e
simulado com essas pausas; nao aparece uma janela de inventario dele para voce.
O jogador controla sua propria troca de offhand normalmente.

Cada modo tem seu proprio kit salvo. Kits personalizados da alpha anterior
sao migrados para Insta Kill. Os antigos corantes-totens do nosso preset sao
convertidos em totens vanilla, preservando apenas o corante de bonus na offhand.
Para usar o preset novo em vez de um kit personalizado, selecione o modo e use
`/box kit padrao`. Nao apague o mundo/config para isso.

## Bau de kit

Abra o **KIT DOS DOIS**, perto do painel. Fechar o bau salva o modo selecionado.

- Linhas1..3:27 slots do inventario.
- Linha4:9 slots da hotbar.
- Linha5, primeiras5 colunas: cabeca, elytra/peitoral, calcas, botas e offhand.
- Linha6: legendas bloqueadas; os outros espacos reservados nao aceitam itens.

Os dois recebem copias independentes e iguais do kit. So um editor pode estar
aberto por vez. Feche-o antes de mudar regras/tamanho ou iniciar.
`/box kit salvar` tambem permite capturar seu inventario completo.

Segure um item e use `/box atributo minecraft:max_health 60 HEAD`, por exemplo,
para adicionar/editar nosso modificador daquele slot. `attack_damage` e dano;
`attack_speed` e cadencia. Depois equipe/organize e salve o kit.

## Gap, giro e foguete

- Conforme a vida e a situacao, o bot tenta comer uma ou duas macas reais.
- Parte das tentativas inclui decolar e buscar uma quina alta, perto do teto;
  as demais podem ocorrer no chao. Precisa de elytra/foguetes no kit e giro ligado.
- Dano repetido, inclusive na absorcao, interrompe a tentativa para retomar a luta.
- O estilo de giro proximo do alvo foi preservado. Acrescentou-se a oportunidade
  de usar foguete no ar para perseguir alvo distante/planando/tentando comer.
  Ele so causa dano se a mira alcancar a hitbox sem parede no caminho.
- O nivel de giro e independente da mira: BAIXO, MEDIO, ALTO, EXTREMO.
  EXTREMO permite usar foguetes/reposicionar com mais frequencia; consome o
  estoque real. A mira continua limitada pela dificuldade, sem hits automaticos.
- Teia oportunista com suporte, alcance/visibilidade e intervalo padrao10s.
- A extensao foguete-na-teia e sincronizada apenas para os participantes durante
  um impulso real. Nao altera outros jogadores/mundos fora do treino.

## Cosmeticos no proprio mod

Incluidos: **punho Blood, aura Money, oculos gamer e chapeu de sapo**, com modelos,
texturas e animacoes dos packs fornecidos. Nao precisa instalar DuckClientZ.
Aparecem no jogador local e no bot. Para conferir em terceira pessoa use F5;
o Blood tambem aparece na mao vazia em primeira pessoa. Com item na mao,
a renderizacao de primeira pessoa continua a normal do jogo.

Use `/box cosmetico blood`, `money`, `oculos` ou `sapo` para alternar cada um.
Os modelos/texturas sao carregados uma vez; animacao usa o relogio do mundo.
O renderer usa vertices/UVs diretos e a API vanilla, sem caches privados de
Sodium. Creditos e identificadores originais em `CREDITOS-COSMETICOS.txt`.
Nao ha site, telemetria, chat global, banco online nem auto-update neste mod.

## Comandos principais

```text
/box criar 13
/box iniciar
/box parar
/box dificuldade LOW|MEDIUM|HIGH|EXPERT
/box modo DUEL|TANK
/box regras NORMAL_SPAM|INSTA_KILL
/box giro BAIXO|MEDIO|ALTO|EXTREMO
/box habilidade giro|gap|retotem|teia|wtap|strafe|foguete_teia
/box kit salvar
/box kit padrao
/box atributo minecraft:attack_damage 20 MAINHAND
/box cosmetico blood|money|oculos|sapo
```

As barras `|` indicam opcoes: digite apenas uma delas. O painel oferece botoes
para modo, regras, nivel de giro e tamanho, e alavancas para as habilidades.
Configuracao e kits ficam em `duckbox-training.json` dentro do mundo.
O inventario, modo, posicao e efeitos anteriores sao salvos antes do treino e
restaurados ao encerrar ou reconectar. Nao apague esse arquivo com uma rodada
pendente. O treino termina antes da morte sem totem para evitar drops do set.

## Validacao e limites

Compila contra as classes reais de Minecraft1.21.4. Ha testes de cadencia, kits,
encantamentos, correspondencia de41 slots, perfil RasyMc, NBT e geracao do mapa;
aplicacao de Mixins comuns e do braco em primeira pessoa; geometria/animacao
finita dos quatro cosmeticos. O Blood espelhado foi comparado com vertices,
UVs e normais dos cubos nativos.

Num TestServer vanilla sem janela, com entidades, itens e fisica reais, foram
verificados dano/locomocao, buffs iniciais, consumo de totem vanilla, resistencia
apos pop, troca corante/totem, reposicao de reserva, consumo de duas macas,
bau/JSON independente por modo e montagem do mapa. O cancelamento ambiental
foi conferido como predicado usado pelo evento; a integracao Fabric e aplicada
em jogo. Os testes de rede validam codecs; nao simulam uma conexao grafica.

**Nao houve teste com cliente grafico.** A aparencia dos cosmeticos e o resultado
fino da recuperacao nas quinas/perseguicao aerea ainda precisam ser avaliados
jogando; nao se promete comportamento indistinguivel de humano ou ganho de FPS.
O clipe enviado excedeu32MiB e nao foi usado como referencia visual validada.
Resultados em `VALIDACAO.txt`.

## Build

Python3.10+ e JDK21:

```text
python bootstrap.py
python build.py
python make_map.py
python test.py
python test_mixins.py
python test_combat.py
```

O bootstrap baixa Minecraft/Yarn/Fabric/bibliotecas para `tools`. Nao entram no
JAR. Compila em nomes Yarn e remapeia para intermediary; alvos de Mixin fixos
da1.21.4. Assets dos quatro cosmeticos ja estao no fonte, sem depender de outro
mod para compilar ou executar. O codigo e MIT; direitos dos assets originais
nao sao alterados por essa licenca.
