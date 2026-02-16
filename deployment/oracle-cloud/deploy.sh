#!/bin/bash
#
# Deploy Script - Install Python dependencies
# Run this after cloning the repository
#
# Usage: bash deploy.sh
#

set -e  # Exit on error

echo "========================================="
echo "Deploying Cloud Agent - Installing Dependencies"
echo "========================================="
echo ""

# Check if running from project root
if [ ! -f "requirements.txt" ]; then
  echo "❌ Error: requirements.txt not found"
  echo "Please run this script from the project root directory"
  exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
  echo "❌ Error: Python $REQUIRED_VERSION+ required, found $PYTHON_VERSION"
  exit 1
fi

echo "✓ Python version: $(python3 --version)"

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Verify agent_skills installed
echo "✅ Verifying agent_skills..."
python -c "import agent_skills; print('✓ agent_skills imported successfully')"

# Check if .env.cloud exists
if [ ! -f ".env.cloud" ]; then
  echo ""
  echo "⚠️ Warning: .env.cloud not found"
  echo "Creating from .env.cloud.example..."
  cp .env.cloud.example .env.cloud
  chmod 600 .env.cloud
  echo "✓ Created .env.cloud (chmod 600)"
  echo ""
  echo "📝 Next step: Edit .env.cloud with your configuration:"
  echo "   - Set VAULT_PATH"
  echo "   - Set GIT_REMOTE_URL"
  echo "   - Set CLAUDE_API_KEY"
  echo "   - Set WHATSAPP_NOTIFICATION_NUMBER"
fi

# Check if vault exists
if [ ! -d "vault" ]; then
  echo ""
  echo "⚠️ Warning: vault/ directory not found"
  echo "You need to either:"
  echo "   1. Clone vault: git clone git@github.com:user/vault.git"
  echo "   2. Or create new vault structure"
fi

echo ""
echo "========================================="
echo "✅ Dependencies installed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure .env.cloud"
echo "2. Setup vault (clone or create)"
echo "3. Run start.sh to start Cloud Agent with PM2"
echo ""
