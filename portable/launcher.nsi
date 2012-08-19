/*

WinPython launcher template script

Copyright © 2012 Pierre Raybaut
Licensed under the terms of the MIT License
(see winpython/__init__.py for details)
 
*/

!include "FileFunc.nsh"

;================================================================
; These lines are automatically replaced when creating launchers:
; (see winpython/make.py)
!define WINPYDIR ""
!define COMMAND ""
!define PARAMETERS ""
!define WORKDIR ""
!define PREPATH ""
!define POSTPATH ""
Icon ""
OutFile ""
;================================================================

SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow

Section ""
Call Execute
SectionEnd

Function Execute
StrCmp ${WORKDIR} "" 0 workdir
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
Goto endworkdir
workdir:
SetOutPath "${WORKDIR}"
endworkdir:

System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDIR", "${WINPYDIR}").r0'
CreateDirectory "$EXEDIR\settings\AppData\Roaming"
CreateDirectory "$EXEDIR\settings\Application Data"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("USERPROFILE", "$EXEDIR\settings").r0'
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("APPDATA", "$EXEDIR\settings\AppData\Roaming").r0'
ReadEnvStr $R0 "PATH"
StrCpy $R0 "${PREPATH};$R0;${POSTPATH}"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PATH", R0).r0'

StrCmp "${PARAMETERS}" "" 0 param
${GetParameters} $R1
Goto endparam
param:
StrCpy $R1 "${PARAMETERS}"
endparam:

Exec '"${COMMAND}" $R1'
FunctionEnd