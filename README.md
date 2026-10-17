# DuckCleans

Extensão para Opera com o painel **DuckCleans GUI**, visual preto com detalhes brancos e interface em português. Apenas os nomes DuckCleans e DuckCleans GUI permanecem em inglês.

Fecha automaticamente abas inativas após um tempo configurável de **15 minutos a 24 horas**. Funciona localmente, sem contas, chaves de API ou serviços externos.

## Instalar no Opera

1. Baixe o arquivo ZIP e **extraia todo o conteúdo** para uma pasta permanente no seu computador.
2. Abra `opera://extensions` na barra de endereços do Opera.
3. Ative **Modo do desenvolvedor**.
4. Clique em **Carregar sem compactação** e selecione a pasta extraída que contém `manifest.json`.
5. Fixe a DuckCleans no menu de extensões. Clique no ícone do patinho para abrir o painel **DuckCleans GUI**.

Não abra apenas o arquivo `dashboard.html`: o gerenciamento de abas exige que a extensão seja instalada. O mesmo pacote é compatível com navegadores Chromium que ofereçam Manifest V3 e `chrome.storage.session`.

## Como usar

- **Visão geral:** veja as abas de todas as janelas, busque pelo título ou site, abra uma aba, favorite e pause ou retome a limpeza.
- **Favoritos:** uma aba com estrela nunca é fechada automaticamente. A proteção acompanha a aba ao navegar para outros sites e dura até fechar a aba, encerrar a sessão do navegador ou recarregar a extensão. As configurações e o histórico ficam salvos.
- **Configurações:** escolha um tempo predefinido, use o controle de 15 a 240 minutos ou digite até 1.440 minutos. O mínimo de 15 minutos é aplicado também na lógica de limpeza.
- **Histórico:** consulte os títulos e horários das últimas 30 abas fechadas automaticamente. Limpar o histórico não zera o contador total de abas fechadas.

## Regras de proteção e tempo

A aba selecionada de cada janela, abas fixadas, abas reproduzindo áudio, páginas de extensões e páginas que não usam HTTP(S) ficam protegidas.

A contagem começa quando uma aba deixa de estar selecionada. Abas abertas em segundo plano recebem o tempo completo a partir da criação ou da primeira observação. Ao instalar a extensão ou começar uma nova sessão do navegador, as abas existentes recebem uma nova contagem.

Desafixar uma aba, encerrar o áudio, remover a estrela, mudar o tempo ou retomar a limpeza dá à aba uma nova contagem completa. A verificação acontece aproximadamente a cada minuto enquanto o navegador está aberto. Se o computador suspender, a verificação pode atrasar; o tempo transcorrido conta quando o navegador voltar.

**Favorite abas com formulários ou trabalho não salvo.** A extensão não identifica alterações não salvas. Reabrir uma aba pelo atalho do Opera pode restaurar a página, mas não garante recuperar o que foi digitado.

## Privacidade e permissões

- `tabs`: lê títulos, endereços e estado das abas; permite ativar e fechar abas.
- `storage`: armazena configurações, contagens e favoritos da sessão e o histórico local.
- `alarms`: agenda as verificações.

Não há rastreamento, fontes externas, solicitações de ícones a sites, scripts injetados em páginas ou servidores externos. Títulos e endereços são exibidos como texto, nunca como HTML.

## Desenvolvimento e testes

Use esta pasta de trabalho existente. Não é necessário criar outro Git worktree. Não há etapa de compilação nem dependências de produção para instalar. Depois de editar os arquivos, clique em **Recarregar** na extensão em `opera://extensions` e recarregue o painel.

Testes da lógica e do processo de segundo plano com APIs do navegador simuladas:

```sh
npm test
```

Teste da interface no Chromium, com mensagens da extensão e dados de exemplo simulados (requer Python, Playwright e Chromium):

```sh
python tests/ui_smoke.py
```

As capturas produzidas por esse teste usam dados demonstrativos. Elas não comprovam acesso real às abas por uma extensão instalada.

O teste completo `python tests/browser_smoke.py` usa um perfil descartável e páginas locais. É possível escolher o executável com `DUCKCLEANS_BROWSER`. **Esse teste está bloqueado nesta máquina por uma política administrativa que impede carregar extensões locais.** A instalação real precisa ser testada no Opera antes de depender da limpeza automática ou publicar na loja.

## Gerar o ZIP

```sh
python scripts/package.py
```

O arquivo é criado em `artifacts/DuckCleans-1.0.0.zip`. Extraia o ZIP antes de usar **Carregar sem compactação** no Opera.
