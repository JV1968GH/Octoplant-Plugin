@echo off
:: Octoplant -- GitHub Copilot Desktop MCP launcher.
:: Bootstrap the user-local runtime before the MCP server inherits stdio.

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
set "VENV_PATH=%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv"
set "RUNTIME_PATH=%LOCALAPPDATA%\AI\Plugins\octoplant\runtime"
if not exist "%LOCAL_PYTHON%" (
    call :bootstrap_runtime
    if errorlevel 1 exit /b 1
)

call :validate_path "%LOCAL_PYTHON%"
if not errorlevel 1 (
    "%LOCAL_PYTHON%" "%SCRIPT%"
    exit /b %ERRORLEVEL%
)

>&2 echo [Octoplant] User-local MCP runtime needs repair: %LOCAL_PYTHON%
call :bootstrap_runtime
if errorlevel 1 exit /b 1
call :validate_path "%LOCAL_PYTHON%"
if errorlevel 1 (
    >&2 echo [Octoplant] FastMCP is still unavailable after bootstrap. Check network or proxy access and retry.
    exit /b 1
)
"%LOCAL_PYTHON%" "%SCRIPT%"
exit /b %ERRORLEVEL%

:validate_path
"%~1" -c "import sys; from mcp.server.fastmcp import FastMCP; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
exit /b %ERRORLEVEL%

:bootstrap_runtime
call :find_base_python
if errorlevel 1 (
    >&2 echo [Octoplant] Python 3.11+ is required to create the user-local MCP runtime.
    >&2 echo [Octoplant] Install Python for the current user, then restart Copilot.
    exit /b 1
)

if not exist "%LOCAL_PYTHON%" (
    >&2 echo [Octoplant] Creating user-local MCP runtime...
    if not exist "%RUNTIME_PATH%" mkdir "%RUNTIME_PATH%" >nul 2>nul
    if not exist "%RUNTIME_PATH%" (
        >&2 echo [Octoplant] Cannot create %RUNTIME_PATH%. Verify write access to LOCALAPPDATA.
        exit /b 1
    )
    %BASE_PYTHON% -m venv "%VENV_PATH%" >nul
    if errorlevel 1 (
        >&2 echo [Octoplant] Creating the user-local MCP runtime failed.
        exit /b 1
    )
) else (
    >&2 echo [Octoplant] Repairing user-local MCP runtime...
    %BASE_PYTHON% -m venv --upgrade "%VENV_PATH%" >nul
    if errorlevel 1 (
        >&2 echo [Octoplant] Repairing the user-local MCP runtime failed.
        exit /b 1
    )
)

>&2 echo [Octoplant] Installing declared MCP runtime dependencies...
"%LOCAL_PYTHON%" -m pip install --disable-pip-version-check --no-input --upgrade "%ROOT%" >nul
if errorlevel 1 (
    >&2 echo [Octoplant] Installing MCP dependencies failed. Check network or proxy access and retry.
    exit /b 1
)
exit /b 0

:find_base_python
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "BASE_PYTHON=py -3"
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "BASE_PYTHON=python"
        exit /b 0
    )
)
exit /b 1
