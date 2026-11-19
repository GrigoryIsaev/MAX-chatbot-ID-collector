MAX API - Минцифры certificate installer

Purpose
-------
Installs the Russian Trusted Root CA and Russian Trusted Sub CA certificates
for the current Windows computer. MAX API documentation instructs developers
to trust the Минцифры certificate and use https://platform-api2.max.ru.

How to use
----------
1. Close the MAX ID Collector and any running MAX bot processes.
2. Right-click Install_MAX_Certificates.bat.
3. Choose "Run as administrator".
4. Approve the Windows permission prompt.
5. Wait for the success message, then restart the application.

The installer downloads the certificate files from the Госуслуги certificate
content host and adds them to the Windows Local Computer certificate stores:
- Root: Trusted Root Certification Authorities
- CA: Intermediate Certification Authorities

Official information:
https://www.gosuslugi.ru/crt
MAX API documentation:
https://dev.max.ru/docs-api/

Security notes
--------------
- Do not disable TLS certificate verification as a workaround.
- This installer changes the Windows trust store and therefore requires
  Administrator permissions.
- It does not change the MAX ID Collector source code or any other bot files.
- It does not install Python, PyInstaller, or other programming tools.
- If Windows cannot download the files, open the official Госуслуги page and
  follow the current instructions for your Windows version.
