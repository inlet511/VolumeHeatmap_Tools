param([string]$HoudiniPreferences = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'houdini20.5'))
$ErrorActionPreference = 'Stop'
$packageDirectory = Join-Path $HoudiniPreferences 'packages'
New-Item -ItemType Directory -Path $packageDirectory -Force | Out-Null
$packageFile = Join-Path $packageDirectory 'volumeheatmap_exporter.json'
if (Test-Path -LiteralPath $packageFile) {
    Copy-Item -LiteralPath $packageFile -Destination ($packageFile + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$pluginRoot = $PSScriptRoot.Replace('\', '/')
$package = @{ enable = $true; hpath = $pluginRoot }
$json = $package | ConvertTo-Json
[System.IO.File]::WriteAllText($packageFile, $json, [System.Text.UTF8Encoding]::new($false))
Write-Output "Installed package: $packageFile"
Write-Output 'Restart Houdini, enable the VolumeHeatmap shelf, and click Pyro Exporter.'
