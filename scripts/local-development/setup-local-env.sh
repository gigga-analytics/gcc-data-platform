#!/bin/bash

# Local Development Environment Setup Script
# Sets up everything needed for local development of ITP Data Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up ITP Data Platform Local Development Environment...${NC}"

# Check operating system
OS="$(uname -s)"
echo -e "Operating System: ${GREEN}$OS${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python dependencies
install_python_deps() {
    echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
    
    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
        echo -e "Python version: ${GREEN}$PYTHON_VERSION${NC}"
        
        if [[ ! "$PYTHON_VERSION" =~ ^3\.[9-11] ]]; then
            echo -e "${RED}⚠️  Python 3.9+ required, found $PYTHON_VERSION${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install data pipeline dependencies
    echo -e "${YELLOW}Installing data pipeline dependencies...${NC}"
    pip install -r data-pipelines/requirements.txt
    
    # Install dbt
    echo -e "${YELLOW}Installing dbt...${NC}"
    pip install dbt-bigquery
    
    echo -e "${GREEN}✅ Python environment setup complete${NC}"
}

# Function to install Google Cloud SDK
install_gcloud() {
    echo -e "${BLUE}☁️ Setting up Google Cloud SDK...${NC}"
    
    if command_exists gcloud; then
        echo -e "${GREEN}✅ Google Cloud SDK already installed${NC}"
        gcloud version
    else
        echo -e "${YELLOW}Installing Google Cloud SDK...${NC}"
        
        case $OS in
            "Linux")
                curl https://sdk.cloud.google.com | bash
                exec -l $SHELL
                ;;
            "Darwin")
                if command_exists brew; then
                    brew install --cask google-cloud-sdk
                else
                    echo -e "${RED}Please install Homebrew first or download gcloud manually${NC}"
                    exit 1
                fi
                ;;
            *)
                echo -e "${RED}Please install Google Cloud SDK manually for $OS${NC}"
                exit 1
                ;;
        esac
    fi
    
    # Initialize gcloud if not already done
    if [ ! -f "$HOME/.config/gcloud/configurations/config_default" ]; then
        echo -e "${YELLOW}Initializing gcloud...${NC}"
        gcloud init
    fi
}

# Function to install Terraform
install_terraform() {
    echo -e "${BLUE}🏗️ Setting up Terraform...${NC}"
    
    if command_exists terraform; then
        TERRAFORM_VERSION=$(terraform --version | head -n1 | cut -d ' ' -f 2)
        echo -e "Terraform version: ${GREEN}$TERRAFORM_VERSION${NC}"
    else
        echo -e "${YELLOW}Installing Terraform...${NC}"
        
        case $OS in
            "Linux")
                wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
                echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
                sudo apt update && sudo apt install terraform
                ;;
            "Darwin")
                if command_exists brew; then
                    brew tap hashicorp/tap
                    brew install hashicorp/tap/terraform
                else
                    echo -e "${RED}Please install Homebrew first or download Terraform manually${NC}"
                    exit 1
                fi
                ;;
            *)
                echo -e "${RED}Please install Terraform manually for $OS${NC}"
                exit 1
                ;;
        esac
    fi
}

# Function to setup Docker (optional for local testing)
setup_docker() {
    echo -e "${BLUE}🐳 Checking Docker setup...${NC}"
    
    if command_exists docker; then
        echo -e "${GREEN}✅ Docker already installed${NC}"
        docker --version
    else
        echo -e "${YELLOW}Docker not found. Install Docker for local container testing.${NC}"
        echo -e "Visit: https://docs.docker.com/get-docker/"
    fi
}

# Function to setup environment variables
setup_env_vars() {
    echo -e "${BLUE}⚙️ Setting up environment variables...${NC}"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# ITP Data Platform Environment Variables
# Copy this file and update with your actual values

# Google Cloud Project Settings
PROJECT_ID=itp-data-platform-dev
REGION=europe-west1
DATASET_PREFIX=dev

# BigQuery Settings
BQ_LOCATION=EU

# Development Settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# API Keys and Secrets (use Google Secret Manager in production)
# ERP_API_KEY=your-erp-api-key
# CRM_API_KEY=your-crm-api-key
# SLACK_WEBHOOK_URL=your-slack-webhook

# Local Development Only
LOCAL_DEVELOPMENT=true
SKIP_AUTH_CHECK=false
EOF
        echo -e "${GREEN}✅ Created .env file template${NC}"
        echo -e "${YELLOW}⚠️  Please update .env file with your actual values${NC}"
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
    
    # Create local configuration for dbt
    if [ ! -d "$HOME/.dbt" ]; then
        mkdir -p "$HOME/.dbt"
    fi
    
    if [ ! -f "$HOME/.dbt/profiles.yml" ]; then
        cat > "$HOME/.dbt/profiles.yml" << 'EOF'
itp_data_platform:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: itp-data-platform-dev
      dataset: dev_analytics
      threads: 4
      timeout_seconds: 300
      location: EU
      priority: interactive
EOF
        echo -e "${GREEN}✅ Created dbt profiles.yml${NC}"
    fi
}

