# Duck Box Trainer — 0.3.25-alpha / Fabric 1.21.4

Treino local de Box PvP com bot ServerPlayerEntity, inventario e fisica vanilla,
arena procedural, modos de combate e quatro cosmeticos locais independentes do
DuckClientZ. Esta e uma alpha: a aparencia e a naturalidade exigem teste em jogo.

## Instalar / atualizar

- Minecraft Java1.21.4, Java21, Fabric Loader0.16.10+ e Fabric API0.119.3+1.21.4.
- Coloque apenas o JAR0.3.25 em `mods`, substituindo o DuckBox anterior.
- Para um mundo novo, copie `saves/DuckBoxTreino` para `.minecraft/saves`.
- O mundo DuckBoxTreino antigo pode ser reutilizado. Na primeira entrada,
  as configuracoes e os baus continuam salvos; use /box configurar para os controles.
- Ha um jogador contra um bot por mundo. Comandos/controles exigem operador;
  o mundo do pacote ja permite comandos. Servidor privado: mod e Fabric API
  tambem no cliente de quem vai treinar. Nao e um bot para servidor publico.

Fabric API: https://modrinth.com/mod/fabric-api/version/0.119.3+1.21.4
O ZIP inclui um template de mundo plano; apenas a arena e gerada pelo mod.

O bot agacha durante o voo de elytra e solta ao parar de planar.
A pausa agachada para repor totens continua funcionando.

## Registro de golpes

O bot confirma seu proprio carregamento e teleporte, pois nao tem um cliente
para enviar essas confirmacoes. Isso remove a protecao indevida de carregamento
no inicio do treino. O evento Fabric de morte agora permite que o totem
vanilla seja processado antes de encerrar a rodada: somente a derrota sem
protecao termina o treino. O corante amarelo continua sendo bonus, sem pop;
o jogador precisa equipar um totem vanilla numa das maos. Tambem foi removida a restauracao de vida nos primeiros
ticks de combate que podia apagar dano recebido logo depois do inicio.
A invulnerabilidade vanilla entre danos continua:15 CPS
nao significa15 perdas de vida por segundo. Resistencia, Protecao e absorcao
tambem reduzem ou escondem temporariamente a perda de vida vermelha.

Durante o treino, `/box golpes` mostra as chamadas de dano que chegaram ao
servidor e quantas foram aceitas ou recusadas por intervalo/protecao/outros.
Nao e um contador de cliques: ataques sem alvo ou fora do alcance nao chegam
a essa etapa. A falha intermitente relatada depois do inicio ainda nao foi
reproduzida em cliente grafico.

## Skin do bot

O bot usa Robot Duck, PNG64x64 incluido no mod, com bracos Steve. A textura
carrega localmente, sem consulta a servidores de skins. A cabeca equipada fica
oculta apenas na renderizacao do bot para mostrar seu rosto; Protecao60 e os
atributos do item permanecem. A skin do jogador nao e alterada. O NPC tambem usa a textura original Vanilla
Cape, amarela e verde, na capa e na elytra. Ela vem no JAR e usa os UVs nativos.

## Comecar

Abra o mundo, aguarde a montagem e escolha **DUEL** para combate. **TANK** e
um treino separado de sobrevivencia/evasao: nesse modo o bot nao ataca.
Escolha as regras, edite o bau do kit se quiser e clique em iniciar.
Os dois ficam frente a frente na faixa amarela por5 segundos (5,4,3,2,1,VAI!), com movimento e
dano bloqueados durante a espera. Os efeitos da gap comecam na liberacao.
Sem W-tap o bot usa alcance maximo2,4; com W-tap, no maximo3 blocos da camera
ate a hitbox, sempre exigindo mira e caminho livre.
`/box parar` encerra e restaura o inventario anterior.

Arena padrao13x13, altura interna7. Tamanhos externos de9,13 ou17 por
comando. O lobby inclui piso, iluminacao, estatua de pato e painel. A montagem
ocorre em lotes. `/box criar` em outro mundo edita um volume17x17x11 e o lobby
ao lado: use um local sem construcoes suas nesse volume.

## Regras: mesmo HP, dano/resistencia diferentes

| Regras | Vida maxima com o set/offhand | Atributo da espada | Resistencia mantida |
| --- | --- | --- | --- |
| Spam | 135 | +25 / Afiacao58 | II, ou I com opcao II desligada |
| Semi Insta | 135 | +25 / Afiacao58 | I |

