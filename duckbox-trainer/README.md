# Duck Box Trainer — teste 0.1.0-alpha / Fabric 1.21.4

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

## Painel no mundo

- Botões: iniciar, parar, dificuldade e tamanho.
- Alavancas: Tank, giro, retotem, gap, teia, W-tap, strafe e foguete na teia.
- Dificuldades: **LOW, MEDIUM, HIGH, EXPERT**.
- Tamanhos: 17, 25, 33 e 41 blocos de largura externa, paredes incluídas.
  Há também tamanhos ímpares intermediários por comando. Altura interna:9.
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

O kit de demonstração tem espada de netherita, elytra inquebrável com +255 de
dano e +255 de velocidade de ataque, cabeça com +1000 de vida, pernas e botas,
foguetes, maçãs encantadas, teias, três totens na hotbar, um na offhand e nove
de reserva. Não há recarga infinita: bot e jogador têm a mesma quantidade.
Ajuste o kit para os atributos utilizados no seu servidor; as regras de dano
continuam vanilla, inclusive os limites nativos de atributos e invulnerabilidade
entre danos. O mod não ignora esses limites para multiplicar hits artificiais.

## Comportamentos desta primeira versão

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

Compilação Java21 contra Minecraft1.21.4/Yarn reais; verificações em JVM com os
registries vanilla, atributos do kit, quantidades de totem, isolamento das
cópias, pacote de sincronização, NBT e codecs de geração do mapa; aplicação
real de Mixin nos dois alvos de teia/foguete. Resultados em `VALIDACAO.txt`.

**Ainda não houve teste de combate com cliente gráfico.** A naturalidade dos
giros, precisão e decisões precisa ser calibrada jogando. O vídeo enviado não
pôde ser aberto porque excedeu32MiB; não é uma reprodução validada daquele
clipe nem do comportamento do BaldTheBot. Esta é uma primeira implementação
scriptada, sem aprendizado de máquina ou garantia de imitar um humano.

## Código-fonte e build

Requisitos de desenvolvimento: Python3.10+ e JDK21. Execute:

```text
python bootstrap.py
python build.py
python make_map.py
python test.py
python test_mixins.py
```

O bootstrap baixa Minecraft, Yarn, Fabric e bibliotecas para `tools`; nada disso
é incorporado ao JAR. O build compila em nomes Yarn e remapeia para intermediary.
Os alvos de Mixin usam nomes intermediary fixos da1.21.4. O mod não suporta
outras versões. Os scripts reutilizam arquivos locais quando presentes.
