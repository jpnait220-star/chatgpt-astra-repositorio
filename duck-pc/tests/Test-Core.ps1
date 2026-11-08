$ErrorActionPreference='Stop'
$module=Join-Path $PSScriptRoot '../src/DuckPC.Core.psm1'
if (!(Test-Path -LiteralPath $module)) { $module=Join-Path $PSScriptRoot '../DuckPC.Core.psm1' }
Import-Module $module -Force -DisableNameChecking
$script:checks=0
function Assert($Value,$Message) { $script:checks++;if (!$Value) { throw "FAILED: $Message" } }
function Put($Root,$Name,$Text='data') {
    $p=Join-Path $Root $Name;[IO.File]::WriteAllText($p,$Text);[IO.File]::SetLastWriteTimeUtc($p,[DateTime]::UtcNow.AddMinutes(-10));return $p
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('duckpc-tests-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temp) | Out-Null
try {
    $root=Join-Path $temp 'Downloads [teste á]' ;[IO.Directory]::CreateDirectory($root)|Out-Null
    $history=Join-Path $temp 'history'
    $jar=Put $root 'DuckClientZ-1.21.4-beta.jar'
    $exe=Put $root 'editor (1).exe'
    $picture=Put $root 'máscara [roxa].png'
    $archive=Put $root 'documentos.zip'
    [void](Put $root 'unfinished.crdownload')
    [void](Put $root 'unfinished.part')
    $recent=Put $root 'ainda-baixando.jar';[IO.File]::SetLastWriteTimeUtc($recent,[DateTime]::UtcNow)
    $project=Join-Path $root 'meu projeto';[IO.Directory]::CreateDirectory($project)|Out-Null;[void](Put $project 'source.java')
    $plan=@(New-DuckDownloadPlan $root)
    Assert ($plan.Count -eq 4) 'Only old complete loose files included'
    Assert (($plan | Where-Object Source -eq $jar).Destination -like '*Minecraft e Mods*1.21.4*') 'Minecraft version grouped'
    Assert (($plan | Where-Object Source -eq $exe).Category -eq 'Instaladores') 'EXE category'
    Assert (($plan | Where-Object Source -eq $picture).Category -eq 'Imagens e Skins') 'Image category'
    Assert (($plan | Where-Object Source -eq $archive).Category -eq 'Compactados') 'ZIP category'
    Assert (Test-Path -LiteralPath $jar) 'Preview does not move'
    $r=Invoke-DuckDownloadPlan -Root $root -Plan $plan -JournalDirectory $history
    Assert ($r.Moved -eq 4 -and $r.Failed -eq 0) 'Move all planned files'
    Assert (!(Test-Path -LiteralPath $jar)) 'Source moved'
    Assert (Test-Path -LiteralPath (Join-Path $project 'source.java')) 'Project folders untouched'
    Assert (Test-Path -LiteralPath $recent) 'Recent download untouched'
    $r2=Undo-DuckDownloads $r.Journal
    Assert ($r2.Restored -eq 4 -and $r2.Skipped -eq 0) 'Restore all moves'
    Assert ([IO.File]::ReadAllText($jar) -eq 'data') 'File bytes preserved'
    $repeat=Undo-DuckDownloads $r.Journal
    Assert ($repeat.Restored -eq 0) 'Undo is idempotent'
    # A destination created after preview never gets overwritten.
    $plan=@(New-DuckDownloadPlan $root)
    $collision=($plan | Where-Object Source -eq $exe).Destination
    [IO.Directory]::CreateDirectory((Split-Path $collision))|Out-Null;[IO.File]::WriteAllText($collision,'existing')
    $r=Invoke-DuckDownloadPlan $root $plan $history
    Assert ([IO.File]::ReadAllText($collision) -eq 'existing') 'Destination collision never overwritten'
    $j=Get-Content -LiteralPath $r.Journal -Raw -Encoding UTF8|ConvertFrom-Json
    $exeEntry=$j.Entries | Where-Object Source -eq $exe
    Assert ($exeEntry.Destination -ne $collision -and $exeEntry.Destination -like '*(2).exe') 'Collision renamed without data loss'
    # Undo collisions / changed output are preserved.
    [IO.File]::WriteAllText($jar,'new at source')
    $imgEntry=$j.Entries | Where-Object Source -eq $picture
    [IO.File]::WriteAllText($imgEntry.Destination,'changed after organization')
    $r2=Undo-DuckDownloads $r.Journal
    Assert ($r2.Skipped -eq 2 -and $r2.Restored -eq 2) 'Undo preserves source collision and edited output'
    Assert ([IO.File]::ReadAllText($jar) -eq 'new at source') 'Source collision preserved'
    Assert ([IO.File]::ReadAllText($imgEntry.Destination) -eq 'changed after organization') 'User edits preserved'
    # Changed source after preview is not moved.
    $one=Put $root 'changed.jar';$plan=@(New-DuckDownloadPlan $root | Where-Object Source -eq $one)
    [IO.File]::WriteAllText($one,'different length')
    $r=Invoke-DuckDownloadPlan $root $plan $history
    Assert ($r.Failed -eq 1 -and (Test-Path -LiteralPath $one)) 'Changed source skipped'
    # Malformed/tampered plans cannot move arbitrary external files.
    $external=Put $temp 'external.jar'
    $fake=[pscustomobject]@{Source=$external;Destination=(Join-Path $root '_DuckOrganizado/fake.jar');Bytes=4;ModifiedTicks=(Get-Item -LiteralPath $external).LastWriteTimeUtc.Ticks}
    $r=Invoke-DuckDownloadPlan $root @($fake) $history
    Assert ($r.Failed -eq 1 -and (Test-Path -LiteralPath $external)) 'External source rejected'
    $inside=Put $root 'escape.jar';$fi=Get-Item -LiteralPath $inside
    $fake=[pscustomobject]@{Source=$inside;Destination=(Join-Path $temp 'escape.jar');Bytes=$fi.Length;ModifiedTicks=$fi.LastWriteTimeUtc.Ticks}
    $r=Invoke-DuckDownloadPlan $root @($fake) $history
    Assert ($r.Failed -eq 1 -and (Test-Path -LiteralPath $inside)) 'External destination rejected'
    # A crash after moving but before final journal update can be undone.
    $recover=Put $root 'recover.jar';$plan=@(New-DuckDownloadPlan $root | Where-Object Source -eq $recover)
    $r=Invoke-DuckDownloadPlan $root $plan $history
    $j=Get-Content -LiteralPath $r.Journal -Raw -Encoding UTF8|ConvertFrom-Json;$j.Entries[0].Status='Pending';$j|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $r.Journal
    $r2=Undo-DuckDownloads $r.Journal
    Assert ($r2.Restored -eq 1 -and (Test-Path -LiteralPath $recover)) 'Interrupted move recovery'
    $settings=@(Get-DuckTuningPlan @('Suggestions','Copilot','GameMode','Capture','Visuals'))
    Assert ($settings.Count -eq 18) 'Expected complete setting plan'
    Assert (@($settings | Where-Object { $_.Path -match 'Defender|WindowsUpdate|Services|Win32Priority' }).Count -eq 0) 'No protection/service changes'
    $threw=$false;try { Get-DuckTuningPlan @('Unknown') } catch { $threw=$true };Assert $threw 'Unknown tweak rejected'
    # Empty batches are safe and do not invent restore entries.
    $r=Invoke-DuckDownloadPlan $root @() $history
    $r2=Undo-DuckDownloads $r.Journal
    Assert ($r.Moved -eq 0 -and $r2.Restored -eq 0 -and $r2.Skipped -eq 0) 'Empty operation safe'
    # A category symlink cannot redirect a move outside Downloads.
    $linkRoot=Join-Path $temp 'link-root';[IO.Directory]::CreateDirectory($linkRoot)|Out-Null
    $linkFile=Put $linkRoot 'redirection.jar'
    $p=@(New-DuckDownloadPlan $linkRoot)
    $output=Join-Path $linkRoot '_DuckOrganizado';[IO.Directory]::CreateDirectory($output)|Out-Null
    $externalDir=Join-Path $temp 'external-dir';[IO.Directory]::CreateDirectory($externalDir)|Out-Null
    New-Item -ItemType SymbolicLink -Path (Join-Path $output 'Minecraft e Mods') -Target $externalDir | Out-Null
    $r=Invoke-DuckDownloadPlan $linkRoot $p $history
    Assert ($r.Failed -eq 1 -and (Test-Path -LiteralPath $linkFile)) 'Symbolic-link category rejected'
    Assert (@(Get-ChildItem -LiteralPath $externalDir).Count -eq 0) 'No data escaped to link target'
    # Larger batch, progress notifications and batched intent log.
    $batchRoot=Join-Path $temp 'batch';[IO.Directory]::CreateDirectory($batchRoot)|Out-Null
    1..125 | ForEach-Object { [void](Put $batchRoot ("mod-1.20.1-v$_.jar")) }
    $p=@(New-DuckDownloadPlan $batchRoot);$script:progressCount=0
    $r=Invoke-DuckDownloadPlan -Root $batchRoot -Plan $p -JournalDirectory $history -Progress { param($done,$total) $script:progressCount++ }
    Assert ($r.Moved -eq 125 -and $script:progressCount -eq 125) 'Batch progress and moves'
    $r2=Undo-DuckDownloads $r.Journal
    Assert ($r2.Restored -eq 125 -and $r2.Skipped -eq 0) 'Large batch fully reversible'
    $mouse=@(Get-DuckTuningPlan @('Mouse'))
    Assert ($mouse.Count -eq 3 -and @($mouse | Where-Object { $_.Kind -ne 'String' -or $_.Path -ne 'Control Panel\Mouse' -or $_.Value -ne '0' }).Count -eq 0) 'Mouse tweak only disables acceleration with proper registry types'
    Add-Type -Path (Join-Path (Split-Path -Parent $module) 'MonitorInfo.cs')
    Assert ([Runtime.InteropServices.Marshal]::SizeOf([type][DuckPC.DisplayMode]) -eq 220) 'Native DEVMODEW layout is 220 bytes'
    # Parser checks for all shipping scripts.
    foreach ($p in Get-ChildItem (Split-Path -Parent $module) -Filter '*.ps*') {
        $tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile($p.FullName,[ref]$tokens,[ref]$errors)
        Assert ($errors.Count -eq 0) ('Script parses: ' + $p.Name)
    }
    Write-Host "PASS: $script:checks checks. Organizer tested with real temporary files. Windows UI/registry not executed on Linux."
} finally { if ([IO.Directory]::Exists($temp)) { Remove-Item -LiteralPath $temp -Recurse -Force } }
