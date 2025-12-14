@echo off
REM Installation script for Windows

echo Installing faneX-ID OnPrem Connector...

REM Create directories
if not exist "C:\Program Files\faneX-ID-Connector" mkdir "C:\Program Files\faneX-ID-Connector"
if not exist "C:\Program Files\faneX-ID-Connector\logs" mkdir "C:\Program Files\faneX-ID-Connector\logs"

REM Copy files
xcopy /E /I /Y * "C:\Program Files\faneX-ID-Connector\"

REM Create service (requires NSSM or similar)
echo Creating Windows service...
echo Please install NSSM (Non-Sucking Service Manager) to create the service
echo Or use: nssm install fanexid-connector "python.exe" "-m uvicorn main:app --host 0.0.0.0 --port 8080"

echo Installation complete!
echo Configure config.ini and then start the service