Afiacao58 permanece no preset. Os valores de dano sao modificadores: ataque
base, encantamento, armadura e efeitos continuam calculados pelo Minecraft.
Os dois modos usam a cadencia selecionada (10,13,15 ou20 CPS) a20TPS; o padrao e15. No Normal Spam,
a tentativa so vira ataque se a recarga nativa estiver completa. O atributo
+255 attack_speed da elytra e mantido e determina essa recarga com os demais
atributos do kit. No Insta Kill permanece o sistema de spam anterior. Dano,
invulnerabilidade entre golpes, alcance e mira continuam com as regras existentes.
Ate6 blocos do alvo, o bot ja tenta os cliques na cadencia selecionada e balanca a mao sem exigir
mira encaixada. Isso nao estende o alcance do dano: so acerta com a linha da
mira livre dentro de2,4 blocos (W-tap off) ou3 (W-tap on).
A precisao da mira e as decisoes variam com a dificuldade.
Na0.3.25, Low equivale ao Medium anterior (inclusive salto/ativacao da elytra).
Medium reage em8 ticks, gira a mira ate18 graus por tick e tem menos erro de
pontaria, strafe mais frequente e troca de totem em4 ticks. High/Expert seguem iguais.

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
- Em Tank, alterna evasao aerea com pausas de gap no chao. Nessas pausas,
  interrompe o voo, pousa, come uma maca real sem pular e depois retoma o voo.
  Tambem programa uma dessas pausas a cada8..16 segundos de treino; precisa
  das habilidades gap/giro e dos respectivos itens para comer/voltar a voar.
  Dano repetido pode interromper a recuperacao para reagir.
- Parte das tentativas inclui decolar e buscar uma quina alta, perto do teto;
  as demais podem ocorrer no chao. Precisa de elytra/foguetes no kit e giro ligado.
- Dano repetido, inclusive na absorcao, interrompe a tentativa para retomar a luta.
- O estilo de giro proximo do alvo foi preservado. Acrescentou-se a oportunidade
  de usar foguete no ar para perseguir alvo distante/planando/tentando comer.
  Ele so causa dano se a mira alcancar a hitbox sem parede no caminho.
- O nivel de giro e independente da mira: BAIXO, MEDIO, ALTO, EXTREMO.
  EXTREMO permite usar foguetes/reposicionar com mais frequencia; consome o
  estoque real. A mira continua limitada pela dificuldade, sem hits automaticos.
- O bot so coloca teia estando no chao, na altura da cabeca acima do bloco dos
  pes e ate3 blocos acima do piso. Nunca coloca no piso, inclusive em Tank.
  Se a cabeca estiver no mesmo bloco dos pes (planando/rastejando baixo), espera
  outra oportunidade. Exige suporte, alcance/visibilidade e intervalo padrao10s.
- A extensao foguete-na-teia e sincronizada apenas para os participantes durante
  um impulso real. Usa multiplicadores0,45 horizontal e0,35 vertical, em vez de
  ignorar totalmente a teia; sem impulso, a teia segue vanilla. Nao altera
  outros jogadores/mundos fora do treino.
- Durante voo de elytra, clicar num bloco com foguete usa o impulso em vez de
  lancar um foguete solto, nas duas maos e apenas durante o treino.
- Contra alvo preso no alto, o bot varia entre perseguir de elytra/foguete e
  subir pulando/colocando blocos. A rota de torre aproxima pelo chao, sem ativar
  a elytra, e so quebra a teia depois de estar apoiado na propria torre, na
  altura do alvo. A rota aerea tenta acertar a parte exposta sem quebrar a teia.
- A linha exata de ataque considera a teia como obstaculo. A hitbox do NPC nao
  foi aumentada. Com teia na cabeca, ele mira nos pes quando ha caminho livre.
- Apos3 segundos continuos de teia na cabeca, tenta colocar blocos acima e nos
  quatro lados, com intervalo entre colocacoes e respeitando colisao/alcance.
  La preta funciona, assim como outras cores e blocos solidos; e preciso
  coloca-los no bau do kit. Ele consome o estoque e pode ficar sem blocos.
  As construcoes do bot sao removidas ao encerrar a rodada; podem ser quebradas.
- Quando fica travado numa quina durante a gap, troca o destino para atravessar
  a arena, evitando insistir olhando para o teto.

