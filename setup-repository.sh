#!/bin/bash

# In The Pocket - Data Platform Repository Setup Script
# Elite Strategic Data Engineering Solution
# Run this script to create the complete repository structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project name
PROJECT_NAME="itp-data-platform"

echo -e "${BLUE}🚀 Setting up In The Pocket Data Platform Repository...${NC}"

# Create main project directory
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

echo -e "${GREEN}📁 Creating directory structure...${NC}"

# Create all directories
mkdir -p .github/workflows
mkdir -p infrastructure/terraform/{environments/{dev,staging,prod},modules/{bigquery,storage,dataflow,functions,monitoring,iam}}
mkdir -p infrastructure/scripts
mkdir -p data-pipelines/src/{ingestion/{financial_systems,crm_erp,marketing},transformation/{staging,intermediate,marts},utils}
mkdir -p data-pipelines/sql/{staging,intermediate,marts/{finance,operations,executive}}
mkdir -p data-pipelines/{config,tests/{unit,integration,data_quality}}
mkdir -p dbt-models/{models/{staging,intermediate,marts},macros,tests,docs}
mkdir -p monitoring/{dashboards/{operational,business},alerts,slo}
mkdir -p docs/{architecture/{decision-records,diagrams,specifications},runbooks,governance,user-guides}
mkdir -p scripts/{local-development,data-migration,utilities}

echo -e "${GREEN}✅ Repository structure created successfully!${NC}"
echo -e "${BLUE}📁 Created directories: $(find . -type d | wc -l)${NC}"

echo -e "\n${YELLOW}🚀 Next Steps:${NC}"
echo -e "1. ${GREEN}cd $PROJECT_NAME${NC}"
echo -e "2. ${GREEN}Copy all file contents from the repository package${NC}"
echo -e "3. ${GREEN}git init${NC}"
echo -e "4. ${GREEN}git add .${NC}"
echo -e "5. ${GREEN}git commit -m 'Initial data platform setup'${NC}"
echo -e "6. ${GREEN}./infrastructure/scripts/setup.sh ${NC}"

echo -e "\n${GREEN}🎉 Elite Data Platform Repository Ready!${NC}"