#!/bin/bash

# Deployment script for Hugging Face Spaces
# This script helps you deploy the NL2SQL app to Hugging Face

set -e  # Exit on error

echo "🚀 NL2SQL Hugging Face Deployment Helper"
echo "========================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Add .gitignore if needed
if [ ! -f ".gitignore" ]; then
    echo "⚠️  .gitignore not found! Creating one..."
    cat > .gitignore << 'EOF'
# Environment
.env
venv/
myvenv/
env/
*.pyc
__pycache__/

# Logs
audit_logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
    echo "✅ .gitignore created"
fi

echo ""
echo "📝 Please provide your Hugging Face Space details:"
echo ""

# Get username
read -p "Hugging Face username: " HF_USERNAME
if [ -z "$HF_USERNAME" ]; then
    echo "❌ Username cannot be empty"
    exit 1
fi

# Get space name
read -p "Space name (e.g., nl2sql-query-system): " SPACE_NAME
if [ -z "$SPACE_NAME" ]; then
    echo "❌ Space name cannot be empty"
    exit 1
fi

# Construct HF repo URL
HF_REPO="https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

echo ""
echo "🔗 Hugging Face Space URL: $HF_REPO"
echo ""

# Check if remote already exists
if git remote get-url hf &> /dev/null; then
    echo "⚠️  'hf' remote already exists. Updating..."
    git remote set-url hf "$HF_REPO"
else
    echo "Adding Hugging Face as remote..."
    git remote add hf "$HF_REPO"
fi

echo "✅ Remote 'hf' configured"
echo ""

# Stage all files
echo "📦 Staging files..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "⚠️  No changes to commit"
else
    # Get commit message
    read -p "Commit message (or press Enter for default): " COMMIT_MSG
    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="Deploy NL2SQL app to Hugging Face Spaces"
    fi
    
    echo "💾 Committing changes..."
    git commit -m "$COMMIT_MSG"
    echo "✅ Changes committed"
fi

echo ""
echo "🚀 Ready to push to Hugging Face!"
echo ""
echo "⚠️  IMPORTANT: Before pushing, make sure you have:"
echo "   1. Created the Space on huggingface.co/spaces"
echo "   2. Set all required secrets in Space Settings → Repository secrets"
echo ""
echo "Required secrets:"
echo "   - NEON_READONLY_CONNECTION_STRING"
echo "   - NEON_DBA_CONNECTION_STRING"
echo "   - GROQ_API_KEY"
echo "   - CLOUDFLARE_ACCOUNT_ID"
echo "   - CLOUDFLARE_AUTH_TOKEN"
echo "   - UPSTASH_VECTOR_URL"
echo "   - UPSTASH_VECTOR_TOKEN"
echo "   - DBA_PASSWORD"
echo ""

read -p "Have you set all secrets? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo "⏸️  Deployment paused. Please set secrets first:"
    echo "   Go to: $HF_REPO/settings"
    echo "   Add each secret under 'Repository secrets'"
    echo ""
    echo "Then run this script again."
    exit 0
fi

echo ""
echo "🚀 Pushing to Hugging Face..."
echo ""

# Try to push
if git push hf main; then
    echo ""
    echo "✅ Successfully deployed to Hugging Face!"
    echo ""
    echo "🎉 Your app will be available at:"
    echo "   $HF_REPO"
    echo ""
    echo "📊 Monitor deployment progress:"
    echo "   - Go to the URL above"
    echo "   - Click on 'Logs' tab to see build progress"
    echo ""
    echo "⏱️  Initial deployment may take 2-3 minutes"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Common solutions:"
    echo "1. Make sure you've created the Space on huggingface.co"
    echo "2. Check your authentication (username and token)"
    echo "3. Generate a token at: https://huggingface.co/settings/tokens"
    echo "4. Use your token as password when git prompts"
    echo ""
    echo "Try again with:"
    echo "   git push hf main"
fi

echo ""
echo "📚 For more help, check:"
echo "   - DEPLOYMENT_CHECKLIST.md"
echo "   - huggingface_deployment.md"