O JAR foguete-1.0 do usuario foi analisado sem ser instalado: seu listener
cancela RIGHT_CLICK_BLOCK quando ha elytra ativa/foguete e chama boostElytra.
Nao altera a teia. A imagem mostra tolerancias de validacao de movimento do
Spigot, que nao sao parametros de lentidao da teia nem configuracoes de Fabric.
O treinador reproduz o uso do foguete e aplica uma adaptacao de lentidao parcial,
limitada ao treino durante o impulso; nao e uma copia da fisica de um servidor.

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
/box regras SPAM|INSTA_KILL
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
bau/JSON independente por modo e montagem do mapa. Tambem foram verificados
colocacao de teia no chao/limite de altura, torre com la preta em ciclo completo
de IA/fisica, armadilha de cabeca apos60ticks, consumo/limpeza dos blocos,
quebra apenas em cima da torre, linha de ataque bloqueada pela teia com pes
expostos ainda acertaveis e uso de um foguete por clique durante voo. O guard
de morte foi testado separadamente com o contrato antes do pop de Fabric e
consumo de totem dos dois pelo Minecraft; nao e execucao completa do launcher. O cancelamento ambiental
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

Na0.3.25 o bot pode quebrar la no caminho com quebra nativa, sem destruir
outros materiais. A teia do alvo continua exigindo subir na torre primeiro.
A limpeza de inicio/fim de rodada remove todas as16 cores de la e teias do
interior da arena, preservando piso, teto, paredes e outros materiais.

Na0.3.25 o preset Normal e kits Normal salvos reconhecidos recuperam o
modificador nativo de velocidade da espada de ouro (-2,4), que faltava no
componente customizado de dano. Sem elytra a espada tem1,6 attack_speed, com
elytra256,6 e mao vazia4. Kits com velocidade personalizada sao preservados.
O icone pronto vanilla exige mirar num alvo vivo, indicador de ataque na mira
e recarga maior que5 ticks; por isso nao aparece pronto com a mao vazia ou
com +255 de velocidade. A barra durante a recarga tambem depende da opcao
Indicador de Ataque do Minecraft e de outros mods que alterem o HUD.

A torre agora completa o ultimo degrau antes de mudar para a quebra da teia.
Armadilhas de cabeca nao interrompem essa subida. A mineracao espera alinhar
a cabeca com o bloco, usa dureza/progresso por tick real e aguarda5 ticks entre
blocos, como a pausa do cliente vanilla. O teste de torre aguarda ate a teia
ser efetivamente quebrada e o bot voltar a acertar o alvo, em vez de terminar
no primeiro salto alto.

Retotem: High e Expert nao tem falhas aleatorias na troca de totem. Medium tem
20% de chance por tentativa de transferencia para a offhand: ao errar, volta
a espada, espera8 ticks e tenta corrigir, preservando todos os itens. A chance
nao afeta a volta do corante quando se recupera. A habilidade precisa estar
ligada e ainda precisa haver totens no inventario; nao ha reposicao infinita.

Na0.3.25 a reposicao acontece quando nao ha mais totem na hotbar, mesmo que
a offhand ainda esteja protegida. O bot pausa/agacha e move ate3 totens reais
da reserva para os slots6..8. Itens deslocados vao para os slots liberados da
reserva, sem exclusao; espadas nesses slots sao preservadas. O HUD de status
mostra o contador Refill. Sem reserva nao ha reposicao. O teste sequencial
consome12 totens vanilla e confirma3 refills, incluindo refill antes do pop
do ultimo totem da offhand.

Na0.3.25 o nome visivel e Spam (NORMAL_SPAM continua aceito em comandos e
configs antigos). Refill: Low8 ticks, Medium5, High3, Expert2. A actionbar usa
cores/simbolos e mostra dificuldade, modo, totens e refills; sem vida do bot
nem estado Combate. Ao comer no chao, o bot trava novos saltos de elytra,
anda devagar em direcao ao interior e deixa de mirar no teto; a deteccao de
travamento agora considera deslocamento horizontal, nao os pulos.

Na0.3.25 o centro do piso fica em **-5 78 111**, com botoes de tamanho apenas
**9x9,13x13,17x17**. A migracao de configs altera limites/posicao sem escrever
blocos no seu mapa. Mundos existentes nao geram arena automaticamente.

