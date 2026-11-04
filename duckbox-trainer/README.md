# Duck Box Trainer — teste 0.2.1-alpha / Fabric 1.21.4

Protótipo local de treino de Box PvP com um jogador controlado pelo servidor.
O NPC usa ServerPlayerEntity: o modelo, a hitbox, a animação, o inventário,
a elytra, o dano, o knockback e a proteção do totem seguem o Minecraft.
Não depende do DuckClientZ, de serviços online ou de plugins Bukkit.

## Instalar e jogar

1. Use Minecraft **Java 1.21.4**, Java 21 e **Fabric Loader 0.16.10 ou posterior**.
2. Instale **Fabric API 0.119.3+1.21.4** e o JAR da pasta `mods` do pacote.
   Fabric API: https://modrinth.com/mod/fabric-api/version/0.119.3+1.21.4
3. Extraia `saves/DuckBoxTreino` para a pasta `.minecraft/saves`.
4. Abra **DuckBoxTreino** no menu de mundos. A arena e o painel serão gerados
   na primeira entrada, em lotes. Aguarde a mensagem de montagem terminar.
5. No painel, clique nos controles e depois em **iniciar**. `/box iniciar`
   e `/box parar` também funcionam. O inventário anterior volta ao terminar.

A construção do mapa é procedural: o ZIP contém um template de mundo plano
válido, e o mod monta a caixa de vidro e o lobby. Não abra o mapa sem o mod.
A versão inicial comporta **um jogador contra um bot por mundo**. O foco é
singleplayer. Comandos e controles exigem permissão de operador; o mapa já
permite comandos. Num servidor privado, o mod e a Fabric API devem estar no
servidor e no cliente que vai treinar. Nenhuma integração com servidor público.

## Cadencia de ataque

O bot tenta atacar a15 CPS em todas as dificuldades, enquanto esta em combate,
com espada e perto do alvo. O agendamento distribui15 tentativas em20 ticks,
sem rajadas de compensacao. A mira continua podendo errar; dano e animacao
seguem as regras vanilla. Retotem, comer e trocar itens pausam as tentativas.
A taxa corresponde a15 por segundo com o servidor rodando a20TPS.

## Painel no mundo

- Botões: iniciar, parar, dificuldade, modo DUEL/TANK e tamanho.
- Alavancas: giro, retotem, gap, teia, W-tap, strafe e foguete na teia.
- Dificuldades: **LOW, MEDIUM, HIGH, EXPERT**.
- Tamanho padrao:13x13. Opcoes:9,13,17,21,25,33 e41 blocos de largura externa, paredes incluídas.
  Há também tamanhos ímpares intermediários por comando. Altura interna:7.
- Para mudar o tamanho, termine a partida. A construção anterior será refeita.

## Comandos

```text
/box
/box criar 25
/box iniciar
/box parar
/box dificuldade EXPERT
/box modo TANK
/box modo DUEL
/box habilidade giro
/box habilidade retotem
/box habilidade gap
/box habilidade teia
/box habilidade wtap
/box habilidade strafe
/box habilidade foguete_teia
/box kit salvar
/box kit padrao
/box atributo minecraft:max_health 100 HEAD
/box atributo minecraft:attack_damage 255 CHEST
/box atributo minecraft:attack_speed 255 CHEST
```

`habilidade` alterna ligado/desligado. `atributo` modifica o item que você está
segurando, com operação de adição e o slot de equipamento indicado. Exemplos:
segure a cabeça para adicionar vida em `HEAD`; segure a elytra para editar dano
ou velocidade em `CHEST`. Depois vista/organize os itens e execute
`/box kit salvar`. O jogador e o bot recebem cópias independentes e iguais do
inventário completo, incluindo equipamento e mão secundária. `kit padrao`
seleciona novamente o preset; não sobrescreve seu inventário naquele momento.
`attack_damage` muda o dano; `attack_speed` muda a cadência de recarga.

O novo kit padrao:

| Item | Configuracao |
| --- | --- |
| Cabeca de RasyMc | Skin real do perfil, Protecao60, +60 de vida |
| Elytra | Inquebravel, +25 de vida, +255 de velocidade de ataque |
| Corante amarelo | Brilho, +30 de vida e +1,5 de dano na offhand; funciona como totem |
| Espada de ouro | Inquebravel, modificador de dano26 e Afiacao54 |

Com os tres itens equipados, sao135 pontos de vida:20 nativos +60+25+30.
Os modificadores usam identificadores diferentes para que os bonus realmente
se somem. A espada soma seu modificador ao ataque base e ao encantamento,
seguindo as regras vanilla; a elytra nao adiciona mais255 de dano.
Ha treze corantes-totens no total (3 na hotbar,1 na offhand,9 de reserva),
128 foguetes,32 macas encantadas e32 teias. Pernas e botas de netherita
continuam no preset e podem ser retiradas pelo editor.
A protecao60 e a afiacao54 sao preservadas nos itens, com os limites de
reducao de dano e invulnerabilidade do Minecraft. Nao se multiplicam hits.

### Bau de kit

Abra o **KIT DOS DOIS** no lobby. O editor tem54 slots:

