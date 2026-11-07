# DuckHideNick — Paper 1.21 / 1.21.1

Esconde somente a etiqueta acima da cabeça. Não modifica o nome da conta, o chat, a lista TAB, seus prefixos, sufixos ou a ordenação da lista.

## Instalação

1. Instale Paper 1.21 ou 1.21.1 com Java 21, LuckPerms e TAB para essa versão.
2. No TAB, mantenha `scoreboard-teams.enabled: true`.
3. Coloque `DuckHideNick-Paper-1.21-1.0.2.jar` em `plugins` e reinicie o servidor.
4. Edite `plugins/DuckHideNick/config.yml` com os nomes dos seus grupos do LuckPerms.
5. Libere a permissão no cargo desejado:
   ```
   /lp group vip permission set escondernick.usar true
   ```

O plugin usa a API oficial de nametags do TAB. Compilado com Paper API 1.21.1, LuckPerms API 5.4 e TAB API 6.2.1. Não substitui o TAB, não inclui esses plugins no JAR e não precisa de ProtocolLib.

## Comandos

- `/escondernick`: esconde a etiqueta original e mostra nove caracteres animados na cor do cargo.
- `/mostrarnick`: restaura a etiqueta original, inclusive prefixo e sufixo gerenciados pelo TAB.
- `/ducknick reload`: recarrega as cores e configurações; permissão `escondernick.admin` (OP por padrão).

A permissão de uso é `escondernick.usar` e vem desativada por padrão. A mensagem de falta de permissão é configurável e começa como:

> Adquira Esconder Nick na loja para usar esse comando.

Não é necessário dar permissão dos comandos separadamente. A permissão é validada pelo plugin para permitir a mensagem personalizada. Console não pode esconder seu próprio nome.

## Cores por cargo

```yaml
cores:
  usar-cor-do-cargo: true
  padrao: '&7'
  usar-cor-do-prefixo-luckperms: true
  cargos:
    vermelho:
      cor: '&c'
      prioridade: 100
    vip:
      cor: '#FFAA00'
```

Por padrão, usa a cor das letras da tag ativa do LuckPerms. Exemplo: `&7[&9Mídia&7] &r` produz os nove caracteres em azul, ignorando colchetes cinza e a cor após a tag. Essa cor tem preferência sobre regras de grupos herdados.

Para desligar a cor do cargo e usar somente `padrao`, configure `cores.usar-cor-do-cargo: false`. Essa nova chave também funciona em configurações antigas; se estiver ausente, o padrão é `true`.

`vermelho` e `vip` são exemplos de grupos do LuckPerms, não são obrigatórios. As regras em `cargos` são alternativas quando a tag não tem cor. Para priorizar somente regras manuais, desative `usar-cor-do-prefixo-luckperms`. A maior `prioridade` vence; quando omitida, usa o peso do grupo. Empates preferem o grupo primário e depois ordem alfabética.
Aceita `&c`, `&#FF0000`, `#FF0000` e o formato RGB legado. Apenas a cor do cargo é aplicada: prefixos e sufixos não entram na etiqueta escondida.

## Comportamento

- São exatamente nove caracteres com a ofuscação nativa `&k`, animada pelo Minecraft.
- A escolha é salva por UUID em `players.yml` e restaurada ao reconectar.
- `etiqueta.mostrar-para-si: true` permite ver a própria etiqueta no F5. O servidor não detecta o modo da câmera; ela também pode aparecer em primeira pessoa se você olhar diretamente para ela. Use `false` para ocultá-la somente do próprio jogador.
- Respeita invisibilidade e `Player.canSee` (plugins de vanish que ocultam jogadores pela API Bukkit).
- Enquanto agachado, reduz o alcance para até 32 blocos e não mostra o texto através de paredes.
- A etiqueta usa o nome nativo de um armor stand invisível e sem hitbox (marker). A orientação horizontal e vertical e o fundo são renderizados pelo próprio Minecraft, como os nomes normais, inclusive ao observar por cima ou por baixo. Acompanha o jogador com a interpolação normal de entidades. Não monta no jogador, não altera passageiros nem impede teleporte.
- Ao remover a permissão, restaura o nome. Se o TAB já tinha escondido a etiqueta antes, preserva esse estado.
- Só jogadores escondidos recebem um marker invisível; a animação não envia atualizações de texto por quadro. Cor/permissão são conferidas uma vez por segundo.

Validação: compilação Java 21 e 25 verificações automatizadas de cores, prioridade de cargos, persistência e chamadas da API de nametag. A aparência e interação com a instalação específica do TAB precisam ser conferidas com dois jogadores no servidor; não foi realizado teste gráfico no Minecraft.

## Compilar

Com Java 21 e Python 3 instalados:

```
python3 build.py
```

O script baixa as dependências de compilação oficiais para `tools/`, gera o JAR em `dist/` e executa as verificações. Nada de `tools/` é incluído no plugin.

## Atualização 1.0.2

Substitua o JAR anterior e reinicie o servidor. `players.yml`, permissões e cores são preservados. A opção antiga `etiqueta.fundo` deixa de se aplicar: o fundo acompanha o estilo nativo do Minecraft/configurações do cliente. A renderização de nomes nativa usa alcance de até 64 blocos (32 no estilo agachado), sujeita à distância de rastreamento de entidades configurada no servidor.
