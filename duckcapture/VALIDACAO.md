# Validação da versão 0.2.1

## Executado no ambiente de desenvolvimento

Linux, Python 3.12.14, PySide6 6.8.3, FFmpeg/ffprobe 7.1.5, codificador libx264. A interface Qt foi aberta em modo offscreen e inspecionada por screenshots reais. As imagens em `docs` são dessa execução, com biblioteca vazia e prévia de HUD ilustrativa.

**47 testes passaram**, sem testes ignorados:

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

Os testes de captura e integração também verificam:

- Writer de captura completo com quadros sintéticos injetados somente no teste e FFmpeg real: início, contador, salvamento de MP4, parada e reinício, inclusive quando o dispositivo de áudio falha.
- Falha nativa antes do primeiro quadro, cancelamento durante preparação e erro real do FFmpeg com diagnóstico preservado.
- Inicialização e liberação COM em capturas repetidas, inclusive quando a primeira amostra falha, com APIs do Windows e dispositivo de áudio simulados.
- Teste de resolução, qualidade e FPS dos candidatos a codificador; fallback e cache por configuração, com a disponibilidade de GPU simulada.
- Diagnóstico persistente na interface, cópia da mensagem, galeria com 126 arquivos, busca além do antigo limite, geração de miniatura real e reprodução de vídeo no Qt.
- Validação de links Spotify e ciclo de abertura/fechamento do WebEngine. Uma página HTML controlada foi renderizada e consultada por JavaScript dentro do widget real; esse teste não acessa o Spotify.

A versão 0.2.1 inclui regressões específicas para os problemas reportados:

- O primeiro import do SoundCard ocorre antes da inicialização COM por thread. A simulação reproduz o erro `0x100000001` quando a ordem é invertida, e verifica primeira captura e capturas seguintes.
- Replay com CSV inacessível, mudança de proporção da janela durante a gravação e exportação de MKV sem duração/índice final. O FFmpeg real gera e valida o MP4 resultante.
- Minimização, retorno, reconexão da fonte e fechamento de janela, com a fronteira Windows simulada e o writer real em execução.
- Links de faixas, álbuns, artistas, episódios e programas; resolução de link curto com respostas de rede simuladas e rejeição de redirecionamento fora dos destinos permitidos.
- Seleção/paginação da janela com registro e liberação de prévias simulados; sons por tipo de arquivo e preferência para silenciar; expansão dos botões.

A configuração de captura solicita baixa latência e quadros IDR forçados em NVIDIA/Intel para ajudar a fechar os segmentos. As opções foram conferidas na ajuda do FFmpeg; a opção AMD de baixa latência foi conferida no código oficial FFmpeg n7.1. **A aquisição WGC, as prévias DWM, o áudio real do fone USB, o som de confirmação e os encoders de GPU não foram executados em Windows neste ambiente.** O comportamento específico do erro de segmento no hardware do usuário permanece pendente de confirmação; os testes cobrem as condições de falha tratadas pelo novo código.

Também foram resolvidas as dependências para Python 3.12 / Windows x64 com pip em modo dry-run. Isso confirma a disponibilidade dos pacotes compatíveis; **não executa seus módulos nativos no Windows**.

O código passou por compilação Python, verificação de nomes/importações e formatação Ruff. O ZIP contém código, imagens, scripts, documentação e testes; não contém um ambiente Python pré-instalado ou binários FFmpeg.

## Ainda não validado no computador Windows

- Execução de Instalar.py / Abrir DuckCapture.py e aprovação pelo Controle de Aplicativo Inteligente e download real de FFmpeg pelo instalador.
- Aquisição de quadros via Windows Graphics Capture em jogos e outros aplicativos.
- Reprodução real de playlists do Spotify, limites de conta gratuita e suporte a codecs do player. Os domínios Spotify retornaram HTTP 403 no proxy deste ambiente; somente a interface incorporada e suas regras de navegação foram testadas localmente.
- Captura WASAPI com o fone USB, sincronização de áudio em uso prolongado, troca de dispositivo e saída de áudio física.
- Prévias DWM de janelas reais, seleção em monitores com DPI diferentes e sons de confirmação audíveis.
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
7. Mover, redimensionar, minimizar por 10 s e restaurar a janela durante a captura. Conferir que o contador continua, o áudio permanece e a imagem retoma. Salvar por F8 antes e depois dessas ações. Verificar NVIDIA/Intel/AMD disponíveis, resolução Full e captura por pelo menos 10 minutos. Medir CPU, memória, GPU e disco antes de recomendar um perfil como leve.
8. Abrir Todos os clipes, buscar um vídeo, reproduzir, editar, trocar a pasta e conferir prints. Carregar uma playlist em Música → Spotify; verificar se a conta gratuita permite prévias e fechar o player.
9. Minimizar DuckCapture para a bandeja, salvar por atalho, reabrir e fechar. Testar interrupção e limpeza de replay temporário; preservar clipes já salvos.

As etapas acima são pendentes; não estão sendo apresentadas como resultados obtidos.
