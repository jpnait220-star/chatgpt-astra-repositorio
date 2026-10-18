# DuckCapture · 0.1.1 alpha

**Leve como um pato, rápido como um clique.** Um aplicativo desktop com replay de janela, editor, HUD e música, com interface em português e uma turma de nove mascotes.

Esta é uma primeira versão para **Windows 10 (versão 2004 ou mais recente) / 11 de 64 bits**. A interface e o processamento de vídeos foram testados no Linux. A captura de uma janela real, áudio WASAPI, atalhos globais e desempenho de GPU ainda precisam de validação em um computador Windows. Não há promessa de 240 FPS ou consumo específico de recursos.

## Como instalar gratuitamente

1. Instale **Python 3.12 de 64 bits**, com o Python Launcher. O [Python 3.12.10 para Windows](https://www.python.org/downloads/release/python-31210/) tem instalador de 64 bits. Não é preciso pagar, criar conta ou comprar certificado.
2. Extraia **a pasta inteira** do ZIP para uma pasta permanente, por exemplo `Documentos\DuckCapture`. Não execute dentro do ZIP.
3. Abra **Abrir DuckCapture.py** com o Python Launcher. Na primeira abertura, ele cria um ambiente Python local, instala as dependências e baixa FFmpeg/ffprobe de Gyan, distribuidor indicado pelo projeto FFmpeg. O download do FFmpeg é verificado com o SHA-256 publicado pelo distribuidor.
4. Aguarde o aplicativo abrir. Nas próximas vezes, use o mesmo **Abrir DuckCapture.py**. O iniciador reaproveita as dependências já instaladas.
5. Para apenas instalar, sem abrir o aplicativo, use **Instalar.py**. Mensagens de instalação ficam em `instalacao.log`; erros ao abrir a interface ficam em `inicializacao.log`, na pasta extraída.

Se o arquivo `.py` abrir em um editor, clique com o botão direito → **Abrir com → Python**. Outra opção é abrir o Terminal na pasta extraída e executar:

```powershell
py -3.12 "Abrir DuckCapture.py"
```

O ZIP 0.1.1 usa iniciadores Python e não inclui os `.cmd` antigos. Isso oferece uma alternativa quando o bloqueio do Windows se refere aos scripts de lote. **Não garante que o Controle de Aplicativo Inteligente aceitará todas as dependências**: ele também pode bloquear um executável ou DLL sem reputação/assinatura aceita. O iniciador não desativa nem modifica a proteção do Windows. Se houver outro bloqueio, o nome do arquivo indicado no aviso é necessário para identificar a causa.

Python e FFmpeg usam executáveis normais como dependências. Não é necessário pagar por uma assinatura para criar um aplicativo; isso não significa que políticas de confiança do Windows aceitarão qualquer distribuição. Esta versão é código Python disponível para inspeção e não é uma distribuição assinada ou certificada pela Microsoft.

A instalação inicial precisa de internet e baixa algumas centenas de MB de dependências. Depois, captura, editor e músicas locais funcionam offline. Mantenha espaço livre para o replay e os vídeos. A proposta de baixo consumo se refere ao funcionamento, não ao tamanho das dependências; ainda não foi medida no Windows.

## Primeiro clipe

1. Abra o jogo ou aplicativo. Para jogos, prefira **janela sem bordas**.
2. No DuckCapture, entre em **Capturar**, atualize as janelas e selecione a desejada.
3. Comece com **Equilibrado / 60 FPS**, ou **Econômico / 30 FPS** em um computador mais simples.
4. Escolha o replay: **15, 30, 60, 90 ou 120 segundos** e clique em **Iniciar captura**.
5. Jogue normalmente. **F8** salva os últimos segundos; **F9** tira um print da janela. Ambos podem ser alterados em Configurações.
6. Os arquivos aparecem na página Início e em `Vídeos\DuckCapture` por padrão. A pasta pode ser alterada.

Antes de o buffer encher, o clipe terá apenas o tempo já capturado. Salvar pode levar alguns segundos: o aplicativo termina o segmento atual e exporta somente até o instante do atalho. Há uma exportação de replay por vez. O botão **Parar** descarta o replay que não foi salvo; vídeos já salvos permanecem.

**Full** mantém a resolução da janela, arredondada para dimensões pares, e usa compressão de alta qualidade. Não é sem perdas e não preserva HDR. Econômico limita a largura a 1280, Equilibrado a 1920 e Alta qualidade a 2560 pixels, preservando a proporção. As opções de FPS são taxas desejadas de saída; a janela e o hardware podem entregar menos quadros diferentes.

## Editor

Importe um vídeo ou selecione um clipe da biblioteca e clique em **Editar selecionado**. Use a barra para posicionar o vídeo e **Dividir aqui**; ajuste início, fim, velocidade, volume e zoom de cada trecho. Importe mais vídeos para juntar, reordene trechos com as setas e use Desfazer quando necessário.

Texto, sticker, preto e branco, filtro quente, contraste e zoom são aplicados ao **exportar MP4**. A prévia reproduz o trecho original, com velocidade e controle de volume; não simula todos os efeitos. Stickers ficam no canto superior direito e o zoom é central. O original é preservado; escolha um nome de saída novo. Projetos de edição não são salvos entre sessões nesta versão.

## HUD

Ative **Aplicar HUD aos próximos clipes** e arraste os elementos no editor. Ajuste escala, opacidade e texto; salve presets próprios ou use Minecraft PvP, Tutorial, Speedrun e Minimal. Também é possível inserir imagens.

O HUD é gravado no vídeo exportado. Não é uma janela flutuante por cima do jogo. Sua prévia é ilustrativa. O teclado acompanha somente W/A/S/D, Espaço, Shift e Ctrl, além dos botões do mouse, enquanto a janela escolhida está em foco. O círculo de clique aparece na posição do cursor. As alterações de HUD valem para o próximo clipe salvo; se ativar durante a captura, as teclas anteriores à ativação não terão sido coletadas.

O FPS mostrado é o FPS configurado da captura, não a taxa interna do jogo. O contador de tempo começa em zero no clipe. Ping de servidor, macros e medição do FPS do jogo não estão implementados. O arquivo `.json` ao lado do clipe guarda a configuração e os estados dos controles usados no HUD; nada é enviado a um servidor.

## Música e Spotify

Coloque MP3, WAV, FLAC, OGG, M4A ou AAC em `Música\DuckCapture Music`, ou escolha outra pasta. A lista é atualizada automaticamente. Há play/pause, anterior/próxima, volume, busca, aleatório e repetição da faixa. O vinil gira enquanto toca e mostra a capa quando o arquivo contém metadados compatíveis.

O elemento Música do HUD exibe o título da faixa local. O áudio do sistema, quando ativado, inclui o que toca na saída padrão do Windows, inclusive outras aplicações. Não há captura de microfone ou isolamento de áudio por aplicativo nesta versão.

Cole um link `https://open.spotify.com/playlist/...` para abrir a playlist no serviço oficial. Esta versão **não importa a playlist para o tocador**, não controla o Spotify por API e não baixa suas músicas.

## Se algo não funcionar

- **Controle de Aplicativo Inteligente:** use a pasta extraída do ZIP 0.1.1 e **Abrir DuckCapture.py**. Se o aviso continuar, registre o nome exato do arquivo bloqueado. Esta versão não altera configurações de segurança.

- **Captura indisponível:** use Windows de 64 bits, com a janela restaurada. Aplicativos protegidos e alguns modos de tela cheia exclusiva podem bloquear a captura.
- **A janela mudou de tamanho:** pare e inicie novamente. A resolução é definida ao começar a sessão.
- **Travamento ou FPS insuficiente:** tente 30 FPS, Econômico e codificador Automático. O aplicativo procura NVIDIA, Intel ou AMD; se nenhum funcionar, utiliza CPU com libx264. Não é possível garantir baixo consumo em todos os computadores.
- **Áudio não disponível:** confira a saída padrão do Windows ou desmarque áudio do sistema. Ao trocar de dispositivo, reinicie a captura.
- **Atalho em uso:** escolha outro em Configurações e clique em Aplicar atalhos.
- **Download do FFmpeg falhou:** baixe o pacote Essentials em [Gyan](https://www.gyan.dev/ffmpeg/builds/), extraia `ffmpeg.exe` e `ffprobe.exe` para a pasta `tools` ao lado de `run.pyw`, e execute Instalar.py novamente. Mantenha os arquivos da mesma distribuição.
- **Erro com texto/HUD:** use uma distribuição FFmpeg com filtro `subtitles` e libass, como Essentials. Uma instalação FFmpeg já existente no PATH precisa oferecer esses recursos.
- **Fechou após um erro:** consulte `instalacao.log` e `inicializacao.log` na pasta extraída. Em Configurações, **Abrir dados e logs** mostra `duckcapture.log` e, quando disponível, `last-encoder.log`.
- **Replay antigo ocupando disco após uma interrupção:** com a captura parada, use **Limpar replay temporário**. Isso preserva os clipes salvos.

Configurações e temporários ficam em `%LOCALAPPDATA%\DuckCapture`. O replay usa segmentos de vídeo comprimido em disco, com retenção limitada ao tempo escolhido e uma pequena margem; o áudio fica em um buffer de memória. A interface reduz a atualização da prévia e só acompanha controles quando o HUD está ativado. As animações do vinil param com a música.

## Desenvolvimento e verificação

Na pasta do projeto, com Python 3.12 e FFmpeg/ffprobe no PATH:

```sh
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements-dev.txt
# Linux:
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Os testes Linux usam Qt offscreen e vídeos sintéticos processados pelo FFmpeg real. Cobrem exportações, duração, áudio, HUD, imagens, preservação do original, buffer, atalhos com API simulada e interação com a interface. **Não substituem um teste de captura no Windows.** Veja [VALIDACAO.md](VALIDACAO.md) para os resultados e o roteiro de teste em Windows.

O conceito em escrita normal está em [CONCEITO.md](CONCEITO.md). A arte da turma está em `duckcapture/assets/mascots.png` e o Duck individual em `duckcapture/assets/duck.png`. Os arquivos originais de arte estão incluídos no pacote.
