@echo off
setlocal EnableExtensions

:: Install official Russian Trusted CA certificates for MAX API.
:: Run this file as Administrator.

net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo Administrator permissions are required.
    echo Right-click this file and select "Run as administrator".
    pause
    exit /b 1
)

set "WORKDIR=%TEMP%\MAX_CA_Install"
set "ROOT_URL=https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt"
set "SUB_URL=https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt"
set "ROOT_FILE=%WORKDIR%\russian_trusted_root_ca_pem.crt"
set "SUB_FILE=%WORKDIR%\russian_trusted_sub_ca_pem.crt"

if not exist "%WORKDIR%" mkdir "%WORKDIR%"
if errorlevel 1 goto :error

echo Downloading Russian Trusted Root CA...
curl.exe --fail --location --silent --show-error "%ROOT_URL%" --output "%ROOT_FILE%"
if errorlevel 1 goto :download_error

echo Downloading Russian Trusted Sub CA...
curl.exe --fail --location --silent --show-error "%SUB_URL%" --output "%SUB_FILE%"
if errorlevel 1 goto :download_error

for %%F in ("%ROOT_FILE%" "%SUB_FILE%") do (
    if not exist "%%~F" goto :download_error
    if %%~zF LSS 500 goto :download_error
)

echo.
echo Installing root certificate into Local Computer - Trusted Root Certification Authorities...
certutil.exe -addstore -f Root "%ROOT_FILE%"
if errorlevel 1 goto :install_error

echo Installing issuing certificate into Local Computer - Intermediate Certification Authorities...
certutil.exe -addstore -f CA "%SUB_FILE%"
if errorlevel 1 goto :install_error

echo.
echo Certificate installation completed.
echo Restart the MAX application or bot process before testing the connection.
echo Official information: https://www.gosuslugi.ru/crt
rmdir /s /q "%WORKDIR%" >nul 2>&1
pause
exit /b 0

:download_error
echo.
echo ERROR: Could not download or validate the certificate files.
echo Check your internet connection and consult https://www.gosuslugi.ru/crt
rmdir /s /q "%WORKDIR%" >nul 2>&1
pause
exit /b 2

:install_error
echo.
echo ERROR: Windows could not install one of the certificates.
echo Check Administrator permissions and consult https://www.gosuslugi.ru/crt
rmdir /s /q "%WORKDIR%" >nul 2>&1
pause
exit /b 3

:error
echo ERROR: Could not create temporary working directory.
pause
exit /b 4
