call "%~dp0env_for_icons.bat"
"%PYTHON%" -c "from winpython.utils import patch_sourcefile;patch_sourcefile(r'%~dp0..\settings\winpython.ini', '[active_environment', '[inactive_environment' )"
