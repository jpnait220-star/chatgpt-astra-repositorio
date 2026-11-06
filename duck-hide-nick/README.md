# DuckHideNick — Paper 1.21 / 1.21.1

Esconde somente a etiqueta acima da cabeça. Não modifica o nome da conta, o chat, a lista TAB, seus prefixos, sufixos ou a ordenação da lista.

## Instalação

1. Instale Paper 1.21 ou 1.21.1 com Java 21, LuckPerms e TAB para essa versão.
2. No TAB, mantenha `scoreboard-teams.enabled: true`.
3. Coloque `DuckHideNick-Paper-1.21-1.0.0.jar` em `plugins` e reinicie o servidor.
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
  padrao: '&7'
  usar-cor-do-prefixo-luckperms: true
  cargos:
    vermelho:
      cor: '&c'
      prioridade: 100
    vip:
      cor: '#FFAA00'
```

`vermelho` e `vip` são os nomes reais dos grupos no LuckPerms. Entre os grupos configurados herdados pelo jogador, vence a maior `prioridade`; quando omitida, usa o peso do grupo no LuckPerms. Empates preferem o grupo primário, depois ordem alfabética. O grupo `default` é uma alternativa final. Sem um cargo específico configurado, tenta a última cor do prefixo do LuckPerms; sem cor usa `padrao`.

Aceita `&c`, `&#FF0000`, `#FF0000` e o formato RGB legado. Apenas a cor do cargo é aplicada: prefixos e sufixos não entram na etiqueta escondida.

## Comportamento

- São exatamente nove caracteres com a ofuscação nativa `&k`, animada pelo Minecraft.
- A escolha é salva por UUID em `players.yml` e restaurada ao reconectar.
- O jogador não vê sua própria etiqueta; os outros veem somente a etiqueta substituta.
- Respeita invisibilidade e `Player.canSee` (plugins de vanish que ocultam jogadores pela API Bukkit).
- Enquanto agachado, reduz o alcance para até 32 blocos e não mostra o texto através de paredes.
- A etiqueta acompanha o jogador, não monta nele; não altera passageiros nem impede teleporte.
- Ao remover a permissão, restaura o nome. Se o TAB já tinha escondido a etiqueta antes, preserva esse estado.
- Só jogadores escondidos recebem uma entidade TextDisplay; a animação não envia atualizações de texto por quadro. Cor/permissão são conferidas uma vez por segundo.

Validação: compilação Java 21 e 21 verificações automatizadas de cores, prioridade de cargos, persistência e chamadas da API de nametag. A aparência e interação com a instalação específica do TAB precisam ser conferidas com dois jogadores no servidor; não foi realizado teste gráfico no Minecraft.

## Compilar

Com Java 21 e Python 3 instalados:

```
python3 build.py
```

O script baixa as dependências de compilação oficiais para `tools/`, gera o JAR em `dist/` e executa as verificações. Nada de `tools/` é incluído no plugin.
