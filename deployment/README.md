# Complete Google Cloud Deployment Guide

## Prerequisites
1. Google Cloud account with billing enabled
2. Google Cloud SDK installed locally
3. MongoDB Atlas account (free tier available)
4. Domain name (optional, for custom domain)

## Step 1: Initial Setup

### 1.1 Create Google Cloud Project
```bash
# Create a new project
gcloud projects create your-chatgpt-app --name="ChatGPT Web App"

# Set as default project
gcloud config set project your-chatgpt-app

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### 1.2 Run Setup Script
```bash
chmod +x deployment/gcloud-setup.sh
./deployment/gcloud-setup.sh
```

## Step 2: Database Setup (MongoDB Atlas)

### 2.1 Create MongoDB Atlas Cluster
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free account and cluster
3. Create database user
4. Whitelist IP addresses (0.0.0.0/0 for Cloud Run)
5. Get connection string

### 2.2 Update Connection String
```bash
# EXAMPLE connection string format (replace with your actual values):
# mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/chatgpt-app

# Your actual connection string will look like:
# mongodb+srv://myuser:mypassword@mycluster.abc123.mongodb.net/chatgpt-app
```

## Step 3: OAuth Configuration

### 3.1 Update Google OAuth Settings
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Update your OAuth 2.0 client:
   - Authorized JavaScript origins: `https://your-domain.com`
   - Authorized redirect URIs: `https://your-domain.com/auth/google`

## Step 4: Deploy to Cloud Run

### 4.1 Update Configuration
```bash
# Edit deployment/deploy.sh
PROJECT_ID="your-actual-project-id"
REGION="your-preferred-region"  # e.g., us-central1, europe-west1
```

### 4.2 Deploy Services
```bash
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### 4.3 Set Environment Variables
```bash
# Set backend environment variables (replace with your actual values)
gcloud run services update chatgpt-backend \
  --set-env-vars="MONGO_URL=YOUR_MONGODB_CONNECTION_STRING,DB_NAME=chatgpt_production,GOOGLE_CLIENT_ID=YOUR_CLIENT_ID,GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET,OPENAI_API_KEY=YOUR_OPENAI_KEY,ADMIN_EMAILS=admin@yourdomain.com" \
  --region=us-central1
```

## Step 5: Custom Domain (Optional)

### 5.1 Set up Custom Domain
```bash
# Map domain to Cloud Run service
gcloud run domain-mappings create \
  --service=chatgpt-frontend \
  --domain=yourdomain.com \
  --region=us-central1

# Update DNS records as instructed by Cloud Run
```

## Step 6: Security & Monitoring

### 6.1 Set up Secret Manager
```bash
# Store sensitive data in Secret Manager (replace with your actual keys)
echo "YOUR_ACTUAL_OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
echo "YOUR_ACTUAL_GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret --data-file=-

# Update Cloud Run to use secrets
gcloud run services update chatgpt-backend \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest" \
  --region=us-central1
```

### 6.2 Enable Monitoring
```bash
# Enable monitoring and logging
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

## Step 7: Continuous Deployment (Optional)

### 7.1 Set up Cloud Build Trigger
1. Go to [Cloud Build Console](https://console.cloud.google.com/cloud-build)
2. Create trigger connected to your GitHub/GitLab repository
3. Use `deployment/cloudbuild.yaml` configuration

## Cost Optimization Tips

1. **Cloud Run**: Only pay for requests, automatically scales to zero
2. **MongoDB Atlas**: Use free tier (512MB) for testing
3. **Load Balancer**: Consider using Cloud Run's built-in HTTPS
4. **Monitoring**: Use free tier limits

## Troubleshooting

### Common Issues:
1. **OAuth errors**: Update redirect URIs in Google Console
2. **Database connection**: Check MongoDB Atlas IP whitelist
3. **CORS errors**: Verify frontend/backend URLs match
4. **Environment variables**: Use Cloud Run console to verify settings

### Useful Commands:
```bash
# View service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=chatgpt-backend"

# Check service status
gcloud run services describe chatgpt-backend --region=us-central1

# Update service
gcloud run services update chatgpt-backend --set-env-vars="KEY=value" --region=us-central1
```

## Production Checklist

- [ ] MongoDB Atlas cluster created and configured
- [ ] Google OAuth credentials updated with production URLs
- [ ] Environment variables set in Cloud Run
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Monitoring and logging enabled
- [ ] Admin emails configured
- [ ] API keys stored securely

## Estimated Costs (Monthly)

- **Small usage** (< 1000 requests/month): $0-10
- **Medium usage** (< 10,000 requests/month): $10-30
- **Large usage** (< 100,000 requests/month): $30-100

The serverless nature of Cloud Run makes this very cost-effective for most use cases!