Para preservar sua construcao, termine o piso/arena e use `/box usar` para
vincular esses limites sem reconstruir; `/box kit abrir` abre o editor sem
precisar mover um bau. Nesse modo os controles ficam por comandos ate o ZIP
com as suas placas/botoes ser integrado. `/box criar` gera a arena e o lobby
do mod e substitui blocos no volume documentado, portanto use-o apenas quando
quiser gerar a construcao automatica. O template novo do ZIP ja vem configurado
para gerar sua propria arena, diferente da sua build personalizada.

**MouseTweaks enviado:** o pacote opcional contem uma copia corrigida do JAR,
com AttackStrengthMixin/DamageWindowMixin e o menu de combate global removidos.
Os demais recursos e arquivos foram preservados; o relatorio JSON registra
os hashes e o total de entradas identicas. Substitua o MouseTweaks antigo,
sem manter duas copias. As licencas originais continuam dentro do JAR.

O Trainer tem No Hit Delay somente de clique local no Insta Kill: limpa o
contador de erro de clique do MinecraftClient. Nao muda a forca do ataque,
a imunidade entre danos, o cooldown de PlayerEntity ou atributos do mundo.
No Spam esse ajuste fica desligado, inclusive na copia corrigida do MouseTweaks
quando usada junto com o Trainer. Fora do treino o MouseTweaks mantem suas
configuracoes locais originais. O Trainer nao depende dele para funcionar.

A lentidao parcial de teia durante elytra agora usa a mesma condicao estavel
no cliente/servidor. O delta enviado no pacote ja foi reduzido pelo cliente;
o handler evita aplicar esse multiplicador uma segunda vez ao mesmo pacote,
preservando as colisoes com blocos e a validacao nativa do movimento. O bot
tenta elytra/foguete na propria teia e, sem saida, minera a teia que o prende.
Testes incluem combinacao real dos Mixins do Trainer e MouseTweaks, ponte
de modo Spam/Insta e movimento nativo sem dupla lentidao. A sensacao de rede
e o HUD ainda precisam de teste com cliente grafico. Atualize cliente e
servidor privado juntos: o payload do treino ganhou o estado Insta Kill.

CPS selecionavel: `/box cps 10`, `/box cps 13` ou `/box cps 15`; `/box cps`
alterna entre os tres valores. O padrao continua15 e a escolha e salva por
mundo. O lobby gerado tem um botao CPS DO BOT; no mapa personalizado use o
comando ate vincular seus botoes. A mudanca vale imediatamente, inclusive
durante o treino, sem rajada acumulada. Aplica aos dois modos; Spam continua
respeitando a recarga nativa e o alcance do dano nao e alterado.

## Command blocks e configuracao do mapa

Todos os comandos `box` podem ser usados em command blocks. Se nao houver
um jogador executor explicito, o bloco escolhe o jogador real vivo mais
proximo no mesmo mundo, ignorando o bot e espectadores. A mensagem vai para
esse jogador; erros aparecem na saida do bloco e retornam falha.
Para escolher explicitamente, use `execute as @p at @s run box iniciar`.

| Comando no bloco | Funcao |
| --- | --- |
| `box iniciar` / `box parar` | Iniciar ou encerrar o treino |
| `box configurar` | Abrir menu de configuracao para o jogador |
| `box cps` ou `box cps 10/13/15` | Alternar ou definir CPS |
| `box dificuldade LOW/MEDIUM/HIGH/EXPERT` | Definir dificuldade |
| `box regras SPAM/INSTA_KILL` | Definir regras de combate |
| `box modo DUEL/TANK` | Definir treino |
| `box giro BAIXO/MEDIO/ALTO/EXTREMO` | Definir nivel do giro |
| `box habilidade giro/gap/retotem/teia/wtap/strafe/foguete_teia` | Alternar habilidade |
| `box kit abrir` | Abrir editor do kit perto do jogador, sem bau fixo |
| `box kit salvar` / `box kit padrao` | Salvar inventario como kit ou restaurar preset |
| `box atributo minecraft:max_health 60 HEAD` | Alterar atributo do item na mao do jogador |
| `box cosmetico blood/money/oculos/sapo` | Alternar cosmetico |
| `box golpes` | Mostrar diagnostico durante o treino |
| `box usar` | Vincular a sua arena pronta sem reconstruir |
| `box criar` ou `box criar 9/13/17` | Gerar arena automatica (substitui blocos) |