# Function to validate setup
validate_setup() {
    echo -e "${BLUE}🔍 Validating setup...${NC}"
    
    # Check Python environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        
        echo -e "${YELLOW}Testing Python imports...${NC}"
        python3 -c "
import google.cloud.bigquery
import pandas as pd
import dbt
print('✅ All Python packages imported successfully')
"
    else
        echo -e "${RED}❌ Python virtual environment not found${NC}"
        exit 1
    fi
    
    # Check gcloud authentication
    echo -e "${YELLOW}Checking gcloud authentication...${NC}"
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${GREEN}✅ gcloud authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  gcloud not authenticated. Run: gcloud auth login${NC}"
    fi
    
    # Check Terraform
    echo -e "${YELLOW}Checking Terraform...${NC}"
    if terraform version > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Terraform working${NC}"
    else
        echo -e "${RED}❌ Terraform not working${NC}"
    fi
}

# Function to setup pre-commit hooks
setup_pre_commit() {
    echo -e "${BLUE}🔧 Setting up pre-commit hooks...${NC}"
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        
        # Install pre-commit
        pip install pre-commit
        
        # Create pre-commit config
        cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        files: ^data-pipelines/
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        files: ^data-pipelines/
        
  - repo: https://github.com/terraform-docs/terraform-docs
    rev: v0.16.0
    hooks:
      - id: terraform-docs-go
        args: ["markdown", "table", "--output-file", "README.md", "./infrastructure/terraform"]
EOF
        
        # Install the git hooks
        pre-commit install
        
        echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
    fi
}

# Function to create useful aliases and scripts
create_dev_shortcuts() {
    echo -e "${BLUE}⚡ Creating development shortcuts...${NC}"
    
    # Create useful development scripts
    mkdir -p scripts/dev
    
    # Quick environment activation script
    cat > scripts/dev/activate.sh << 'EOF'
#!/bin/bash
# Quick activation script for development environment

source venv/bin/activate
source .env

echo "🚀 ITP Data Platform Development Environment Activated"
echo "Python: $(python --version)"
echo "Project: $PROJECT_ID"
echo ""
echo "Available commands:"
echo "  make test          - Run all tests"
echo "  make lint          - Run linting"
echo "  make dbt-run       - Run dbt models"
echo "  make deploy-dev    - Deploy to development"
EOF
    chmod +x scripts/dev/activate.sh
    
    # Quick test script
    cat > scripts/dev/test-pipeline.sh << 'EOF'
#!/bin/bash
# Quick pipeline test script

set -e

echo "🧪 Running pipeline tests..."

# Activate environment
source venv/bin/activate
source .env

# Run Python tests
echo "Running Python unit tests..."
cd data-pipelines
python -m pytest tests/unit/ -v

# Run integration tests (if environment allows)
if [ "$RUN_INTEGRATION_TESTS" = "true" ]; then
    echo "Running integration tests..."
    python -m pytest tests/integration/ -v
fi

# Test dbt models
echo "Testing dbt models..."
cd ../dbt-models
dbt test --target dev

echo "✅ All tests passed!"
EOF
    chmod +x scripts/dev/test-pipeline.sh
    
    echo -e "${GREEN}✅ Development shortcuts created${NC}"
}

# Main setup function
main() {
    echo -e "${BLUE}Starting setup process...${NC}"
    
    # Install core dependencies
    install_python_deps
    install_gcloud
    install_terraform
    setup_docker
    
    # Setup configuration
    setup_env_vars
    
    # Setup development tools
    setup_pre_commit
    create_dev_shortcuts
    
    # Validate everything works
    validate_setup
    
    echo -e "\n${GREEN}🎉 Setup complete!${NC}"
    echo -e "\n${BLUE}Next steps:${NC}"
    echo -e "1. Update .env file with your project settings"
    echo -e "2. Run: ${YELLOW}gcloud auth login${NC}"
    echo -e "3. Run: ${YELLOW}gcloud auth application-default login${NC}"
    echo -e "4. Activate environment: ${YELLOW}source scripts/dev/activate.sh${NC}"
    echo -e "5. Test setup: ${YELLOW}./scripts/dev/test-pipeline.sh${NC}"
    echo -e "\n${GREEN}Happy coding! 🚀${NC}"
}

# Run main function
main "$@"