@echo off
:: Octoplant -- GitHub Copilot Desktop MCP launcher
:: Zoekt Python in de conda "mcp-op" omgeving op meerdere standaardlocaties.
:: Vereiste: Anaconda of Miniconda met een omgeving genaamd "mcp-op".

setlocal
set "ENV_NAME=mcp-op"
set "SCRIPT=%~dp0..\server.py"
set "CONDA_EXE="

:: Zoek Python in bekende conda-installaties
for %%B in (
    "%USERPROFILE%\.conda"
    "%USERPROFILE%\anaconda3"
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\AppData\Local\anaconda3"
    "%USERPROFILE%\AppData\Local\miniconda3"
    "C:\ProgramData\anaconda3"
    "C:\ProgramData\miniconda3"
    "C:\tools\anaconda3"
    "C:\tools\miniconda3"
) do (
    if exist "%%~B\envs\%ENV_NAME%\python.exe" (
        "%%~B\envs\%ENV_NAME%\python.exe" "%SCRIPT%"
        exit /b %ERRORLEVEL%
    )
)

:: Zoek conda.exe op bekende locaties als conda niet in PATH staat
for %%C in (
    "%USERPROFILE%\anaconda3\Scripts\conda.exe"
    "%USERPROFILE%\miniconda3\Scripts\conda.exe"
    "%USERPROFILE%\AppData\Local\anaconda3\Scripts\conda.exe"
    "%USERPROFILE%\AppData\Local\miniconda3\Scripts\conda.exe"
    "C:\ProgramData\anaconda3\Scripts\conda.exe"
    "C:\ProgramData\miniconda3\Scripts\conda.exe"
    "C:\tools\anaconda3\Scripts\conda.exe"
    "C:\tools\miniconda3\Scripts\conda.exe"
) do (
    if exist "%%~C" (
        set "CONDA_EXE=%%~C"
        goto :run_conda
    )
)

:: Laatste fallback: conda run via PATH
conda run -n %ENV_NAME% --no-capture-output python "%SCRIPT%"
exit /b %ERRORLEVEL%

:run_conda
"%CONDA_EXE%" run -n %ENV_NAME% --no-capture-output python "%SCRIPT%"
exit /b %ERRORLEVEL%
