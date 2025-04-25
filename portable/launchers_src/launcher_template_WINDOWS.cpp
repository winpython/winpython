/*
DataLab-WinPython launcher script
---------------------------------

Licensed under the terms of the BSD 3-Clause
(see ./LICENSE for details)

*/

#include <windows.h>
#include <string>

int WINAPI WinMain(HINSTANCE /*hInstance*/, HINSTANCE /*hPrevInstance*/, LPSTR /*lpCmdLine*/, int /*nShowCmd*/) {
    // Get the path to the current executable
    wchar_t exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);

    // Determine the directory of the executable
    std::wstring exeDir = exePath;
    exeDir = exeDir.substr(0, exeDir.find_last_of(L"\\/"));

    // Get command line string
    LPWSTR commandLine = GetCommandLineW();
    // Skip the current executable path and name
    std::wstring args;
    if (commandLine) {
        // If path is double quoted, skip the entire double quote
        if (commandLine[0] == L'"') {
            LPWSTR closingQuote = wcschr(commandLine + 1, L'"');
            if (closingQuote) {
                args = closingQuote + 1; // Skip closing quote and space
            }
        // Otherwise skip to first space
        } else {
            LPWSTR spacePos = wcschr(commandLine, L' ');
            if (spacePos) {
                args = spacePos + 1; // Skip space
            }
        }
    }

    // Define the path to the "scripts" directory
    std::wstring scriptsDir = exeDir + L"\\scripts";

    // Check if the "scripts" directory exists
    DWORD attributes = GetFileAttributesW(scriptsDir.c_str());
    if (attributes == INVALID_FILE_ATTRIBUTES || !(attributes & FILE_ATTRIBUTE_DIRECTORY)) {
        MessageBoxW(NULL, L"The 'scripts' directory does not exist. Please ensure it is in the same folder as the launcher.", 
                    L"Launcher Error", MB_ICONERROR);
        return 1;
    }

    // Set the working directory to the "scripts" folder
    if (!SetCurrentDirectoryW(scriptsDir.c_str())) {
        MessageBoxW(NULL, L"Failed to set the working directory to 'scripts'.", 
                    L"Launcher Error", MB_ICONERROR);
        return 1;
    }

    // Define the command to run
    std::wstring target = L"cmd.exe /c \"" LAUNCH_TARGET L"\"";

    // Append arguments if present
    if (!args.empty()) {
        target += L" " + args;
    }

    // Configure the process startup info
    STARTUPINFO si = { sizeof(si) };
    si.dwFlags = STARTF_USESHOWWINDOW; // Prevent the window from appearing
    si.wShowWindow = SW_HIDE;         // Hide the command window

    PROCESS_INFORMATION pi = {};

    // Start the process with CREATE_NO_WINDOW flag
    if (!CreateProcessW(
            NULL,                          // Application name (NULL because we pass the command in the command line)
            &target[0],                    // Command line
            NULL,                          // Process security attributes
            NULL,                          // Thread security attributes
            FALSE,                         // Inherit handles
            CREATE_NO_WINDOW,              // Flags to prevent creating a window
            NULL,                          // Environment block (NULL to inherit parent)
            NULL,                          // Current directory (NULL to use the parent process's current directory)
            &si,                           // Startup info
            &pi                            // Process information
        )) {
        MessageBoxW(NULL, L"Failed to launch the script.", L"Launcher Error", MB_ICONERROR);
        return 1;
    }

    // Wait for the script to finish
    WaitForSingleObject(pi.hProcess, INFINITE);

    // Cleanup
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return 0;
}
