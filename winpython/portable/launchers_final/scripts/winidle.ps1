# The '.' so variables stay in this session
. (Join-Path ([System.IO.Path]::GetDirectoryName($myInvocation.MyCommand.Definition)) "WinPython_PS_Prompt.ps1") $Args
$flatArgs = @("-m", "idlelib") + ($args | ForEach-Object { "`"$_`"" })

#& (Join-Path $env:WINPYDIR "python.exe")  $flatArgs
Start-Process -FilePath (Join-Path $env:WINPYDIR "pythonw.exe") -ArgumentList $flatArgs -WindowStyle Hidden
