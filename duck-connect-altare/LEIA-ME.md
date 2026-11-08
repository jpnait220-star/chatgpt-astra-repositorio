# Duck Connect + Community — Altare

API compatível com cosméticos, presença, chat e anúncios do DuckClient. Não está publicada na sua conta ainda. O modo dedicado deste pacote não depende de Vercel, Upstash ou Supabase.

A Altare confirma Node.js e endereço HTTPS de app, sem pausa por inatividade: https://altare.gg/en/products/app-hosting . Disponibilidade, recursos e regras precisam ser conferidos na sua conta.

## Instalar

1. Crie um **app Node.js separado** na Altare. Não reinstale/substitua o servidor Minecraft.
2. Use Node.js 22 ou 24. Envie o conteúdo deste ZIP para a raiz do app.
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
