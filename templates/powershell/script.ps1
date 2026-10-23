param([Parameter(Mandatory = $true)][string]$Path, [switch]$Help)
if ($Help) { Write-Output "Usage: script.ps1 -Path DIRECTORY"; exit 0 }
if (-not (Test-Path -LiteralPath $Path -PathType Container)) { throw "Directory not found" }
Get-ChildItem -LiteralPath $Path -File | Select-Object Name, Length | ConvertTo-Json
