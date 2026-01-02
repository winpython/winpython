### WinPython_PS_Prompt.ps1 ###

# $env:PYTHONIOENCODING = "utf-8"

$tmp_dp0 = [System.IO.Path]::GetDirectoryName($myInvocation.MyCommand.Definition)
$tmp_output = & ([System.IO.Path]::Combine(  $tmp_dp0 , "..",  "python" , "python.exe")) ([System.IO.Path]::Combine($tmp_dp0 , "WinPythonIni.py"))

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

    # Set as a PowerShell global variable
    if ($tmp_name -ne "HOME") { Set-Variable -Name $tmp_name -Value $tmp_value }
    Set-Variable -Name $tmp_name -Value $tmp_value -Scope Global -Force
    # set as environment variable for child processes
    Set-Item -Path "Env:\$tmp_name" -Value $tmp_value
    # Write-Host $tmp_name   " = "  $tmp_value

    # If running in GH Actions, also append to GITHUB_ENV so future steps see it
    if ($env:GITHUB_ENV) {
        # Use Add-Content to append "NAME=value" to the GITHUB_ENV file
        # Escape any newlines in $tmp_value to avoid breaking the file format
        $tmp_escapedValue = $tmp_value -replace "`n", '%0A' -replace "`r", ''
        Add-Content -Path $env:GITHUB_ENV -Value "$tmp_name=$tmp_escapedValue"
    }

    #Write-Host "Set `$${name} = $tmp_value"
}

# emulate %__CD%
$tmp_envCD = $env:__CD__
if (($tmp_dp0 -eq $tmp_envCD ) -or ($tmp_dp0 -eq { Join-Path $tmp_envCD 'scripts' }  )) {
        Set-Location -LiteralPath $WINPYWORKDIR1
}

# Clean-up NameSpace
rv tmp_pair
rv tmp_name
rv tmp_value
rv tmp_idx

rv tmp_dp0
rv tmp_output
rv tmp_envCD