- Linhas1 a3: inventario principal (27 slots).
- Linha4: hotbar (9 slots).
- Linha5, primeiras5 colunas: cabeca, elytra/peitoral, calcas, botas, offhand.
- Linha6: legendas bloqueadas; os espacos reservados nao aceitam itens.

Edite e feche o bau para salvar. Na proxima rodada os dois recebem copias
independentes e iguais, incluindo atributos e encantamentos. So um editor
pode ficar aberto por vez. Feche-o antes de mudar o mapa ou iniciar o treino.

### Atualizar a alpha anterior

Substitua o JAR0.1.0 pelo0.2.0; nao deixe os dois em `mods`.
No mundo DuckBoxTreino antigo, a arena padrao25x25 migra para13x13 e o lobby
e reconstruido na entrada; o modo inicial volta para DUEL. Um kit que voce salvou manualmente e preservado;
use **/box kit padrao** se quiser aplicar o novo preset de RasyMc.
O pacote tambem inclui um template de mundo novo. Nao sobrescreva um mundo
com inventario de treino ainda pendente de restauracao.

## Comportamentos desta primeira versão

- Ataque tem prioridade durante reposicionamentos curtos perto do alvo; nao ha
  um giro360 continuo bloqueando os hits. O PvP so e liberado entre os dois
  participantes da rodada, mesmo se o mundo desabilitar PvP.
- Mira com erro e atraso de reação por dificuldade. O bot gira suavemente e
  pode errar ataques. Só causa dano se o raio da mira alcançar a hitbox, dentro
  do alcance permitido e sem bloco sólido no caminho.
- Pulo seguido de tentativa de ativar a elytra; foguetes são itens reais,
  consumidos do inventário. Os giros alteram a orientação e a trajetória, sem
  teletransportar o bot para produzir esquivas.
- Retotem em duas etapas: seleciona um totem da hotbar e, após um intervalo,
  passa para a offhand. Sem totens na hotbar, pausa e agacha para mover até
  três existentes da reserva. A pausa simula o uso do inventário; não existe
  uma janela de inventário visível do NPC para o outro jogador.
- Recuperação: pode fugir e comer quando está em desvantagem ou o jogador
  está comendo. Interrompe a tentativa após dano repetido e pode tentar de
  novo depois. Não usa foguete mantendo uma alimentação artificialmente
  ininterrupta: o foguete vem antes de iniciar a maçã.
- Teia oportunista próxima a suporte, com checagem de alcance e visibilidade,
  usando a interação de bloco nativa. Intervalo mínimo padrão:10 segundos.
- Tank: percorre a borda, busca recuperar vida e tenta posicionar teia quando
  há suporte. O bot não ataca nesse modo.
- Foguete na teia: extensão sincronizada para os dois participantes, apenas
  enquanto um foguete real está impulsionando a elytra. Não remove teias e
  não altera outros jogadores nem mundos fora da partida.

## Estado e cuidados de uso

As configurações e o kit ficam em `duckbox-training.json`, dentro do mundo.
Antes da rodada, o mod grava uma cópia do inventário original, posição, modo
de jogo, vida, fome, saturação, slot e efeitos. Restaura ao encerrar; se houver
uma interrupção, tenta recuperar na próxima entrada. Não apague esse arquivo
com uma rodada em andamento. A partida termina antes da morte real para evitar
a queda do inventário. As paredes da caixa ficam protegidas durante a partida;
as teias continuam quebráveis.

Use o mundo incluído para o primeiro teste. `/box criar` em outro mundo edita
um volume de41×41×11 à frente do ponto inicial e cria o lobby ao lado. Não use
a construção sobre suas construções existentes. O mod não aplica anticheat,
auto-update, coleta de dados, cosméticos online ou conexões externas no jogo.

## Validação e limites da alpha

Compilacao contra Minecraft1.21.4 real; verificacoes de atributos,
encantamentos, perfil RasyMc, IDs exclusivos dos bonus, correspondencia de41
slots, limites dos reposicionamentos, pacotes e NBT do mapa. Aplicacao real
de tres Mixins nos alvos de teia/foguete/PvP.

Teste adicional num **TestServer vanilla sem janela**, com mundos, jogadores,
inventarios e fisica reais: o bot se movimenta e causa dano ao alvo de
sobrevivencia perto dele; o kit equipado resulta em135 de vida; o bau abre,
bloqueia legendas, salva hotbar/inventario/offhand e recarrega o JSON. A arena
detalhada tambem e montada nesse mundo. Nao e uma partida com cliente grafico
nem um teste de todas as dificuldades; a aparencia e a naturalidade dos giros
ainda precisam ser avaliadas jogando. O teste de combate usa PvP vanilla
ativado; a injecao limitada de PvP e validada separadamente pelo transformador
Mixin. Resultados e limites em `VALIDACAO.txt`.

## Código-fonte e build

Requisitos de desenvolvimento: Python3.10+ e JDK21. Execute:

```text
python bootstrap.py
python build.py
python make_map.py
python test.py
python test_mixins.py
python test_combat.py
```

O bootstrap baixa Minecraft, Yarn, Fabric e bibliotecas para `tools`; nada disso
é incorporado ao JAR. O build compila em nomes Yarn e remapeia para intermediary.
Os alvos de Mixin usam nomes intermediary fixos da1.21.4. O mod não suporta
outras versões. Os scripts reutilizam arquivos locais quando presentes.
