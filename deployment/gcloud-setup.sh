#!/bin/bash

# Google Cloud Deployment Setup Script
# Run this script to set up your GCP project for deployment

echo "🚀 Setting up Google Cloud deployment..."

# Set your project variables
PROJECT_ID="your-chatgpt-app"  # Change this to your desired project ID
REGION="us-central1"           # Change to your preferred region
SERVICE_NAME="chatgpt-web-app"

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable dns.googleapis.com

# Set default configurations
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

echo "✅ Google Cloud setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up MongoDB Atlas account"
echo "2. Update OAuth redirect URIs"
echo "3. Deploy services"