Nas linhas com `/`, escolha apenas um valor, por exemplo `box cps 13`.
Use blocos de impulso acionados por botao para as opcoes que alternam valores.
O menu usa o inventario vanilla e icones bloqueados, sem itens transferiveis.
Jogadores sem permissao nao ganham acesso aos comandos pelo chat: o command
block autorizado pode abrir o menu para eles. Alteracoes que exigem treino
parado continuam exigindo isso. Na build personalizada, use `box usar` e os
comandos; nao use `box criar` para vincular suas placas e botoes.

Confirmacoes de giro ON/OFF, habilidades, cosmeticos, CPS, dificuldade, modo,
regras e nivel do giro aparecem na actionbar, com cores. Durante o treino,
o status normal aguarda2 segundos para nao apagar a confirmacao. Ajuda,
erros, salvamento de kit e avisos importantes continuam no chat/saida do
command block.


## Quatro perfis de kit e cofres

Cada mundo salva ate quatro perfis, com inventario/equipamento independente.
Cada perfil possui um unico inventario compartilhado entre Spam e Semi Insta. O kit antigo e
migrado para o perfil1; editar um perfil nao altera os outros. Os dois
participantes recebem copias do kit do perfil selecionado ao iniciar.

- `/box chest profile 1`: entrega um bau editor do perfil1 (aceita1..4).
  Coloque-o no mapa e abra para editar; os itens sao salvos ao fechar.
  Esse bau edita sempre seu proprio perfil, sem mudar o perfil selecionado.
- `/box profile 1`: seleciona o kit para o proximo treino. Em command block
  use `box profile 1`, sem barra. Aceita somente1,2,3 ou4.
- `/box configurar`: o botao Perfil do kit alterna entre os quatro.
- `/box chest stock` (ou `/box chest cofre`): entrega o cofre de suprimentos.
  Coloque no mapa; como operador, agache e abra para editar seus27 modelos.
  Abra sem agachar para pegar copias: clique esquerdo copia a pilha,
  direito copia um item, Shift+clique manda para o inventario. O modelo
  permanece no bau e pode ser retirado novamente. Slots vazios nao fornecem
  nada. As duas funcoes de bau sobrevivem ao salvamento do mundo.

Os comandos tambem funcionam em command blocks com o mesmo alvo dos demais.
O cofre usa o PNG roxo original; os baus de perfil usam o PNG azul original.
Os baus especiais usam renderizacao propria de bloco simples, inclusive
quando encostados. A textura azul usa o mapeamento antigo de UV adaptado no
modelo, preservando os pixels originais. Os perfis nao dependem da posicao fisica
do bau: pode mover/colocar novos exemplares pelo comando.

## Nomes com cores e gradientes

Segure um item e use:

```
/box rename &e&lEspada do Pato
/box rename &#FFAA00Pato
/box rename <gradient:#FFFF00:#FF8800>Espada Duck</gradient>
/box rename <rainbow>Kit colorido</rainbow>
/box rename profile 2 <gradient:#00FFFF:#9900FF>Treino</gradient>
```

Aceita codigos legacy `&`/`§`, hex `&#RRGGBB` e `&x&R&R&G&G&B&B`,
gradientes estaticos com duas ou mais cores e tags comuns de negrito,
italico, sublinhado e cores. Pode colar esses formatos gerados no Birdflop;
nao e um interpretador completo de plugins MiniMessage nem animacao de nome.
O limite e256 caracteres visiveis e4096 caracteres de codigo. Nomes dos kits
sao salvos junto dos perfis. Renomear nao altera atributos nem encantamentos.


## Nao correr no retotem e Teia no pe

As duas tecnicas sao opcionais e independentes (inicialmente desligadas),
com botoes em `/box configurar` e comandos em chat/command block:

- `/box habilidade nao_correr_retotem`: segura o combate, pulando, atacando e
  fazendo retotem/refill normalmente. Nao foge para comer enquanto o jogador
  continua atacando. Se estiver perdendo em vida relativa, tem50% de chance de
  recuperar por oportunidade, com decisao mantida10 segundos. Tambem pode
  recuperar quando o jogador se afasta mais de tres blocos e esta comendo. Nao altera alcance ou velocidade dos golpes.
- `/box habilidade teia_pe`: permite plantar uma teia nos proprios pes no
  chao quando o jogador esta no chao, se afasta ou o bot perde vida relativa.
  Tambem adota essa tecnica quando o jogador teia seus pes. Nessa postura
  mira/ataca sem giro/foguete e tenta teiar os pes do adversario ao alcance,
  com intervalo. Se o jogador se afasta mais de cinco blocos ou voa para cima,
  minera a propria teia com a quebra normal e volta a perseguir; pode repetir
  depois. Depende de Teia estar ligada e de ter teias no inventario para por
  novas. Nao duplica itens nem quebra blocos fora de la/teia.


