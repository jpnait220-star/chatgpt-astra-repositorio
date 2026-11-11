# Duck Community original — host separada na Altare

Este ZIP é **somente da Community original**, com o HTML, os cards, os scripts, os logos e as configurações do Supabase recebidos em DuckCommunity-Completo.zip. Ele abre a Community em qualquer hostname. Não contém a página ou a API do Connect.

## Instalar na nova host

1. Crie uma aplicação Node.js separada na Altare. Use Node.js 20.20.2 ou superior (22/24 recomendado para novas instalações).
2. Envie e extraia o ZIP na raiz dessa nova aplicação. `server.mjs`, `package.json` e `public/` precisam ficar diretamente na raiz.
3. Configure `PORT` ou `SERVER_PORT` com a **porta alocada para a nova host**. Não reutilize 25668 só porque essa era a porta do Connect; use a porta que aparece no novo painel.
4. Comando de inicialização: **`npm start`**. Não há dependências npm de execução para instalar.
5. Na Altare, mova/aponte o domínio **duckcommunity.go.altare.global** para a nova aplicação e sua porta. Se ele continuar cadastrado na aplicação antiga, remova aquela associação antes de cadastrá-lo na nova.
6. Deixe **duckconnect.go.altare.global** apontado para a aplicação antiga. Não desligue o Connect nem altere o domínio nos mods.
7. Acesse o domínio da Community com Ctrl+F5. `/health` na nova host deve mostrar `service: duck-community`; o log deve dizer `Duck Community original em 0.0.0.0:PORTA`.

O fato de o código não usar o hostname para escolher a página evita depender de como o proxy repassa o cabeçalho Host. Mas o domínio ainda precisa apontar para a aplicação nova no painel: este ZIP não muda DNS nem configura a Altare automaticamente.

## Dados preservados

Continuam sendo usados o mesmo Supabase, os projetos e arquivos originais. Não copie/edite tabelas ou crie um novo banco para esta migração. A chave do config.js é publishable (própria para uso no navegador), não service_role.

O site inclui as interfaces originais de contas, membros, Discord, suporte e administração. O bot Discord existente continua separado e precisa estar online para funções de sincronização/envio/tickets. Este pacote não instala o bot nem muda seus registros.

A única correção de compatibilidade nos arquivos do site é a mesma do pacote integrado 1.0.2: o Discord antigo não tenta acessar elementos removidos quando o Discord V3 já está ativo. O restante dos 13 arquivos foi preservado.

Usuários precisam entrar novamente no domínio novo. Se a confirmação de e-mail levar à Vercel antiga, ajuste em Supabase → Authentication → URL Configuration o Site URL e os Redirect URLs para https://duckcommunity.go.altare.global. Nenhuma senha ou sessão foi migrada para arquivos do servidor.

## Verificação

`npm test` verifica porta/binding, homepages iguais para todos os hostnames, bytes e tipos dos 13 arquivos, requisições HEAD, erros de método e bloqueio de caminhos fora do site.

Os mesmos arquivos da Community foram conferidos em Chromium no pacote integrado 1.0.2: cinco projetos, imagens carregadas, links de versões, busca e formulário de login, sem erros JavaScript. Os 12 downloads cadastrados responderam HTTP 200 em verificações de disponibilidade. Login real, publicação, upload e envio de mensagens/tickets não foram executados.

É necessário enviar este ZIP à nova host para publicar. Não basta baixar o arquivo ou publicar o ZIP no GitHub.
