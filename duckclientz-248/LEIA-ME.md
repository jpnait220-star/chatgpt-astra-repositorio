# DuckClientZ beta 2.48 — remoção de FireworkKey e Elytra Bug Fix

Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base beta 2.47.

O módulo FireworkKey foi removido da lista de módulos, junto com seu código de uso, temporização, restauração de slot, ícone e chamada por frame. Seus atalhos deixam de executar ações do client.

Dentro do módulo Elytra, a opção Elytra Bug Fix e a correção de velocidade de voo correspondente foram removidas. Elytra Physics, Desativar Elytra (visual) e Inclinação continuam disponíveis. Na 1.21.1, o mixin exclusivo dessa correção foi removido do JAR, da lista de mixins e do refmap. Nas demais versões, foi removido somente o método de correção dentro do mixin compartilhado, preservando seus outros eventos.

Os outros módulos, o comportamento de CPS da 2.46 e o RenderTop da 2.47 são preservados. As opções de otimização de efeitos e de uso de itens do FixOptimizer não são o módulo FireworkKey e permanecem como estavam.

## Instalação

Feche o jogo e substitua o JAR antigo por somente o arquivo correspondente à sua versão de Minecraft. O ZIP reúne as quatro versões; não coloque todas em mods.

As versões 2.41 ou mais novas podem receber esta revisão pelo auto-update assinado do GitHub, quando habilitado. A 2.40 original precisa da substituição manual uma vez por consultar o endereço antigo da Vercel.

## Verificação

Em cada versão, foram conferidos a lista e a ordem de todos os módulos, removendo exclusivamente o registro de FireworkKey. Todos os mixins ativos apontam para classes presentes no JAR. A construção real de ElytraFeature foi executada com uma classe-base de teste, confirmando as três opções restantes e a ausência de Bug Fix. As classes alteradas também passaram no carregamento/verificação da JVM com os JARs reais do Minecraft.

O pacote foi conferido contra a 2.47: não há referências restantes às classes removidas nem ao campo bugFix; todos os demais arquivos ficam idênticos, exceto os pontos listados em build-report.json. O CPS, o TargetLight, os serviços e o atualizador são preservados. São validados a assinatura, o hash, o tamanho e a identidade dos downloads.

Não foi executada uma sessão real de Minecraft para verificar visualmente o menu. Classes e stubs de teste não são incluídos nos mods.