## Alteracoes0.3.25

- `/box habilidade resistencia2` alterna ResistenciaII no Spam. Desligada,
  mantem ResistenciaI da gap para os dois; Semi Insta continua com ResistenciaI.
  A escolha e salva e reaplicada depois de um totem.
- `/box regras SEMI_INSTA` e o nome novo de Insta Kill. `INSTA_KILL` continua
  aceito e os kits/perfis salvos preservam a mesma identidade.
- A actionbar mostra dificuldade, modo e totens. CPS, perfil, refill e fase
  cinza foram removidos; confirmacoes de configuracao continuam temporarias.
- Os dois pontos da contagem foram movidos um bloco para dentro da arena.
- O bot responde no chat ao terminar: mensagens de boa partida, quase e,
  quando o jogador vence com ate2 totens restantes, elogios de luta apertada.
- O gerador agora cria somente a arena, sem lobby, pato, caminho e painel de
  botoes. Use `/box configurar` ou seus command blocks no mapa personalizado.
  `/box usar` continua vinculando o mapa pronto sem reconstruir sua schematic.
  `/box criar` gera a caixa e substitui os blocos dentro do volume da arena.
- Spam usa vidro/concreto azul; Semi Insta usa vermelho. Trocar as regras
  recolore apenas esses materiais nas bordas da caixa, preservando a estrutura.
- `/box limparpainel` e opcional para remover o antigo lobby gerado, na antiga
  area externa a oeste. Nao use se construiu algo la que queira preservar.
  A atualizacao nao apaga essa area automaticamente.
- Baus especiais colocados no mundo agora usam renderizador proprio e sincronizam
  o papel visual no NBT. Reabra o mundo apos instalar para recarregar os baus.

A validacao inclui testes nativos de servidor/Mixin e malhas sem GPU. Ainda
precisa conferir as texturas e o combate dentro do cliente grafico.


## Alternar Duel/Tank com o mesmo comando

`/box modo` alterna entre Duel e Tank. Repita o mesmo comando para voltar.
Em command block use `box modo`, sem barra, ligado a um botao de impulso.
A confirmacao aparece na actionbar e a escolha fica salva. Encerre o treino
antes de alternar. Os formatos antigos `box modo DUEL` e `box modo TANK`
continuam aceitos para preservar mapas com command blocks existentes.


## Outros comandos de um so botao

- `box regras`: Spam / Semi Insta.
- `box dificuldade LOW`, `MEDIUM`, `HIGH` ou `EXPERT`: comandos separados por nivel.
- `box giro`: Baixo / Medio / Alto / Extremo (intensidade).
- `box profile`: perfis1 /2 /3 /4.
- `box tamanho`:9 /13 /17. Em mapa personalizado apenas muda os limites;
  no mapa gerado reconstrui o volume da caixa, como o controle de tamanho.
- `box cps`:10 /13 /15.
- `box habilidade nome`: liga/desliga a tecnica indicada.

Use sem barra nos command blocks, com um botao de impulso. No chat coloque
`/` antes de `box`. Cada execucao avanca uma opcao e mostra o valor na
 actionbar. Os comandos com valor explicito continuam aceitos para mapas antigos.


Calca, botas e elytra dos kits padrao recebem Protecao60 nos dois modos.
Ao carregar os perfis existentes, os equipamentos nesses slots sao atualizados
para no minimo Protecao60, sem retirar outros encantamentos, nomes, atributos
ou Inquebravel. Slots vazios permanecem vazios e itens fora de seus slots de
equipamento nao sao alterados. O mesmo kit atualizado e copiado para os dois.


Os perfis agora alteram somente inventario/equipamento. Trocar Spam/Semi Insta
nao muda itens, atributos ou o perfil selecionado. Na migracao, cada perfil
preserva seu kit salvo do modo atualmente selecionado; na ausencia dele, usa
o kit Spam antigo ou o Semi Insta antigo. As entradas antigas por modo ficam
no JSON como copia de seguranca. A partir dai, edicoes sao compartilhadas
pelos dois modos e cada perfil continua independente dos demais.


## Atualizacao0.3.25

