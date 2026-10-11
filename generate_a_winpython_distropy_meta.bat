cd /D %~dp0
rem  <toml> [315 | 315:slim ...] [--dry-run] [--lock-dir <dir> [--lock-overwrite]]
rem  e.g. --lock-dir winpython\portable\cycle_2026_04 : copies pylock/requir there, never replaces unless --lock-overwrite
call "C:\WinPdev\WPy64-31190\python-3.11.9.amd64\python.exe" %~dp0\build_winpython_meta.py %*
