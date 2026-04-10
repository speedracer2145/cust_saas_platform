# Helper script to check and free port 8000

Write-Host "Checking port 8000..." -ForegroundColor Cyan

$connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connection) {
    $pid = $connection.OwningProcess
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "Port 8000 is in use by:" -ForegroundColor Yellow
        Write-Host "  Process ID: $pid" -ForegroundColor Yellow
        Write-Host "  Process Name: $($process.ProcessName)" -ForegroundColor Yellow
        Write-Host "  Path: $($process.Path)" -ForegroundColor Yellow
        
        $response = Read-Host "Do you want to stop this process? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Stop-Process -Id $pid -Force
            Write-Host "Process stopped. Port 8000 is now free." -ForegroundColor Green
        } else {
            Write-Host "Process not stopped. Please use a different port or stop the process manually." -ForegroundColor Red
        }
    }
} else {
    Write-Host "Port 8000 is free!" -ForegroundColor Green
}

