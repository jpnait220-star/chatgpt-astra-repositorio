# Duck Connect — pacote separado para Altare

Somente o site Connect e a API usada pelos mods. Não inclui o site DuckzinCommunity, os cards de projetos ou arquivos/configuração do Supabase da Community.

## Instalar

1. Pare o app do Connect e faça uma cópia dos arquivos atuais.
2. Extraia este ZIP na raiz da aplicação do Connect. Para remover completamente o site antigo, substitua a pasta public/ pela deste pacote (não apenas mescle as pastas).
3. Mantenha o domínio https://duckconnect.go.altare.global nesta aplicação.
4. Preserve PORT/SERVER_PORT com a porta realmente alocada pelo painel (na instalação anterior era 25668).
5. Comando de inicialização: npm start. Compatível com Node.js 20.20.2 ou superior; 22/24 recomendado para novas instalações. Não há dependências npm de execução.
6. Abra /health: deve responder status online e service duck-cosmetics. O console deve mostrar Duck Connect em 0.0.0.0:PORTA.

Não altere os domínios nos JARs. A Community deve permanecer na outra host com seu pacote separado e domínio duckcommunity.go.altare.global.

As rotas /community e /chat são APIs internas de presença/chat do mod, não o site DuckzinCommunity. Elas e as rotas de cosméticos/anúncios são preservadas por compatibilidade. O arquivo interno lib/community.mjs implementa essas APIs; não o apague.

## Estado e limites

Mantenha uma única instância. Equipamentos, presença, sessões e chat recente do Connect continuam temporários em RAM e expiram. Reiniciar limpa esse estado; os clients republicam seus equipamentos/presença. Este serviço não contém o banco dos projetos/usuários da Community e não apaga o Supabase ao reiniciar.

São preservadas as validações, limites e comprovação de identidade para anúncios do pacote anterior. A separação não altera o código dos mods nem o canal de atualização assinado.

npm test cobre o protocolo anterior e confirma que os arquivos da Community não são servidos. A publicação na sua host requer extrair o pacote e reiniciar; baixar o ZIP não atualiza a Altare automaticamente.
