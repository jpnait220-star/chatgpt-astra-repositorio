# Duck Connect

API de cosméticos compatível com DuckClientZ beta.2.17, mais página responsiva
com status real e instruções de conexão. Sem dependências de execução.

## Vercel

1. Importe este repositório na Vercel e escolha **Root Directory: duck-cosmetics**.
   Framework: Other; Node.js22 ou superior. A configuração já está em vercel.json.
2. Em Storage, conecte um banco **Upstash Redis** ao projeto. Configure as variáveis
   UPSTASH_REDIS_REST_URL e UPSTASH_REDIS_REST_TOKEN em Production e Preview.
   Também são aceitos os nomes KV_REST_API_URL e KV_REST_API_TOKEN.
   Mantenha banco e Function próximos geograficamente, pelo timeout de1s do backend
   e1,5s do client. Nunca coloque o token Redis no JAR ou frontend.
3. Publique/republique. Abra /health: precisa retornar200 e status online.
   Sem banco, retorna503; a página não anuncia uma conexão funcional.
4. No mod, ative Cosmeticos Online, configure Servico de cosmeticos com a raiz
   HTTPS (sem /api ou /profile), habilite Mostrar e Compartilhar.
   Todos usam o mesmo serviço. O compartilhamento vem desligado no mod.
5. O domínio usado pelo client precisa aceitar requisições públicas sem login
   Vercel/Deployment Protection. Use o domínio de produção, não uma preview protegida.

**Importante:** esta API mantém compatibilidade com o protocolo atual, que envia
UUID autodeclarado. Não verifica posse de conta Minecraft; não use este protocolo
para conceder compras, permissões ou acesso. Autenticação de conta exige atualização
também do mod. Ela serve para sincronizar IDs de cosméticos, não arquivos ou modelos.

## Desenvolvimento

```sh
npm test
npm run dev
```

Acesse http://localhost:3000. Somente no desenvolvimento, um armazenamento em memória
permite testar dois clientes. Ele expira registros em120s e não persiste reinícios.
Na Vercel, memória local e disco não são usados como substitutos para Redis.
Em hospedagem Node própria, configure Redis e NODE_ENV=production; o servidor
escuta127.0.0.1, para uso atrás de proxy HTTPS.

## Protocolo

- GET /health → status e protocolo. Sem contagem/lista pública de jogadores.
- POST /profile → {"uuid":"...","cosmetics":["duckMask"]} → {"ok":true}.
- GET /profiles?ids=uuid1,uuid2 → objeto UUID:lista de IDs.
- Limites:32 UUIDs por consulta,32 cosméticos por publicação,16KiB por corpo,
 600requisições por IP/minuto; rate keys têm expiração e usam hash do IP.
- Expiração Redis120s; envio vazio limpa o visual anterior. Cache HTTP desativado.
- Nenhuma senha, token Minecraft, chat ou endereço de servidor é solicitado.
- Credenciais Redis ficam exclusivamente nas variáveis privadas do servidor.

A frequência da consulta/renderização continua sendo controlada pelo client;
esta API não acrescenta trabalho por frame. A latência pública e o comportamento
visual no Minecraft ainda precisam de teste depois da implantação.
