# Builds the RECIPIENT_LIST secret value from newsletter/recipients.txt
# (one address per line, # comments allowed) and copies it to the clipboard.
param([string]$Path = (Join-Path $PSScriptRoot "recipients.txt"))

if (-not (Test-Path $Path)) { Write-Error "Not found: $Path"; exit 1 }

$lines = Get-Content -Path $Path -Encoding UTF8 |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith("#") }

$seen = @{}
$emails = @()
$bad = @()
foreach ($line in $lines) {
    $key = $line.ToLower()
    if ($line -notmatch '^[^@\s,]+@[^@\s,]+\.[^@\s,]+$') { $bad += $line; continue }
    if ($seen.ContainsKey($key)) { Write-Warning "Duplicate skipped: $line"; continue }
    $seen[$key] = $true
    $emails += $line
}

if ($bad.Count -gt 0) {
    Write-Host "Invalid lines - fix these first, nothing was copied:" -ForegroundColor Red
    $bad | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    exit 1
}
if ($emails.Count -eq 0) { Write-Error "No addresses in $Path"; exit 1 }

$emails -join "," | Set-Clipboard
$emails | ForEach-Object { Write-Host "  $_" }
Write-Host ""
Write-Host "Copied $($emails.Count) recipients to the clipboard." -ForegroundColor Green
Write-Host "Next run's log should say: Email sent successfully to $($emails.Count) recipients."
