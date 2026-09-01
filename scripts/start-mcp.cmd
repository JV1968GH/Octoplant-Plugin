@echo off
:: Octoplant -- GitHub Copilot Desktop MCP launcher.
:: The runtime is user-local so the installed plugin directory may remain read-only.

setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0.."
set "SCRIPT=%ROOT%\server.py"
set "OVERRIDE_PYTHON=%OCTOPLANT_MCP_PYTHON%"

if defined OVERRIDE_PYTHON (
    call :validate_path "%OVERRIDE_PYTHON%"
    if not errorlevel 1 (
        "%OVERRIDE_PYTHON%" "%SCRIPT%"
        exit /b %ERRORLEVEL%
    )
    >&2 echo [Octoplant] OCTOPLANT_MCP_PYTHON is not a Python 3.11+ runtime with FastMCP; using the installed runtime.
)

if not defined LOCALAPPDATA (
    >&2 echo [Octoplant] LOCALAPPDATA is unavailable; cannot locate the user-local MCP runtime.
    >&2 echo [Octoplant] Run scripts\install.ps1 from the plugin directory after restoring LOCALAPPDATA.
    exit /b 1
)

set "LOCAL_PYTHON=%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv\Scripts\python.exe"
if not exist "%LOCAL_PYTHON%" (
    >&2 echo [Octoplant] User-local MCP runtime was not found: %LOCAL_PYTHON%
    >&2 echo [Octoplant] Run scripts\install.ps1 from the plugin directory.
    exit /b 1
)

call :validate_path "%LOCAL_PYTHON%"
if not errorlevel 1 (
    "%LOCAL_PYTHON%" "%SCRIPT%"
    exit /b %ERRORLEVEL%
)

>&2 echo [Octoplant] User-local MCP runtime is missing Python 3.11+ or FastMCP.
>&2 echo [Octoplant] Run scripts\install.ps1 to repair %LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv.
exit /b 1

:validate_path
"%~1" -c "import sys; from mcp.server.fastmcp import FastMCP; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
exit /b %ERRORLEVEL%
