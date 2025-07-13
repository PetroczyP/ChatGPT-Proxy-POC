#!/bin/bash

# GitHub Publishing Script for ChatGPT Proxy POC App
# Replace YOUR_USERNAME with your actual GitHub username

echo "🚀 Publishing ChatGPT Proxy POC App to GitHub..."

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the app root directory"
    exit 1
fi

# Get GitHub username from user
echo "Please enter your GitHub username:"
read GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub username cannot be empty"
    exit 1
fi

# Repository URL
REPO_URL="https://github.com/${GITHUB_USERNAME}/chatgpt-proxy-poc.git"

echo "📋 Repository URL: $REPO_URL"
echo "📋 Make sure you've created the repository on GitHub first!"
echo ""

# Remove any existing origin remote
git remote remove origin 2>/dev/null || true

# Add the GitHub repository as remote origin
echo "🔗 Adding GitHub remote..."
git remote add origin "$REPO_URL"

# Verify remote was added
echo "✅ Remote added:"
git remote -v

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Successfully published to GitHub!"
    echo "🌐 Your repository is now available at:"
    echo "   https://github.com/${GITHUB_USERNAME}/chatgpt-proxy-poc"
    echo ""
    echo "✅ What's included:"
    echo "   - Complete ChatGPT Proxy POC application"
    echo "   - Google OAuth authentication"
    echo "   - Admin panel with API key management"
    echo "   - Google Cloud deployment scripts"
    echo "   - Comprehensive documentation"
    echo "   - Docker setup for development"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Visit your GitHub repository"
    echo "   2. Verify the README.md displays properly"
    echo "   3. Consider starring your own repo! ⭐"
    echo "   4. Share it with others or deploy to Google Cloud"
else
    echo ""
    echo "❌ Error pushing to GitHub. Please check:"
    echo "   1. Repository exists on GitHub"
    echo "   2. Repository name is exactly: chatgpt-proxy-poc"
    echo "   3. You have push access to the repository"
    echo "   4. Your GitHub authentication is set up"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - Make sure you created the repository on GitHub first"
    echo "   - Check if you need to authenticate with GitHub"
    echo "   - Verify the repository URL is correct"
fi