### WinPython_PS_Prompt.ps1 ###

# $env:PYTHONIOENCODING = "utf-8"

$tmp_dp0 = [System.IO.Path]::GetDirectoryName($myInvocation.MyCommand.Definition)
$tmp_output = & ([System.IO.Path]::Combine(  $tmp_dp0 , "..",  "python" , "python.exe")) ([System.IO.Path]::Combine($tmp_dp0 , "WinPythonIni.py")) $args

foreach ($tmp_pair in ($tmp_output -split '&&')) {
    $tmp_pair = $tmp_pair.Trim()
    if ($tmp_pair -eq '') { continue }

    # Remove leading "set " (case-insensitive)
    $tmp_pair = $tmp_pair -replace '^(?i)set\s+',''

    # Find first '=' so values can contain '='
    $tmp_idx = $tmp_pair.IndexOf('=')
    if ($tmp_idx -lt 0) {
        Write-Warning "Skipping invalid pair (no '='): '$tmp_pair'"
        continue
    }

    $tmp_name  = $tmp_pair.Substring(0, $tmp_idx).Trim()
    $tmp_value = $tmp_pair.Substring($tmp_idx + 1).Trim()

    # Unquote a quoted value (single or double quotes)
    if ($tmp_value -match '^(["''])(.*)\1$') { $tmp_value = $Matches[2] }

    # set as environment variable for child processes like python
    Set-Item -Path "Env:\$tmp_name" -Value $tmp_value
    #Write-Host $tmp_name   " = "  $tmp_value
}

# emulate %__CD%
$tmp_envCD = $env:__CD__.TrimEnd('\')
$tmp_envCDscript = ( Join-Path $tmp_envCD 'scripts' )
if (($tmp_dp0 -eq $tmp_envCD ) -or ($tmp_dp0 -eq ( Join-Path $tmp_envCD 'scripts' )  )) {
        Set-Location -LiteralPath $env:WINPYWORKDIR1
}

# Clean-up NameSpace
rv tmp_pair
rv tmp_name
rv tmp_value
rv tmp_idx

rv tmp_dp0
rv tmp_output
rv tmp_envCD
