# DuckCapture 0.5.2

Clipador para Windows 10/11 de 64 bits. Interface em português, tema escuro, fonte Manrope, detalhes claros e menus arredondados.

## Abrir

O instalador pronto, quando disponível, fica em [Downloads no GitHub](https://github.com/jpnait220-star/chatgpt-astra-repositorio/releases/tag/DuckCapture-v0.5.2). Instale `DuckCapture-Setup-0.5.2.exe` e abra pelo atalho DuckCapture.

Este ZIP contém o projeto e o gerador do instalador. Extraia a pasta inteira. Para gerar o Setup em um Windows com Python 3.12 x64, execute `CRIAR-INSTALADOR.bat`. O resultado fica em `installer_saida/DuckCapture-Setup-0.5.2.exe`. Também é possível executar o projeto com `Abrir DuckCapture.py`; a primeira abertura instala as dependências e o FFmpeg.

## O que mudou

- Barras de rolagem com pontas redondas, seletor de cores próprio, menus e controles arredondados.
- Ícones vetoriais de controle, clipe, print e ações; fonte Manrope incluída no pacote e na exportação de textos/HUD.
- Inclinação em perspectiva conforme o canto sob o mouse, nos cards, clipes e controles de qualidade. Brilho e transições sem animação contínua quando ocioso.
- Editor dividido em prévia, ajustes e sequência. Pontas arrastáveis para cortar, divisão, desfazer, texto, filtros, imagens e exportação MP4.
- Som original de clipe de 1,08 s, mais encorpado e com volume ajustável. Ele confirma o pedido de clipe; a conclusão aparece na biblioteca.
- Correção do índice de monitor usado pelo modo F11; controle de tempo por timestamps nativos e espera precisa no Windows; menos cópias e redimensionamentos por quadro.
- O limite de resolução selecionado é respeitado, inclusive no perfil Full. Perfis econômicos/modo leve podem reduzir a resolução efetiva, indicada ao iniciar.
- Taxa de imagens novas gravadas no topo; o tooltip mostra recebidas, repetições, saída e meta. Um arquivo marcado como 60 FPS pode repetir quadros se a fonte entregar menos imagens.

## Spotify

Com o Spotify instalado no Windows, abra uma música e clique em **Conectar / atualizar** na aba Spotify do DuckCapture. Título, artista, reproduzir/pausar e troca de faixa ficam no DuckCapture; o aplicativo oficial reproduz o áudio. Contas gratuitas seguem os anúncios, limites de pulo e disponibilidade do Spotify. Não é necessário Spotify Premium para essa integração com os controles do Windows.

Você pode colar um link de música, álbum ou playlist e escolher **Abrir esse link no Spotify do PC**. **Abrir prévia** usa o player oficial incorporado; a duração disponível depende do serviço. O site completo deixou de ser usado como player, pois carregar a página não garante suporte à reprodução protegida. Não há carregamento de página sem prazo: a prévia informa falha após 18 segundos.

## Captura e editor

Escolha a janela, configure qualidade/FPS e inicie a captura. F8 salva os últimos segundos; F9 faz um print. Os atalhos podem ser alterados. Em F11, o monitor do jogo é usado somente enquanto o processo selecionado está em primeiro plano. Minimizar mantém o último quadro e o áudio até a janela voltar a fornecer imagens.

Na biblioteca, abra um clipe no editor. A prévia mostra o vídeo original com corte, velocidade e volume; texto, filtro, imagem e zoom são aplicados na exportação. O arquivo original permanece preservado.

## Desenvolvimento

`python -m pip install -r requirements-dev.txt` e `python -m pytest -q`.
O aplicativo usa Python 3.12, PySide6 e FFmpeg. Captura e controle de sessões Spotify dependem do Windows. As verificações e seus limites estão em [VALIDACAO.md](VALIDACAO.md). Licenças: [THIRD-PARTY.md](THIRD-PARTY.md).

## Novidades da versão 0.5.2

- Captura: conversão nativa para YUV420 antes do envio ao FFmpeg, com 62,5% menos bytes por quadro no pipe; retenção segura do buffer nativo sem a cópia integral anterior. Mantém seleção automática de NVIDIA NVENC, Intel QSV, AMD AMF ou CPU.
- Menos concorrência durante a gravação: miniaturas em segundo plano adiadas, prévia suspensa com a janela oculta e FFmpeg de exportação com prioridade menor no Windows. O indicador distingue quadros novos de repetições.
- Criar link: arquivos acima de 200 MB recebem uma cópia comprimida automaticamente antes do envio manual ao Catbox. Não corta o vídeo e preserva o original. A cópia pode perder qualidade/resolução; vídeos extremamente longos ainda podem exigir divisão. Catbox continua com limite de 200 MB por arquivo e o link é público. A incorporação no Discord depende dele.
- HUD redesenhado: mouse com formato curvo e botões ativos, teclado arredondado, cartões de FPS/CPS/tempo e música com disco, faixa, artista e progresso. Selecione um elemento e use Destaque, Texto e Fundo para mudar as cores. A prévia e o vídeo usam a mesma geometria.
- Música no HUD usa a faixa local ou a sessão oficial do Spotify instalado, inclusive fora da aba Música. A animação do disco acompanha o estado de reprodução; o progresso depende dos dados fornecidos pelo Spotify.
- Papel de parede: preparação em segundo plano e cache de vídeos pesados, dimensionamento conforme a tela (até 1440p), sem a redução fixa para 720p. Pausa durante captura/exportação e ao minimizar. Vídeos preparados usam 24 FPS para reduzir o custo de decodificação.
- Mantém fade de navegação, perspectiva nos controles, retorno suave, som de confirmação opcional no final do clipe e recuperação de troca de janela/F11.

As otimizações não garantem uma taxa de FPS em qualquer hardware. Consulte [VALIDACAO.md](VALIDACAO.md) para testes e limites.
