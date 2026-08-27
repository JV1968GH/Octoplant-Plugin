@echo off
:: Octoplant -- GitHub Copilot Desktop MCP launcher.
:: Candidate runtimes are verified for Python 3.11+ and server dependencies
:: before the server receives stdio.

setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0.."
set "SCRIPT=%ROOT%\server.py"
set "LOCAL_PYTHON=%ROOT%\.venv\Scripts\python.exe"

if exist "%LOCAL_PYTHON%" (
    call :validate_path "%LOCAL_PYTHON%"
    if not errorlevel 1 (
        "%LOCAL_PYTHON%" "%SCRIPT%"
        exit /b %ERRORLEVEL%
    )
    >&2 echo [Octoplant] Plugin-local .venv cannot start the MCP runtime; trying system launchers.
)

call :validate_py_launcher
if not errorlevel 1 (
    py -3 "%SCRIPT%"
    exit /b %ERRORLEVEL%
)

call :validate_path_launcher
if not errorlevel 1 (
    python "%SCRIPT%"
    exit /b %ERRORLEVEL%
)

>&2 echo [Octoplant] No suitable Python 3.11+ runtime with server dependencies was found. Run scripts\install.ps1.
exit /b 1

:validate_path
"%~1" -c "import sys; from mcp.server.fastmcp import FastMCP; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
exit /b %ERRORLEVEL%

:validate_py_launcher
where py >nul 2>nul || exit /b 1
py -3 -c "import sys; from mcp.server.fastmcp import FastMCP; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
exit /b %ERRORLEVEL%

:validate_path_launcher
where python >nul 2>nul || exit /b 1
python -c "import sys; from mcp.server.fastmcp import FastMCP; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
exit /b %ERRORLEVEL%
