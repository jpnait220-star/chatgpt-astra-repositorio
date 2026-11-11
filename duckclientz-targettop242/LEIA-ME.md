# DuckClientZ beta.2.42 — TargetLight RenderTop + Altare

Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Base: a transição 2.41 construída sobre os quatro JARs 2.40 enviados pelo usuário.

## TargetLight / TargetHighlight

Em **TargetHighlight**, foram adicionadas:

- **RenderTop**: ativado por padrão. Desenha o contorno da hitbox por cima do modelo usando o material de linhas sem teste de profundidade já presente no mod. Desative para usar o caminho anterior.
- **Apenas elytra**: desativado por padrão. Quando ligado, seleciona e destaca somente alvos que estão efetivamente planando com a elytra ativada. Apenas equipar a elytra não basta. O filtro entra antes do limite de jogadores próximos e é conferido novamente ao renderizar.

Box usa o contorno por cima. Both mantém o preenchimento normal e um único contorno por cima. Filled mantém o preenchimento normal e acrescenta o contorno por cima quando RenderTop está ligado. O preenchimento continua usando sua profundidade normal; o RenderTop foi implementado para garantir a visibilidade do **contorno**, sem mudar globalmente os outros elementos.

Não altera tamanho/posição da hitbox física, alcance de ataque, física da elytra ou detecção de golpes. Mantém as cores por vida, fade, distância e limite de alvos existentes.

## Conexão Altare

O endereço ativo é `https://duckconnect.go.altare.global`. `https://duckcommunity.go.altare.global` é outro domínio do mesmo serviço. Os testes públicos confirmaram saúde HTTP 200, envio/consulta/limpeza de cosméticos e leitura cruzada entre os dois domínios. As rotas de comunidade e chat rejeitaram entradas inválidas; não foram enviadas mensagens públicas de teste.

A configuração assinada na revisão 2 foi ativada após esses testes. O transporte do client também foi validado contra o HTTPS real da Altare. Nenhum certificado ou verificação TLS foi desativado no mod.

O serviço precisa permanecer ligado na Altare. Reiniciar o Node limpa o estado online/chat temporário; os clients republicam os equipamentos/presença. Falhas de hospedagem ainda podem interromper a conexão.

## Instalação e auto-update

Feche o Minecraft, guarde o JAR anterior fora de `mods` e coloque **somente o JAR correspondente à sua versão**. Não deixe dois DuckClientZ juntos. Suas configurações não são apagadas.

- Quem ainda usa a **2.40 original** precisa trocar manualmente uma vez: aquele atualizador consulta a Vercel pausada e não descobre sozinho um domínio novo.
- Quem já instalou a **2.41** pode receber a 2.42 pelo manifesto assinado do GitHub ao iniciar o jogo, com atualização automática habilitada. É necessário fechar e abrir o Minecraft para carregar o arquivo novo.
- A **2.42** continua usando o mesmo canal GitHub para as próximas versões. Assinatura Ed25519, limites de URL, SHA-256, tamanho e identidade do mod continuam verificados.

Alterações futuras de endereço do serviço podem ser feitas por configuração assinada sem recompilar novamente os JARs 2.41/2.42. O cache pode levar cerca de um minuto quando estava pendente, e até dez minutos quando já estava ativo; abrir o jogo novamente pode usar o último endereço verificado em cache.

## Verificação e limites dos testes

- Os JARs finais passaram pela verificação estrutural de bytecode e integridade.
- Entre entradas existentes da 2.41, só `TargetHighlight.class` e `fabric.mod.json` mudaram. Os utilitários de renderização originais, demais módulos, migração de rede e updater permanecem byte a byte iguais.
- Foram adicionadas duas classes: política/adaptador TargetTop242 e cópia da geometria nativa dedicada ao contorno. Os stubs usados na compilação/teste **não** foram incluídos nos mods.
- Por versão: 16 verificações de lógica com entidades/consumidores simulados; API nativa de planagem conferida nos mappings; registro das opções e material em cache NO_DEPTH_TEST/COLOR_ONLY verificados. Garante a seleção e o encaminhamento esperados, mas não substitui teste gráfico com GPU.
- Manifesto de atualização assinado validado pelas classes de atualização dos quatro próprios JARs: transição 2.41 -> 2.42, ausência de loop, SHA-256/tamanho/identidade e configuração ativa assinada.

**Não foi realizado teste visual dentro do Minecraft nem benchmark de FPS/anticheat.** Os testes de rede pública e de lógica estão separados da validação gráfica que depende do jogo.
