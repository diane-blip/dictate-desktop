# Creates a local environment; never starts Dictate or adds startup persistence.
[CmdletBinding()]
param([string]$Python = '')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        if ($Python) { & $Python -m venv .venv } else { & py -3.12 -m venv .venv }
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 with its py launcher first.' }
    }
    & .\.venv\Scripts\python.exe -c "import sys,struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8, 'Use 64-bit Python 3.12 for this release'"
    if ($LASTEXITCODE -ne 0) { throw 'The existing .venv is not Python 3.12.' }
    & .\.venv\Scripts\python.exe -m pip install pip==26.2.1
    if ($LASTEXITCODE -ne 0) { throw 'Package installer update failed.' }
    & .\.venv\Scripts\python.exe -m pip install --only-binary=:all: --require-hashes -r requirements.lock
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & .\.venv\Scripts\python.exe -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency verification failed.' }
    if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
    if (-not (Test-Path -LiteralPath 'config.local.toml')) {
        Set-Content -LiteralPath 'config.local.toml' -Encoding ascii -Value '# Override settings from config.toml here.'
    }
    Write-Host 'Installed. Add your API key to .env, then run .\.venv\Scripts\python.exe dictate.py'
} finally {
    Pop-Location
}
