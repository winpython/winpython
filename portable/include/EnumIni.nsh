/*
    @FILENAME   = EnumIni.nsh
    @AUTHORS    = Zinthose, Iceman_K
    @REVISIONS  = zenpoy[http://forums.winamp.com/member.php?u=401997]
    @URL        = http://nsis.sourceforge.net/mediawiki/index.php?title=Enumerate_INI
*/
!ifndef __EnumIni__
!define __EnumIni__

    ## Includes
        !include "TextFunc.nsh"
        !ifndef StrLoc
            !include "StrFunc.nsh"
            ${StrLoc}
        !endif
    
    ## Macro to remove leading and trailing whitespaces from a string.
    ## Derived from the function originaly posted by Iceman_K at: 
    ##  http://nsis.sourceforge.net/Remove_leading_and_trailing_whitespaces_from_a_string
        !ifmacrondef _Trim
            !macro _Trim _UserVar _OriginalString
                !define Trim_UID ${__LINE__}
                
                Push $R1
                Push $R2
                Push `${_OriginalString}`
                Pop $R1
                
                Loop_${Trim_UID}:
                    StrCpy $R2 "$R1" 1
                    StrCmp "$R2" " " TrimLeft_${Trim_UID}
                    StrCmp "$R2" "$\r" TrimLeft_${Trim_UID}
                    StrCmp "$R2" "$\n" TrimLeft_${Trim_UID}
                    StrCmp "$R2" "$\t" TrimLeft_${Trim_UID}
                    GoTo Loop2_${Trim_UID}
                TrimLeft_${Trim_UID}:   
                    StrCpy $R1 "$R1" "" 1
                    Goto Loop_${Trim_UID}
             
                Loop2_${Trim_UID}:
                    StrCpy $R2 "$R1" 1 -1
                    StrCmp "$R2" " " TrimRight_${Trim_UID}
                    StrCmp "$R2" "$\r" TrimRight_${Trim_UID}
                    StrCmp "$R2" "$\n" TrimRight_${Trim_UID}
                    StrCmp "$R2" "$\t" TrimRight_${Trim_UID}
                    GoTo Done_${Trim_UID}
                TrimRight_${Trim_UID}:  
                    StrCpy $R1 "$R1" -1
                    Goto Loop2_${Trim_UID}
                 
                Done_${Trim_UID}:
                    Pop $R2
                    Exch $R1
                    Pop ${_UserVar}
                !undef Trim_UID
            !macroend
            !ifdef Trim
                !warning `Trim Macro Previously Defined! Beware of bugs!`
            !else
                !define Trim `!insertmacro _Trim`
            !endif
        !endif
    
    ## Global variable needed for indexing the enumerations
        !ifmacrondef EnumIni_IDX_VAR
            !macro EnumIni_IDX_VAR
                !ifndef EnumIni_IDX_VAR
                    VAR /GLOBAL EnumIni_IDX_VAR
                    !define EnumIni_IDX_VAR $EnumIni_IDX_VAR
                !endif
            !macroend 
        !endif
        
    /*  ## EnumIniKey ##
            Nearly identical in use to the builtin EnumRegKey function, the EnumIniKey macro 
            allows for enumeration of an existing ini file's sections.
        
        ## Example ##
            StrCpy $0 0
            loop:
                ${EnumIniKey} $1 `c:\boot.ini` $0
                StrCmp $1 "" done
                IntOp $0 $0 + 1
                MessageBox MB_YESNO|MB_ICONQUESTION "Key=$1$\n$\n$\nMore?" IDYES loop
            done:
    */
    !ifmacrondef _EnumIniKey
        !insertmacro EnumIni_IDX_VAR
        !macro _EnumIniKey _UserVar _IniFilePath _Index
            !define EnumIniKey_UID ${__LINE__}
            ClearErrors
            
            Push $R0
            Push $R1
            
            Push `${_IniFilePath}`
            Push `${_Index}`
            
            Pop $R1 ; ${_Index}
            Pop $R0 ; ${_IniFilePath}
			
            IfFileExists $R0 0 Else_IfFileExists_${EnumIniKey_UID}
                StrCpy $EnumIni_IDX_VAR -1 
                ## PATCH Added to Correct 0 length file infinite loop issue discovered by zenpoy
                ## [http://forums.winamp.com/member.php?u=401997] on January 9th 2012
                    ${LineSum} $R0 $R1
                    IfErrors Else_IfFileExists_${EnumINIKey_UID}
                    IntCmp $R1 0 Else_IfFileExists_${EnumINIKey_UID} Else_IfFileExists_${EnumINIKey_UID} 0
                ## End Revision
                ${LineFind} $R0 "/NUL" "1:-1" "EnumIniKey_CALLBACK"
                IfErrors Else_IfFileExists_${EnumIniKey_UID}
                Goto EndIf_FileExists_${EnumIniKey_UID}
            Else_IfFileExists_${EnumIniKey_UID}:
                StrCpy $R0 ''
                SetErrors
            EndIf_FileExists_${EnumIniKey_UID}:
    
            Pop $R1
            Exch $R0
            Pop ${_UserVar}
            
            !undef EnumIniKey_UID
        !macroend
        !ifndef EnumIniKey
            !define EnumIniKey `!insertmacro _EnumIniKey`
        !endif
        !ifdef __GLOBAL__
            !verbose push
            !verbose 0
            Function EnumIniKey_CALLBACK
                !insertmacro _Trim $R9 $R9
                
                StrCmp $R9 '' End
                StrCpy $R0 $R9 1
                StrCmp $R0 '[' 0 End
                IntOp $EnumIni_IDX_VAR $EnumIni_IDX_VAR + 1
                IntCmp $R1 $EnumIni_IDX_VAR 0 End End
                    ${StrLoc} $R0 $R9 "]" ">"
                    IntCmp $R0 0 End
                    IntOp $R0 $R0 - 1
                    StrCpy $R0 $R9 $R0 1
                    Push 'StopLineFind'
                    Return
                End:
                StrCpy $R0 ''
                Push '' 
            FunctionEnd
            !verbose pop
        !else
            !Error `An illegal attempt was made to insert the EnumIniValue_CALLBACK function outside the Global namespace!`
        !endif
    !endif
    
    /*  ## EnumIniValue ##
            Nearly identical in use to the builtin EnumRegValue function, the EnumIniValue macro 
            allows for enumeration of an existing ini file section.
        
        ## Example ##
            StrCpy $0 0
            loop:
                ${EnumIniValue} $1 `c:\boot.ini` `boot loader` $0
                StrCmp $1 "" done
                IntOp $0 $0 + 1
                ReadIniStr $2 `c:\boot.ini` `boot loader` $1
                MessageBox MB_YESNO|MB_ICONQUESTION "Value=$1$\n$\t$2$\n$\n$\nMore?" IDYES loop
            done:
    */
    !ifmacrondef _EnumIniValue
        !insertmacro EnumIni_IDX_VAR
        !macro _EnumIniValue _UserVar _IniFilePath _Section _Index
            !define EnumIniValue_UID ${__LINE__}
            ClearErrors
            
            Push $R0
            Push $R1
            Push $R2
            Push $R3
    
            Push `${_IniFilePath}`
            Push `${_Section}`
            Push `${_Index}`
                
            Pop $R2 ; ${_Index}
            Pop $R1 ; ${_Section}
            Pop $R0 ; ${_IniFilePath}
    
            IfFileExists $R0 0 Else_IfFileExists_${EnumIniValue_UID}
                StrCpy $EnumIni_IDX_VAR -1 
                ${LineFind} $R0 "/NUL" "1:-1" "EnumIniValue_CALLBACK"
                IfErrors Else_IfFileExists_${EnumIniValue_UID}
                Goto EndIf_FileExists_${EnumIniValue_UID}
            Else_IfFileExists_${EnumIniValue_UID}:
                StrCpy $R0 ''
                SetErrors
            EndIf_FileExists_${EnumIniValue_UID}:
    
            Pop $R3
            Pop $R2
            Pop $R1
            Exch $R0
            Pop ${_UserVar}
            !undef EnumIniValue_UID
        !macroend
        !ifndef EnumIniValue
            !define EnumIniValue `!insertmacro _EnumIniValue`
        !endif
        !ifdef __GLOBAL__
            !verbose push
            !verbose 0
            Function EnumIniValue_CALLBACK
                !insertmacro _Trim $R9 $R9
                
                StrCmp $R9 '' End
                StrCpy $R0 $R9 1
                StrCmp $R0 ';' End
                StrCmp $R0 '#' End
                StrCmp $R0 '[' Key
                StrCmp $R3 [$R1] 0 End
                IntOp $EnumIni_IDX_VAR $EnumIni_IDX_VAR + 1
                IntCmp $R2 $EnumIni_IDX_VAR 0 End End
                    ${StrLoc} $R0 $R9 "=" ">"
                    IntCmp $R0 0 0 0 ValueSet
                        StrCpy $R0 $R9
                    ValueSet:
                    StrCpy $R0 $R9 $R0
                    Push 'StopLineFind'
                    Return
                Key:
                    StrCpy $R3 $R9
                End:
                StrCpy $R0 ''
                Push '' 
            FunctionEnd
            !verbose pop
        !else
            !Error `An illegal attempt was made to insert the EnumIniValue_CALLBACK function outside the Global namespace!`
        !endif
    !endif
!endif