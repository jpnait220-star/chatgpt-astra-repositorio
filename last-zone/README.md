# Last Zone v6

Protótipo de battle royale com app Electron Windows, alternativa HTML e servidor Node.js para dois humanos e bots.

## Downloads

Os pacotes são publicados na [release v6](https://github.com/jpnait220-star/chatgpt-astra-repositorio/releases/tag/last-zone-v6.0.0) pelo workflow `Publish Last Zone v6 downloads`.

## Reproduzir os pacotes

Requer Node.js 24, npm e Python 3.12. Na pasta `last-zone`:

```sh
python3 build_release.py
cd desktop-build
npm ci
node build.mjs win32
cd ..
python3 scripts/package_downloads.py
```

Saídas em `release-dist/`. Electron está fixado em 45.3.2 e o empacotador em 20.3.0, com lockfile. O workflow compila a partir desta branch e publica ZIP Windows, ZIP do servidor, HTML, guia e SHA-256. O ZIP Windows não fica no histórico Git.

## Servidor

```sh
node server.mjs
```

Leia `ALTARE-GUIA.txt`; a porta vem de `PORT`, `SERVER_PORT`, `server-config.json` ou 8080. Protocolo 4. O servidor usa apenas módulos nativos do Node.

## Validação e limites

Os testes de navegador requerem Python Playwright e Chromium em `/usr/bin/chromium`. `test_revamp.py` verifica kits, cura real do bot, navegação de porta, movimento, safe e áudio. `test_duo.py` usa dois clientes reais com o servidor local. `test_native_proxy.cjs` verifica a ponte do app. `test_desktop.py` depende de um app Linux gerado com `node build.mjs linux`.

Os testes locais passaram nos cenários descritos em `VALIDACAO-DUO.txt`. A compilação Windows não substitui execução em Windows. Desempenho em GPU física e hospedagem entre redes reais ainda precisam de validação.

Créditos e condições dos samples de áudio estão em `AUDIO-CREDITS.txt`. Bibliotecas e conteúdo do jogo têm suas respectivas licenças; esta publicação não concede direitos adicionais sobre os recursos de terceiros.
