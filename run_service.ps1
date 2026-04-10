# PowerShell script to run start_service.py with the specified Python path
# Usage: .\run_service.ps1 [arguments]

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$PythonPath = "python"

if (-not (Get-Command $PythonPath -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $(Get-Command $PythonPath | Select-Object -ExpandProperty Source)" -ForegroundColor Green

# Set UTF-8 encoding for Python output
$env:PYTHONIOENCODING = "utf-8"

$Script = "start_service.py"

if (-not (Test-Path $Script)) {
    Write-Host "Error: Script not found: $Script" -ForegroundColor Red
    exit 1
}

# Run the script with arguments and capture exit code
try {
    & $PythonPath $Script $Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Host "`nError: Script exited with code $exitCode" -ForegroundColor Red
        exit $exitCode
    }
} catch {
    Write-Host "`nError: Failed to run script: $_" -ForegroundColor Red
    exit 1
}

