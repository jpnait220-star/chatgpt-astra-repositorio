# DuckCapture · 0.2.1 alpha

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

O ZIP 0.2.1 usa iniciadores Python e não inclui os `.cmd` antigos. Isso oferece uma alternativa quando o bloqueio do Windows se refere aos scripts de lote. **Não garante que o Controle de Aplicativo Inteligente aceitará todas as dependências**: ele também pode bloquear um executável ou DLL sem reputação/assinatura aceita. O iniciador não desativa nem modifica a proteção do Windows. Se houver outro bloqueio, o nome do arquivo indicado no aviso é necessário para identificar a causa.

Python e FFmpeg usam executáveis normais como dependências. Não é necessário pagar por uma assinatura para criar um aplicativo; isso não significa que políticas de confiança do Windows aceitarão qualquer distribuição. Esta versão é código Python disponível para inspeção e não é uma distribuição assinada ou certificada pela Microsoft.

A instalação inicial precisa de internet e baixa algumas centenas de MB de dependências. Depois, captura, editor e músicas locais funcionam offline. Mantenha espaço livre para o replay e os vídeos. A proposta de baixo consumo se refere ao funcionamento, não ao tamanho das dependências; ainda não foi medida no Windows.

## Atualizar sem reinstalar

Feche o DuckCapture, inclusive o ícone na bandeja. Extraia o ZIP novo e copie o conteúdo da pasta `DuckCapture` para a pasta onde o aplicativo já está instalado. Aceite substituir os arquivos do pacote. Preserve `.venv`, `tools`, os clipes e suas músicas. Evite mover ou renomear a pasta de instalação; o ambiente Python guarda alguns caminhos.

Abra **Abrir DuckCapture.py**. Se o iniciador continuar sem abrir uma janela, abra o Terminal nessa pasta e execute o comando abaixo para ver o erro diretamente:

```powershell
.\.venv\Scripts\python.exe -u -m duckcapture
```

## Primeiro clipe

1. Abra o jogo ou aplicativo. Para jogos, prefira **janela sem bordas**.
2. No DuckCapture, entre em **Capturar → Escolher janela**. Veja as prévias, busque pelo nome e clique na imagem ou no botão da janela desejada. As prévias nativas funcionam no Windows; janelas protegidas ou minimizadas podem aparecer sem imagem.
3. Comece com **Equilibrado / 60 FPS**, ou **Econômico / 30 FPS** em um computador mais simples.
4. Escolha o replay: **15, 30, 60, 90 ou 120 segundos** e clique em **Iniciar captura**.
5. Aguarde **REPLAY ATIVO** e confira o contador aumentando. Durante a preparação, o painel informa a etapa atual; o teste dos codificadores pode demorar alguns segundos. Jogue normalmente. **F8** salva os últimos segundos; **F9** tira um print da janela. Ambos podem ser alterados em Configurações.
6. Abra **Todos os clipes**, no menu ou no botão da página Início, para ver todos os vídeos e prints. Há busca por nome, filtro por tipo, miniaturas e reprodução com dois cliques. A página Início mostra os 12 mais recentes. Os arquivos ficam em `Vídeos\DuckCapture` por padrão. A pasta pode ser alterada.

Antes de o buffer encher, o clipe terá apenas o tempo já capturado. Salvar pode levar alguns segundos: o aplicativo congela os segmentos necessários e exporta somente até o instante do atalho. Ele confere o vídeo antes de confirmar o salvamento. Um som curto confirma o clipe salvo; outro som confirma o print. Desative **Som ao salvar clipes e prints** em Configurações se preferir silêncio. Há uma exportação de replay por vez. O botão **Parar captura** descarta o replay que não foi salvo; vídeos já salvos permanecem.

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

Na aba **Spotify**, use **Colar link** ou cole um endereço de música, álbum, artista, playlist, episódio ou programa. Pressione Enter ou clique em **Ouvir no app**. São aceitos links `https://open.spotify.com/...`, URIs `spotify:track:...` e links curtos `https://spotify.link/...`. Links curtos dependem de uma resposta do serviço para serem resolvidos. O conteúdo abre dentro do DuckCapture, no player oficial incorporado. Clique em reproduzir nos controles abaixo. O tocador local é pausado ao carregar o Spotify. Ao voltar a reproduzir um arquivo local, o player Spotify é fechado para evitar duas músicas ao mesmo tempo.

**Conta gratuita:** o player pode oferecer apenas prévias de 30 segundos; não há garantia de faixas completas. Esta versão usa o embed oficial, não o Web Playback SDK (que exige Premium para reprodução completa), e não baixa músicas nem remove limitações do serviço. Músicas locais tocam completas. Links que tentam abrir outras janelas mostram um aviso no próprio aplicativo.

