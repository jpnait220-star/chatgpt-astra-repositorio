# Validação da versão 0.5.1

O pacote foi desenvolvido a partir do ZIP DuckCapture 0.4.8 enviado pelo usuário.

## Verificações locais

Resultado: **130 testes aprovados** com Python 3.12 e Qt em modo offscreen no Linux.

- Testes automatizados de captura sintética com FFmpeg real, exportação MP4, áudio, fila F8, instalação, configurações, HUD, galeria, editor e interface.
- Casos novos: índice de monitor começando em 1, bloqueio de captura do monitor sem foco, 600 timestamps nativos a 60 FPS sob atraso variável das chamadas Python, cache de imagem e resolução de saída.
- Casos de UI: transformação real dos quatro cantos, alteração dos pixels do card, movimento reduzido, validação do seletor de cores, interrupção de transições e cortes inválidos/desfazer.
- Spotify: seleção exclusiva da sessão do aplicativo Spotify (nunca do Chrome), respeito aos controles disponíveis, timeout do navegador e descarte das páginas sem destruir um perfil em uso.
- Som WAV estéreo de 1,08 s, pico abaixo de 0 dBFS e início/fim suavizados.
- Revisão de telas em 1360×930 e 1000×700. O editor não cria rolagem horizontal na largura mínima.
- Lint de nomes/importações, compilação Python e abertura do aplicativo com fontes, ícones e FFmpeg em ambiente isolado.

## Windows

O workflow `.github/workflows/duckcapture-windows.yml` compila com Python 3.12 x64, PyInstaller e Inno Setup. Antes de publicar, executa o próprio aplicativo compilado com `--check-installation`, verifica dependências e recursos, codifica/lê um vídeo real de teste e abre a janela. O resultado JSON, a captura de tela e o log ficam nos artefatos da execução.

## Limites

Os testes de F11 simulam a fronteira da API de captura; não substituem testes com um jogo real, GPU, troca de monitor, áudio USB e carga concorrente. O ajuste remove erros observados no código, mas não garante 60 imagens distintas por segundo em todo computador.

Os controles Spotify foram testados com sessões simuladas; música completa, anúncios, comandos permitidos e login continuam sob controle do Spotify instalado. É necessário testar com a conta e o aplicativo do usuário. A reprodução dentro da prévia web depende do serviço e não representa garantia de músicas completas em um navegador Qt.

A fonte e os ícones do player web oficial são definidos pelo Spotify. A nova fonte Manrope cobre a interface do DuckCapture, os textos exportados e o HUD.

## Novidades verificadas na 0.5.1

- Mistura do som no final: preservação dos primeiros segundos, duração exata, controle de pico, clipes curtos e áudio do jogo. Exportação real com e sem dispositivo de áudio, com o som de confirmação ligado e desligado.
- Upload para API simulada em servidor HTTP local: abertura não envia arquivos, formulário multipart transmite o conteúdo, nome local não é exposto, resposta validada, histórico, limite de tamanho e cancelamento. Nenhum clipe pessoal foi publicado nos testes.
- O acesso HTTPS ao Catbox é bloqueado pelo proxy deste ambiente (403 no túnel); o serviço real e a incorporação no Discord não foram validados aqui.
- Botões e seletores criados em diálogos recebem animação; retorno gradual não altera o tamanho nem a área clicável.
- Wallpaper ignora quadros enquanto pausado, mantém áudio mudo e reprodução em loop. O diagnóstico de instalação também decodifica um MP4 real pelo player Qt.

## Recuperação ao salvar e alternar F11

- Teste com FFmpeg real: salvar durante captura em janela, trocar para monitor com o HWND antigo ainda válido, verificar movimento no MP4 exportado e voltar à janela sem encerrar o replay.
- Regressões de relógio nativo reiniciado, callbacks atrasados da fonte antiga, encerramento nativo lento e prazo de conexão da nova fonte.
- A seleção de uma nova janela ainda viva exige mesmo processo, mesma classe, tamanho de janela principal e ausência de proprietário; diálogos e outros processos são rejeitados.
- O jogo e a GPU do usuário ainda precisam de teste no PC real. O teste simula a fronteira do Windows Graphics Capture.
