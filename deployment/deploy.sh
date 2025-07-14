#!/bin/bash

# Google Cloud Run Deployment Script
set -e

# Configuration
PROJECT_ID="emergent-poc"      # Your actual project ID
REGION="us-central1"           # Update this if you prefer different region
BACKEND_SERVICE="chatgpt-backend"
FRONTEND_SERVICE="chatgpt-frontend"

echo "🚀 Deploying to Google Cloud Run..."

# Build and deploy backend
echo "📦 Building and deploying backend..."
gcloud builds submit backend/ \
  --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE \
  --dockerfile deployment/Dockerfile.backend

gcloud run deploy $BACKEND_SERVICE \
  --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --set-env-vars="ENVIRONMENT=production"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --format="value(status.url)")
echo "Backend deployed at: $BACKEND_URL"

# Update frontend environment variable
echo "REACT_APP_BACKEND_URL=$BACKEND_URL" > frontend/.env.production

# Build and deploy frontend
echo "📦 Building and deploying frontend..."
gcloud builds submit . \
  --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE \
  --dockerfile deployment/Dockerfile.frontend

gcloud run deploy $FRONTEND_SERVICE \
  --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo ""
echo "⚠️  Next steps:"
echo "1. Update Google OAuth redirect URIs with: $FRONTEND_URL"
echo "2. Set up MongoDB Atlas and update connection string"
echo "3. Configure environment variables in Cloud Run"