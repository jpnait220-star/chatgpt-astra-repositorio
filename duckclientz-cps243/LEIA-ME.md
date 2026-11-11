# DuckClientZ 1.5.28-beta.2.43 — CPS com troca de botão

Disponível para Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base: beta 2.42, preservando RenderTop, filtro de elytra, recursos anteriores e conexão com a Altare.

## Usar

No módulo **CPS**, mantenha o marcador **`{middle}`** no campo Texto.

- Sem outro botão ativo, ele mostra o CPS do meio, incluindo as ações de meio já contadas pelo client.
- Ao clicar ou segurar o botão esquerdo ou direito no jogo, `{middle}` mostra o CPS desse botão. Ele não soma os contadores.
- Se esquerdo e direito estiverem segurados, usa o último dos dois pressionado. Ao soltá-lo, acompanha o outro ainda segurado.
- O botão esquerdo/direito segurado tem prioridade sobre o meio. Ao soltá-lo com o meio ainda pressionado, volta imediatamente ao meio.
- Entre cliques, conserva a seleção por até um segundo após soltar, evitando piscar para o meio a cada clique. Pressionar novamente o meio retoma o contador do meio imediatamente, se esquerdo/direito não estiverem segurados.
- Segurar um botão não inventa cliques: o número pode cair a zero se só houve um clique e nenhum outro foi realizado.
- Abrir uma tela, sair do mundo ou perder o foco limpa a seleção temporária. Leituras físicas dos botões recuperam solturas perdidas.
- Cliques sintéticos do próprio AutoClicker não trocam a seleção manual.

Os marcadores `{cps}` e `{right}` continuam com o comportamento anterior. Não são alteradas teclas, botões de ataque, ação de quebrar/colocar blocos, frequência do AutoClicker ou combate. A mudança é no contador exibido por `{middle}`.

## Instalar e atualizar

Feche o Minecraft, retire o JAR anterior do DuckClientZ de `mods` e coloque **apenas** o JAR correspondente ao seu Minecraft. Não instale as quatro versões juntas.

A beta 2.41 ou mais nova usa o canal assinado no GitHub. Com o auto-update habilitado, recebe a beta 2.43; reinicie o jogo quando o atualizador solicitar. A beta 2.40 original ainda consulta a Vercel pausada e precisa da troca manual uma vez. Não há como fazer aquela versão buscar um endereço novo sem atualizar o arquivo original.

Os serviços do mod continuam em `https://duckconnect.go.altare.global`. A migração da Community original para `https://duckcommunity.go.altare.global` é um pacote separado para a Altare; trocar o JAR não instala arquivos na hospedagem.

## Validação e limites

21 casos do seletor puro passaram, incluindo alternância, retenção de botão, expiração, soltura perdida, botões inválidos e relógio monotônico negativo/com overflow. Em cada versão, mais 32 verificações executam os métodos estáticos extraídos do JAR final e o corpo real do observador de mouse, com apenas os serviços de Minecraft/tempo substituídos no teste. Verificação estrutural ASM e verificador da JVM também passaram.

Assinatura do atualizador, hash, tamanho, identidade de cada JAR e ausência de atualização para a mesma versão são verificados com o código do atualizador já usado pelos clients. Nenhum teste auxiliar/stub entra nos JARs finais.

Comparado à beta 2.42, mudam somente a versão em `fabric.mod.json`, `CpsDisplay.class` e `MixinCpsMiddle230.class`; é adicionado `AdaptiveCps243.class`. RenderTop, AutoClickerRuntime, ClientData, renderizadores, demais módulos e classes de serviço/atualização permanecem idênticos.

Não foi realizado teste visual ou de entrada em uma sessão real do Minecraft. Os testes não comprovam compatibilidade com qualquer outro mod que remapeie botões fora dos eventos normais do jogo.
