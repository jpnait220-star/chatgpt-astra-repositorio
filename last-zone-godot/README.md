# Last Zone — Godot 0.1

Primeira versão jogável da migração para **Godot 4.6.3**. É um projeto nativo em GDScript, separado da versão HTML/Three.js.

## Abrir e editar

1. Extraia `LastZone-Godot-Projeto.zip`.
2. Instale o editor **Godot 4.6.3 Standard** pelo site oficial https://godotengine.org/download/ (não precisa da edição .NET).
3. No gerenciador do Godot, escolha **Importar** e selecione `last-zone-godot/project.godot`.
4. Espere a importação dos recursos terminar e pressione **F6/F5** para iniciar a cena/projeto.

O projeto usa o renderizador Compatibility/OpenGL. Não precisa de Node.js, npm ou navegador para rodar no editor. Os recursos de áudio estão incluídos e seus créditos estão em `AUDIO-CREDITS.txt`.

## Controles iniciais

WASD move, Shift corre, Espaço pula, Ctrl alterna agachar e C agacha enquanto pressionado. Mouse mira, botão esquerdo atira e botão direito aproxima a mira. R recarrega, 1/2/3 troca de arma, H usa kit, E coleta, T coloca gelo, V transpõe e F permite olhar livre. Esc abre a pausa. Confira o menu dentro do jogo para opções e teclas disponíveis nesta versão.

## Aplicativo exportado

No Windows, extraia **toda** a pasta `LastZone-Godot-Windows.zip` e abra `LastZone.exe`. No Linux, extraia `LastZone-Godot-Linux.zip`, dê permissão de execução a `LastZone.x86_64` e abra o arquivo.

**O executável Windows deste protótipo não tem assinatura digital.** O Controle Inteligente de Aplicativos/Smart App Control pode bloqueá-lo. Trocar de motor não remove essa exigência do Windows. Não é necessário desligar essa proteção para editar/jogar pelo editor Godot já instalado e autorizado no seu computador. A confiança do executável distribuído exige um processo de assinatura apropriado; certificado autoassinado não estabelece confiança pública.

## Escopo desta primeira migração

Esta versão prepara uma partida **solo com bots** e reconstrói mapa, personagem, física, câmera, tiro e loot no Godot. Inclui 48 participantes, 108 kits, 200 HP, velocidade 14% maior, salto com tolerância, controle no ar, gelo durante o pulo e passos espaciais. Personagens articulados, três armas, colete/capacete, dano de cabeça e safe usam física nativa. O projeto foi criado para continuar evoluindo no editor.

**Multiplayer por internet, protocolo do servidor Node/Altare e paridade completa com o HTML ainda não foram portados.** Não envie este projeto Godot para substituir o servidor Node existente. Os pacotes HTML e servidor da release v6 continuam sendo uma implementação separada.

## Exportar novamente

Instale os **templates oficiais de exportação da mesma versão 4.6.3** no editor. Os presets incluídos geram Windows x64 e Linux x64 com o pacote do jogo embutido:

```sh
godot --headless --path . --editor --import
mkdir -p build/windows build/linux
godot --headless --path . --export-release "Windows Desktop" build/windows/LastZone.exe
godot --headless --path . --export-release "Linux" build/linux/LastZone.x86_64
python3 scripts/package_release.py
```

Saídas em `build/downloads/`, com hashes SHA-256 e ZIP do projeto sem caches. O workflow `Publish Last Zone Godot prototype` baixa binário e templates oficiais do Godot, verifica seus SHA-512, importa o projeto, executa `tests/smoke.gd`, exporta e publica os downloads em uma prerelease própria.

## Prévia real do protótipo

![Cidade em Godot](https://github.com/jpnait220-star/chatgpt-astra-repositorio/releases/download/last-zone-godot-v0.1.0/godot-town.png)

![Personagem](https://github.com/jpnait220-star/chatgpt-astra-repositorio/releases/download/last-zone-godot-v0.1.0/godot-character.png)

## Limites de validação

Teste automatizado headless demonstra lógica e física em Linux; não mede FPS real em GPU de jogador. Uma exportação Windows com estrutura PE válida não equivale a executar o jogo em um PC Windows. A assinatura/reputação do aplicativo e a compatibilidade dos drivers precisam de validação no sistema de destino.

## Créditos do motor

Desenvolvido com Godot Engine 4.6.3, licença MIT. Autores e licenças das bibliotecas do motor: https://github.com/godotengine/godot/blob/4.6.3-stable/COPYRIGHT.txt e https://godotengine.org/license/. Esta licença do motor não concede direitos adicionais sobre o jogo ou seus recursos. As licenças de áudio estão em `AUDIO-CREDITS.txt`.

```text
Copyright (c) 2014-present Godot Engine contributors (see AUTHORS.md).
Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
