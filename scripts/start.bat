@echo off
REM Enhanced AUTOBOT Windows initialization script
REM Run as Administrator for best results

setlocal enabledelayedexpansion

REM Configuration
set "PROJECT_DIR=%~dp0.."
set "PYTHON_MIN_VERSION=3.9"
set "NODE_MIN_VERSION=18"
set "LOG_FILE=%PROJECT_DIR%\startup.log"
set "PID_FILE=%PROJECT_DIR%\.autobot.pid"

REM Colors (if supported)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Create logs directory
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Logging functions
call :log "Starting AUTOBOT Windows initialization..."

REM Check if running as administrator
call :check_admin

REM Parse command line arguments
if "%1"=="stop" (
    call :stop_autobot
    exit /b 0
)
if "%1"=="restart" (
    call :stop_autobot
    timeout /t 2 /nobreak >nul
)
if "%1"=="health" (
    call :health_check
    exit /b
)

REM Check if already running
call :is_running
if !errorlevel! equ 0 (
    call :warn "AUTOBOT is already running. Use 'start.bat stop' to stop it first."
    pause
    exit /b 1
)

REM Perform setup steps
call :check_python
call :check_node
call :setup_directories
call :setup_env_file
call :setup_python_env
call :setup_node_env
call :health_check
call :start_application

call :log "AUTOBOT initialization completed!"
echo.
echo ^🚀 AUTOBOT is now running!
echo ^📊 Dashboard: http://localhost:3000
echo ^🔌 API: http://localhost:5000/api/health
echo ^📁 Logs: %PROJECT_DIR%\logs\
echo.
echo Use 'start.bat stop' to stop the application
pause
exit /b 0

REM Function definitions below

:log
echo [%date% %time%] %~1 | tee -a "%LOG_FILE%" 2>nul || echo [%date% %time%] %~1
echo [%date% %time%] %~1 >> "%LOG_FILE%" 2>nul
exit /b

:warn
echo [%date% %time%] WARNING: %~1 | tee -a "%LOG_FILE%" 2>nul || echo [%date% %time%] WARNING: %~1
echo [%date% %time%] WARNING: %~1 >> "%LOG_FILE%" 2>nul
exit /b

:error
echo [%date% %time%] ERROR: %~1 | tee -a "%LOG_FILE%" 2>nul || echo [%date% %time%] ERROR: %~1
echo [%date% %time%] ERROR: %~1 >> "%LOG_FILE%" 2>nul
exit /b

:info
echo [%date% %time%] INFO: %~1 | tee -a "%LOG_FILE%" 2>nul || echo [%date% %time%] INFO: %~1
echo [%date% %time%] INFO: %~1 >> "%LOG_FILE%" 2>nul
exit /b

:check_admin
call :info "Checking administrator privileges..."
net session >nul 2>&1
if !errorlevel! neq 0 (
    call :warn "Not running as administrator. Some features may not work properly."
    call :warn "For best results, right-click and 'Run as administrator'"
)
exit /b

:check_python
call :info "Checking Python installation..."

where python >nul 2>&1
if !errorlevel! neq 0 (
    where python3 >nul 2>&1
    if !errorlevel! neq 0 (
        call :error "Python is not installed or not in PATH."
        call :error "Please install Python 3.9+ from https://python.org"
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=python3"
    )
) else (
    set "PYTHON_CMD=python"
)

REM Get Python version
for /f "delims=" %%i in ('!PYTHON_CMD! -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"') do set "PYTHON_VERSION=%%i"
call :info "Found Python !PYTHON_VERSION!"

REM Simple version check (assuming format X.Y)
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set "major=%%a"
    set "minor=%%b"
)
if !major! lss 3 (
    call :error "Python !PYTHON_VERSION! is too old. Please install Python 3.9+"
    pause
    exit /b 1
)
if !major! equ 3 if !minor! lss 9 (
    call :error "Python !PYTHON_VERSION! is too old. Please install Python 3.9+"
    pause
    exit /b 1
)

call :log "Python version check passed"
exit /b

:check_node
call :info "Checking Node.js installation..."

where node >nul 2>&1
if !errorlevel! neq 0 (
    call :warn "Node.js is not installed. Frontend features will be limited."
    call :warn "Consider installing Node.js from https://nodejs.org"
    exit /b
)

for /f "delims=" %%i in ('node -v') do set "NODE_VERSION=%%i"
set "NODE_VERSION=!NODE_VERSION:~1!"
call :info "Found Node.js !NODE_VERSION!"
call :log "Node.js check completed"
exit /b

:is_running
if exist "%PID_FILE%" (
    set /p pid=<"%PID_FILE%"
    tasklist /fi "pid eq !pid!" | find "!pid!" >nul 2>&1
    if !errorlevel! equ 0 (
        exit /b 0
    ) else (
        del "%PID_FILE%" >nul 2>&1
        exit /b 1
    )
)
exit /b 1

:stop_autobot
call :info "Stopping AUTOBOT processes..."

REM Stop by PID file
if exist "%PID_FILE%" (
    set /p pid=<"%PID_FILE%"
    taskkill /pid !pid! /f >nul 2>&1
    del "%PID_FILE%" >nul 2>&1
)

