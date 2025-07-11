#!/bin/bash
# Enhanced AUTOBOT initialization script with health checks and auto-recovery
# Run with: ./scripts/start.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_MIN_VERSION="3.9"
NODE_MIN_VERSION="18"
LOG_FILE="$PROJECT_DIR/startup.log"
PID_FILE="$PROJECT_DIR/.autobot.pid"

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison function
version_compare() {
    if [[ $1 == $2 ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

# Check Python version
check_python() {
    info "Checking Python installation..."
    
    if ! command_exists python3; then
        error "Python 3 is not installed. Please install Python 3.9 or later."
        exit 1
    fi
    
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    info "Found Python $python_version"
    
    version_compare "$python_version" "$PYTHON_MIN_VERSION"
    case $? in
        2)
            error "Python $python_version is too old. Please install Python $PYTHON_MIN_VERSION or later."
            exit 1
            ;;
        0|1)
            log "Python version check passed"
            ;;
    esac
}

# Check Node.js version
check_node() {
    info "Checking Node.js installation..."
    
    if ! command_exists node; then
        warn "Node.js is not installed. Frontend features will be limited."
        return 0
    fi
    
    local node_version=$(node -v | sed 's/v//')
    info "Found Node.js $node_version"
    
    version_compare "$node_version" "$NODE_MIN_VERSION"
    case $? in
        2)
            warn "Node.js $node_version is old. Please consider upgrading to $NODE_MIN_VERSION or later."
            ;;
        0|1)
            log "Node.js version check passed"
            ;;
    esac
}

# Check if process is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Stop existing processes
stop_autobot() {
    info "Stopping existing AUTOBOT processes..."
    
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid"
            sleep 2
            if ps -p "$pid" > /dev/null 2>&1; then
                warn "Process $pid didn't stop gracefully, forcing..."
                kill -9 "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill any remaining processes
    pkill -f "autobot" 2>/dev/null || true
    pkill -f "python.*api.py" 2>/dev/null || true
    
    log "Stopped existing processes"
}

# Setup Python virtual environment
setup_python_env() {
    info "Setting up Python environment..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install dependencies with error handling
    log "Installing Python dependencies..."
    if pip install -r requirements.txt; then
        log "Python dependencies installed successfully"
    else
        error "Failed to install Python dependencies"
        
        # Try installing core dependencies individually
        warn "Attempting to install core dependencies individually..."
        
        core_deps=("flask" "flask-cors" "requests" "python-dotenv")
        for dep in "${core_deps[@]}"; do
            if pip install "$dep"; then
                log "Installed $dep"
            else
                error "Failed to install $dep"
            fi
        done
    fi
}

# Setup Node.js dependencies
setup_node_env() {
    if ! command_exists node; then
        warn "Skipping Node.js setup - Node.js not installed"
        return 0
    fi
    
    info "Setting up Node.js environment..."
    
    cd "$PROJECT_DIR/web"
    
    if [[ ! -d "node_modules" ]]; then
        log "Installing Node.js dependencies..."
        if command_exists npm; then
            npm install
        elif command_exists yarn; then
            yarn install
        else
            warn "Neither npm nor yarn found. Skipping Node.js dependencies."
            return 0
        fi
    else
        info "Node.js dependencies already installed"
    fi
    
    log "Node.js environment ready"
}

