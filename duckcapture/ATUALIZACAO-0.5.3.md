# DuckCapture 0.5.3

Feche o DuckCapture anterior e execute **DuckCapture-Setup-0.5.3.exe**. Configurações e clipes são preservados. O ZIP contém o código-fonte.

- **Salvar e apertar F11:** clipes sem HUD agora copiam o vídeo já gravado, sem recodificar e sem abrir outro codificador na GPU. Isso reduz o trabalho ao salvar e preserva a qualidade do vídeo. O corte, áudio e som final são mantidos.
- **HUD:** durante a captura, a exportação usa CPU com dois threads e prioridade menor, evitando uma segunda sessão de codificação na GPU durante a troca F11. O processamento pode demorar mais, mas não altera a velocidade de reprodução do clipe. FPS de saída constante.
- **Recuperação:** acompanha a fonte separadamente do envio ao codificador, tolera a recriação temporária da janela e mantém a sessão de monitor ao dar Alt+Tab, descartando imagens de outros aplicativos.
- **Papel de parede:** normalização para MP4/H.264, imagem de fundo durante preparação/pausa e estado de carregamento visível em Aparência. O vídeo continua pausando durante a gravação para priorizar o jogo.

Testes com FFmpeg real, cortes fora de quadros-chave, troca F11 simulada e reprodução Qt. A medição em jogos e a comparação com Medal dependem de testes no mesmo PC; não há promessa de FPS fixo ou desempenho superior sem essa comparação.
