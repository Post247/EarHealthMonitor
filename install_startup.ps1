# Creates (or refreshes) the Windows Startup shortcut so Ear Health Monitor
# launches automatically at login. Idempotent — safe to run repeatedly.
#
# Usage:  powershell -ExecutionPolicy Bypass -File install_startup.ps1

$ErrorActionPreference = "Stop"

$appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = (Get-Command pythonw -ErrorAction Stop).Source
$startup = [Environment]::GetFolderPath('Startup')
$lnk = Join-Path $startup "EarHealthMonitor.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = $pythonw
$sc.Arguments = "app.py"
$sc.WorkingDirectory = $appDir
$sc.Description = "Ear Health Monitor - starts at login"
$sc.WindowStyle = 1
$sc.Save()

Write-Host "Startup shortcut installed: $lnk"
Write-Host "Target: $pythonw app.py (workdir $appDir)"

# Remove with:  Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\EarHealthMonitor.lnk"