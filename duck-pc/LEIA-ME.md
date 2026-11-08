# DuckPC 1.0.1 — Windows 11 e Downloads

Utilitário portátil para seu Ryzen 7 1700, Radeon RX 580, 32 GB de RAM e SSD. O objetivo é reduzir sugestões/apps dispensáveis e organizar seus arquivos. Não promete ganho de FPS nem conserta defeito físico no SSD.

## Abrir

1. Baixe e **extraia o ZIP inteiro** para uma pasta, por exemplo `Downloads\DuckPC`.
2. Abra **Abrir-DuckPC.cmd** com dois cliques. Use sua conta normal, sem executar como outro administrador.
3. Comece pela aba **Meu PC → Analisar meu PC**. Depois revise as outras abas.

Usa o Windows PowerShell 5.1 que já vem no Windows 11; não precisa de Python, Java, instalador ou serviço. A janela pode abrir um console junto. O lançador usa `ExecutionPolicy Bypass` somente nesse processo; não altera a política global. Restrições de uma organização continuam podendo bloquear a execução. Não desative antivírus/proteção para executar.

## Downloads e ícones

**Nada é movido ao abrir o programa.** Em **Downloads com ícones**:

1. Confira a pasta detectada ou clique em **Escolher pasta**. Suporta Downloads redirecionado pelo Windows.
2. Clique em **Gerar prévia** e confira arquivos e destinos.
3. Clique em **Organizar arquivos** para mover os arquivos revisados.

Destino: uma pasta `_DuckOrganizado` dentro da pasta escolhida. Dentro dela:

- **Minecraft e Mods:** `.jar`, modpacks e arquivos Minecraft. Subpastas por versão identificada no nome (`1.20.1`, `1.21.4` etc.). JAR sem versão identificável vai para `Sem versao no nome`.
- **Instaladores:** `.exe`, `.msi`, `.msix` etc. Todas as versões são mantidas.
- **Compactados:** ZIP/RAR/7Z genéricos.
- **Imagens e Skins**, **Videos**, **Audios**, **Documentos e Logs**, **Codigo e Configs**, **Outros**.

Cada categoria recebe seu próprio ícone. Os ícones são copiados para `%LOCALAPPDATA%\DuckPC\icons`, para continuarem funcionando mesmo que o programa saia de Downloads. Use F5 no Explorador; o cache de ícones pode demorar a atualizar. A personalização usa `desktop.ini` e o atributo de pasta necessário ao Explorador, somente nas pastas criadas pelo DuckPC.

Só arquivos soltos são organizados. **Não percorre nem move pastas/projetos existentes.** Ignora downloads parciais, itens ocultos/do sistema/links e arquivos alterados há menos de dois minutos. Se o arquivo mudar depois da prévia, ele fica na origem. Alguns downloads não usam extensão parcial: aguarde terminarem e gere outra prévia.

Não apaga, deduplica, abre ou executa JARs/instaladores. Não sobrescreve nomes repetidos: adiciona `(2)`, `(3)` etc. Não identifica versões pelo conteúdo do mod; usa somente o nome. Nomes/caminhos muito longos ou arquivos bloqueados podem ser ignorados e registrados no histórico.

### Desfazer organização

**Desfazer última organização** devolve os arquivos ao local original. Se já existir outro arquivo com o mesmo nome, ou se tamanho/data de modificação do arquivo organizado mudaram, preserva ambos e registra o motivo. As pastas vazias e os ícones permanecem, sem excluir nada.

A verificação de alterações usa tamanho e data, não lê todos os arquivos grandes para gerar hash; isso reduz o trabalho do SSD. Ela não detecta uma edição que preserve intencionalmente o mesmo tamanho e a mesma data. Evite renomear/editar manualmente os arquivos antes de desfazer.

O histórico é gravado antes de mover, com atualizações em lotes. Se o aplicativo for interrompido, a opção de desfazer também considera movimentos pendentes. Guarde `%LOCALAPPDATA%\DuckPC\Historico`; sem ele, o aplicativo não conhece os locais anteriores. O histórico contém caminhos locais, e não é enviado para fora do PC.

## Ajustes reversíveis

Revisão e aplicação são separadas. A seleção padrão contém:

- Reduzir dicas, anúncios e sugestões para o usuário atual.
- Política/ícone do Copilot **clássico**. A disponibilidade varia por build/edição do Windows; não remove o app Copilot novo.
- Ativar Modo de Jogo.

Desligar a captura Xbox/Game Bar, reduzir animações/transparência e desativar aceleração do mouse são opções **desmarcadas**, porque você pode usar clipes e preferir o visual normal.

Antes de alterar o registro, o DuckPC salva os valores anteriores e seus tipos. **Restaurar último ajuste** os recupera; valores modificados por outro programa depois do DuckPC são preservados. Algumas alterações só aparecem depois de sair e entrar novamente no Windows. Ele não reinicia a máquina nem o Explorador sozinho.

Não muda Defender, Firewall, Windows Update, serviços essenciais, paginação, configuração de BIOS, drivers AMD ou overclock. Não instala programas de limpeza e não fica em segundo plano.