O player usa internet apenas quando carregado e pode usar mais memória que o tocador local. **Fechar player** encerra sua página. A sessão web é temporária. A integração não transmite os clipes ao Spotify, e o título da faixa do Spotify não é coletado para o HUD. A reprodução real depende do serviço, dos codecs e das permissões disponíveis no computador; não foi validada no ambiente de desenvolvimento porque o proxy bloqueia o Spotify.

## Se algo não funcionar

- **Controle de Aplicativo Inteligente:** use a pasta extraída do ZIP 0.2.1 e **Abrir DuckCapture.py**. Se o aviso continuar, registre o nome exato do arquivo bloqueado. Esta versão não altera configurações de segurança.

- **Iniciar volta ao zero:** o painel mostra o diagnóstico e mantém a mensagem mesmo depois de parar. Use **Copiar diagnóstico**. Tente 30 FPS / Econômico / Automático com a janela restaurada. O aplicativo verifica os codificadores na resolução e no perfil que serão usados; se o modo automático não encontrar GPU compatível, tenta libx264.
- **Captura indisponível:** use Windows de 64 bits, com a janela restaurada. Aplicativos protegidos e alguns modos de tela cheia exclusiva podem bloquear a captura.
- **Mover ou redimensionar:** a sessão continua. O vídeo é ajustado à resolução inicial, preservando proporções e usando faixas pretas quando necessário.
- **Minimizar:** a sessão e o áudio continuam; quando o Windows não fornece imagens, o último quadro fica congelado até restaurar. Conteúdo que o aplicativo deixa de desenhar minimizado não pode ser gravado em movimento. Inicie a captura com a janela restaurada.
- **A janela foi fechada:** a captura termina; os clipes salvos permanecem.
- **Travamento ou FPS insuficiente:** tente 30 FPS, Econômico e codificador Automático. O aplicativo procura NVIDIA, Intel ou AMD; se nenhum funcionar, utiliza CPU com libx264. Não é possível garantir baixo consumo em todos os computadores.
- **Erro `0x100000001`:** a versão 0.2.1 corrige a ordem de inicialização COM usada pelo SoundCard. Feche o aplicativo por completo antes de atualizar e testar novamente.
- **Áudio não disponível:** o vídeo continua e o painel avisa **SEM ÁUDIO**. Confira a saída padrão do Windows e reinicie a captura para tentar o áudio novamente. Se o áudio parar durante uma sessão, os próximos clipes serão salvos sem faixa de áudio; clipes já salvos permanecem intactos.
- **Atalho em uso:** escolha outro em Configurações e clique em Aplicar atalhos.
- **Download do FFmpeg falhou:** baixe o pacote Essentials em [Gyan](https://www.gyan.dev/ffmpeg/builds/), extraia `ffmpeg.exe` e `ffprobe.exe` para a pasta `tools` ao lado de `run.pyw`, e execute Instalar.py novamente. Mantenha os arquivos da mesma distribuição.
- **Erro com texto/HUD:** use uma distribuição FFmpeg com filtro `subtitles` e libass, como Essentials. Uma instalação FFmpeg já existente no PATH precisa oferecer esses recursos.
- **Fechou após um erro:** consulte `instalacao.log` e `inicializacao.log` na pasta extraída. Em Configurações, **Abrir dados e logs** mostra `duckcapture.log` e, quando disponível, `last-encoder.log`.
- **Replay antigo ocupando disco após uma interrupção:** com a captura parada, use **Limpar replay temporário**. Isso preserva os clipes salvos.

Configurações e temporários ficam em `%LOCALAPPDATA%\DuckCapture`. O replay usa segmentos de vídeo comprimido em disco, com retenção limitada ao tempo escolhido e uma pequena margem; o áudio fica em um buffer de memória. A interface reduz a atualização da prévia e só acompanha controles quando o HUD está ativado. As animações do vinil param com a música. Em Configurações, desmarque **Animações suaves, expansão dos ícones e brilho** para reduzir movimento. As miniaturas de vídeo são geradas uma por vez, para arquivos visíveis na galeria; novas tarefas de miniatura aguardam enquanto a captura está ativa.

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

O conceito em escrita normal está em [CONCEITO.md](CONCEITO.md). A arte da turma está em `duckcapture/assets/mascots.png` , a nova grade de personagens em `duckcapture/assets/mascots-grid.png` e o Duck individual em `duckcapture/assets/duck.png`. Os arquivos originais de arte estão incluídos no pacote.
