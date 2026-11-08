#requires -Version 5.1
$ErrorActionPreference='Stop'
if ($env:OS -ne 'Windows_NT') { throw 'DuckPC foi feito para Windows 11.' }
Import-Module (Join-Path $PSScriptRoot 'DuckPC.Core.psm1') -Force -DisableNameChecking
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -Path (Join-Path $PSScriptRoot 'MonitorInfo.cs')
[Windows.Forms.Application]::EnableVisualStyles()
$script:DataRoot=Join-Path $env:LOCALAPPDATA 'DuckPC'
$script:History=Join-Path $script:DataRoot 'Historico'
$script:Icons=Join-Path $script:DataRoot 'icons'
[IO.Directory]::CreateDirectory($script:History) | Out-Null
[IO.Directory]::CreateDirectory($script:Icons) | Out-Null
Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'icons') -Filter '*.ico' | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $script:Icons -Force }
$script:Plan=@();$script:PlannedRoot='';$script:Busy=$false
$script:Candidates=@('Microsoft.Copilot','Clipchamp.Clipchamp','Microsoft.BingNews','Microsoft.BingWeather','Microsoft.GetHelp','Microsoft.Getstarted','Microsoft.MicrosoftSolitaireCollection','Microsoft.YourPhone')
$form=New-Object Windows.Forms.Form
$form.Text='DuckPC 1.0.1 - Windows e Downloads';$form.Size=New-Object Drawing.Size(1080,780);$form.MinimumSize=New-Object Drawing.Size(940,680);$form.StartPosition='CenterScreen'
$form.Font=New-Object Drawing.Font('Segoe UI',10)
$form.BackColor=[Drawing.Color]::FromArgb(25,27,35);$form.ForeColor=[Drawing.Color]::WhiteSmoke
$tabs=New-Object Windows.Forms.TabControl;$tabs.Dock='Fill';$form.Controls.Add($tabs)
function New-Page($Title) {
    $p=New-Object Windows.Forms.TabPage;$p.Text=$Title;$p.BackColor=[Drawing.Color]::FromArgb(31,34,44);$p.ForeColor=[Drawing.Color]::WhiteSmoke;$p.AutoScroll=$true;[void]$tabs.TabPages.Add($p);return $p
}
function Label($Parent,$Text,$X,$Y,$Width=900,$Height=35) {
    $c=New-Object Windows.Forms.Label;$c.Text=$Text;$c.Location=New-Object Drawing.Point($X,$Y);$c.Size=New-Object Drawing.Size($Width,$Height);$Parent.Controls.Add($c);return $c
}
function Button($Parent,$Text,$X,$Y,$Width=240) {
    $c=New-Object Windows.Forms.Button;$c.Text=$Text;$c.Location=New-Object Drawing.Point($X,$Y);$c.Size=New-Object Drawing.Size($Width,40);$c.FlatStyle='Flat';$c.BackColor=[Drawing.Color]::FromArgb(61,52,100);$c.ForeColor=[Drawing.Color]::White;$Parent.Controls.Add($c);return $c
}
function Check($Parent,$Text,$X,$Y,$Checked=$false) {
    $c=New-Object Windows.Forms.CheckBox;$c.Text=$Text;$c.Location=New-Object Drawing.Point($X,$Y);$c.Size=New-Object Drawing.Size(960,38);$c.Checked=$Checked;$Parent.Controls.Add($c);return $c
}
function TextBox($Parent,$X,$Y,$Width,$Height,$Multi=$false) {
    $c=New-Object Windows.Forms.TextBox;$c.Location=New-Object Drawing.Point($X,$Y);$c.Size=New-Object Drawing.Size($Width,$Height);$c.Multiline=$Multi
    if ($Multi) { $c.ScrollBars='Both';$c.ReadOnly=$true;$c.WordWrap=$false }
    $c.BackColor=[Drawing.Color]::FromArgb(19,21,28);$c.ForeColor=[Drawing.Color]::WhiteSmoke;$Parent.Controls.Add($c);return $c
}
function Confirm($Text) { return [Windows.Forms.MessageBox]::Show($form,$Text,'DuckPC - revisar','YesNo','Question') -eq 'Yes' }
function Inform($Text) { [void][Windows.Forms.MessageBox]::Show($form,$Text,'DuckPC','OK','Information') }
function Run-Action([scriptblock]$Body) {
    if ($script:Busy) { return };$script:Busy=$true;$form.UseWaitCursor=$true
    try { & $Body } catch { [void][Windows.Forms.MessageBox]::Show($form,$_.Exception.Message,'DuckPC - operacao nao concluida','OK','Warning') }
    finally { $form.UseWaitCursor=$false;$script:Busy=$false }
}
function Latest-History($Prefix) {
    $items=@(Get-ChildItem -LiteralPath $script:History -Filter "$Prefix-*.json" | Sort-Object LastWriteTimeUtc -Descending)
    foreach ($item in $items) {
        $data=Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($Prefix -eq 'downloads') { $entries=@($data.Entries) } else { $entries=@($data) }
        if (@($entries | Where-Object { $_.Status -in @('Pending','Moved','Applied','UndoSkipped') }).Count -gt 0) { return $item.FullName }
    }
    return $null
}
$homePage=New-Page 'Meu PC'
[void](Label $homePage 'Diagnostico local - Ryzen 7 1700 / RX 580 / 32 GB / SSD' 22 18)
[void](Label $homePage 'Confira o disco e a inicializacao antes de desativar programas. Nenhum ajuste roda sozinho.' 22 55)
$scan=Button $homePage 'Analisar meu PC' 22 100
$startup=Button $homePage 'Apps na inicializacao' 280 100
$storage=Button $homePage 'Armazenamento / limpeza' 538 100
$ssd=Button $homePage 'Otimizar unidades (Windows)' 22 151 300
$report=TextBox $homePage 22 210 990 440 $true
$report.Text="Clique em Analisar meu PC. O programa nao executa benchmark de escrita no SSD.`r`n`r`nSe o SSD estiver quase cheio, degradado, superaquecendo ou com erros de cabo/controlador,`r`najustes do Windows nao resolvem a causa. Mantenha backup dos seus projetos.`r`n`r`nO botao de unidades abre o otimizador oficial do Windows, que escolhe a operacao`r`napropriada para cada unidade (por exemplo, ReTrim para SSD)."
$startup.Add_Click({ Start-Process 'ms-settings:startupapps' })
$storage.Add_Click({ Start-Process 'ms-settings:storagesense' })
$ssd.Add_Click({ Run-Action { Start-Process 'dfrgui.exe' } })
$scan.Add_Click({ Run-Action {
    $lines=New-Object Collections.Generic.List[string]
    $os=Get-CimInstance Win32_OperatingSystem
    $lines.Add(('Windows: {0} / build {1}' -f $os.Caption,$os.BuildNumber))
    $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
    $lines.Add(('CPU: {0}' -f $cpu.Name))
    $lines.Add(('RAM: {0:N1} GB total / {1:N1} GB disponivel agora' -f ($os.TotalVisibleMemorySize/1MB),($os.FreePhysicalMemory/1MB)))
    Get-CimInstance Win32_VideoController | ForEach-Object { $lines.Add(('GPU: {0} / driver {1}' -f $_.Name,$_.DriverVersion)) }
    $lines.Add('');$lines.Add('UNIDADES:')
    Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
        $percent=0;if ($_.Size) { $percent=100*$_.FreeSpace/$_.Size }
        $lines.Add(('{0} livre: {1:N1} GB de {2:N1} GB ({3:N0}%)' -f $_.DeviceID,($_.FreeSpace/1GB),($_.Size/1GB),$percent))
        if ($percent -lt 15) { $lines.Add('  Pouco espaco livre: mover arquivos grandes pode ajudar o SSD.') }
    }
    try {
        Get-PhysicalDisk -ErrorAction Stop | ForEach-Object { $lines.Add(('Disco: {0} / tipo {1} / saude {2} / status {3}' -f $_.FriendlyName,$_.MediaType,$_.HealthStatus,($_.OperationalStatus -join ', '))) }
    } catch { $lines.Add('Saude detalhada indisponivel com este controlador/permissao. Isso nao confirma que o SSD esteja saudavel.') }
    $lines.Add('');$lines.Add('INICIALIZACAO (apenas leitura; caminho do comando nao e executado):')
    Get-CimInstance Win32_StartupCommand | Sort-Object Name | ForEach-Object { $lines.Add(('{0} | {1}' -f $_.Name,$_.Command)) }
    $lines.Add('');$lines.Add('Sugestao: no botao de inicializacao, desative apenas apps reconhecidos e desnecessarios ao ligar.')
    $lines.Add('Mantenha drivers oficiais AMD, arquivo de paginacao automatico e protecao do Windows.')
    $lines.Add('O Windows pode nao oferecer Recall neste hardware. Remover Copilot nao e um ganho garantido de FPS.')
    $report.Lines=$lines.ToArray()
} })
$downloads=New-Page 'Downloads com icones'
[void](Label $downloads 'Organize apenas os arquivos soltos. Pastas existentes e arquivos em download ficam onde estao.' 22 18)
$rootBox=TextBox $downloads 22 62 700 30
$rootBox.Text=Get-DuckDownloads
$choose=Button $downloads 'Escolher pasta' 738 57 230
$preview=Button $downloads '1. Gerar previa' 22 110
$move=Button $downloads '2. Organizar arquivos' 280 110
$undoFiles=Button $downloads 'Desfazer ultima organizacao' 538 110 300
[void](Label $downloads 'Destino: _DuckOrganizado, com pastas e icones por tipo. Nenhuma versao antiga sera apagada.' 22 162)
$grid=New-Object Windows.Forms.DataGridView;$grid.Location=New-Object Drawing.Point(22,205);$grid.Size=New-Object Drawing.Size(990,370)
$grid.ReadOnly=$true;$grid.AllowUserToAddRows=$false;$grid.AllowUserToDeleteRows=$false;$grid.RowHeadersVisible=$false;$grid.AutoSizeColumnsMode='Fill';$grid.BackgroundColor=[Drawing.Color]::FromArgb(22,24,31)
$grid.DefaultCellStyle.BackColor=[Drawing.Color]::FromArgb(35,38,48);$grid.DefaultCellStyle.ForeColor=[Drawing.Color]::WhiteSmoke;$grid.DefaultCellStyle.SelectionBackColor=[Drawing.Color]::FromArgb(72,58,109)
[void]$grid.Columns.Add('File','Arquivo');[void]$grid.Columns.Add('Dest','Destino');[void]$grid.Columns.Add('Size','MB');$grid.Columns[2].FillWeight=25
$downloads.Controls.Add($grid)
$downloadStatus=Label $downloads 'Gere a previa antes de mover. Arquivos alterados nos ultimos 2 minutos sao ignorados.' 22 590 990 65
$choose.Add_Click({ if ($script:Busy) { return };$dialog=New-Object Windows.Forms.FolderBrowserDialog;$dialog.Description='Escolha a pasta Downloads';if ($dialog.ShowDialog($form) -eq 'OK') { $rootBox.Text=$dialog.SelectedPath;$script:Plan=@();$grid.Rows.Clear() };$dialog.Dispose() })
$preview.Add_Click({ Run-Action {
    $script:Plan=@(New-DuckDownloadPlan -Root $rootBox.Text);$script:PlannedRoot=$rootBox.Text;$grid.Rows.Clear()
    foreach ($item in $script:Plan) { [void]$grid.Rows.Add([IO.Path]::GetFileName($item.Source),$item.Destination,([math]::Round($item.Bytes/1MB,2))) }
    $downloadStatus.Text=('{0} arquivos prontos. Confira todos os destinos antes de organizar. Pastas nao foram movidas.' -f $script:Plan.Count)
} })
$move.Add_Click({ Run-Action {
    if (!$script:Plan.Count -or $rootBox.Text -ne $script:PlannedRoot) { Inform 'Gere uma previa para a pasta atual primeiro.';return }
    if (!(Confirm ('Mover {0} arquivos conforme a previa? Nao sera apagado nem sobrescrito nenhum arquivo.' -f $script:Plan.Count))) { return }
    $result=Invoke-DuckDownloadPlan -Root $rootBox.Text -Plan $script:Plan -JournalDirectory $script:History -IconRoot $script:Icons -Progress { param($done,$total) $downloadStatus.Text="Organizando: $done de $total";[Windows.Forms.Application]::DoEvents() }
    $downloadStatus.Text=('Movidos: {0}. Ignorados/erros: {1}. Historico: {2}' -f $result.Moved,$result.Failed,$result.Journal)
    $script:Plan=@();$grid.Rows.Clear();Inform ($downloadStatus.Text + "`r`nAtualize o Explorador (F5) para ver os icones.")
} })
$undoFiles.Add_Click({ Run-Action {
    $path=Latest-History 'downloads';if (!$path) { Inform 'Nenhuma organizacao pendente para desfazer.';return }
    if (!(Confirm "Desfazer esta organizacao?`r`n$path`r`nArquivos modificados ou com conflito nao serao movidos.")) { return }
    $r=Undo-DuckDownloads $path;$script:Plan=@();$grid.Rows.Clear();Inform ('Restaurados: {0}. Ignorados: {1}. As pastas ficam disponiveis; nada e apagado.' -f $r.Restored,$r.Skipped)
} })
$settings=New-Page 'Ajustes reversiveis'
[void](Label $settings 'Escolha e revise os ajustes. Efeito varia por versao do Windows; alguns pedem sair e entrar novamente.' 22 18)
$cTips=Check $settings 'Reduzir dicas, anuncios e sugestoes do Windows para este usuario' 22 70 $true
$cCopilot=Check $settings 'Ocultar/desativar o Copilot classico (o app novo e tratado na aba de apps)' 22 116 $true
$cGame=Check $settings 'Ativar Modo de Jogo do Windows' 22 162 $true
$cCapture=Check $settings 'Desligar captura em segundo plano do Windows (afeta clipes Xbox/Game Bar)' 22 208
$cVisuals=Check $settings 'Reduzir transparencia e animacoes de janelas/barra de tarefas' 22 254
$cMouse=Check $settings 'Mouse sem aceleracao (mira mais consistente; nao zera latencia nem aumenta CPS)' 22 294
$inspect=Button $settings 'Revisar selecao' 22 340
$apply=Button $settings 'Aplicar com backup' 280 340
$undoSettings=Button $settings 'Restaurar ultimo ajuste' 538 340 300
$settingsReport=TextBox $settings 22 400 990 220 $true
function Selected-Options {
    $options=@();if ($cTips.Checked) { $options+='Suggestions' };if ($cCopilot.Checked) { $options+='Copilot' };if ($cGame.Checked) { $options+='GameMode' };if ($cCapture.Checked) { $options+='Capture' };if ($cVisuals.Checked) { $options+='Visuals' };if ($cMouse.Checked) { $options+='Mouse' };return $options
}
$inspect.Add_Click({ Run-Action { $settingsReport.Text=(@(Get-DuckTuningPlan @(Selected-Options)) | ForEach-Object { 'HKCU\{0} | {1} = {2} ({3})' -f $_.Path,$_.Name,$_.Value,$_.Kind }) -join "`r`n" } })
$apply.Add_Click({ Run-Action {
    $options=@(Selected-Options);if (!$options.Count) { Inform 'Nenhum ajuste selecionado.';return }
    $plan=@(Get-DuckTuningPlan $options);$settingsReport.Text=($plan | ForEach-Object { 'HKCU\{0} | {1} = {2}' -f $_.Path,$_.Name,$_.Value }) -join "`r`n"
    if (!(Confirm ('Aplicar {0} valores revisados acima? O estado anterior sera salvo. A captura so muda se voce marcou essa opcao.' -f $plan.Count))) { return }
    $r=Invoke-DuckTuning $options $script:History;if ('Mouse' -in $options) { [void][DuckPC.MonitorInfo]::ApplyMouseRegistry() };Inform ('Aplicados: {0}; erros: {1}. Backup: {2}.`r`nSe necessario, saia e entre novamente no Windows.' -f $r.Applied,$r.Failed,$r.Journal)
} })
$undoSettings.Add_Click({ Run-Action {
    $path=Latest-History 'ajustes';if (!$path) { Inform 'Nenhum ajuste pendente para restaurar.';return }
    if (!(Confirm "Restaurar os valores anteriores deste backup?`r`n$path")) { return }
    $r=Undo-DuckTuning $path;[void][DuckPC.MonitorInfo]::ApplyMouseRegistry();Inform ('Restaurados: {0}. Preservados/erros: {1}.' -f $r.Restored,$r.Skipped)
} })
$inputPage=New-Page 'Mouse e monitor'
[void](Label $inputPage 'Leia os Hz do monitor e ajuste o mouse, sem overclock de monitor ou USB.' 22 18)
[void](Label $inputPage 'A opcao Mouse sem aceleracao fica em Ajustes reversiveis, desmarcada por padrao.' 22 57)
$readMonitor=Button $inputPage 'Ler Hz dos monitores' 22 105
$displaySettings=Button $inputPage 'Configurar 75 Hz no Windows' 280 105 300
$amdSettings=Button $inputPage 'Abrir AMD Software' 598 105 300
$monitorReport=TextBox $inputPage 22 170 990 170 $true
$latencyHelp=TextBox $inputPage 22 365 990 270 $true
$latencyHelp.Text=@'
75 Hz e a taxa do monitor, nao uma garantia de 75 FPS. O DuckPC le os modos
anunciados pelo driver e abre a tela oficial do Windows para voce escolher 75 Hz.
O Windows faz a confirmacao e reversao do modo, sem forcarmos overclock.