## Mouse e monitor de 75 Hz

A aba **Mouse e monitor** lê a frequência atual por monitor e enumera os modos anunciados pelo driver na resolução atual. **Configurar 75 Hz no Windows** abre as opções avançadas de exibição do próprio Windows. Selecione seu monitor e 75 Hz se estiver disponível; a confirmação e a reversão ficam a cargo do Windows. O aplicativo **não força frequência não suportada**, não cria resolução personalizada e não faz overclock de monitor ou USB.

O botão **Abrir AMD Software** abre o programa da AMD já instalado no caminho oficial. Confira FreeSync e Radeon Anti-Lag se estiverem disponíveis para seu monitor/cabo/driver/jogo. Não instala driver nem altera configurações proprietárias da AMD em silêncio. RX 580 não é motivo para instalar Anti-Lag 2 ou pacotes genéricos de “input zero”.

**Mouse sem aceleração**, na aba de ajustes, desliga a aceleração do ponteiro para tornar o movimento mais consistente. A preferência vem desmarcada e tem backup; ela não aumenta CPS, não reduz o debounce do botão, não muda polling rate, não altera o controle de velocidade do ponteiro e não garante reduzir a latência do clique. Jogos que usam entrada bruta podem ignorar a aceleração do Windows. O aplicativo notifica o Windows ao aplicar/restaurar; se o driver não atualizar na hora, saia e entre novamente na conta.

75 Hz é a taxa de atualização do monitor; não é um limite automático nem uma garantia de 75 FPS. Para limitar FPS, configure o próprio jogo. Com FreeSync ativo, um limite um pouco abaixo do teto do monitor pode evitar sair da faixa variável. Sem FreeSync, VSync/limites devem ser avaliados conforme a preferência por fluidez, tearing e resposta. Não existe ajuste universal de clique sem atraso.

## Apps opcionais e IA

A aba **Apps opcionais** lista apenas pacotes conhecidos instalados para seu usuário: Copilot, Clipchamp, Notícias, Clima, Ajuda, Dicas, Solitaire e Vincular ao Celular. **Nenhum vem marcado para remoção.** Revise e marque só o que não usa.

A remoção usa a API normal do Windows para seu usuário. Não remove arquivos manualmente nem provisionamento de outras contas. Apps podem ser reinstalados pela Microsoft Store, mas não há botão de desfazer a desinstalação pelo registro. Não remove Office, Xbox, Store, drivers, bibliotecas de outros programas ou todos os pacotes por curinga.

O Ryzen 7 1700 não é hardware Copilot+ com NPU. A disponibilidade de Recall depende do Windows/hardware; o DuckPC não força a remoção de componentes de sistema de IA que talvez nem estejam presentes. Remover um app que já não roda não garante melhorar FPS.

## SSD lento

A análise mostra espaço livre, memória disponível, GPU/driver, estado reportado pelo Windows e apps na inicialização. Não executa benchmark de escrita. Um estado “Healthy” não é teste completo de saúde; alguns controladores não expõem todos os dados.

Pouco espaço livre pode piorar o SSD; tente manter margem, por exemplo 15–20%, e faça backup dos projetos. **Armazenamento / limpeza** abre as opções oficiais do Windows para você escolher o que limpar. O DuckPC não apaga temporários, caches, lixeira, saves, mods ou Downloads automaticamente.

**Otimizar unidades** abre o aplicativo oficial do Windows, que escolhe a manutenção apropriada a cada unidade, como ReTrim para SSD. Não executa uma desfragmentação forçada por script. Se o disco continuar lento, confira saúde/temperatura/cabos/controlador e uso de disco durante a travada.

## Dados e validação

Tudo fica local. Não há telemetria, conexão de rede durante o uso, tarefa agendada, inicialização automática ou alteração silenciosa.

O organizador foi testado com arquivos temporários reais, conflitos, desfazer, downloads recentes/parciais, alterações após prévia, caminhos externos e recuperação de interrupção. Foram concluídas **36 verificações**, incluindo compilação do componente nativo e tamanho da estrutura de leitura de monitor. Os scripts passaram pela análise sintática do PowerShell 7.4.6; o código usa sintaxe compatível com 5.1. **A interface WinForms, registro, Appx, leitura real dos modos de monitor, atualização do mouse, saúde do SSD e ícones do Explorador precisam ser validados no seu Windows 11**; o ambiente de desenvolvimento é Linux. Não foi aplicado nenhum ajuste ao seu computador durante a criação.

Código-fonte: `DuckPC.ps1`, `DuckPC.Core.psm1` e `MonitorInfo.cs`. Testes: `tests\Test-Core.ps1`.

## Correção 1.0.1

Corrigido o erro de inicialização “Não é possível substituir a variável HOME”. A variável da página foi renomeada; o problema não era a extração do ZIP. A validação agora procura atribuições e parâmetros que usem variáveis reservadas do PowerShell.

Extraia esta versão em uma pasta nova e abra `Abrir-DuckPC.cmd`. Histórico, backups e ícones continuam em `%LOCALAPPDATA%\DuckPC`; não é preciso apagar esses dados.
