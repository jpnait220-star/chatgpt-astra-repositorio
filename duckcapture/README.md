# DuckCapture

Um aplicativo de clipes para Windows, com visual escuro, detalhes amarelos e uma turma de patinhos.

**[Baixar DuckCapture 0.2.0 — ZIP](https://github.com/jpnait220-star/chatgpt-astra-repositorio/raw/refs/heads/asasa/downloads/DuckCapture-0.2.0.zip)**

Instale Python 3.12 de 64 bits, extraia a pasta e abra **Abrir DuckCapture.py**. Ele prepara as dependências na primeira execução. Tudo é gratuito. [Instruções completas](LEIA-ME.md).

**Já instalou?** Feche o aplicativo e copie o conteúdo da nova pasta `DuckCapture` sobre a antiga, substituindo os arquivos do pacote e preservando `.venv`, `tools` e seus clipes. Abra `Abrir DuckCapture.py`.

O ZIP 0.2.0 não inclui os iniciadores `.cmd`. Essa alternativa não garante a aprovação do Controle de Aplicativo Inteligente para outros arquivos ou dependências.

![Tela inicial do aplicativo](docs/inicio.png)

- Replay de uma janela: 15, 30, 60, 90 ou 120 segundos; clipe e print com atalhos configuráveis.
- Perfis Econômico, Equilibrado, Alta qualidade e Full; seleção de FPS e codificador.
- Editor com trechos, cortes, divisão, união, velocidade, volume, texto, sticker, filtros, zoom e exportação MP4.
- Editor de HUD com elementos arrastáveis, teclas, mouse, cliques, texto, imagens, música e presets.
- Tocador de músicas locais com vinil animado e aba Spotify com player oficial incorporado. Em contas gratuitas, a reprodução pode se limitar a prévias.
- **Todos os clipes**: galeria sem o antigo limite de 100 arquivos, busca, filtros, miniaturas e reprodução interna.
- Menu com ícones vetoriais, brilho ao mover o mouse, botões magnéticos sutis e transições; efeitos podem ser desativados.
- Captura com etapas de preparação, erro persistente e botão para copiar o diagnóstico. Falha de áudio mantém o vídeo com aviso explícito.
- Arquivos locais e dicas opcionais de nove mascotes.

**Versão alpha:** interface e processamento de vídeos testados no Linux; captura real, áudio do Windows, atalhos globais e desempenho de GPU ainda precisam de validação no Windows. Não é um instalador independente: utiliza Python e FFmpeg. [Resultados e limites](VALIDACAO.md).

![Editor de HUD](docs/hud.png)

[Conceito organizado](CONCEITO.md) · [Componentes utilizados](THIRD-PARTY.md)
