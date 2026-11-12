# DuckClientZ beta 2.47 — RenderTop sobre o jogador, com bloqueio por paredes

Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base beta 2.46.

## RenderTop

A 2.45 passou todas as linhas do TargetLight pelo depth test da cena. Isso ocultava as linhas atrás das paredes, mas também ocultava as linhas atrás do próprio modelo do jogador, impedindo o comportamento desejado de RenderTop.

Com RenderTop ligado, o contorno agora usa uma camada sobre os modelos, depois de recortar as partes ocultas pelos blocos. Antes de desenhar cada uma das 12 arestas, são calculados os intervalos de oclusão a partir da câmera e das caixas da forma visual dos blocos. O recorte usa a geometria do triângulo entre câmera e aresta, sem depender de amostras esparsas de raycast.

Assim, em espaço aberto, as linhas de trás da hitbox aparecem sobre o jogador; uma parede inteira oculta o contorno, e uma cobertura parcial oculta seus trechos correspondentes. Blocos atrás do alvo não ocultam o contorno à frente deles. Modelos de blocos personalizados são tratados conforme suas formas visuais fornecidas pelo jogo, que podem diferir da textura exibida.

RenderTop desligado mantém o contorno com profundidade nativa. Box e Both usam o novo contorno quando ligado. Filled mantém o preenchimento com profundidade e recebe o contorno sobre o jogador. Apenas elytra e os filtros anteriores permanecem funcionando.

Há um limite de trabalho de 8192 células e 4096 caixas por alvo. Em situações fora desses limites, o desenho volta ao contorno com profundidade nativa, para evitar uma busca muito grande. O contorno extra não atravessa os blocos nesse fallback.

## Instalar

Feche o jogo e substitua o JAR anterior por somente o arquivo correspondente ao seu Minecraft. O ZIP reúne as quatro versões; não coloque todas em mods. Ative RenderTop nas opções de TargetHighlight/TargetLight.

Auto-update assinado do GitHub disponível para 2.41 ou mais novas, quando habilitado. A 2.40 original precisa da substituição manual uma vez devido ao endereço antigo da Vercel.

## Verificações e limites

O recorte passou por cinco cenários específicos e 120000 comparações com um teste de interseção de raios independente. Em cada versão, 61 verificações executaram o encaminhamento e a coleta/recorte reais, capturando as linhas antes da GPU: espaço aberto, chão, parede inteira/parcial/atrás, RenderTop desligado, Filled/Both, fallback e filtros de elytra.

Também foram conferidas as APIs nativas de formas de blocos, a estrutura das classes e seu carregamento pela JVM com os JARs reais do Minecraft. Assinatura, hash, tamanho e identidade dos downloads são validados pelo leitor do próprio atualizador.

Não foi executada uma sessão real de Minecraft/GPU para validar visualmente os contornos ou medir o FPS no seu computador.

Comparada à 2.46, mudam apenas TargetTop242, a descrição de RenderTop em TargetHighlight e fabric.mod.json. São adicionadas TargetOverlay247, TargetRawLine247 e BlockShadow247. A geometria normal, os materiais das teias, o CPS da 2.46, os outros módulos, os serviços e o atualizador permanecem byte a byte idênticos. Classes e stubs de testes não entram nos mods.
