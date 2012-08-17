; Copyright © 2012 Pierre Raybaut
; Licensed under the terms of the MIT License
; (see winpython/__init__.py for details)

!include "FileFunc.nsh"

; The following lines are automatically replaced when creating launchers:
!define WINPYDIR "$EXEDIR\python-2.7.3.amd64"
!define COMMAND "${WINPYDIR}\python.exe"
!define PREPATH "${WINPYDIR}\Lib\site-packages\PyQt4"
!define POSTPATH "${WINPYDIR}\;${WINPYDIR}\DLLs;${WINPYDIR}\Scripts;${WINPYDIR}\..\tools;${WINPYDIR}\..\tools\gnuwin32\bin;${WINPYDIR}\..\tools\TortoiseHg-x64"
Icon "icons\python.ico"
OutFile "python.exe"

SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow

Section ""
Call Execute
SectionEnd

Function Execute
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDIR", "${WINPYDIR}").r0'
ReadEnvStr $R0 "PATH"
StrCpy $R0 "${PREPATH};$R0;${POSTPATH}"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PATH", R0).r0'
${GetParameters} $R1
Exec '"${COMMAND}" $R1'
FunctionEnd