### WinPython_PS_Prompt.ps1 ###
$0 = $myInvocation.MyCommand.Definition
$dp0 = [System.IO.Path]::GetDirectoryName($0)

# default if env.cfg fails
$env:WINPYthon_subdirectory_name = "python"
$env:WINPYthon_exe = "python.exe"
# Define the path to the config file
Get-Content (${PSScriptRoot} +"\env.ini") | ForEach-Object {
    $parts = $_ -split '=', 2
    if ($parts.Count -eq 2) {
        Set-Variable -Name ($parts[0]).Trim() -Value $parts[1].Trim() -Scope Global
    }
}

# $env:PYTHONUTF8 = 1 would create issues in "movable" patching
$env:WINPYDIRBASE = "$dp0\.."
# get a normalize path
# http://stackoverflow.com/questions/1645843/resolve-absolute-path-from-relative-path-and-or-file-name
$env:WINPYDIRBASE = [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE )

# avoid double_init (will only resize screen)
if (-not ($env:WINPYDIR -eq [System.IO.Path]::GetFullPath( $env:WINPYDIRBASE+"\{self.python_dir_name}")) ) {
$env:WINPYDIR = $env:WINPYDIRBASE+ "\" +$env:WINPYthon_subdirectory_name
# 2019-08-25 pyjulia needs absolutely a variable PYTHON=%WINPYDIR%python.exe
$env:PYTHON = $env:WINPYthon_exe
$env:PYTHONPATHz = "%WINPYDIR%;%WINPYDIR%\Lib;%WINPYDIR%\DLLs"

$env:WINPYVER = $env:WINPYVER
# rem 2023-02-12 try utf-8 on console
# rem see https://github.com/pypa/pip/issues/11798#issuecomment-1427069681
$env:PYTHONIOENCODING = "utf-8"

$env:HOME = "$env:WINPYDIRBASE\settings"

# rem read https://github.com/winpython/winpython/issues/839
# $env:USERPROFILE = "$env:HOME"

$env:WINPYDIRBASE = ""
$env:JUPYTER_DATA_DIR = "$env:HOME"

if (-not $env:PATH.ToLower().Contains(";"+ $env:WINPYDIR.ToLower()+ ";"))  {
  $env:PATH = "$env:WINPYDIR\\Lib\site-packages\PyQt5;$env:WINPYDIR\\;$env:WINPYDIR\\DLLs;$env:WINPYDIR\\Scripts;$env:WINPYDIR\\..\t;$env:WINPYDIR\\..\n;$env:path" }


#rem force default pyqt5 kit for Spyder if PyQt5 module is there
if (Test-Path "$env:WINPYDIR\Lib\site-packages\PyQt5\__init__.py") { $env:QT_API = "pyqt5" } 

# PyQt5 qt.conf creation and winpython.ini creation done via Winpythonini.py (called per env_for_icons.bat for now)
# Start-Process -FilePath $env:PYTHON -ArgumentList ($env:WINPYDIRBASE + '\scripts\WinPythonIni.py')


### Set-WindowSize

Function Set-WindowSize {
Param([int]$x=$host.ui.rawui.windowsize.width,
      [int]$y=$host.ui.rawui.windowsize.heigth,
      [int]$buffer=$host.UI.RawUI.BufferSize.heigth)
    $buffersize = new-object System.Management.Automation.Host.Size($x,$buffer)
    $host.UI.RawUI.BufferSize = $buffersize
    $size = New-Object System.Management.Automation.Host.Size($x,$y)
    $host.ui.rawui.WindowSize = $size
}
# Windows10 yelling at us with 150 40 6000
# Set-WindowSize 195 40 6000 

### Colorize to distinguish
$host.ui.RawUI.BackgroundColor = "Black"
$host.ui.RawUI.ForegroundColor = "White"
}
