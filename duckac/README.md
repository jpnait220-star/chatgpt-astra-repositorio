# DuckAC V9.2

Autoclique para Windows 10/11, com interface escura, detalhes dourados e indicação visual do botão selecionado.

## Abrir

Baixe **DuckAC-V9.2-Windows.zip**, extraia e abra **DuckAC_V9_2.exe**. Não precisa instalar Python.
Se a versão V8 ficou oculta, encerre **DuckAC_V8.exe** no Gerenciador de Tarefas antes de abrir a nova. As versões compartilham a proteção contra instâncias duplicadas.

## Usar

- Escolha a frequência de 1 a 25 CPS e o botão **Esq.**, **Meio** ou **Dir.**.
- Use **Shift + R** para ativar/desativar ou grave outro atalho no painel.
- **F12 sempre para o autoclique**; essa tecla fica reservada.
- O botão **Parar** desativa sem fechar. **X / Alt+F4** encerra o motor e a janela; minimizar mantém o aplicativo aberto.
- Se a interface deixar de responder por mais de 1,5 segundo, o motor desativa e exige nova ativação.
- O teste de CPS conta eventos recebidos na área de teste, incluindo o botão do meio.
- A pausa de inventário usa E/Esc e contexto da janela. Pode ser desligada pelo painel.

Configurações ficam em `%APPDATA%\DuckAC\settings.json`. A interface principal não recebe cliques automáticos.

## Ajustes da V9.2

A janela principal agora usa a moldura nativa do Windows, mantendo sua entrada normal na barra de tarefas ao minimizar. Foi removida a alternância de janela sem bordas que podia recriar o identificador da janela. Se a janela for ocultada pelo aplicativo (estado withdrawn), a verificação da interface encerra o motor e a janela. Fechar encerra; minimizar mantém o aplicativo acessível pela barra de tarefas. Não há ícone na área de notificação ao lado do relógio.

## Ajustes anteriores

- Verificação da janela sob o ponteiro antes de cada clique: o painel fica protegido mesmo com outra janela em foco e após minimizar/restaurar.
- Arrastar a barra de CPS e soltar sobre X ou minimizar não ativa esses botões. Os botões exigem pressionar e soltar no mesmo controle.
- Movimentos dentro do mesmo valor de CPS não redesenham nem salvam a configuração novamente.
- Diagnóstico local em `%APPDATA%\DuckAC\duckac.log` e `falha-nativa.log`, para investigar eventual fechamento que não seja reproduzido nos testes.

## Correções de encerramento

O encerramento para o motor antes de salvar ou fechar janelas auxiliares. Falhas na configuração, destruição da janela e saída do loop da interface também executam a limpeza. O envio de cliques respeita o encerramento mesmo quando uma consulta de janela demora; botões pressionados são liberados ao cancelar. Erros de interface desativam o autoclique.

Não há processo de bandeja separado neste projeto. O executável empacotado pode aparecer com dois processos enquanto está aberto (inicializador e aplicativo); ambos devem terminar ao fechar.

## Desenvolvimento

Python 3.10+ com Tkinter. `INICIAR_DuckAC.bat` abre o código-fonte; `CRIAR_EXE.bat` empacota com PyInstaller. Pillow é necessário apenas para regenerar as imagens ou capturar a prévia nos testes.

```
python -m unittest discover -s tests -v
python tests/check_interface.py
python tests/check_shutdown_ui.py
```

Os testes usam entradas simuladas; não enviam cliques ao sistema. O workflow Windows também abre e fecha o EXE e verifica se o processo termina.
