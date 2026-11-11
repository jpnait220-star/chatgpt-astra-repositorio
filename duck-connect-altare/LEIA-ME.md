# Duck Community original + Duck Connect — Altare 1.0.2

Este pacote usa os **13 arquivos originais** enviados em `DuckCommunity-Completo.zip`. HTML, estilos, logos, configuração pública do Supabase e 12 dos 13 arquivos estão idênticos ao ZIP. Em `discord-app.js`, foi acrescentada somente uma verificação de compatibilidade: quando o Discord V3 do próprio HTML já está ativo, a interface antiga não tenta acessar elementos que foram removidos. Isso evita o erro `Cannot set properties of null (setting href)` e permite que a inicialização da conta continue. O visual, os cards, as URLs e o conteúdo do site são preservados. Substitui a página de downloads provisória da versão 1.0.1 pela Community original.

## Os dois sites na mesma aplicação

- `https://duckcommunity.go.altare.global/`: Canto de Duckzin / DuckzinCommunity original, incluindo projetos, cards, imagens, arquivos de download, membros, conta e interfaces de Discord/suporte/administração existentes.
- `https://duckconnect.go.altare.global/`: página do Connect e serviço de cosméticos/presença/chat do mod.
- Uma única instância Node.js, a mesma porta **25668**, comando **`npm start`**. Os dois domínios HTTPS da Altare devem encaminhar para essa aplicação.
- A página inicial é escolhida pelo cabeçalho HTTP `Host`. Os caminhos `/community/` e `/connect/` também abrem os respectivos sites para diagnóstico.

## Atualizar na Altare

1. Pare somente a aplicação web do Connect/Community.
2. Faça uma cópia dos arquivos atuais.
3. Extraia o conteúdo deste ZIP na raiz da aplicação. Substitua `server.mjs`, `package.json`, `LEIA-ME.md` e as pastas `public/`, `lib/` e `test/`. O `server.mjs` deve ficar diretamente na raiz, sem outra pasta envolvendo o pacote.
4. Preserve as configurações e variáveis do painel: `PORT`/`SERVER_PORT` devem usar a porta alocada **25668**. O exemplo `.env.example` não é carregado automaticamente.
5. Inicie com **`npm start`**. Não há dependências npm de execução para instalar. Compatível com Node.js 20.20.2; para novas instalações, prefira Node.js 22 ou 24.
6. Abra ambos os domínios e use Ctrl+F5 para descartar o HTML antigo. Nos dois endereços, `/health` deve retornar HTTP 200 com `status: online`.

Não precisa alterar os JARs por causa desta atualização dos sites. Ela não consegue atualizar a beta 2.40 original, que ainda consulta o domínio pausado da Vercel.

## Dados e funções da Community original

A Community continua usando o **mesmo projeto Supabase** especificado no `config.js` original. Os projetos, versões, imagens, arquivos, usuários e canais não são recriados nem substituídos por um catálogo inventado. As consultas públicas ao banco responderam com 5 projetos, 12 versões e uma comunidade Discord durante a validação.

O `config.js` contém uma chave **publishable**, própria para o navegador, já presente no site original. O pacote não contém chave `service_role`, chave secreta do Supabase, token Discord ou chave privada de atualização.

- Downloads e imagens dos projetos continuam vindo do Storage do Supabase. Fontes e bibliotecas do site também usam os serviços externos originais.
- O bot que sincroniza Discord e atende a fila de suporte continua sendo um processo separado já existente. Este ZIP não contém nem instala esse bot. Seu funcionamento depende dele estar online e do esquema/permissões do Supabase existentes.
- Contas continuam no mesmo banco. Como o domínio mudou, usuários precisarão entrar novamente no site; o login salvo no navegador para o endereço antigo não acompanha o domínio novo.
- Caso a confirmação de e-mail volte ao endereço antigo, no painel **Supabase → Authentication → URL Configuration**, configure o Site URL para `https://duckcommunity.go.altare.global` e autorize esse endereço nos Redirect URLs. Essa configuração da conta não está incluída no ZIP.

Nenhum projeto, arquivo ou registro foi publicado, apagado ou editado no banco durante os testes. Não foram enviados chat/mensagens, abertos tickets ou criadas contas de teste.

## Estado do Connect

O Connect mantém o modo dedicado anterior, com uma única instância e estado temporário em RAM. Equipamentos, presença, sessões e chat recente expiram; o chat é limitado a 40 mensagens. Reiniciar limpa esse estado e os clients republicam os equipamentos/presença. Isso não apaga os projetos, arquivos ou usuários da Community no Supabase.

São mantidos os limites e verificações anteriores da API: corpo de até 16 KiB, limites por conexão/IP, até 10 mil perfis temporários e validação de sessão/Mojang para anúncios. O IP vem da conexão TCP; não são aceitos cabeçalhos Vercel inventados pelo cliente. O proxy da Altare pode agrupar jogadores em um mesmo IP. Não execute réplicas sem armazenamento compartilhado para o Connect.

## Validação

- `npm test`: 16 testes Node, incluindo API anterior, seleção por domínio, tipos MIME, proteção contra caminhos arbitrários, políticas do navegador e hashes dos arquivos originais e a única adaptação de compatibilidade em `discord-app.js`.
- O manifesto `test/community-original-sha256.json` registra os hashes dos arquivos do ZIP recebido.
- Consultas públicas ao Supabase verificam a disponibilidade dos registros sem alterar dados.
- Login com senha, publicação administrativa, upload, envio de Discord e tickets exigem as contas e serviços reais; essas ações não foram realizadas durante a migração.

Este pacote precisa ser enviado para sua conta Altare. Publicar o ZIP no GitHub não atualiza os arquivos da host automaticamente.
