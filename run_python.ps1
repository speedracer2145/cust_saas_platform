# PowerShell script to run Python scripts with the specified Python path
# Usage: .\run_python.ps1 <script_name> [arguments]

param(
    [Parameter(Mandatory=$true)]
    [string]$Script,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$PythonPath = "python"

if (-not (Get-Command $PythonPath -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $(Get-Command $PythonPath | Select-Object -ExpandProperty Source)" -ForegroundColor Green

if (-not (Test-Path $Script)) {
    Write-Host "Error: Script not found: $Script" -ForegroundColor Red
    exit 1
}

# Run the script with arguments
& $PythonPath $Script $Arguments

