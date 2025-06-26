#!/bin/bash

# Deployment script for ITP Data Platform
# Usage: ./deploy.sh [environment] [component]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-"dev"}
COMPONENT=${2:-"all"}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${BLUE}🚀 Deploying ITP Data Platform...${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Component: ${GREEN}$COMPONENT${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid environments: dev, staging, prod"
    exit 1
fi

# Set environment-specific variables
case $ENVIRONMENT in
    "dev")
        PROJECT_ID="itp-data-platform-dev"
        ;;
    "staging")
        PROJECT_ID="itp-data-platform-staging"
        ;;
    "prod")
        PROJECT_ID="itp-data-platform-prod"
        ;;
esac

echo -e "Project ID: ${GREEN}$PROJECT_ID${NC}"

# Functions
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is required but not installed${NC}"
        exit 1
    fi
    
    # Check terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is required but not installed${NC}"
        exit 1
    fi
    
    # Check dbt
    if ! command -v dbt &> /dev/null; then
        echo -e "${RED}❌ dbt is required but not installed${NC}"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ Not authenticated with gcloud${NC}"
        echo "Run: gcloud auth login"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

deploy_infrastructure() {
    echo -e "${BLUE}🏗️ Deploying infrastructure...${NC}"
    
    cd "$PROJECT_ROOT/infrastructure/terraform/environments/$ENVIRONMENT"
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    echo -e "${YELLOW}📋 Planning infrastructure changes...${NC}"
    terraform plan -out=tfplan
    
    # Apply changes
    echo -e "${YELLOW}⚡ Applying infrastructure changes...${NC}"
    terraform apply tfplan
    
    # Clean up plan file
    rm -f tfplan
    
    echo -e "${GREEN}✅ Infrastructure deployment completed${NC}"
}

deploy_functions() {
    echo -e "${BLUE}⚡ Deploying Cloud Functions...${NC}"
    
    cd "$PROJECT_ROOT/data-pipelines"
    
    # Create deployment package
    echo -e "${YELLOW}📦 Creating deployment packages...${NC}"
    
    # Financial ingestion function
    mkdir -p dist/financial-ingestion
    cp -r src/ingestion/financial_systems/* dist/financial-ingestion/
    cp requirements.txt dist/financial-ingestion/
    
    cd dist/financial-ingestion
    zip -r ../financial-ingestion.zip .
    cd ../..
    
    # Upload to Cloud Storage
    gsutil cp dist/financial-ingestion.zip gs://$PROJECT_ID-$ENVIRONMENT-functions-source/
    
    # Deploy function
    gcloud functions deploy $ENVIRONMENT-financial-ingestion \
        --runtime python39 \
        --trigger-topic $ENVIRONMENT-financial-trigger \
        --source gs://$PROJECT_ID-$ENVIRONMENT-functions-source/financial-ingestion.zip \
        --entry-point main \
        --project $PROJECT_ID
    
    echo -e "${GREEN}✅ Cloud Functions deployment completed${NC}"
}

deploy_dbt() {
    echo -e "${BLUE}📊 Deploying dbt models...${NC}"
    
    cd "$PROJECT_ROOT/dbt-models"
    
    # Install dependencies
    dbt deps
    
    # Run models
    echo -e "${YELLOW}🔄 Running dbt models...${NC}"
    dbt run --target $ENVIRONMENT
    
    # Run tests
    echo -e "${YELLOW}🧪 Running dbt tests...${NC}"
    dbt test --target $ENVIRONMENT
    
    # Generate documentation
    echo -e "${YELLOW}📚 Generating documentation...${NC}"
    dbt docs generate --target $ENVIRONMENT
    
    echo -e "${GREEN}✅ dbt deployment completed${NC}"
}

deploy_monitoring() {
    echo -e "${BLUE}📊 Deploying monitoring configuration...${NC}"
    
    # Deploy custom metrics
    python3 "$PROJECT_ROOT/scripts/deploy-monitoring.py" --environment $ENVIRONMENT
    
    # Create dashboards
    gcloud monitoring dashboards create \
        --config-from-file="$PROJECT_ROOT/monitoring/dashboards/operational/data_platform_ops.json" \
        --project $PROJECT_ID
    
    echo -e "${GREEN}✅ Monitoring deployment completed${NC}"
}

run_health_checks() {
    echo -e "${BLUE}🏥 Running health checks...${NC}"
    
    # Test BigQuery connectivity
    echo -e "${YELLOW}Testing BigQuery...${NC}"
    bq ls --project_id=$PROJECT_ID > /dev/null
    
    # Test Cloud Functions
    echo -e "${YELLOW}Testing Cloud Functions...${NC}"
    gcloud functions list --project=$PROJECT_ID | grep -q "$ENVIRONMENT-financial-ingestion"
    
    # Test dbt models
    echo -e "${YELLOW}Testing dbt models...${NC}"
    cd "$PROJECT_ROOT/dbt-models"
    dbt test --target $ENVIRONMENT --select tag:health_check
    
    echo -e "${GREEN}✅ Health checks passed${NC}"
}

# Main deployment logic
main() {
    check_prerequisites
    
    case $COMPONENT in
        "infrastructure"|"infra")
            deploy_infrastructure
            ;;
        "functions")
            deploy_functions
            ;;
        "dbt")
            deploy_dbt
            ;;
        "monitoring")
            deploy_monitoring
            ;;
        "all")
            deploy_infrastructure
            deploy_functions
            deploy_dbt
            deploy_monitoring
            run_health_checks
            ;;
        *)
            echo -e "${RED}❌ Invalid component: $COMPONENT${NC}"
            echo "Valid components: infrastructure, functions, dbt, monitoring, all"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    
    # Show next steps
    echo -e "\n${BLUE}📋 Next Steps:${NC}"
    echo -e "1. Monitor dashboards: https://console.cloud.google.com/monitoring/dashboards"
    echo -e "2. Check data freshness: Run data quality checks"
    echo -e "3. Verify pipelines: Check Cloud Functions logs"
    echo -e "4. Review costs: Monitor BigQuery and storage usage"
}

# Run main function
main "$@"
