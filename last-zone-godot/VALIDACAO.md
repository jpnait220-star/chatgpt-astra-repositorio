# Validação desta migração

Godot 4.6.3 Standard, Linux, renderizador Compatibility/OpenGL.

- `godot --headless --path . --script res://tests/smoke.gd`: passou com 48 atores, 108 kits no chão, 200 HP, velocidade 14% maior, salto e pouso em relevo real, controle no ar, gelo durante o salto, colisão/linha de visão, uso de kits e HUD na área visível. O teste encerra e remove a cena, sem erro de script ou recursos pendentes na execução final.
- Mundo: quatro consultas reais de física coincidiram com a altura da malha. Casas, rampas e vegetação usam colisão nativa.
- Bot: teste isolado verificou aquisição de alvo, rajadas, bloqueio de tiros por parede, passos, cura e morte.
- `godot --path . --script res://tests/preview.gd`: renderização real por Mesa/llvmpipe em display virtual. Capturas da cidade, vista aérea e personagem. Shaders compilados sem erro; aviso de V-Sync indisponível é específico do display virtual.
- A compilação e os binários exportados são verificados pelo workflow de publicação. A execução em Windows e o FPS em GPU física não foram testados aqui.

Esta é a primeira versão solo em Godot. Multiplayer, servidor Altare/Node, paraquedas e paridade completa com a versão HTML ainda não foram migrados. O pacote Windows não possui assinatura de editor confiável; o Controle Inteligente de Aplicativos pode bloqueá-lo.
