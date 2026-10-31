# Conectar o Supabase gratuito

A adaptacao esta implementada e testada em PostgreSQL local (PGlite). Ainda nao
ha projeto Supabase conectado e os cosmeticos/chat de producao continuam
bloqueados pelo limite do Upstash. Esta mudanca nao corrige FPS.

1. Crie um projeto no plano Free: https://supabase.com/dashboard/new
2. Abra SQL Editor nesse projeto e execute [schema.sql](schema.sql).
3. Nas variaveis de ambiente de Production do projeto Duck Connect na Vercel,
   configure `SUPABASE_URL` e `SUPABASE_SECRET_KEY` (ou a chave legada
   `SUPABASE_SERVICE_ROLE_KEY`). Estas chaves ficam somente no servidor;
   nao as coloque no mod, no navegador, no GitHub ou no chat.
4. Faca novo deploy do Duck Connect. Verifique `/health` retornando online e
   teste a troca de cosmeticos entre duas instancias. O endereco dos mods e
   os endpoints permanecem os mesmos; nao precisa atualizar o JAR para migrar.

O suporte ao Supabase tem prioridade quando ambas as variaveis estao presentes.
Para desfazer a selecao, remova as variaveis Supabase e redeploy. Redis so voltara
se a capacidade do Upstash estiver disponivel. Nao ha fallback em memoria em
producao. O plano Free do Supabase tambem tem limites de recursos/banda.

O SQL usa tabelas privadas, RLS e uma funcao de acesso restrita ao service_role.
Mantem TTLs, limite de32 consultas/itens,40 mensagens recentes e rate limiting.
Contador e cosmeticos sao compartilhados entre instancias do servidor.

Validacao: `npm ci && npm test` —13 testes passam. Os testes novos executam o
SQL em PostgreSQL real via PGlite, verificam publicacao/consulta de cosmeticos,
presenca e chat entre instancias, expiracao, limites, anuncios com prova Mojang
simulada, atomicidade e proibicao de acesso pelos papeis anon/authenticated.
Nenhuma mensagem foi publicada no chat real durante os testes.