# Check and create required directories
setup_directories() {
    info "Setting up project directories..."
    
    local dirs=(
        "database"
        "IA/treinamento/dados_uso"
        "metrics"
        "logs"
        "web/dist"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$PROJECT_DIR/$dir"
        log "Created directory: $dir"
    done
}

# Create .env file if it doesn't exist
setup_env_file() {
    info "Checking environment configuration..."
    
    local env_file="$PROJECT_DIR/.env"
    
    if [[ ! -f "$env_file" ]]; then
        log "Creating .env file template..."
        cat > "$env_file" << 'EOF'
# AUTOBOT Configuration
# Copy this file and fill in your actual values

# Bitrix24 Integration
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.com/rest/1/your_webhook_key/
BITRIX_USER_ID=1

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3

# Application Settings
DEBUG_MODE=false
PORT=5000

# Database (optional)
DATABASE_URL=sqlite:///database/autobot.db

# Security (generate secure random strings)
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
EOF
        warn "Created .env template. Please edit it with your actual configuration."
        warn "The application may not work properly until you configure .env"
    else
        log "Environment file exists"
    fi
}

# Health check function
health_check() {
    info "Performing health checks..."
    
    local checks_passed=0
    local total_checks=3
    
    # Check Python environment
    if source venv/bin/activate && python3 -c "import flask, requests" 2>/dev/null; then
        log "✓ Python environment check passed"
        ((checks_passed++))
    else
        error "✗ Python environment check failed"
    fi
    
    # Check .env file
    if [[ -f ".env" ]] && grep -q "BITRIX_WEBHOOK_URL" ".env"; then
        log "✓ Environment configuration check passed"
        ((checks_passed++))
    else
        error "✗ Environment configuration check failed"
    fi
    
    # Check directories
    if [[ -d "database" ]] && [[ -d "IA/treinamento" ]]; then
        log "✓ Directory structure check passed"
        ((checks_passed++))
    else
        error "✗ Directory structure check failed"
    fi
    
    info "Health check: $checks_passed/$total_checks checks passed"
    
    if [[ $checks_passed -eq $total_checks ]]; then
        return 0
    else
        return 1
    fi
}

# Start the application
start_application() {
    info "Starting AUTOBOT application..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Start the API server
    log "Starting API server on port ${PORT:-5000}..."
    
    # Use nohup to run in background
    nohup python -m autobot.api > logs/api.log 2>&1 &
    local api_pid=$!
    echo $api_pid > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 3
    
    # Check if the process is still running
    if ps -p "$api_pid" > /dev/null 2>&1; then
        log "API server started successfully (PID: $api_pid)"
        
        # Test API endpoint
        if curl -s -f "http://localhost:${PORT:-5000}/api/health" > /dev/null; then
            log "✓ API health check passed"
        else
            warn "API health check failed - server may still be starting up"
        fi
    else
        error "Failed to start API server"
        return 1
    fi
    
    # Start frontend if Node.js is available
    if command_exists node && [[ -d "web/node_modules" ]]; then
        info "Starting frontend development server..."
        cd web
        nohup npm run dev > ../logs/frontend.log 2>&1 &
        log "Frontend server starting..."
    fi
    
    log "AUTOBOT started successfully!"
    info "API: http://localhost:${PORT:-5000}"
    if command_exists node; then
        info "Frontend: http://localhost:3000"
    fi
    info "Logs: $PROJECT_DIR/logs/"
}

# Auto-recovery function
auto_recovery() {
    info "Attempting auto-recovery..."
    
    # Stop any hanging processes
    stop_autobot
    
    # Clean up corrupted files
    rm -f "$PID_FILE"
    rm -f logs/*.log
    
    # Recreate directories
    setup_directories
    
    # Reinstall critical dependencies
    source venv/bin/activate
    pip install flask flask-cors requests python-dotenv
    
    log "Auto-recovery completed"
}

# Main execution
main() {
    log "Starting AUTOBOT initialization..."
    log "Project directory: $PROJECT_DIR"
    
    # Handle command line arguments
    case "${1:-}" in
        "stop")
            stop_autobot
            exit 0
            ;;
        "restart")
            stop_autobot
            sleep 2
            ;;
        "recover")
            auto_recovery
            ;;
        "health")
            health_check
            exit $?
            ;;
    esac
    
    # Check if already running
    if is_running; then
        warn "AUTOBOT is already running. Use './scripts/start.sh stop' to stop it first."
        exit 1
    fi
    
    # Perform checks and setup
    check_python
    check_node
    setup_directories
    setup_env_file
    setup_python_env
    setup_node_env
    
    # Health check
    if health_check; then
        log "All health checks passed"
    else
        warn "Some health checks failed. Attempting to start anyway..."
    fi
    
    # Start the application
    if start_application; then
        log "AUTOBOT initialization completed successfully!"
        
        # Show status
        echo
        echo "🚀 AUTOBOT is now running!"
        echo "📊 Dashboard: http://localhost:3000"
        echo "🔌 API: http://localhost:${PORT:-5000}/api/health"
        echo "📁 Logs: $PROJECT_DIR/logs/"
        echo
        echo "Use './scripts/start.sh stop' to stop the application"
        echo "Use './scripts/start.sh health' to check system health"
        
    else
        error "Failed to start AUTOBOT"
        exit 1
    fi
}

# Run main function
main "$@"