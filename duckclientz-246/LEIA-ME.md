# DuckClientZ beta 2.46 — CPS middle com descida e subida suaves

Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base beta 2.45.

## Comportamento do {middle}

O middle continua contando seus cliques independentemente do número exibido. Ao segurar o esquerdo ou direito configurado para **Atacar**, o indicador passa a acompanhar os CPS reais desse botão com uma transição de aproximadamente 0,6 segundo. Por exemplo, se o middle está em 20 e você segura o direito de ataque, o indicador desce até os CPS do direito; segurá-lo sem novos cliques acaba levando a contagem a zero.

Ao soltar esse botão de ataque, o indicador volta a acompanhar o middle e **sobe gradualmente**, também em aproximadamente 0,6 segundo, até sua contagem atual. Não recupera uma contagem antiga congelada. Mudanças de contagem durante a transição são consideradas.

Um botão configurado apenas para Usar/colocar/comer não assume o indicador. O vínculo nativo de ataque e os vínculos extras do Multi Key Bindings (us.kenny, presente no MouseTweaks enviado) são reconhecidos; esse mod é opcional. Parar de clicar normalmente mantém a queda suave de aproximadamente 0,9 segundo.

São mudanças na exibição: os contadores reais, ataques, ações do mouse e AutoClicker permanecem como na 2.45. Não precisa alterar a configuração do HUD.

## Instalar

Feche o jogo e substitua o JAR anterior por **somente um** JAR correspondente ao seu Minecraft. O ZIP reúne as quatro versões; não coloque todas na pasta mods.

Versões 2.41 ou mais novas podem receber esta revisão pelo auto-update assinado do GitHub, quando habilitado. A 2.40 original precisa da troca manual uma vez, pois consulta a Vercel pausada. Reinicie quando o atualizador solicitar.

## Validação e limites

Passaram 21 verificações de tempo, incluindo descida, subida, mudança de alvo durante a subida, queda normal e overflow do relógio. Em cada versão, foram executadas 17 verificações do observador e formatador extraídos do próprio JAR, tanto com ataque nativo quanto com vínculo extra. Também foi testada a execução sem o mod opcional de múltiplos vínculos. Foram conferidas as assinaturas dos métodos e campos de entrada nos quatro JARs reais do Minecraft, a estrutura das classes, a integridade do JAR e a preservação dos outros arquivos.

A assinatura, o hash, o tamanho e a identidade dos artefatos são validados com o leitor do próprio atualizador. Não foi executada uma sessão real de Minecraft para observar o HUD em jogo.

Comparada à 2.45, mudam apenas fabric.mod.json, AdaptiveCps243 e SmoothCps244; é adicionada AttackBindings246. TargetLight e sua oclusão por blocos, os demais módulos, CpsDisplay, os mixins, as rotas dos serviços e o atualizador permanecem byte a byte iguais à 2.45. Stubs e classes de teste não são incluídos nos mods.
