/* WinPython launcher template script
Copyright © 2012 Pierre Raybaut
Licensed under the terms of the MIT License
(see winpython/__init__.py for details)
*/
;================================================================
; These lines are automatically filled when winpython/make.py creates launchers:
!addincludedir ""
!define COMMAND ""
!define PARAMETERS ""
!define WORKDIR ""
Icon ""
OutFile ""
;================================================================
# Standard NSIS plugins
!include "WordFunc.nsh"
!include "FileFunc.nsh"

SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow
RequestExecutionLevel user

Section ""
Call Execute
SectionEnd

Function Execute
;Set working Directory ===========================
StrCmp ${WORKDIR} "" 0 workdir
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
Goto end_workdir
workdir:
SetOutPath "${WORKDIR}"
end_workdir:
;Get Command line parameters =====================
${GetParameters} $R1
StrCmp "${PARAMETERS}" "" end_param 0
StrCpy $R1 "${PARAMETERS} $R1"
end_param:
;===== Execution =================================
Exec '"${COMMAND}" $R1'
FunctionEnd