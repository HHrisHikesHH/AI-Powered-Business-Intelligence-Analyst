#!/bin/bash
# Development bootstrap script for AI-Powered Business Intelligence Analyst
# Creates venv, installs dependencies, verifies setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    log_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11 or later."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        log_error "Python 3.11 or later is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    log_info "Python version: $(python3 --version)"
}

# Check disk space (at least 2GB free)
check_disk_space() {
    log_info "Checking available disk space..."
    AVAILABLE_SPACE=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
    
    if [ "$AVAILABLE_SPACE" -lt 2 ]; then
        log_warn "Low disk space: ${AVAILABLE_SPACE}GB available. Recommended: at least 2GB"
    else
        log_info "Disk space: ${AVAILABLE_SPACE}GB available"
    fi
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    cd "$BACKEND_DIR"
    
    if [ -d "$VENV_DIR" ]; then
        log_warn "Virtual environment already exists at $VENV_DIR"
        read -p "Remove existing venv and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
            python3 -m venv venv
            log_info "Virtual environment recreated"
        else
            log_info "Using existing virtual environment"
        fi
    else
        python3 -m venv venv
        log_info "Virtual environment created"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    cd "$BACKEND_DIR"
    
    # Activate venv
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install CPU-only PyTorch first (required by sentence-transformers)
    log_info "Installing CPU-only PyTorch (this may take a few minutes)..."
    pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet || {
        log_error "Failed to install CPU-only PyTorch"
        exit 1
    }
    
    # Install remaining requirements
    log_info "Installing remaining dependencies..."
    pip install -r requirements.txt --quiet || {
        log_error "Failed to install requirements"
        exit 1
    }
    
    log_info "All dependencies installed successfully"
    
    # Show installed torch info
    log_info "Verifying PyTorch installation..."
    python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')" || {
        log_warn "Could not verify PyTorch installation"
    }
}

# Verify PostgreSQL connectivity
check_postgres() {
    log_info "Checking PostgreSQL connectivity..."
    
    # Load .env if it exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    elif [ -f "$BACKEND_DIR/.env" ]; then
        set -a
        source "$BACKEND_DIR/.env"
        set +a
    else
        log_warn ".env file not found. Skipping PostgreSQL check."
        log_warn "Create .env file with POSTGRES_* variables to enable database checks."
        return 0
    fi
    
    POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
    POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    POSTGRES_USER="${POSTGRES_USER:-postgres}"
    POSTGRES_DB="${POSTGRES_DB:-ai_bi_db}"
    
    # Check if psql is available
    if ! command -v psql &> /dev/null; then
        log_warn "psql not found. Install postgresql-client to enable database checks."
        return 0
    fi
    
    # Test connection
    if PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "SELECT 1;" &> /dev/null; then
        log_info "PostgreSQL connection successful"
        
        # Check if database exists
        if PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
            log_info "Database '$POSTGRES_DB' exists"
        else
            log_warn "Database '$POSTGRES_DB' does not exist. Run 'make migrate' to create it."
        fi
    else
        log_warn "Could not connect to PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT"
        log_warn "Ensure PostgreSQL is running and credentials in .env are correct."
    fi
}

# Print diagnostics
print_diagnostics() {
    log_info "Setup complete! Diagnostics:"
    echo ""
    echo "  Virtual environment: $VENV_DIR"
    echo "  Python: $(python3 --version)"
    echo "  Project root: $PROJECT_ROOT"
    echo ""
    echo "Next steps:"
    echo "  1. Activate virtual environment:"
    echo "     cd backend && source venv/bin/activate"
    echo ""
    echo "  2. Set up environment variables:"
    echo "     cp backend/.env.example backend/.env"
    echo "     # Edit backend/.env and add your GROQ_API_KEY"
    echo "     # IMPORTANT: For local dev, use REDIS_HOST=localhost (not 'redis')"
    echo ""
    echo "  3. Start Redis (required for Celery):"
    echo "     docker-compose up -d redis"
    echo "     # OR install locally: sudo apt-get install redis-server"
    echo ""
    echo "  4. Initialize database (if using local PostgreSQL):"
    echo "     make migrate"
    echo "     make seed"
    echo ""
    echo "  5. Run the application:"
    echo "     uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
    echo ""
    echo "  6. Run Celery worker (in another terminal):"
    echo "     celery -A app.celery_app worker --loglevel=info"
    echo ""
    echo "For Docker-based development, use:"
    echo "  make build && make up"
}

# Main execution
main() {
    log_info "Starting development setup..."
    echo ""
    
    check_python
    check_disk_space
    create_venv
    install_dependencies
    check_postgres
    print_diagnostics
    
    log_info "Setup complete!"
}

main "$@"

