# DuckClientZ beta 2.45 — queda lenta do CPS e TargetLight com oclusão

Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base beta 2.44.

## CPS: dois comportamentos diferentes

- Quando a contagem cai naturalmente porque você parou de clicar, o número desce lentamente, em aproximadamente **0,9 segundo**, em vez de saltar.
- Trocar o botão que alimenta `{middle}` usa uma transição rápida de cerca de **80 ms**.
- Ao soltar o esquerdo/direito sem manter outro botão pressionado, a escolha manual é liberada após cerca de **120 ms**. Mantendo o meio pressionado, a seleção volta a ele imediatamente, com transição visual rápida quando há queda.
- Subidas continuam imediatas. Os contadores reais de um segundo, ataques, teclas, AutoClicker e ações de quebrar/colocar blocos não são alterados.

Isso diferencia a parada normal de cliques da troca/liberação de botão, como solicitado. Não precisa mudar configurações no mod.

## TargetHighlight / TargetLight

O contorno agora usa o material nativo de linhas com teste de profundidade **LEQUAL**. A renderização do TargetLight não passa pelo material sem profundidade das teias, independentemente da opção RenderTop. Box, Filled e Both passam pela geometria com profundidade.

Assim, blocos sólidos devem ocultar as partes do destaque que estão atrás deles. A opção Apenas elytra e seus filtros são preservados. RenderTop mantém o contorno extra no modo Filled, respeitando a oclusão. Como o depth test considera a cena, partes realmente encobertas por modelos também podem ficar ocultas; não há mais um contorno que ignore toda a profundidade para aparecer sobre qualquer objeto.

## Instalar

Feche o jogo e substitua o JAR anterior por **somente um** dos JARs deste ZIP, correspondente ao seu Minecraft. As versões 2.41 ou mais novas podem receber esta revisão pelo auto-update assinado do GitHub, quando habilitado. A 2.40 original precisa da substituição manual uma vez, pois procura a Vercel pausada. Reinicie quando o atualizador solicitar.

## Verificação

30 verificações das duas velocidades e da liberação de botão passaram. Em cada versão: 17 verificações executaram o formatador real e o observador físico do JAR, mais 16 verificações dos filtros/encaminhamento de renderização do TargetLight. Também foram conferidos o material nativo e seu depth test nos JARs reais do Minecraft para as quatro versões, além da estrutura ASM/JVM, integridade e preservação dos outros arquivos.

A assinatura do atualizador, o hash, o tamanho e a identidade dos artefatos são validados. Não foi executada uma sessão real de Minecraft/GPU para observar o resultado em paredes, elytra ou diferentes configurações gráficas.

Comparada à 2.44, mudam fabric.mod.json, AdaptiveCps243, SmoothCps244, TargetTop242, TargetTopGeometry242 e a descrição do RenderTop em TargetHighlight. A classe CpsDisplay, os mixins de entrada, os outros módulos, o roteamento de serviços e o atualizador permanecem idênticos. Não é incluído nenhum stub de testes nos mods.
