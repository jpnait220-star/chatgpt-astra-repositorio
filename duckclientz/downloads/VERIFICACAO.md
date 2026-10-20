# DuckClientZ 1.5.28-beta.1 — verificação

Pacote Fabric para Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Instale somente o JAR correspondente à sua versão, retirando o antigo da pasta `mods`. Os quatro originais 1.5.27 foram preservados. Os hashes dos arquivos entregues estão em `SHA256SUMS.txt` no ZIP e no manifesto do projeto.

## Correções incluídas

- Cosméticos: renderizador de modelos implementado na 1.20.1, finalização de vértices corrigida e chamadas por reflexão adaptadas aos nomes usados pelo Minecraft em produção. Recursos com caminhos inválidos foram normalizados.
- Color Filter: renderização implementada na 1.20.1/1.21.4; estado OpenGL e controles ajustados nas versões antigas. Na 1.21.11, o processamento usa uma textura intermediária e aplica o filtro ao quadro final.
- Elytra: animação aplicada ao modelo real das asas nas quatro versões, inclusive com intensidade padrão. Desligar a física devolve os ângulos do modelo vanilla. A opção de ocultar ganhou o hook ausente na 1.20.1.
- HitRange: a 1.21.11 ganhou tamanho configurável de 1 a 12, padrão 6, como nas demais versões. Esse controle muda o círculo visual; não aumenta o alcance dos ataques.
- Totem: limites e valores inválidos dos controles numéricos corrigidos; trava de rotação e ordem dos parâmetros de som ajustadas nas versões antigas; ativação da animação de HUD implementada na 1.20.1.
- Pets: atualização duplicada removida. Fonte da interface convertida para contornos aceitos pelo Minecraft, preservando caracteres, métricas e licença.

## Resultados

| Verificação | 1.20.1 | 1.21.1 | 1.21.4 | 1.21.11 |
|---|---|---|---|---|
| Cliente real com Fabric iniciou e carregou os hooks testados | Passou | Passou | Passou | Passou |
| Construção dos 19 modelos com recursos reais do jogo | Passou | Passou | Passou | Passou |
| Filtro OpenGL compilado e executado sem erro de GL | Passou | Passou | Passou | Usa outro pipeline |
| Cosméticos e filtro em cinza conferidos visualmente em terceira pessoa | Sim | Captura inconclusiva | Sim | Sim |
| Física da elytra altera o modelo e desligar restaura o valor vanilla | Passou | Passou | Passou | Passou |
| Referências diretas ao Minecraft auditadas / não resolvidas | 1.266 / 0 | 1.324 / 0 | 1.293 / 0 | 1.588 / 0 |

Os JARs instalados nas quatro instâncias de teste têm os mesmos SHA-256 dos candidatos entregues. A auditoria de referências diretas é uma verificação de compatibilidade de membros; não substitui executar todos os caminhos do mod.

Os 13 testes automatizados passaram. Eles incluem reprodução do defeito numérico nos originais e sua correção nos quatro candidatos, resolução de nomes, grafo do filtro, isolamento dos uniformes da passagem de cópia, integridade dos JARs e preservação dos 2.937 glifos e das métricas da fonte.

No teste do modelo real da elytra, os ângulos nas versões 1.20.1/1.21.1 foram aproximadamente 0,26179853 antes, 0,35435754 com física e 0,2617987 ao desligar. Nas versões 1.21.4/1.21.11 foram 0,0; 0,23255894; 0,0. Nas versões antigas, o teste estabiliza primeiro a interpolação vanilla.

A animação do totem foi acionada e observada no HUD da 1.21.4. Os testes de controles numéricos passaram nas quatro versões, mas isso não cobre todas as combinações visuais de escala, duração, mão e alterações durante a animação.

## Ambiente e limites

Testes em Linux, Java 21, Fabric Loader 0.19.5, Xvfb e Mesa por software, com Fabric API correspondente a cada versão. Foi usada uma identidade local de teste e mundos isolados. O mod auxiliar de testes, o Minecraft e suas dependências não fazem parte do ZIP entregue.

Esta entrega é beta. Ainda não foram validados: seu conjunto de mods; Sodium/Iris e shaders; execução no Windows; desempenho/FPS; áudio real; Java 17 na 1.20.1; todos os estados de voo e ocultação visual da elytra; círculo do HitRange em todas as versões; todas as opções do Totem Editor. A 1.21.1 passou nos testes de modelos e filtro, mas sua captura visual não permitiu concluir a avaliação da aparência.

A revisão concentrou-se nos problemas relatados e nas dependências desses recursos. A descompilação e a auditoria dos binários não representam uma revisão manual completa nem uma garantia de ausência de erros em todos os módulos.

As evidências detalhadas permanecem em `duckclientz/reports/` no projeto: resultados de integração por versão, auditorias de referências, log dos 13 testes e capturas visuais válidas. Se ocorrer um erro ao testar, informe a versão do Minecraft, a lista de mods e envie `logs/latest.log`.
