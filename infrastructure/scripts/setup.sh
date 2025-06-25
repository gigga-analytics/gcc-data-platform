#!/bin/bash

# Initial setup script for ITP Data Platform

set -e

echo "🚀 Setting up ITP Data Platform..."

# Check prerequisites
command -v gcloud >/dev/null 2>&1 || { echo "gcloud CLI is required but not installed."; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "Terraform is required but not installed."; exit 1; }

# Set variables
PROJECT_ID=${1:-"itp-data-platform-dev"}
REGION=${2:-"europe-west1"}

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Enable required APIs
echo "Enabling GCP APIs..."
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID
gcloud services enable dataflow.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable monitoring.googleapis.com --project=$PROJECT_ID

# Create Terraform state bucket
echo "Creating Terraform state bucket..."
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-terraform-state

# Initialize Terraform
echo "Initializing Terraform..."
cd ../terraform/environments/dev
terraform init

echo "✅ Setup complete!"
echo "Next steps:"
echo "1. Configure terraform.tfvars"
echo "2. Run terraform plan"
echo "3. Run terraform apply"