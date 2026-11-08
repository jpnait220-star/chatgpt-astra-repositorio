Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Write-DuckJson($Path, $Value) {
    $parent = Split-Path -Parent $Path
    if (!(Test-Path -LiteralPath $parent)) { [IO.Directory]::CreateDirectory($parent) | Out-Null }
    $temp = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        $json = ConvertTo-Json -InputObject $Value -Depth 12
        [IO.File]::WriteAllText($temp, $json, (New-Object Text.UTF8Encoding($false)))
        if ([IO.File]::Exists($Path)) {
            $previous = $Path + '.previous-' + [guid]::NewGuid().ToString('N')
            [IO.File]::Replace($temp, $Path, $previous)
            if ([IO.File]::Exists($previous)) { [IO.File]::Delete($previous) }
        }
        else { [IO.File]::Move($temp, $Path) }
    } finally { if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) } }
}
function Get-DuckDownloads {
    if ($env:OS -eq 'Windows_NT') {
        $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
        $value = Get-ItemPropertyValue -LiteralPath $key -Name '{374DE290-123F-4565-9164-39C4925E467B}' -ErrorAction SilentlyContinue
        if ($value) { return [Environment]::ExpandEnvironmentVariables($value) }
    }
    return Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
}
function Get-DuckCategory($File) {
    $ext = $File.Extension.ToLowerInvariant()
    if ($ext -eq '.jar') { return 'Minecraft e Mods' }
    if ($ext -in @('.zip','.7z','.rar','.mrpack','.mcpack','.mcworld','.litematic','.schem','.schematic')) {
        if ($ext -in @('.mrpack','.mcpack','.mcworld','.litematic','.schem','.schematic') -or $File.Name -match '(?i)minecraft|duck|fabric|forge|modpack|cosmetic|boxpvp') { return 'Minecraft e Mods' }
        return 'Compactados'
    }
    if ($ext -in @('.exe','.msi','.msix','.appx','.msixbundle')) { return 'Instaladores' }
    if ($ext -in @('.png','.jpg','.jpeg','.gif','.webp','.bmp','.ico','.svg')) { return 'Imagens e Skins' }
    if ($ext -in @('.mp4','.mkv','.mov','.webm','.avi')) { return 'Videos' }
    if ($ext -in @('.mp3','.wav','.flac','.ogg','.m4a')) { return 'Audios' }
    if ($ext -in @('.java','.kt','.gradle','.py','.js','.ts','.json','.yml','.yaml','.toml','.xml','.html','.css','.ps1','.bat','.cmd')) { return 'Codigo e Configs' }
    if ($ext -in @('.pdf','.txt','.md','.doc','.docx','.xls','.xlsx','.csv','.log','.rtf')) { return 'Documentos e Logs' }
    return 'Outros'
}
function Assert-DuckChild($Path, $Root) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (!$full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Caminho fora da pasta autorizada.' }
    # Do not traverse directory junctions or symbolic links.
    $parent = Split-Path -Parent $full
    while ($parent -and $parent.Length -ge $prefix.TrimEnd([IO.Path]::DirectorySeparatorChar).Length) {
        if (Test-Path -LiteralPath $parent) {
            $item = Get-Item -LiteralPath $parent -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Pasta com link/junction: operacao ignorada.' }
        }
        $next = Split-Path -Parent $parent
        if ($next -eq $parent) { break }; $parent = $next
    }
    return $full
}
function Get-DuckUniquePath($Path, $Reserved) {
    $candidate = $Path; $n = 2
    while ([IO.File]::Exists($candidate) -or [IO.Directory]::Exists($candidate) -or ($Reserved -and $Reserved.Contains($candidate))) {
        $candidate = Join-Path (Split-Path -Parent $Path) (([IO.Path]::GetFileNameWithoutExtension($Path)) + " ($n)" + [IO.Path]::GetExtension($Path)); $n++
    }
    return $candidate
}
function New-DuckDownloadPlan {
    param([Parameter(Mandatory=$true)][string]$Root, [int]$MinimumAgeSeconds=120)
    $rootItem = Get-Item -LiteralPath $Root -Force
    if (!$rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Escolha uma pasta normal, sem link ou junction.' }
    $rootPath = $rootItem.FullName
    $output = Join-Path $rootPath '_DuckOrganizado'
    $reserved = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($file in (Get-ChildItem -LiteralPath $rootPath -File -Force | Sort-Object Name)) {
        if (($file.Attributes -band ([IO.FileAttributes]::Hidden -bor [IO.FileAttributes]::System -bor [IO.FileAttributes]::ReparsePoint)) -ne 0) { continue }
        if ($file.Extension -match '(?i)^\.(crdownload|part|tmp|download|partial)$' -or $file.Name -match '(?i)^~\$|^desktop\.ini$') { continue }
        if ($file.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddSeconds(-$MinimumAgeSeconds)) { continue }
        $category = Get-DuckCategory $file
        $targetDir = Join-Path $output $category
        if ($category -eq 'Minecraft e Mods') {
            $version = [regex]::Match($file.Name, '(?<!\d)1\.(?:1[6-9]|2[0-9])(?:\.\d{1,2})?(?!\d)')
            if ($version.Success) { $targetDir = Join-Path $targetDir $version.Value }
            elseif ($file.Extension -eq '.jar') { $targetDir = Join-Path $targetDir 'Sem versao no nome' }
        }
        $destination = Get-DuckUniquePath (Join-Path $targetDir $file.Name) $reserved
        [void]$reserved.Add($destination)
        [pscustomobject]@{ Source=$file.FullName; Destination=$destination; Category=$category; Bytes=[long]$file.Length; ModifiedTicks=$file.LastWriteTimeUtc.Ticks }
    }
}
function Set-DuckFolderIcons($Root, $IconRoot) {
    if ($env:OS -ne 'Windows_NT' -or !(Test-Path -LiteralPath $IconRoot)) { return }
    $map = @{'Minecraft e Mods'='mods';'Compactados'='archives';'Instaladores'='installers';'Imagens e Skins'='images';'Videos'='videos';'Audios'='audio';'Codigo e Configs'='code';'Documentos e Logs'='documents';'Outros'='other'}
    foreach ($name in $map.Keys) {
        $folder = Join-Path (Join-Path $Root '_DuckOrganizado') $name
        if (!(Test-Path -LiteralPath $folder)) { continue }
        $icon = Join-Path $IconRoot ($map[$name] + '.ico')
        $ini = Join-Path $folder 'desktop.ini'
        if (Test-Path -LiteralPath $ini) { continue }
        [IO.File]::WriteAllText($ini, "[.ShellClassInfo]`r`nIconResource=$icon,0`r`nInfoTip=Organizado pelo DuckPC`r`n", [Text.Encoding]::Unicode)
        [IO.File]::SetAttributes($ini, ([IO.FileAttributes]::Hidden -bor [IO.FileAttributes]::System))
        [IO.File]::SetAttributes($folder, ((Get-Item -LiteralPath $folder -Force).Attributes -bor [IO.FileAttributes]::ReadOnly))
    }
}
function Invoke-DuckDownloadPlan {
    param([string]$Root, [object[]]$Plan, [string]$JournalDirectory, [string]$IconRoot='', [scriptblock]$Progress=$null)
    $rootPath = (Get-Item -LiteralPath $Root).FullName
    $output = Join-Path $rootPath '_DuckOrganizado'
    $journalPath = Join-Path $JournalDirectory ('downloads-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N') + '.json')
    $entries = @($Plan | ForEach-Object { [pscustomobject]@{ Source=[string]$_.Source; Destination=[string]$_.Destination; Bytes=[long]$_.Bytes; ModifiedTicks=[long]$_.ModifiedTicks; Status='Pending'; Error='' } })
    $journal = [pscustomobject]@{ Version=1; Root=$rootPath; Output=$output; CreatedUtc=[DateTime]::UtcNow.ToString('o'); Entries=$entries }
    # Save every intent before moving anything. Pending entries remain recoverable
    # after an interruption, without rewriting the full log for every file.
    Write-DuckJson $journalPath $journal
    $done=0
    foreach ($entry in $entries) {
        try {
            $source = Assert-DuckChild $entry.Source $rootPath
            if ((Split-Path -Parent $source) -ne $rootPath) { throw 'Apenas arquivos soltos da pasta escolhida podem ser organizados.' }
            $file = Get-Item -LiteralPath $source -Force
            if ($file.PSIsContainer -or ($file.Attributes -band ([IO.FileAttributes]::ReparsePoint -bor [IO.FileAttributes]::Hidden -bor [IO.FileAttributes]::System))) { throw 'Item nao e um arquivo comum visivel.' }
            if ($file.Length -ne $entry.Bytes -or $file.LastWriteTimeUtc.Ticks -ne $entry.ModifiedTicks) { throw 'Arquivo mudou depois da previa; gere outra previa.' }
            $target = Assert-DuckChild $entry.Destination $output
            $target = Get-DuckUniquePath $target $null
            if ($target.Length -gt 240) { throw 'Caminho muito longo; arquivo mantido na origem.' }
            if ($entry.Destination -ne $target) { $entry.Destination=$target;Write-DuckJson $journalPath $journal }
            [IO.Directory]::CreateDirectory((Split-Path -Parent $target)) | Out-Null
            [IO.File]::Move($source, $target)
            $entry.Status = 'Moved'
        } catch { $entry.Status='Failed'; $entry.Error=$_.Exception.Message }
        $done++
        if ($done % 25 -eq 0) { Write-DuckJson $journalPath $journal }
        if ($Progress) { try { & $Progress $done $entries.Count } catch {} }
    }
    Write-DuckJson $journalPath $journal
    if ($IconRoot) { try { Set-DuckFolderIcons $rootPath $IconRoot } catch { Write-Warning $_.Exception.Message } }
    return [pscustomobject]@{ Journal=$journalPath; Moved=@($entries | Where-Object Status -eq 'Moved').Count; Failed=@($entries | Where-Object Status -eq 'Failed').Count }
}
function Undo-DuckDownloads([string]$JournalPath) {
    $journal = Get-Content -LiteralPath $JournalPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($journal.Version -ne 1) { throw 'Formato de historico desconhecido.' }
    $restored=0; $skipped=0; $processed=0
    if (!$journal.Entries.Count) { return [pscustomobject]@{ Restored=0; Skipped=0 } }
    foreach ($entry in @($journal.Entries)[($journal.Entries.Count-1)..0]) {
        if ($entry.Status -notin @('Moved','Pending','UndoSkipped')) { continue }
        try {
            $source = Assert-DuckChild $entry.Source $journal.Root
            $target = Assert-DuckChild $entry.Destination (Join-Path $journal.Root '_DuckOrganizado')
            if ((Split-Path -Parent $source) -ne $journal.Root) { throw 'Origem fora da raiz.' }
            if ([IO.File]::Exists($source) -and ![IO.File]::Exists($target)) {
                $recovered=Get-Item -LiteralPath $source -Force
                if ($recovered.Length -eq $entry.Bytes -and $recovered.LastWriteTimeUtc.Ticks -eq $entry.ModifiedTicks) { $entry.Status='Restored';$entry.Error='';$restored++;continue }
            }
            if ([IO.File]::Exists($source) -or [IO.Directory]::Exists($source)) { throw 'Ja existe outro arquivo com o nome original; nenhum foi sobrescrito.' }
            $file = Get-Item -LiteralPath $target -Force
            if ($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Destino nao e um arquivo normal.' }
            if ($file.Length -ne $entry.Bytes -or $file.LastWriteTimeUtc.Ticks -ne $entry.ModifiedTicks) { throw 'Arquivo alterado depois de organizar; mantido no destino.' }
            [IO.File]::Move($target,$source); $entry.Status='Restored'; $entry.Error=''; $restored++
        } catch { $entry.Status='UndoSkipped'; $entry.Error=$_.Exception.Message; $skipped++ }
        $processed++
        if ($processed % 25 -eq 0) { Write-DuckJson $JournalPath $journal }
    }
    Write-DuckJson $JournalPath $journal
    return [pscustomobject]@{ Restored=$restored; Skipped=$skipped }
}
function Get-DuckTuningPlan([string[]]$Options) {
    $spec = @{
        Suggestions=@(
            @('Software\Microsoft\Windows\CurrentVersion\UserProfileEngagement','ScoobeSystemSettingEnabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo','Enabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\Privacy','TailoredExperiencesWithDiagnosticDataEnabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager','SystemPaneSuggestionsEnabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager','SoftLandingEnabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager','SubscribedContent-338388Enabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager','SubscribedContent-338389Enabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager','SubscribedContent-353694Enabled',0),
            @('Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager','SubscribedContent-353696Enabled',0)
        )
        Copilot=@(@('Software\Policies\Microsoft\Windows\WindowsCopilot','TurnOffWindowsCopilot',1),@('Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced','ShowCopilotButton',0))
        GameMode=@(@('Software\Microsoft\GameBar','AllowAutoGameMode',1),@('Software\Microsoft\GameBar','AutoGameModeEnabled',1))
        Capture=@(@('System\GameConfigStore','GameDVR_Enabled',0),@('Software\Microsoft\Windows\CurrentVersion\GameDVR','AppCaptureEnabled',0))
        Mouse=@(@('Control Panel\Mouse','MouseSpeed','0'),@('Control Panel\Mouse','MouseThreshold1','0'),@('Control Panel\Mouse','MouseThreshold2','0'))
        Visuals=@(@('Control Panel\Desktop\WindowMetrics','MinAnimate','0'),@('Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced','TaskbarAnimations',0),@('Software\Microsoft\Windows\CurrentVersion\Themes\Personalize','EnableTransparency',0))
    }
    foreach ($option in $Options) {
        if (!$spec.ContainsKey($option)) { throw "Ajuste desconhecido: $option" }
        foreach ($row in $spec[$option]) {
            $kind='DWord'; if ($row[2] -is [string]) { $kind='String' }
            [pscustomobject]@{ Option=$option; Path=$row[0]; Name=$row[1]; Value=$row[2]; Kind=$kind }
        }
    }
}
function Invoke-DuckTuning([string[]]$Options,[string]$JournalDirectory) {
    if ($env:OS -ne 'Windows_NT') { throw 'Ajustes de sistema disponiveis apenas no Windows.' }
    $path=Join-Path $JournalDirectory ('ajustes-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N') + '.json')
    $entries=New-Object Collections.ArrayList
    foreach ($item in @(Get-DuckTuningPlan $Options)) {
        $key=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($item.Path)
        $exists=$false; $old=$null; $oldKind='DWord'
        if ($key) { try { $exists=$key.GetValueNames() -contains $item.Name; if ($exists) { $old=$key.GetValue($item.Name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames); $oldKind=$key.GetValueKind($item.Name).ToString() } } finally { $key.Dispose() } }
        $entry=[pscustomobject]@{ OwnerSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value; Path=$item.Path; Name=$item.Name; Value=$item.Value; Kind=$item.Kind; Existed=$exists; OldValue=$old; OldKind=$oldKind; Status='Pending'; Error='' }
        [void]$entries.Add($entry);Write-DuckJson $path @($entries.ToArray())
        try { $key=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($item.Path); try { $key.SetValue($item.Name,$item.Value,([Enum]::Parse([Microsoft.Win32.RegistryValueKind],$item.Kind))) } finally { $key.Dispose() }; $entry.Status='Applied' }
        catch { $entry.Status='Failed';$entry.Error=$_.Exception.Message }
        Write-DuckJson $path @($entries.ToArray())
    }
    [pscustomobject]@{ Journal=$path; Applied=@($entries | Where-Object Status -eq 'Applied').Count; Failed=@($entries | Where-Object Status -eq 'Failed').Count }
}
function Undo-DuckTuning([string]$JournalPath) {
    if ($env:OS -ne 'Windows_NT') { throw 'Somente Windows.' }
    $entries=@(Get-Content -LiteralPath $JournalPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    $allowed=@{};foreach ($a in @(Get-DuckTuningPlan @('Suggestions','Copilot','GameMode','Capture','Visuals','Mouse'))) { $allowed[$a.Path+'|'+$a.Name]=$true }
    $restored=0;$skipped=0
    foreach ($entry in $entries) {
        if ($entry.Status -notin @('Applied','Pending','UndoSkipped')) { continue }
        try {
            if ($entry.OwnerSid -ne [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) { throw 'Backup pertence a outro usuario do Windows.' }
            if (!$allowed.ContainsKey($entry.Path+'|'+$entry.Name)) { throw 'Entrada fora da lista de ajustes autorizados.' }
            $key=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($entry.Path)
            try {
                $current=$key.GetValue($entry.Name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
                if ([string]$current -ne [string]$entry.Value -or $key.GetValueKind($entry.Name).ToString() -ne $entry.Kind) { throw 'Valor modificado por outro programa; preservado.' }
                if ($entry.Existed) { $key.SetValue($entry.Name,$entry.OldValue,([Enum]::Parse([Microsoft.Win32.RegistryValueKind],$entry.OldKind))) }
                else { $key.DeleteValue($entry.Name,$false) }
            } finally { $key.Dispose() }
            $entry.Status='Restored';$entry.Error='';$restored++
        } catch { $entry.Status='UndoSkipped';$entry.Error=$_.Exception.Message;$skipped++ }
        Write-DuckJson $JournalPath $entries
    }
    [pscustomobject]@{Restored=$restored;Skipped=$skipped}
}
Export-ModuleMember -Function Get-DuckDownloads,New-DuckDownloadPlan,Invoke-DuckDownloadPlan,Undo-DuckDownloads,Get-DuckTuningPlan,Invoke-DuckTuning,Undo-DuckTuning
