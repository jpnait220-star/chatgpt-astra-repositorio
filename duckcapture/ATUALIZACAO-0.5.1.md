# DuckCapture 0.5.1

- F11 após salvar clipe: reconexão acompanha a nova janela do jogo, reinicializa o relógio dos quadros e não espera indefinidamente a liberação da fonte antiga. Quadros atrasados da fonte anterior são descartados.
- Animações em mais botões e seletores, retorno lento ao retirar o mouse e onda de brilho ao clicar.
- Fade entre todas as páginas principais, incluindo Editor e Música.
- Vídeo local como papel de parede em loop, silencioso, com escurecimento regulável. Pausa durante captura, minimização e com animações desativadas.
- Botão Criar link na galeria: envio manual de MP4 ao Catbox, progresso, cancelamento, cópia do link e histórico local. Limite de 200 MB por arquivo.
- Som de confirmação misturado perto do fim dos novos clipes, preservando a duração e o áudio do jogo. Opção e volume em Configurações.

Feche a versão antiga, instale DuckCapture-Setup-0.5.1.exe e abra pelo atalho. Não é necessário instalar Python. Seus clipes e configurações são preservados.

O Catbox é um serviço externo: qualquer pessoa com o link pode assistir ou baixar. Não há exclusão remota pelo aplicativo. O link abre o MP4; a incorporação no Discord depende dos limites e das configurações do Discord. O envio foi testado com servidor local simulando a API, sem publicar clipes pessoais. O acesso direto ao Catbox é bloqueado na rede do ambiente de desenvolvimento, portanto a integração externa precisa ser conferida no PC do usuário.

O ZIP contém o projeto e o gerador do instalador.
