# Validação da versão 0.2.0

## Executado no ambiente de desenvolvimento

Linux, Python 3.12.14, PySide6 6.8.3, FFmpeg/ffprobe 7.1.5, codificador libx264. A interface Qt foi aberta em modo offscreen e inspecionada por screenshots reais. As imagens em `docs` são dessa execução, com biblioteca vazia e prévia de HUD ilustrativa.

**35 testes passaram**, sem testes ignorados:

- Corte, união, velocidade, volume, texto, filtro e zoom em exportações MP4 reais, preservando o arquivo original.
- Velocidade de 0,25×, entrada sem áudio, geração de faixa silenciosa e sticker.
- Replay a partir de segmentos reais do FFmpeg: duração final, corte com frações de segundo, áudio, HUD e imagem gravada nos pixels.
- HUD com teclas pressionadas renderizado por libass; validação dos pixels do resultado.
- Snapshot de áudio preservado quando o buffer circular é descartado, com silêncio nos períodos sem amostras.
- Limpeza do buffer respeitando uma exportação em andamento, retenção dos segmentos recentes e cores de screenshot.
- Recuperação dos atalhos anteriores quando um novo atalho está ocupado, usando uma API Win32 simulada.
- Interface das sete páginas, persistência de configurações, movimento do HUD, carregamento real de vídeo no Qt, divisão/desfazer e lista de música local.
- Validação de limites de edição, atalhos e links de playlist.

Cinco testes cobrem o iniciador: caminhos com espaços/acentos, registro de falhas de subprocessos, reutilização da instalação, interrupção quando a preparação falha, diagnóstico de encerramento precoce e rejeição de uma versão Python incompatível. As partes específicas do Windows usam simulações nesses testes.

A versão 0.2.0 acrescenta validações de:

- Writer de captura completo com quadros sintéticos injetados somente no teste e FFmpeg real: início, contador, salvamento de MP4, parada e reinício, inclusive quando o dispositivo de áudio falha.
- Falha nativa antes do primeiro quadro, cancelamento durante preparação e erro real do FFmpeg com diagnóstico preservado.
- Inicialização e liberação COM em capturas repetidas, inclusive quando a primeira amostra falha, com APIs do Windows e dispositivo de áudio simulados.
- Teste de resolução, qualidade e FPS dos candidatos a codificador; fallback e cache por configuração, com a disponibilidade de GPU simulada.
- Diagnóstico persistente na interface, cópia da mensagem, galeria com 126 arquivos, busca além do antigo limite, geração de miniatura real e reprodução de vídeo no Qt.
- Validação de links Spotify e ciclo de abertura/fechamento do WebEngine. Uma página HTML controlada foi renderizada e consultada por JavaScript dentro do widget real; esse teste não acessa o Spotify.

O relato de captura que volta ao zero não veio com log do Windows: **a causa específica no computador do usuário ainda não foi confirmada**. Foram corrigidos problemas concretos de inicialização do áudio, inicialização COM por thread, verificação do codificador e exibição de erros. Os testes sintéticos não validam a aquisição WGC nem o áudio WASAPI reais.

Também foram resolvidas as dependências para Python 3.12 / Windows x64 com pip em modo dry-run. Isso confirma a disponibilidade dos pacotes compatíveis; **não executa seus módulos nativos no Windows**.

O código passou por compilação Python, verificação de nomes/importações e formatação Ruff. O ZIP contém código, imagens, scripts, documentação e testes; não contém um ambiente Python pré-instalado ou binários FFmpeg.

## Ainda não validado no computador Windows

- Execução de Instalar.py / Abrir DuckCapture.py e aprovação pelo Controle de Aplicativo Inteligente e download real de FFmpeg pelo instalador.
- Aquisição de quadros via Windows Graphics Capture em jogos e outros aplicativos.
- Reprodução real de playlists do Spotify, limites de conta gratuita e suporte a codecs do player. Os domínios Spotify retornaram HTTP 403 no proxy deste ambiente; somente a interface incorporada e suas regras de navegação foram testadas localmente.
- Captura WASAPI, sincronização de áudio em uso prolongado, troca de dispositivo e saída de áudio física.
- Atalhos globais reais, bandeja do sistema, redimensionamento, fechamento/minimização da janela e mudanças de monitor/DPI.
- Codificadores NVIDIA/Intel/AMD, jogos em tela cheia, taxas altas, consumo de CPU/RAM/GPU e espaço utilizado durante sessões longas.

A rede desta máquina bloqueou o domínio Gyan com HTTP 403 no proxy. FFmpeg já estava disponível no sistema para os testes. A verificação SHA-256 do instalador permanece habilitada; nenhuma validação de integridade foi desativada. Há instalação manual documentada como alternativa. Isso não demonstra um erro no servidor Gyan ou na rede do usuário.

## Roteiro de teste no Windows

1. Instalar e abrir o pacote em uma pasta sem privilégios administrativos, com espaços e acentos no caminho.
2. Selecionar uma janela em movimento; iniciar 30 FPS / Econômico / 15 s com áudio desativado; salvar após 20 s. Conferir que o MP4 termina na ação do atalho e tem aproximadamente 15 s.
3. Repetir com áudio do sistema, música local e durações de 30 e 120 s. Conferir sincronização e ausência de cortes de áudio.
4. Testar F8/F9 com o jogo em foco e mudar os atalhos. Confirmar que uma combinação ocupada é recusada sem perder os atalhos anteriores.
5. Ativar HUD, mover elementos, salvar um preset, pressionar teclas e clicar no jogo. Trocar o foco para outro aplicativo e confirmar que os controles deixam de acender no HUD.
6. Importar o clipe, dividir, reordenar, mudar velocidade, inserir texto/imagem, exportar e reproduzir o MP4 em outro player.
7. Verificar NVIDIA/Intel/AMD disponíveis, resolução Full, alteração de tamanho da janela e captura por pelo menos 10 minutos. Medir CPU, memória, GPU e disco antes de recomendar um perfil como leve.
8. Abrir Todos os clipes, buscar um vídeo, reproduzir, editar, trocar a pasta e conferir prints. Carregar uma playlist em Música → Spotify; verificar se a conta gratuita permite prévias e fechar o player.
9. Minimizar DuckCapture para a bandeja, salvar por atalho, reabrir e fechar. Testar interrupção e limpeza de replay temporário; preservar clipes já salvos.

As etapas acima são pendentes; não estão sendo apresentadas como resultados obtidos.