RX 580: no AMD Software, confira FreeSync se monitor e cabo suportarem.
Se aparecer Radeon Anti-Lag para seu jogo, teste ligado e desligado.
Nao precisa instalar driver desconhecido, Anti-Lag 2 ou algum pacote "input zero".

Para jogos, desative gravacao em segundo plano somente se nao usar os clipes.
Use o polling do mouse no software oficial do fabricante, sem overclock de USB.
Mouse sem aceleracao melhora a consistencia do movimento, nao o atraso do clique.

Se quiser estabilidade, use o limitador de FPS do proprio jogo. 75 Hz nao trava
os FPS automaticamente; com FreeSync, um limite um pouco abaixo do teto pode
ajudar a permanecer na faixa variavel. Teste a resposta no seu jogo.
'@
$readMonitor.Add_Click({ Run-Action {
    $parts=New-Object Collections.Generic.List[string]
    foreach ($screen in [Windows.Forms.Screen]::AllScreens) { $parts.Add([DuckPC.MonitorInfo]::Describe($screen.DeviceName)) }
    $monitorReport.Text=$parts.ToArray() -join "`r`n`r`n"
} })
$displaySettings.Add_Click({ Start-Process 'ms-settings:display-advanced' })
$amdSettings.Add_Click({ Run-Action {
    $amd=Join-Path $env:ProgramFiles 'AMD\CNext\CNext\RadeonSoftware.exe'
    if (Test-Path -LiteralPath $amd) { Start-Process -FilePath $amd }
    else { Inform 'Abra o AMD Software pelo menu Iniciar. A disponibilidade de FreeSync e Anti-Lag depende do monitor, cabo, driver e jogo.' }
} })
$apps=New-Page 'Apps opcionais'
[void](Label $apps 'Somente apps da lista abaixo podem ser removidos, apenas deste usuario. Marque somente os que nao usa.' 22 18)
[void](Label $apps 'Remover app nao tem desfazer pelo registro: reinstale depois pela Microsoft Store. Nao ha remocao automatica.' 22 56 990 50)
$findApps=Button $apps 'Listar apps opcionais instalados' 22 115 340
$removeApps=Button $apps 'Remover somente os marcados' 382 115 340
$appList=New-Object Windows.Forms.CheckedListBox;$appList.Location=New-Object Drawing.Point(22,180);$appList.Size=New-Object Drawing.Size(990,260);$appList.CheckOnClick=$true
$appList.BackColor=[Drawing.Color]::FromArgb(22,24,31);$appList.ForeColor=[Drawing.Color]::White;$apps.Controls.Add($appList)
$appLog=TextBox $apps 22 465 990 170 $true
$findApps.Add_Click({ Run-Action {
    $appList.Items.Clear()
    Get-AppxPackage | Where-Object { $_.Name -in $script:Candidates } | Sort-Object Name | ForEach-Object { [void]$appList.Items.Add($_.PackageFullName,$false) }
    $appLog.Text='Nenhum app esta marcado por padrao. Copilot so aparece se o pacote estiver instalado para este usuario.'
} })
$removeApps.Add_Click({ Run-Action {
    $selected=@($appList.CheckedItems | ForEach-Object { [string]$_ })
    if (!$selected.Count) { Inform 'Selecione os apps que voce nao usa.';return }
    if (!(Confirm ("Remover apenas estes apps deste usuario? Para recuperar, use a Microsoft Store.`r`n`r`n" + ($selected -join "`r`n")))) { return }
    $results=New-Object Collections.Generic.List[string]
    foreach ($package in $selected) {
        try {
            $found=@(Get-AppxPackage | Where-Object { $_.PackageFullName -eq $package -and $_.Name -in $script:Candidates })
            if (!$found.Count) { throw 'Pacote nao encontrado ou fora da lista permitida.' }
            Remove-AppxPackage -Package $package -ErrorAction Stop
            $results.Add('Removido: ' + $package)
        } catch { $results.Add('Nao removido: ' + $package + ' | ' + $_.Exception.Message) }
    }
    $appLog.Lines=$results.ToArray()
    $log=Join-Path $script:History ('apps-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '.txt');[IO.File]::WriteAllLines($log,$results.ToArray())
    $appList.Items.Clear()
} })
$form.Add_FormClosing({ param($sender,$e) if ($script:Busy) { $e.Cancel=$true } })
[void]$form.ShowDialog()
$form.Dispose()