- `/spawn` retorna ao ponto salvo por `/box setspawn` (fallback **-146 65 93**).
  Ao terminar ou sair do x1, o inventario original e restaurado e o jogador
  volta ao ponto salvo, inclusive sua dimensao e direcao.
  Ao redimensionar/gerar e ser levado ao teto, retorna apos60ticks (3segundos
  a20TPS). A tarefa e cancelada se entrar em um treino nesse intervalo.
- Espada de ouro Duck:25 de attack damage, Sharpness58. Os perfis existentes
  com espada identificada do Trainer sao atualizados sem alterar outros itens.
- Semi Insta: a janela de protecao inicial entre danos passa de10 para5ticks
  para os dois participantes. CPS permanece selecionavel e Spam mantem o
  intervalo vanilla. So afeta dano de um participante contra o outro no treino.
- Quando o alvo teia os pes, o bot prioriza aproximar e atacar, suspendendo o
  giro orbital. A tecnica de teiar os proprios pes exige alcance de ataque.
- Teia nos pes nao interrompe ataques para minerar. O bot so minera sua propria
  teia se ela estiver na cabeca, com ele em pe, no chao e sem elytra ativada.
  Voando, tenta foguete/movimento para sair. Preserva a mineracao necessaria
  de teia no alto ao usar torre para alcancar o alvo.
- Falas de fim de luta usam `DuckBot »`; o resultado do treino e texto de sistema.
- Baus possuem sincronizacao dedicada de funcao por dimensao/posicao. A
  textura e reenviada ao entrar e apos colocar/mudar um bau, sem copiar seu
  estoque nem gerar/carregar chunks adicionais. Requer atualizar o mod no
  cliente e no servidor privado, quando houver.

Testes de servidor/codec/Mixin sem janela; renderizacao final precisa ser
conferida no jogo.


## Spawn configuravel, NPC e cabecas

- `/box setspawn`: salva sua posicao, dimensao e direcao como spawn do treino.
  Vitoria, derrota, `/spawn` e retorno de tamanho apos3segundos usam esse ponto.
  Antes de configurar, o destino anterior -146/65/93 continua como fallback.
- `/box spawnbot`: coloca ou reposiciona um unico DuckBot de lobby aqui. Ele
  fica parado, sem itens, com skin/capa e cosmeticos atuais, olhando para o
  jogador real mais proximo ate16blocos. Persiste a posicao entre sessoes.
  E separado do bot de combate e permanece depois da luta.
- `/box skull <nick>`: consulta o perfil original na Mojang e entrega a cabeca
  com skin, Vida+60 ao equipar e Protecao60. Consulta assincrona com timeout;
  depende de conexao com a Mojang e nao inventa UUID de conta original.
- `/box cps` agora alterna10/13/15/20; `/box cps 20` seleciona diretamente.
  O limite e20 tentativas por segundo a20TPS, sem alterar o intervalo de dano.
- Recuperacao de vida tem duracao maxima por tentativa e periodo de combate
  antes de repetir: evita o ciclo infinito de planar/comer sem voltar a bater.
  Retotem continua permitido durante esse periodo e Tank continua sendo treino
  de evasao. O bot tambem recupera a espada se ela acabar fora da hotbar.
- Ao tomar teia no rosto, cancela comer para reagir. Teia no pe so prende a
  decisao da IA se o bloco correto existe e realmente intersecta o bot.
- Mais mensagens de fim de luta; o prefixo DuckBot voltou junto do NPC de lobby.

Reinicie o Minecraft para substituir o JAR. Em servidor privado, atualize os
clientes e servidor: foram adicionados payloads de baus e do NPC de lobby.


## Blocos com as texturas enviadas

`/box blocos` abre um catalogo com24 blocos de painel. Clique para receber o
bloco. `/box bloco kit_1` entrega diretamente um modelo; o comando sugere
os nomes disponiveis. Tambem pode usar `/give @s duckbox:painel_kit_1`.
Os quatro kits sao paineis visuais; seu inventario continua configurado nos
baus de perfil. Os demais paineis sao decorativos para sua build/command blocks.

Os24 PNGs do ZIP corrigido foram incluidos sem editar pixels:512x512
e o painel completo1536x1024. Sao exibidos por renderizacao propria,
sem colocar essas imagens grandes no atlas dos blocos do Minecraft. O painel
completo preserva proporcao3:2 dentro de um bloco; para ficar grande e legivel,
monte3blocos por2blocos com as seis partes start_1...start_6. Nao precisa de
resource pack separado. A frente segue a direcao em que o bloco foi colocado.

