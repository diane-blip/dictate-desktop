# Optional shortcuts only. Does not install packages or start Dictate.
[CmdletBinding(SupportsShouldProcess)]
param([switch]$Remove)
$ErrorActionPreference = 'Stop'
$appDir = $PSScriptRoot
$python = Join-Path $appDir '.venv\Scripts\pythonw.exe'
$script = Join-Path $appDir 'dictate.py'
$legacyLauncher = Join-Path $appDir 'start-dictate.vbs'
if (-not $Remove -and -not (Test-Path -LiteralPath $python)) {
    throw 'Run install.ps1 before creating shortcuts.'
}
$shell = New-Object -ComObject WScript.Shell
$shortcuts = foreach ($folder in @('Startup', 'Desktop')) {
    $path = Join-Path ([Environment]::GetFolderPath($folder)) 'Dictate.lnk'
    $shortcut = $shell.CreateShortcut($path)
    $exists = Test-Path -LiteralPath $path
    $ours = $shortcut.TargetPath -eq $python -or $shortcut.TargetPath -eq $legacyLauncher -or (
        $shortcut.TargetPath -eq (Join-Path $env:WINDIR 'System32\wscript.exe') -and
        $shortcut.Arguments -eq ('"' + $legacyLauncher + '"')
    )
    if ($exists -and -not $ours) {
        throw "A Dictate shortcut from another installation exists at $path. No shortcuts were changed."
    }
    [pscustomobject]@{ Path = $path; Shortcut = $shortcut; Exists = $exists }
}
# Validate every destination before changing any of them.
foreach ($entry in $shortcuts) {
    if ($Remove) {
        if ($entry.Exists -and $PSCmdlet.ShouldProcess($entry.Path, 'Remove shortcut')) {
            Remove-Item -LiteralPath $entry.Path
        }
    } elseif ($PSCmdlet.ShouldProcess($entry.Path, 'Create shortcut')) {
        $shortcut = $entry.Shortcut
        $shortcut.TargetPath = $python
        $shortcut.Arguments = '"' + $script + '"'
        $shortcut.WorkingDirectory = $appDir
        $shortcut.IconLocation = (Join-Path $appDir 'dictate.ico') + ',0'
        $shortcut.Description = 'Dictate: hold to speak'
        $shortcut.Save()
    }
}
