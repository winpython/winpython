@echo on
set icon_name=%1
set LAUNCH_TARGET=%2
set launcher_name=%3
set subsystem=%4
set destination=%5

set icon_name=%icon_name:"=%
set LAUNCH_TARGET=%LAUNCH_TARGET:"=%
set launcher_name=%launcher_name:"=%
set subsystem=%subsystem:"=%

set ROOT_PATH=%~dp0..\
set SCRIPT_PATH=%~dp0
set TEMPO_PATH=%ROOT_PATH%launchers_temp
set OUTPUT_DIR=%ROOT_PATH%launchers_%destination%

set "ICON_FILE=%ROOT_PATH%icons\%icon_name%"
set LAUNCHER_EXE=%OUTPUT_DIR%\%launcher_name%.exe


:: Paths to template WINDOWS or CONSOLE
set SOURCE_FILE=%SCRIPT_PATH%launcher_template_%subsystem%.cpp
echo SOURCE_FILE=%SOURCE_FILE%

set "RESOURCE_FILE=%TEMPO_PATH%\%icon_name%.rc"
set "RESOURCE_OBJ=%TEMPO_PATH%\%icon_name%.res"


:: create pDirectory if needed
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%TEMPO_PATH%" mkdir "%TEMPO_PATH%"

cd/d %TEMPO_PATH%

:: Check if MSVC environment is already initialized
if not defined VSINSTALLDIR (
    echo Initializing MSVC environment...
    call %VCVARS_PATH%
    if errorlevel 1 (
        echo [ERROR] Failed to initialize MSVC environment.
        exit /b 1
    )
)

@echo on

:: Walk through .bat files in the current directory
    echo Processing %icon_name%..
    :: Stonebig: Remove previous .exe file
    echo launcher_exe_action del /q "%LAUNCHER_EXE%"
    if exist "%LAUNCHER_EXE%" (
       move "%LAUNCHER_EXE%" "%LAUNCHER_EXE%.old.exe"
       del /q "%LAUNCHER_EXE%.old.exe"
    )
   :: Stonebig: Remove intermediate .res and.rc file
    if exist "%RESOURCE_OBJ%" (
       move "%RESOURCE_OBJ%" "%RESOURCE_OBJ%.old.exe"
       del /q "%RESOURCE_OBJ%.old.exe"
    )
    if exist "%RESOURCE_FILE%" (
       move "%RESOURCE_FILE%" "%RESOURCE_FILE%.old.exe"
       del /q "%RESOURCE_FILE%.old.exe"
    )
    :: Remove intermediate .obj file
    del /q "launcher_template_%subsystem%.obj"

    :: Check if the icon exists
    if exist "%ICON_FILE%" (
        echo Icon found: "%ICON_FILE%"
    ) else (
        echo No icon found for "%ICON_FILE%"  stoping
        pause
        exit
    )


    :: Create resource file
    echo Creating resource file...
    > "%RESOURCE_FILE%" echo IDI_ICON1 ICON "%ICON_FILE%"
    :: Compile resource
    echo Compiling resource...
    rc /fo "%RESOURCE_OBJ%" "%RESOURCE_FILE%"

    :: Compile the launcher executable
    echo Compiling launcher executable...
    cl /EHsc /O2 /DUNICODE /W4 "%SOURCE_FILE%" "%RESOURCE_OBJ%" ^
        /Fe"%LAUNCHER_EXE%%" ^
        /DLAUNCH_TARGET=\"%LAUNCH_TARGET%\" ^
        User32.lib ^
        /link /SUBSYSTEM:%subsystem%
        

    if errorlevel 1 (
        echo [ERROR] Failed to build launcher for %LAUNCH_TARGET%
        exit /b 1
    )

    if exist "%LAUNCHER_EXE%" (
        echo [SUCCESS] Launcher created: "%LAUNCHER_EXE%""
    ) else (
        echo [ERROR] Failed to build launcher "%LAUNCHER_EXE%" from  "%icon_name%" to call "%LAUNCH_TARGET%"  
        exit /b 1
    )

echo All launchers processed.
rem exit /b 0