O cofre e o bau de perfil agora tambem sao blocos registrados do DuckBox, com
um tipo de block entity e renderizador proprios. Baus especiais antigos em
chunks carregados sao convertidos mantendo itens, perfil, nome e orientacao;
nao sao alterados baus vanilla sem a identificacao do Trainer. Novos baus
nao se juntam em bau duplo. O modelo de textura nao depende mais de conseguir
substituir o renderizador dos baus vanilla.

## Hologramas fixos no bloco

1. `/box holo &eTexto`: prepara o texto. Clique com botao direito no bloco
   e face desejados para fixar. Aceita RGB/gradientes e `\n` para nova linha.
2. `/box moveholo`: clique primeiro no bloco do holograma e depois no bloco
   de destino. Preserva o mesmo texto/cores e continua fixo na nova face.
3. `/box holo remover`: prepara a remocao; clique no bloco do texto.
4. `/box holo cancelar`: cancela a operacao pendente.

O texto usa text_display nativo com billboard FIXED: nao acompanha o olhar,
nao depende de mirar para aparecer, nao fica na frente da camera e nao anima
a posicao. E salvo no mundo; quebrar o bloco com a mao/ferramenta remove o texto
anexado. Comandos de edicao aguardam clique por60segundos. Criar outro texto
na mesma face atualiza o anterior em vez de acumular entidades.


### Resistencia e Totem pop rapido

A regra normal voltou a manter resistencia infinita:II no Spam com a opcao
ResistenciaII ligada; I no Spam sem essa opcao e no Semi Insta. Reaplica apos
um totem. `/box habilidade totem_pop_rapido` alterna o novo modo (tambem no
menu `/box configurar`): ligado, remove somente a manutencao da resistencia.
Nao altera CPS, dano, armadura, vida ou outras habilidades. A gap inicial ainda
da resistenciaI finita e o totem pode limpar os efeitos normalmente. Comer
outra gap concede os efeitos normais. A escolha e salva por mundo.

### Torre e blocos do kit

A escolha de rota alterna torre e voo quando ha blocos, em vez de sortear
voo repetidamente. A torre aceita apoio de vidro e abandona uma tentativa
sem progresso para tentar alcancar o alvo voando. O kit novo inclui 64 las
pretas; inventarios personalizados existentes sao preservados. Coloque la
(de qualquer cor) no bau do perfil se o seu kit antigo nao tiver blocos.
O bot prioriza la, inclusive na reserva, e nao usa os baus/painéis do mapa
como material de construcao. Continua quebrando apenas la e teia.

### Novidades desta versao

- `/box holotamanho 1.5`: depois clique no bloco do holograma. Valores de0.1 a10;
  o tamanho inicial e0.5, portanto1.0 duplica o texto inicial. O ajuste e individual,
  salvo no mundo, e preservado ao mover ou reescrever o texto na mesma face.
- `/box blocos` agora inclui Strafe, tamanho da box, teia, teia no pe e W-tap.
  Kits e demais imagens atualizados a partir do ZIP corrigido, sem mudar IDs
  dos blocos que ja estao no mapa. Nao precisa recriar o mundo.
- Bau de perfil amarelo/vermelho Mega Box, com o mesmo modelo de UV legado
  no item e no bloco colocado; perfis e inventarios existentes preservados.

### Torre, tesoura e Speed

O bot escolhe uma coluna livre ao lado do jogador na teia elevada, aproxima
pelo chao sem o salto/giro do combate e alinha a torre antes de colocar os
blocos. O tempo limite de construcao comeca na torre, nao durante a aproximacao.
Usa blocos reais do inventario e continua alternando com a rota de voo.
Nos perfis personalizados, mantenha la no kit para habilitar essa alternativa.

Quando precisa quebrar la ou teia, procura tesoura tambem na reserva do
inventario, usa a velocidade/durabilidade nativa da ferramenta e volta para
a espada depois. Nao cria tesoura nem permite quebrar a estrutura da arena.

Speed do jogador e espelhado no bot com a mesma forca e tempo restante,
inclusive efeitos mais fracos/curtos substituindo os anteriores. Quando o
jogador perde Speed (fim do tempo, leite, totem), o bot perde tambem. Nao
renova a duracao da pocao nem muda a velocidade do jogador.