REM Kill any remaining processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq autobot*" >nul 2>&1
taskkill /f /im node.exe /fi "WINDOWTITLE eq *autobot*" >nul 2>&1

call :log "Stopped AUTOBOT processes"
exit /b

:setup_directories
call :info "Setting up project directories..."

cd /d "%PROJECT_DIR%"

if not exist "database" mkdir "database"
if not exist "IA\treinamento\dados_uso" mkdir "IA\treinamento\dados_uso"
if not exist "metrics" mkdir "metrics"
if not exist "logs" mkdir "logs"
if not exist "web\dist" mkdir "web\dist"

call :log "Project directories created"
exit /b

:setup_env_file
call :info "Checking environment configuration..."

if not exist "%PROJECT_DIR%\.env" (
    call :log "Creating .env template..."
    (
        echo # AUTOBOT Configuration
        echo # Fill in your actual values
        echo.
        echo # Bitrix24 Integration
        echo BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.com/rest/1/your_webhook_key/
        echo BITRIX_USER_ID=1
        echo.
        echo # AI Configuration
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo OLLAMA_HOST=localhost
        echo OLLAMA_PORT=11434
        echo OLLAMA_MODEL=llama3
        echo.
        echo # Application Settings
        echo DEBUG_MODE=false
        echo PORT=5000
        echo.
        echo # Database
        echo DATABASE_URL=sqlite:///database/autobot.db
    ) > "%PROJECT_DIR%\.env"
    
    call :warn "Created .env template. Please edit it with your configuration."
) else (
    call :log "Environment file exists"
)
exit /b

:setup_python_env
call :info "Setting up Python environment..."

cd /d "%PROJECT_DIR%"

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    call :log "Creating Python virtual environment..."
    !PYTHON_CMD! -m venv venv
    if !errorlevel! neq 0 (
        call :error "Failed to create virtual environment"
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip setuptools wheel

REM Install dependencies
call :log "Installing Python dependencies..."
pip install -r requirements.txt
if !errorlevel! neq 0 (
    call :warn "Some dependencies failed to install. Trying core dependencies..."
    pip install flask flask-cors requests python-dotenv
)

call :log "Python environment ready"
exit /b

:setup_node_env
where node >nul 2>&1
if !errorlevel! neq 0 (
    call :warn "Skipping Node.js setup - Node.js not installed"
    exit /b
)

call :info "Setting up Node.js environment..."

cd /d "%PROJECT_DIR%\web"

if not exist "node_modules" (
    call :log "Installing Node.js dependencies..."
    where npm >nul 2>&1
    if !errorlevel! equ 0 (
        npm install
    ) else (
        where yarn >nul 2>&1
        if !errorlevel! equ 0 (
            yarn install
        ) else (
            call :warn "Neither npm nor yarn found"
        )
    )
) else (
    call :info "Node.js dependencies already installed"
)

call :log "Node.js environment ready"
exit /b

:health_check
call :info "Performing health checks..."

cd /d "%PROJECT_DIR%"

set "checks_passed=0"
set "total_checks=3"

REM Check Python environment
call venv\Scripts\activate.bat
python -c "import flask, requests" >nul 2>&1
if !errorlevel! equ 0 (
    call :log "✓ Python environment check passed"
    set /a checks_passed+=1
) else (
    call :error "✗ Python environment check failed"
)

REM Check .env file
if exist ".env" (
    findstr "BITRIX_WEBHOOK_URL" ".env" >nul 2>&1
    if !errorlevel! equ 0 (
        call :log "✓ Environment configuration check passed"
        set /a checks_passed+=1
    ) else (
        call :error "✗ Environment configuration incomplete"
    )
) else (
    call :error "✗ Environment configuration missing"
)

REM Check directories
if exist "database" if exist "IA\treinamento" (
    call :log "✓ Directory structure check passed"
    set /a checks_passed+=1
) else (
    call :error "✗ Directory structure check failed"
)

call :info "Health check: !checks_passed!/!total_checks! checks passed"
exit /b

:start_application
call :info "Starting AUTOBOT application..."

cd /d "%PROJECT_DIR%"
call venv\Scripts\activate.bat

REM Start API server
call :log "Starting API server..."

start /b "AUTOBOT API" python -m autobot.api > logs\api.log 2>&1

REM Get the PID (Windows doesn't make this easy)
timeout /t 2 /nobreak >nul

REM Test if API is responding
call :info "Testing API server..."
timeout /t 5 /nobreak >nul

powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:5000/api/health' -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if !errorlevel! equ 0 (
    call :log "✓ API server is responding"
) else (
    call :warn "API server may still be starting up"
)

REM Start frontend if possible
where node >nul 2>&1
if !errorlevel! equ 0 (
    if exist "web\node_modules" (
        call :info "Starting frontend server..."
        cd web
        start /b "AUTOBOT Frontend" npm run dev > ..\logs\frontend.log 2>&1
        cd ..
    )
)

call :log "AUTOBOT started successfully!"
exit /b