# DuckClientZ beta.2.41 — transição da hospedagem

Base: os quatro JARs beta.2.40 enviados pelo usuário, identificados em `inspection.json`. Minecraft 1.20.1, 1.21.1, 1.21.4 e 1.21.11. Esta atualização prepara a migração de Connect, Community, presença, chat e anúncios sem alterar o conteúdo de renderização/HUDs/cosméticos da base.

## Estado desta entrega

**Os mods estão prontos; o endereço do serviço ainda não está ativado.** O usuário pediu terminar os JARs antes de enviar os novos endereços. A configuração assinada inicial é explicitamente desativada, sem um IP inventado e sem anúncio de que o serviço já está online.

Enquanto o domínio não for configurado, a conexão social/cosméticos online pode mostrar aguardando ou falha de envio/comunidade indisponível. Os cosméticos e recursos locais continuam seguindo suas configurações existentes. Não foi realizado teste gráfico dentro do Minecraft nem medição de FPS.

## Instalar esta transição

1. Feche completamente o Minecraft.
2. Guarde uma cópia do JAR anterior fora da pasta `mods`.
3. Coloque somente o JAR beta.2.41 correspondente à sua versão do Minecraft em `mods`; não deixe duas versões do Duck juntas.
4. Abra normalmente. Configurações e perfil já salvos não são apagados por esta migração.

**A beta.2.40 original não consegue descobrir esta atualização com a Vercel pausada**, pois consulta `duck-connect.vercel.app/updates`. Uma troca manual de transição é necessária, salvo se o endereço antigo voltar a funcionar. Não há bypass da assinatura do atualizador ou do bloqueio da hospedagem.

## Novo atualizador

A beta.2.41 consulta o manifesto assinado no GitHub:

`https://raw.githubusercontent.com/jpnait220-star/chatgpt-astra-repositorio/asasa/downloads/DuckClientZ-update.json`

A chave pública e a validação Ed25519 original foram preservadas. O download continua verificando nome/versão, tamanho, SHA-256 e identidade do JAR. A instalação continua ocorrendo ao fechar o jogo; é necessário reiniciar o Minecraft para carregar a versão nova.

`DuckClientZ-update241-draft.json` é o manifesto **de preparação**, já assinado para os arquivos entregues. Ele não é promovido silenciosamente ao canal automático antes de o serviço HTTPS ser confirmado. Versões futuras poderão usar o canal GitHub mesmo que a hospedagem de cosméticos fique indisponível.

## Configuração do domínio sem recompilar os mods

Todos os caminhos sociais usam uma única base HTTPS. A configuração do serviço é assinada separadamente, em:

`https://raw.githubusercontent.com/jpnait220-star/chatgpt-astra-repositorio/asasa/downloads/DuckClientZ-service.json`

O mod valida a assinatura antes de aceitar o domínio. Somente HTTPS, com hostname público e raiz de serviço; não aceita HTTP aberto, credenciais na URL, query ou fragmento na raiz. A validação normal do certificado TLS não foi desativada.

O endereço é resolvido nos workers de rede já existentes, sem baixar configuração no render thread. O último documento verificado é guardado em `config/duckclientz/shared/service-route.json`. Estado pendente é revisto a cada 60 segundos de atividade de rede; estado ativo a cada 10 minutos. Falhas usam backoff até 15 minutos e preservam o último endereço válido. Uma revisão assinada mais antiga não substitui uma revisão mais nova já carregada.

Depois de publicar um domínio novo válido, clientes já na 2.41 podem recebê-lo sem reinstalação. Isso **não** faz a 2.40 consultar um endereço de atualização que ela ainda não conhece.

## Próxima ação na Altare

Enviar o endereço HTTPS público definitivo do app. Conectar e comunidade podem compartilhar o mesmo app/domínio; IP e porta de Minecraft não comprovam HTTPS. O endereço deverá passar em `/health`, em publicação/consulta de cosméticos e no protocolo de comunidade antes de ativar a configuração pública.

Não publique uma chave privada nem coloque senhas no mod. Os envelopes e a chave pública distribuídos são públicos por projeto; a chave privada permanece fora dos arquivos entregues.

## Verificação técnica

- Integridade ZIP/JAR e metadados em todas as quatro versões.
- Comparação byte a byte: apenas `fabric.mod.json`, `CosmeticSharing.class`, `ClientUpdater229.class` e o texto de serviço em `CosmeticsOnline.class` foram alterados entre as entradas existentes. As classes novas são do resolvedor de serviço.
- 29 verificações de configuração assinada: assinatura inválida, tamanho, URLs impróprias, cache, backoff, estado pendente, troca de endereço e proteção contra rollback em memória.
- Estrutura de bytecode e hook de transporte em cada JAR.
- 7 verificações HTTPS por versão usando o método de transporte extraído do JAR final e servidor TLS local com certificado de teste. Confirma envio, consulta, comunidade, nenhuma chamada ao serviço quando pendente, verificação de hostname e limite de resposta. A CA de teste é usada só pelo JVM de teste, sem alterar o mod nem o sistema.
- Verificação do manifesto assinado com as classes originais de atualização dos quatro JARs: transição .40 -> .41, hash/tamanho/identidade, ausência de loop na .41 e rejeição de arquivo corrompido.

As credenciais e certificados privados de teste, ferramentas de compilação e JARs originais não são incluídos no pacote de fontes.
