# DuckClientZ beta 2.44 — CPS descendo suavemente

Quatro versões: Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base beta 2.43, preservando a seleção automática de botão em {middle}, RenderTop, elytra e serviços da Altare.

## Exibição

O número do CPS agora diminui gradualmente em cerca de **350 ms**, em vez de saltar direto de um valor alto para outro baixo ou para zero. A animação vale para o contador esquerdo, direito e o marcador adaptativo **{middle}**, inclusive quando ele troca para o botão que você está clicando/segurando.

Aumentos continuam imediatos. A animação é baseada no tempo, não no número de frames. Ao retornar ao HUD após uma pausa longa, ele sincroniza com a contagem atual para não mostrar um valor antigo.

Isso é somente visual. A janela real de um segundo, os métodos currentLeftCps/currentRightCps/currentMiddleCps, os eventos físicos, a seleção de botão, o AutoClicker e as ações do jogo não são alterados. Não são criados cliques extras ao segurar.

Não precisa mudar configurações: a animação já vem aplicada. Mantenha {middle} no texto se quiser acompanhar o botão ativo conforme a beta 2.43.

## Instalar

Feche o Minecraft e substitua o JAR antigo por **somente um** JAR deste ZIP, correspondente à sua versão do jogo.

Clientes beta 2.41 ou superiores podem receber a revisão pelo auto-update assinado do GitHub quando ele estiver habilitado. A beta 2.40 original precisa da troca manual uma vez, pois ainda consulta a Vercel pausada. Reinicie o jogo quando o atualizador solicitar.

## Verificação

- 45 verificações de animação: queda progressiva, subida imediata, canais independentes, pausa e relógio monotônico negativo/com overflow.
- Em cada Minecraft, 17 verificações executam o formatador real e o corpo do observador de mouse extraídos do JAR, confirmando queda gradual por parada e troca de botão sem modificar o CPS real.
- Verificação estrutural ASM/JVM, integridade ZIP e preservação dos arquivos anteriores.
- Assinatura do canal, identidade, hash e tamanho de cada JAR final verificados pelo código do atualizador original.

Não foi realizado teste visual em uma sessão real de Minecraft.

Comparada à beta 2.43, esta revisão altera somente fabric.mod.json e CpsDisplay.class; adiciona SmoothCps244.class. Os outros arquivos permanecem idênticos, incluindo o seletor de botões da 2.43, mixins de entrada, AutoClickerRuntime, ClientData, RenderTop e roteamento/atualizador.
