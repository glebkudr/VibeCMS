# PowerShell script to automate frontend build/dev and docker-compose restart
param()

$ErrorActionPreference = 'Stop'

$frontendDir = "admin_app/frontend"
$projectRoot = Get-Location

Write-Host "[INFO] Killing old 'npm run dev' or 'vite' processes..."
Get-Process | Where-Object { $_.Path -and ($_.Path -like "*npm*" -or $_.Path -like "*node*") -and ($_.StartInfo.Arguments -like "*run dev*" -or $_.StartInfo.Arguments -like "*vite*") } | ForEach-Object { try { Stop-Process -Id $_.Id -Force } catch {} }

Set-Location $frontendDir

Write-Host "[INFO] Building frontend..."
npm run build

Write-Host "[INFO] Starting 'npm run dev' in background..."
Start-Process -FilePath "npm" -ArgumentList "run dev" -WindowStyle Hidden

Set-Location $projectRoot

Write-Host "[INFO] Running docker-compose..."
docker-compose --env-file .env.dev up --build -d

Write-Host "[SUCCESS] All done!" 