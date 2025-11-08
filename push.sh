#!/bin/bash

# 🚀 One-Click Git Push Script (for VisualAid-Full-English)
# Automatically commits, ignores heavy folders, and pushes to GitHub using HTTPS.

# ---- Step 1: Your GitHub repo URL (HTTPS version) ----
REPO_URL="https://github.com/tyagishubh-collab/Evara-AI.git"

# ---- Step 2: Setup and Safety Checks ----
echo "🔍 Checking Git repository..."
if [ ! -d ".git" ]; then
  echo "🆕 No git repo found — initializing one."
  git init
  git remote add origin "$REPO_URL"
else
  echo "✅ Existing git repo detected."
fi

# ---- Step 3: Ignore heavy and unnecessary folders ----
echo "🧹 Updating .gitignore..."
cat > .gitignore <<EOL
venv/
__pycache__/
.DS_Store
*.pyc
*.pyo
*.pyd
*.log
.env
EOL

# ---- Step 4: Add and Commit ----
echo "📤 Adding and committing changes..."
git add .
if git diff --cached --quiet; then
  echo "⚠️ No new changes to commit."
else
  git commit -m "Automated commit from push.sh"
fi

# ---- Step 5: Push to GitHub ----
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main || echo "⚠️ Push failed — check your GitHub access or token."

echo "✅ Done! Your project is now up on GitHub."
