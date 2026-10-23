#requires -Version 5.1
param([string]$Name = "*", [switch]$Help)
if ($Help) {
  Write-Output "Usage: windows-services-report.ps1 [-Name PATTERN] [-Help]"
  exit 0
}
try {
  $services = @(Get-Service -Name $Name -ErrorAction Stop | Select-Object Name, DisplayName, Status)
  ConvertTo-Json -InputObject $services -Depth 4
} catch {
  Write-Error $_
  exit 2
}
