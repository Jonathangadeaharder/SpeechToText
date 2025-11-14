@echo off
REM Script to copy admin password from C:\Intune\localadm.txt to clipboard (no auto-paste)

REM Check if file exists
if not exist "C:\Intune\localadm.txt" (
    echo Error: C:\Intune\localadm.txt not found
    exit /b 1
)

REM Use PowerShell to extract password (handles UTF-16 encoding)
REM Password is on line 5, format: "Password:   z}0Svtan"
powershell -NoProfile -Command "$content = Get-Content -Path 'C:\Intune\localadm.txt' -Encoding Unicode; $passwordLine = $content[4]; if ($passwordLine -match 'Password:\s+(.+)') { $password = $matches[1].Trim(); Set-Clipboard -Value $password; Write-Host 'Password copied to clipboard'; } else { Write-Host 'Password not found'; exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    echo Error extracting password
    exit /b 1
)

exit /b 0
