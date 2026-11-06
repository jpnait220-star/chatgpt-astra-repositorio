# Duck Box Trainer0.3.30-alpha / Fabric 1.21.11

Instale Java21, Fabric Loader0.17.3+ e Fabric API0.141.3+1.21.11.
Coloque somente DuckBoxTrainer-1.21.11-0.3.30-alpha.jar em mods.
Substitua o JAR anterior e reinicie o Minecraft.

Em Criar Mundo, escolha Mundo de Duckzin. O mod copia o mapa pronto para uma
pasta nova, sem sobrescrever mundos existentes. Tambem pode copiar a pasta
saves/DuckBoxTreino do pacote completo para .minecraft/saves.
Use o mapa incluido nesta versao: os itens e dados foram adaptados para1.21.11.

Inclui o mundo novo Mundo de Duckzin (3).zip enviado pelo autor: arena pronta,
giro BAIXO como padrao, perfil1 com os itens salvos e perfis2-4vazios.
O icone do mod e do mundo usa o avatar original de robo/pato fornecido.

O critico do bot reconhece a descida real de elytra mesmo quando o voo zera
a distancia acumulada de queda. Sprint pode continuar ligado. Subir/estar
no chao nao concede criticos. As outras condicoes nativas continuam valendo.

Comandos principais (Tab mostra os argumentos/controles disponiveis):
- /box iniciar, /box parar, /box configurar
- /box modo, /box profile 1 (ate4), /box chest profile 1 (ate4)
- /box setspawn, /spawn, /box spawnbot
- /box skull jogador, /box blocos, /box bloco nome
- /box holo texto, /box moveholo, /box holotamanho escala
- /box golpes
Os comandos de configuracao tambem funcionam em command blocks, usando o
jogador real mais proximo. O mundo vem em Adventure; durante o treino o
jogador pode colocar apenas la e teia. Para editar a construcao use Creative.

Ha um jogador contra um bot por mundo. O bot usa inventario real, potes,
totens vanilla e fisica nativa. Cosmeticos sao exclusivos do bot. Nao requer
DuckClientZ nem MouseTweaks; nao instale um MouseTweaks de outra versao.
Em servidor privado, instale o mod e Fabric API tambem no cliente.

Fontes: Python3.10+ e JDK21 para compilar (o alvo do JAR e Java21).
python build.py
python test_mixins.py
python test_combat.py
python test_meshes.py

Testes usam bibliotecas Minecraft reais: carregamento do mapa convertido,
kits, atributos, totem vanilla, dano do critico com PlayerEntity transformado,
comandos, Mixins e meshes dos cosmeticos/baus. Nao houve teste grafico no
Minecraft nem garantia de FPS/naturalidade em todas as dificuldades.
Licenca do codigo: MIT. Direitos/creditos dos assets em CREDITOS-COSMETICOS.txt.
