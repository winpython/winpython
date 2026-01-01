### WinPython_PS_Prompt.ps1 ###

$env:WINPYDIRBASE = [System.IO.Path]::GetDirectoryName($myInvocation.MyCommand.Definition) + "\.."
# get a normalize path
$env:WINPYDIRBASE = [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE )

$env:WINPYDIR = $env:WINPYDIRBASE+ "\" +$env:WINPYthon_subdirectory_name
# 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%python.exe
$env:PYTHON = $env:WINPYDIRBASE+ "\python\python.exe" 

# rem 2023-02-12 try utf-8 on console
$env:PYTHONIOENCODING = "utf-8"

if (-not $env:PATH.ToLower().Contains(";"+ $env:WINPYDIR.ToLower()+ ";"))  {
  $env:PATH = "$env:WINPYDIR\Lib\site-packages\PyQt5;$env:WINPYDIR\;$env:WINPYDIR\DLLs;$env:WINPYDIR\Scripts;$env:WINPYDIR\..\t;$env:WINPYDIR\..\n;$env:path" }

#rem force default pyqt5 kit for Spyder if PyQt5 module is there
if (Test-Path "$env:WINPYDIR\Lib\site-packages\PyQt5\__init__.py") { $env:QT_API = "pyqt5" } 

$output = & $env:PYTHON ($env:WINPYDIRBASE + '\scripts\WinPythonIni.py')
$pairs = $output -split '&&'
$pair = $pair -replace '^(?i)set\s+',''
foreach ($pair in $pairs) {
    $pair = $pair.Trim()
    if ($pair -eq '') { continue }

    # Remove leading "set " (case-insensitive)
    $pair = $pair -replace '^(?i)set\s+',''

    # Find first '=' so values can contain '='
    $idx = $pair.IndexOf('=')
    if ($idx -lt 0) {
        Write-Warning "Skipping invalid pair (no '='): '$pair'"
        continue
    }

    $name  = $pair.Substring(0, $idx).Trim()
    $value = $pair.Substring($idx + 1).Trim()

    # Unquote a quoted value (single or double quotes)
    if ($value -match '^(["''])(.*)\1$') { $value = $Matches[2] }

    # Set as a PowerShell global variable
    Set-Variable -Name $name -Value $value -Scope Global -Force

    # Also set as environment variable for child processes
    $env:name = $value

    # If running in GH Actions, also append to GITHUB_ENV so future steps see it
    if ($env:GITHUB_ENV) {
        # Use Add-Content to append "NAME=value" to the GITHUB_ENV file
        # Escape any newlines in $value to avoid breaking the file format
        $escapedValue = $value -replace "`n", '%0A' -replace "`r", ''
        Add-Content -Path $env:GITHUB_ENV -Value "$name=$escapedValue"
    }

    #Write-Host "Set `$${name} = $value"
}

# directory of the running script (fallback to MyInvocation for older hosts)
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Definition }

# emulate %__CD% and build scripts\ path
$envCD = Normalize-DirPath $env:__CD__
$scriptsPath = if ($envCD) { Join-Path $envCD 'scripts' } else { $null }

# target to change into (environment variable WINPYWORKDIR1)
$target = $WINPYWORKDIR1

if ($target) {
    if ($scriptsPath -and $scriptDir -and ($scriptsPath -eq $scriptDir)) {
        Set-Location -LiteralPath $target
    }
    elseif ($envCD -and $scriptDir -and ($envCD -eq $scriptDir)) {
        Set-Location -LiteralPath $target
    }
}