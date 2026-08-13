cd /D %~dp0
rem  <toml> [315 | 315:slim ...] [--dry-run]
call "C:\WinPdev\WPy64-31190\python-3.11.9.amd64\python.exe" %~dp0\build_winpython_meta.py %*
