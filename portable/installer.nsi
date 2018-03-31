/*

WinPython installer script

Copyright © 2012 Pierre Raybaut
Licensed under the terms of the MIT License
(see winpython/__init__.py for details)
 
*/

;================================================================
; These lines are automatically replaced when creating installer:
; (see winpython/make.py)
!define DISTDIR "D:\Pierre\maketest\winpython-2.7.3.amd64"
!define ARCH "16bit"
!define VERSION "2.7.3.0"
!define RELEASELEVEL "beta2" ; empty means final release
;================================================================

!define ID "WinPython"
!define ID_INSTALL "WinPy"
!define FILE_DESCRIPTION "${ID} Installer"
!define COMPANY "${ID}"
!define BRANDING "${ID}, the portable Python Distribution for Scientists"

SetCompressor /SOLID LZMA
SetCompressorDictSize 16 ; MB

; Includes
;------------------------------------------------------------------------------
!include "MUI2.nsh"
!include "Sections.nsh"
!include "FileFunc.nsh"

; General
;------------------------------------------------------------------------------
Name "${ID} ${ARCH} ${VERSION}${RELEASELEVEL}"
OutFile "${DISTDIR}\..\${ID}${ARCH}-${VERSION}${RELEASELEVEL}.exe"

; 2018-03-31 need to minimize path length of installation:
;InstallDir "$EXEDIR\${ID}${ARCH}-${VERSION}${RELEASELEVEL}"
InstallDir "$EXEDIR\${ID_INSTALL}${ARCH}-${VERSION}${RELEASELEVEL}"
BrandingText "${BRANDING}"
XPStyle on
RequestExecutionLevel user

; Interface Configuration
;------------------------------------------------------------------------------
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "images\banner.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "images\banner.bmp"
!define MUI_ABORTWARNING
!define MUI_ICON "icons\install.ico"

; Pages
;------------------------------------------------------------------------------
!define MUI_WELCOMEFINISHPAGE_BITMAP "images\win.bmp"
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_REBOOTLATER_DEFAULT
#!define MUI_FINISHPAGE_RUN "$INSTDIR\${ID}.exe"
!define MUI_FINISHPAGE_LINK "Visit ${ID} official website"
!define MUI_FINISHPAGE_LINK_LOCATION "http://winpython.github.io/"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
;------------------------------------------------------------------------------
Section "" SecWinPython
    SectionIn RO
    SetOutPath "$INSTDIR"
    File /r "${DISTDIR}\*.*"
SectionEnd

; Functions
;------------------------------------------------------------------------------
Function .onInit
    ; Check if an instance of this installer is already running
    System::Call 'kernel32::CreateMutexA(i 0, i 0, t "${ID}") i .r1 ?e'
    Pop $R0
    StrCmp $R0 0 +3
        MessageBox MB_OK|MB_ICONEXCLAMATION "Installer is already running."
        Abort
    
    InitPluginsDir
    File /oname=$PLUGINSDIR\splash.bmp "images\splash.bmp"
    advsplash::show 1000 600 400 -1 $PLUGINSDIR\splash
    Delete $PLUGINSDIR\splash.bmp
FunctionEnd

; Descriptions
;------------------------------------------------------------------------------
VIAddVersionKey "ProductName" "${ID}"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "LegalCopyright" "Copyright © 2012 Pierre RAYBAUT"
VIAddVersionKey "FileDescription" "${FILE_DESCRIPTION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIProductVersion "${VERSION}"
