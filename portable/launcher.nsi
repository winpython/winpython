/*

WinPython launcher template script

Copyright © 2012 Pierre Raybaut
Licensed under the terms of the MIT License
(see winpython/__init__.py for details)
 
*/

;================================================================
; These lines are automatically replaced when creating launchers:
; (see winpython/make.py)
!addincludedir ""
!define WINPYDIR ""
!define WINPYVER ""
!define COMMAND ""
!define PARAMETERS ""
!define WORKDIR ""
!define PREPATH ""
!define POSTPATH ""
!define SETTINGSDIR ""
!define SETTINGSNAME ""
Icon ""
OutFile ""
;================================================================

# Standard NSIS plugins
!include "WordFunc.nsh"
!include "FileFunc.nsh"
!include "TextReplace.nsh"

# Custom NSIS plugins
!include "ReplaceInFileWithTextReplace.nsh"
!include "EnumIni.nsh"

SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow
RequestExecutionLevel user

Section ""
Call Execute
SectionEnd

Function Execute
StrCmp ${WORKDIR} "" 0 workdir
System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
SetOutPath $0
Goto end_workdir
workdir:
SetOutPath "${WORKDIR}"
end_workdir:

System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDIR", "${WINPYDIR}").r0'
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYVER", "${WINPYVER}").r0'


;================================================================
; Settings directory
IfFileExists "$EXEDIR\settings\*.*" 0 end_settings
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("HOME", "$EXEDIR\settings").r0'
StrCmp "${SETTINGSDIR}" "" end_settings
CreateDirectory "$EXEDIR\settings\${SETTINGSDIR}"
; Handle portability in Spyder's settings
StrCpy $R5 "$EXEDIR\settings\${SETTINGSDIR}\${SETTINGSNAME}"
ReadINIStr $0 $R5 "main" last_drive
${GetRoot} $EXEDIR $1
StrCmp $0 "" write_settings
StrCmp $0 $1 end_settings
${ReplaceInFile} $R5 "$0\\" "$1\\"
write_settings:
WriteINIStr $R5 "main" last_drive $1
end_settings:
;================================================================


; WinPython settings
IfFileExists "$EXEDIR\settings\*.*" 0 winpython_settings_profile
StrCpy $R6 "$EXEDIR\settings\winpython.ini"
Goto winpython_settings_continue
winpython_settings_profile:
StrCpy $R6 "$PROFILE\winpython.ini"
winpython_settings_continue:
IfFileExists $R6 winpython_settings_done
ClearErrors
FileOpen $0 $R6 w
IfErrors winpython_settings_done
FileWrite $0 "[debug]$\r$\nstate = disabled"
FileWrite $0 "$\r$\n"
FileWrite $0 "$\r$\n[environment]"
FileWrite $0 "$\r$\n## <?> Uncomment lines to override environment variables"
FileWrite $0 "$\r$\n#PATH = "
FileWrite $0 "$\r$\n#PYTHONPATH = "
FileWrite $0 "$\r$\n#PYTHONSTARTUP = "
FileClose $0
winpython_settings_done:


; Debug state
IfFileExists $R6 0 no_debug
ReadINIStr $R7 $R6 "debug" "state"
StrCmp $R7 "" no_debug
StrCmp $R7 "disabled" no_debug
StrCpy $R7 "enabled"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("WINPYDEBUG", "True").r0'
no_debug:


;================================================================
; Environment variables
ReadEnvStr $R0 "PATH"

IfFileExists $R6 0 envvar_done
StrCpy $R9 0
envvar_loop:
    ${EnumIniValue} $1 $R6 "environment" $R9
    StrCmp $1 "" envvar_done
    IntOp $R9 $R9 + 1
    ReadINIStr $2 $R6 "environment" $1

    ${StrFilter} $1 "+" "" " " $1 ; Upper case + remove trailing spaces
    StrCmp $1 "PATH" found_path
    System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("$1", "$2").r0'
    Goto end_found_path

    found_path:
    StrCpy $R0 $2
    StrCmp $R7 "disabled" end_found_path
    MessageBox MB_OK|MB_ICONINFORMATION "Found PATH=$2"
    end_found_path:

    StrCmp $R7 "disabled" envvar_loop
    MessageBox MB_YESNO|MB_ICONQUESTION "$R9: Name='$1'$\nValue='$2'$\n$\n$\nMore?" IDYES envvar_loop
envvar_done:

StrCpy $R0 "${PREPATH};$R0;${POSTPATH}"
System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PATH", R0).r0'
;================================================================


; Command line parameters
${GetParameters} $R1
StrCmp "${PARAMETERS}" "" end_param 0
StrCpy $R1 "${PARAMETERS} $R1"
end_param:

Exec '"${COMMAND}" $R1'
FunctionEnd