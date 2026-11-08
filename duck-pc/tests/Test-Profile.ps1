$ErrorActionPreference='Stop'
$modulePath=Join-Path $PSScriptRoot '../src/DuckPC.Core.psm1'
if (!(Test-Path -LiteralPath $modulePath)) { $modulePath=Join-Path $PSScriptRoot '../DuckPC.Core.psm1' }
Import-Module $modulePath -Force -DisableNameChecking
$loadedModule=Get-Module DuckPC.Core
$script:profileChecks=0
function Assert-Profile($Value,$Message) { $script:profileChecks++;if (!$Value) { throw "FAILED: $Message" } }
# Isolate Windows-only registry I/O, while exercising real profile state,
# idempotency, backup-path validation and persisted JSON on temporary files.
& $loadedModule {
    $script:FakeValues=@{};$script:ApplyCalls=0;$script:FailNext=$false
    function script:Get-DuckOwnerSid { return 'test-owner' }
    function script:Get-DuckRegistrySnapshot($Path,$Name) {
        $k=$Path+'|'+$Name
        if ($script:FakeValues.ContainsKey($k)) { return $script:FakeValues[$k] }
        return [pscustomobject]@{Exists=$false;Value=$null;Kind=''}
    }
    function script:Invoke-DuckTuning([string[]]$Options,[string]$JournalDirectory) {
        $script:ApplyCalls++;$entries=@();$failed=0
        foreach ($i in @(Get-DuckTuningPlan $Options)) {
            $key=$i.Path+'|'+$i.Name;$old=Get-DuckRegistrySnapshot $i.Path $i.Name
            $entry=[pscustomobject]@{Path=$i.Path;Name=$i.Name;Value=$i.Value;Kind=$i.Kind;Existed=$old.Exists;OldValue=$old.Value;OldKind=$old.Kind;Status='Applied'}
            if ($script:FailNext) { $failed++;$entry.Status='Failed';$script:FailNext=$false }
            else { $script:FakeValues[$key]=[pscustomobject]@{Exists=$true;Value=$i.Value;Kind=$i.Kind} }
            $entries+=$entry
        }
        $journal=Join-Path $JournalDirectory ('ajustes-'+[guid]::NewGuid().ToString('N')+'.json')
        Write-DuckJson $journal $entries
        return [pscustomobject]@{Journal=$journal;Applied=$entries.Count-$failed;Failed=$failed}
    }
    function script:Undo-DuckTuning([string]$JournalPath) {
        $entries=@(Get-Content -LiteralPath $JournalPath -Raw -Encoding UTF8|ConvertFrom-Json)
        $restored=0;$skipped=0
        foreach ($e in $entries) {
            $key=$e.Path+'|'+$e.Name;$now=Get-DuckRegistrySnapshot $e.Path $e.Name
            if (!$now.Exists -or [string]$now.Value -ne [string]$e.Value -or $now.Kind -ne $e.Kind) { $skipped++;continue }
            if ($e.Existed) { $script:FakeValues[$key]=[pscustomobject]@{Exists=$true;Value=$e.OldValue;Kind=$e.OldKind} }
            else { $script:FakeValues.Remove($key) }
            $restored++
        }
        return [pscustomobject]@{Restored=$restored;Skipped=$skipped}
    }
}
$temp=Join-Path ([IO.Path]::GetTempPath()) ('duckpc-profile-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temp)|Out-Null
try {
    $history=Join-Path $temp 'Historico';$statePath=Join-Path $temp 'perfil-ativo.json'
    $r=Invoke-DuckRecommendedProfile $statePath $history
    Assert-Profile ($r.Status -eq 'Applied' -and $r.Applied -eq 16) 'One click applies the complete 16-value profile'
    $firstBackup=$r.Journal;$firstHash=(Get-FileHash -LiteralPath $firstBackup).Hash
    Assert-Profile ((Test-Path -LiteralPath $statePath) -and (Test-Path -LiteralPath $firstBackup)) 'Profile state and original backup persist'
    $r=Invoke-DuckRecommendedProfile $statePath $history
    Assert-Profile ($r.Status -eq 'AlreadyApplied' -and (& $loadedModule {$script:ApplyCalls}) -eq 1) 'Repeated click performs no writes or new tuning'
    Assert-Profile ($r.Journal -eq $firstBackup -and (Get-FileHash -LiteralPath $firstBackup).Hash -eq $firstHash) 'Original backup remains unchanged'
    & $loadedModule { $script:FakeValues['Software\Microsoft\GameBar|AutoGameModeEnabled'].Value=99 }
    $r=Invoke-DuckRecommendedProfile $statePath $history
    Assert-Profile ($r.Status -eq 'ChangedExternally' -and (& $loadedModule {$script:ApplyCalls}) -eq 1) 'External drift detected without reapplying'
    Assert-Profile ((& $loadedModule {$script:FakeValues['Software\Microsoft\GameBar|AutoGameModeEnabled'].Value}) -eq 99) 'External preferences preserved'
    $r=Undo-DuckRecommendedProfile $statePath $history
    Assert-Profile ($r.Status -eq 'Restored' -and $r.Restored -eq 15 -and $r.Skipped -eq 1) 'Whole profile restore uses original backup and preserves drift'
    $r=Undo-DuckRecommendedProfile $statePath $history
    Assert-Profile ($r.Status -eq 'NoProfile') 'Restore is idempotent'
    $r=Invoke-DuckRecommendedProfile $statePath $history
    Assert-Profile ($r.Status -eq 'Applied' -and $r.Journal -ne $firstBackup) 'Explicit reapply after restore creates new baseline'
    # Wrong owner and tampered backup paths must not be accepted.
    $state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
    $originalJournal=$state.BaselineJournal;$state.OwnerSid='another-user'
    $state|ConvertTo-Json|Set-Content -LiteralPath $statePath -Encoding UTF8
    $threw=$false;try { Invoke-DuckRecommendedProfile $statePath $history|Out-Null } catch {$threw=$true}
    Assert-Profile $threw 'Another user profile rejected'
    $state.OwnerSid='test-owner';$state.BaselineJournal=Join-Path $temp 'outside.json'
    $state|ConvertTo-Json|Set-Content -LiteralPath $statePath -Encoding UTF8
    $threw=$false;try { Undo-DuckRecommendedProfile $statePath $history|Out-Null } catch {$threw=$true}
    Assert-Profile $threw 'Backup path outside history rejected'
    $state.BaselineJournal=$originalJournal;$state|ConvertTo-Json|Set-Content -LiteralPath $statePath -Encoding UTF8
    [void](Undo-DuckRecommendedProfile $statePath $history)
    & $loadedModule { $script:FakeValues=@{};$script:FailNext=$true }
    $partialState=Join-Path $temp 'partial.json'
    $r=Invoke-DuckRecommendedProfile $partialState $history
    Assert-Profile ($r.Status -eq 'Partial' -and $r.Failed -eq 1 -and !(Test-Path -LiteralPath $partialState)) 'Partial failure is not advertised as optimized'
    Assert-Profile (Test-Path -LiteralPath $r.Journal) 'Partial operation keeps rollback history'
    & $loadedModule {
        foreach ($i in @(Get-DuckTuningPlan @('Suggestions','Copilot','GameMode','Visuals'))) { $script:FakeValues[$i.Path+'|'+$i.Name]=[pscustomobject]@{Exists=$true;Value=$i.Value;Kind=$i.Kind} }
    }
    $before=& $loadedModule {$script:ApplyCalls}
    $r=Invoke-DuckRecommendedProfile (Join-Path $temp 'no-baseline.json') $history
    Assert-Profile ($r.Status -eq 'AlreadyConfigured' -and (& $loadedModule {$script:ApplyCalls}) -eq $before) 'Already configured PC is not retuned'
    Write-Host "PASS: $script:profileChecks profile checks, Windows I/O mocked; real temporary state/history tested."
} finally { Remove-Item -LiteralPath $temp -Recurse -Force }
