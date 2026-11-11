# Dois sites na mesma host — versão 1.0.1

- https://duckcommunity.go.altare.global/ → Community com catálogo de 138 JARs publicados, busca e filtro por Minecraft.
- https://duckconnect.go.altare.global/ → Connect com estado da API.
- Ambos continuam apontando para a mesma aplicação/porta 25668. Não crie outro processo ou outra host.
- A seleção usa o cabeçalho Host enviado pelo proxy HTTPS. Os caminhos /community/ e /connect/ também abrem cada página em qualquer domínio para diagnóstico.

## Atualizar a instalação existente

1. Pare o app na Altare.
2. Faça uma cópia dos arquivos atuais. Extraia o conteúdo deste ZIP na raiz, substituindo server.mjs, package.json e as pastas public/, lib/ e test/.
3. Preserve as variáveis/configurações da host, incluindo a porta 25668. Não precisa alterar os domínios.
4. Inicie novamente com `npm start`.
5. Abra os dois domínios e atualize a página com Ctrl+F5. A API /health deve continuar online nos dois.

A Community incluída é uma página nova de downloads; não é uma cópia do site duckzincommunity.vercel.app. A Vercel retorna 402 e não permite recuperar o site antigo. Para preservar o visual e as outras funções antigas, envie o ZIP/código daquele projeto. O catálogo atual é uma lista dos arquivos publicados no GitHub na data deste pacote; novas publicações exigem atualizar public/releases.json. Os JARs são baixados diretamente do GitHub.

O mod não precisa ser reinstalado por causa desta mudança nas páginas. Reiniciar o app limpa o estado temporário em RAM conforme descrito abaixo.

16 testes Node passaram, incluindo seleção por domínio, arquivos estáticos e compatibilidade da API. Busca, filtro, paginação, links e layout móvel também foram verificados em Chromium local. Publicação na sua conta Altare requer enviar este pacote.

---

# Duck Connect + Community — Altare

API compatível com cosméticos, presença, chat e anúncios do DuckClient. A API já foi testada no endereço público da Altare. Este pacote 1.0.1 precisa ser enviado à host para atualizar as páginas. O modo dedicado deste pacote não depende de Vercel, Upstash ou Supabase.

A Altare confirma Node.js e endereço HTTPS de app, sem pausa por inatividade: https://altare.gg/en/products/app-hosting . Disponibilidade, recursos e regras precisam ser conferidos na sua conta.

## Instalar

1. Crie um **app Node.js separado** na Altare. Não reinstale/substitua o servidor Minecraft.
2. Compatível com Node.js 20.20.2 da sua host; para novas instalações, prefira Node.js 22 ou 24. Envie o conteúdo deste ZIP para a raiz do app.
3. Comando `npm start` ou `node server.mjs`. Arquivo de entrada: `server.mjs`. Não há dependências de execução para instalar.
4. Configure `PORT` ou `SERVER_PORT` com a **porta realmente alocada** no painel. O processo escuta em `0.0.0.0`. O arquivo `.env.example` é só uma referência; o app não carrega `.env` sozinho.
5. Use o **endereço HTTPS do App hosting**, não IP:porta de Minecraft nem HTTP sem certificado. O proxy da Altare precisa encaminhar para a porta do processo.
6. Abra `https://SEU-ENDERECO/health`. Precisa retornar HTTP 200 com `status: online`. Teste de fora da rede da hospedagem.
7. Informe o endereço HTTPS público para atualizar o client e testar as quatro versões. Este ZIP sozinho não altera os JARs dos jogadores.

O domínio `duck-connect.vercel.app` está bloqueado antes de executar código. Mudar somente a hospedagem não consegue fazer esse domínio antigo redirecionar. O client precisa usar o endereço novo. Este pacote não contém credenciais nem chave privada de atualização.

## Estado temporário

Execute **uma única instância/processo Node.js** sempre ativo. Equipamentos, presença, sessões e chat recente ficam em RAM com expiração; o chat é limitado a 40 mensagens. Depois de reiniciar o serviço, os clients republicam seus equipamentos/presença e o chat recente é perdido. As escolhas de cosméticos salvas no mod não são apagadas.

Não é banco permanente de compras, senhas ou inventários. Não execute várias réplicas neste modo: cada uma teria estado diferente. Para escalar entre processos ou manter histórico permanente, é necessário armazenamento compartilhado persistente.

Limites e validação preservados: até 10 mil perfis temporários, 32 IDs por consulta/equipamento, corpo de até 16 KiB e limite por conexão/IP. UUID/nick autodeclarado não comprova a identidade da conta e não pode autorizar compras/permissões. Anúncios privilegiados continuam exigindo comprovação pelo serviço de sessão Mojang.

O IP usa a conexão TCP, sem confiar em um cabeçalho Vercel inventado pelo cliente. Se o proxy da Altare agrupar todos os jogadores em um IP local, o limite pode ficar compartilhado (600 por minuto). Confira o proxy real antes de confiar em cabeçalhos de origem ou ajustar limites. Não desligue limites indiscriminadamente.

A hospedagem também tem limites de recursos e termos. Ainda será necessário reduzir consultas redundantes do client, adicionar cache/backoff e medir tráfego. O serviço é compatível com o protocolo atual; não inclui uma atualização assinada dos mods.

## Validar

`npm test` usa dados fictícios e HTTP local. Testa protocolo, expiração, limites, sessões/chat e anúncios. HTTPS, proxy da Altare, disponibilidade pública e visualização dentro do Minecraft só podem ser validados depois de publicar no seu app.
